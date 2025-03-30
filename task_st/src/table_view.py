import streamlit as st
import os
import json
from .utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .task_runner import run_task_via_cmd
from .common import render_batch_operations

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    st.markdown("### 任务列表")
    
    # 检查是否有AgGrid可用，如果有则使用AgGrid
    if HAS_AGGRID:
        render_aggrid_table(filtered_df, current_taskfile)
    else:
        render_standard_table(filtered_df, current_taskfile)
    
    # 批量操作部分 - 这部分对两种表格视图都适用
    render_batch_operations(current_taskfile, view_key="table")

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格"""
    # 准备表格数据
    # 添加工具列方便用户进行操作
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # 为每个任务添加一个按钮列
    filtered_df_copy['buttons'] = '操作'
    
    # 只显示需要的列
    display_cols = ['name', 'emoji', 'description', 'tags_str', 'directory', 'buttons']
    filtered_df_display = filtered_df_copy[display_cols]
    
    # 配置AgGrid
    gb = GridOptionsBuilder.from_dataframe(filtered_df_display)
    
    # 设置列属性
    gb.configure_column('name', header_name="任务名称", width=150)
    gb.configure_column('emoji', header_name="图标", width=70)
    gb.configure_column('description', header_name="描述", width=300)
    gb.configure_column('tags_str', header_name="标签", width=150)
    gb.configure_column('directory', header_name="目录", width=200)
    
    # 添加自定义按钮渲染器
    btn_renderer = JsCode("""
    function(params) {
        var task = params.data.name;
        return `
            <div style="display: flex; gap: 5px;">
                <button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px;"
                    onclick="document.dispatchEvent(new CustomEvent('run_task', {detail: {task: '${task}'}}))">
                    运行
                </button>
                <button style="background-color: #2196F3; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px;"
                    onclick="document.dispatchEvent(new CustomEvent('open_files', {detail: {task: '${task}'}}))">
                    文件
                </button>
                <button style="background-color: #9E9E9E; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px;"
                    onclick="document.dispatchEvent(new CustomEvent('copy_cmd', {detail: {task: '${task}'}}))">
                    复制
                </button>
            </div>
        `;
    }
    """)
    
    # 配置按钮列
    gb.configure_column(
        'buttons',
        header_name="操作",
        cellRenderer=btn_renderer,
        width=200
    )
    
    # 配置多选模式和排序
    gb.configure_selection(selection_mode='multiple', use_checkbox=True, pre_selected_rows=[])
    gb.configure_grid_options(domLayout='normal')
    gb.configure_default_column(sortable=True, filterable=True)
    
    # 添加事件回调
    js_event_handlers = JsCode("""
    function(e) {
        if (!window.taskEventsAttached) {
            window.taskEventsAttached = true;
            
            document.addEventListener('run_task', function(e) {
                const task = e.detail.task;
                const data = {
                    type: 'run_task',
                    task: task
                };
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: JSON.stringify(data)
                }, "*");
            });
            
            document.addEventListener('open_files', function(e) {
                const task = e.detail.task;
                const data = {
                    type: 'open_files',
                    task: task
                };
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: JSON.stringify(data)
                }, "*");
            });
            
            document.addEventListener('copy_cmd', function(e) {
                const task = e.detail.task;
                const data = {
                    type: 'copy_cmd',
                    task: task
                };
                window.parent.postMessage({
                    type: "streamlit:setComponentValue",
                    value: JSON.stringify(data)
                }, "*");
            });
        }
    }
    """)
    
    # 应用设置
    grid_options = gb.build()
    grid_options['onGridReady'] = js_event_handlers
    
    # 显示表格
    response = AgGrid(
        filtered_df_display,
        gridOptions=grid_options,
        height=500,
        fit_columns_on_grid_load=True,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        custom_css={
            ".ag-cell-value": {"display": "flex", "align-items": "center"},
            ".ag-header-cell-text": {"color": "#1D5077", "font-weight": "bold"}
        },
        key="task_grid"
    )
    
    # 处理选中的行
    selected_rows = response.get('selected_rows', [])
    if len(selected_rows) > 0:
        # 更新会话状态中的选择
        selected_names = [row.get('name') for row in selected_rows]
        st.session_state.selected_tasks = selected_names
    
    # 处理按钮事件
    event_data = response.get('data_changed', None)
    if not event_data:
        custom_value = response.get('custom_value')
        if custom_value:
            try:
                if isinstance(custom_value, str):
                    custom_value = json.loads(custom_value)
                
                event_type = custom_value.get('type')
                task_name = custom_value.get('task')
                
                if event_type == 'run_task' and task_name:
                    with st.spinner(f"正在启动任务 {task_name}..."):
                        result = run_task_via_cmd(task_name, current_taskfile)
                    st.success(f"任务 {task_name} 已在新窗口启动")
                
                elif event_type == 'copy_cmd' and task_name:
                    cmd = get_task_command(task_name, current_taskfile)
                    copy_to_clipboard(cmd)
                    st.success(f"已复制命令: {cmd}")
                
                elif event_type == 'open_files' and task_name:
                    # 获取该任务目录中的文件
                    task_dir = filtered_df[filtered_df['name'] == task_name]['directory'].values[0]
                    if task_dir and os.path.exists(task_dir):
                        files = get_directory_files(task_dir)
                        if files:
                            st.markdown(f"### {task_name} 文件")
                            file_cols = st.columns(min(5, len(files)))
                            for i, file in enumerate(files):
                                with file_cols[i % len(file_cols)]:
                                    file_path = os.path.join(task_dir, file)
                                    if st.button(file, key=f"file_{task_name}_{i}"):
                                        if open_file(file_path):
                                            st.success(f"已打开: {file}")
                        else:
                            st.info(f"任务 {task_name} 目录中没有找到文件")
            except Exception as e:
                st.error(f"处理按钮事件时出错: {str(e)}")

def render_standard_table(filtered_df, current_taskfile):
    """不使用AgGrid，使用标准Streamlit表格组件渲染表格"""
    # 显示命令列
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # 只显示需要的列
    display_cols = ['name', 'emoji', 'description', 'tags_str', 'directory']
    st.dataframe(filtered_df_copy[display_cols], height=400)
    
    # 添加交互式操作，允许选择任务
    st.markdown("#### 选择任务")
    
    # 显示多选框
    col1, col2 = st.columns([1, 1])
    with col1:
        for i, (_, row) in enumerate(filtered_df.iloc[::2].iterrows()):
            task_name = row['name']
            task_selected = st.checkbox(
                f"{row['emoji']} {task_name}", 
                key=f"std_task_{task_name}"
            )
            if task_selected:
                if 'selected_tasks' not in st.session_state:
                    st.session_state.selected_tasks = []
                if task_name not in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.append(task_name)
            elif 'selected_tasks' in st.session_state and task_name in st.session_state.selected_tasks:
                st.session_state.selected_tasks.remove(task_name)
                
    with col2:
        for i, (_, row) in enumerate(filtered_df.iloc[1::2].iterrows()):
            task_name = row['name']
            task_selected = st.checkbox(
                f"{row['emoji']} {task_name}", 
                key=f"std_task_{task_name}"
            )
            if task_selected:
                if 'selected_tasks' not in st.session_state:
                    st.session_state.selected_tasks = []
                if task_name not in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.append(task_name)
            elif 'selected_tasks' in st.session_state and task_name in st.session_state.selected_tasks:
                st.session_state.selected_tasks.remove(task_name)
    
    # 显示任务操作按钮
    st.markdown("#### 任务操作")
    cols = st.columns(3)
    
    # 选择单个任务进行操作
    selected_task = st.selectbox(
        "选择要操作的任务:", 
        options=list(filtered_df['name']),
        key="std_selected_task"
    )
    
    if selected_task:
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button("运行任务", key="std_run_btn"):
                with st.spinner(f"正在启动任务 {selected_task}..."):
                    result = run_task_via_cmd(selected_task, current_taskfile)
                st.success(f"任务 {selected_task} 已在新窗口启动")
        
        with action_cols[1]:
            if st.button("打开文件", key="std_file_btn"):
                task_dir = filtered_df[filtered_df['name'] == selected_task]['directory'].values[0]
                if task_dir and os.path.exists(task_dir):
                    files = get_directory_files(task_dir)
                    if files:
                        st.markdown(f"### {selected_task} 文件")
                        file_cols = st.columns(min(5, len(files)))
                        for i, file in enumerate(files):
                            with file_cols[i % len(file_cols)]:
                                file_path = os.path.join(task_dir, file)
                                if st.button(file, key=f"file_{selected_task}_{i}"):
                                    if open_file(file_path):
                                        st.success(f"已打开: {file}")
                    else:
                        st.info(f"任务 {selected_task} 目录中没有找到文件")
        
        with action_cols[2]:
            if st.button("复制命令", key="std_copy_btn"):
                cmd = get_task_command(selected_task, current_taskfile)
                copy_to_clipboard(cmd)
                st.success(f"已复制命令: {cmd}") 