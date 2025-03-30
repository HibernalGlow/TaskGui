import streamlit as st
from .utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .task_runner import run_task_via_cmd, run_multiple_tasks
import os
import pandas as pd
import json

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
    if selected_rows:
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

def render_card_view(filtered_df, current_taskfile):
    """渲染卡片视图"""
    st.markdown("### 任务卡片")
    
    # 每行显示的卡片数量
    cards_per_row = 3
    
    # 创建行
    for i in range(0, len(filtered_df), cards_per_row):
        cols = st.columns(cards_per_row)
        # 获取当前行的任务
        row_tasks = filtered_df.iloc[i:min(i+cards_per_row, len(filtered_df))]
        
        # 为每个列填充卡片
        for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
            with cols[col_idx]:
                with st.container():
                    # 卡片标题
                    st.markdown(f"### {task['emoji']} {task['name']}")
                    
                    # 描述
                    st.markdown(f"**描述**: {task['description']}")
                    
                    # 标签
                    tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
                    st.markdown(f"**标签**: {tags_str}")
                    
                    # 目录
                    st.markdown(f"**目录**: `{task['directory']}`")
                    
                    # 命令
                    cmd = get_task_command(task['name'], current_taskfile)
                    st.code(cmd, language="bash")
                    
                    # 选择框
                    is_selected = task['name'] in st.session_state.selected_tasks if 'selected_tasks' in st.session_state else False
                    if st.checkbox("选择此任务", value=is_selected, key=f"card_{task['name']}"):
                        if 'selected_tasks' not in st.session_state:
                            st.session_state.selected_tasks = []
                        if task['name'] not in st.session_state.selected_tasks:
                            st.session_state.selected_tasks.append(task['name'])
                    elif 'selected_tasks' in st.session_state and task['name'] in st.session_state.selected_tasks:
                        st.session_state.selected_tasks.remove(task['name'])
                    
                    # 操作按钮
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("运行", key=f"run_card_{task['name']}"):
                            with st.spinner(f"正在启动任务 {task['name']}..."):
                                result = run_task_via_cmd(task['name'], current_taskfile)
                            st.success(f"任务 {task['name']} 已在新窗口启动")
                    
                    with col2:
                        # 文件按钮
                        if st.button("文件", key=f"file_card_{task['name']}"):
                            if task['directory'] and os.path.exists(task['directory']):
                                files = get_directory_files(task['directory'])
                                if files:
                                    st.markdown("##### 文件列表")
                                    for i, file in enumerate(files):
                                        file_path = os.path.join(task['directory'], file)
                                        if st.button(file, key=f"file_card_{task['name']}_{i}"):
                                            if open_file(file_path):
                                                st.success(f"已打开: {file}")
                                else:
                                    st.info("没有找到文件")
                    
                    with col3:
                        # 复制命令按钮
                        if st.button("复制", key=f"copy_card_{task['name']}"):
                            copy_to_clipboard(cmd)
                            st.success("命令已复制")
                    
                    st.markdown("---")
    
    # 批量操作部分
    render_batch_operations(current_taskfile, view_key="card")

def render_group_view(filtered_df, current_taskfile):
    """渲染分组视图"""
    st.markdown("### 任务分组")
    
    # 按主标签分组
    if filtered_df.empty or 'tags' not in filtered_df.columns:
        st.warning("没有任务可显示或任务没有标签")
        return
    
    # 获取每个任务的主标签（第一个标签）
    filtered_df['primary_tag'] = filtered_df['tags'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else '未分类'
    )
    
    # 获取所有主标签
    primary_tags = sorted(filtered_df['primary_tag'].unique())
    
    # 为每个标签创建一个部分
    for tag in primary_tags:
        with st.expander(f"📂 {tag} ({len(filtered_df[filtered_df['primary_tag'] == tag])})", expanded=True):
            tag_tasks = filtered_df[filtered_df['primary_tag'] == tag]
            
            # 为该标签下的每个任务创建一个容器
            for _, task in tag_tasks.iterrows():
                with st.container():
                    # 标题行
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {task['emoji']} {task['name']}")
                    with col2:
                        # 选择框
                        is_selected = task['name'] in st.session_state.selected_tasks if 'selected_tasks' in st.session_state else False
                        if st.checkbox("选择", value=is_selected, key=f"group_{task['name']}"):
                            if 'selected_tasks' not in st.session_state:
                                st.session_state.selected_tasks = []
                            if task['name'] not in st.session_state.selected_tasks:
                                st.session_state.selected_tasks.append(task['name'])
                        elif 'selected_tasks' in st.session_state and task['name'] in st.session_state.selected_tasks:
                            st.session_state.selected_tasks.remove(task['name'])
                    
                    # 任务信息
                    st.markdown(f"**描述**: {task['description']}")
                    
                    # 显示所有标签
                    tags_str = ', '.join([f"#{t}" for t in task['tags']]) if isinstance(task['tags'], list) else ''
                    st.markdown(f"**标签**: {tags_str}")
                    
                    # 目录
                    st.markdown(f"**目录**: `{task['directory']}`")
                    
                    # 命令
                    cmd = get_task_command(task['name'], current_taskfile)
                    st.code(cmd, language="bash")
                    
                    # 操作按钮
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("运行", key=f"run_group_{task['name']}"):
                            with st.spinner(f"正在启动任务 {task['name']}..."):
                                result = run_task_via_cmd(task['name'], current_taskfile)
                            st.success(f"任务 {task['name']} 已在新窗口启动")
                    
                    with col2:
                        # 文件按钮
                        if st.button("文件", key=f"file_group_{task['name']}"):
                            if task['directory'] and os.path.exists(task['directory']):
                                files = get_directory_files(task['directory'])
                                if files:
                                    st.markdown("##### 文件列表")
                                    for i, file in enumerate(files):
                                        file_path = os.path.join(task['directory'], file)
                                        if st.button(file, key=f"file_group_{task['name']}_{i}"):
                                            if open_file(file_path):
                                                st.success(f"已打开: {file}")
                                else:
                                    st.info("没有找到文件")
                    
                    with col3:
                        # 复制命令按钮
                        if st.button("复制", key=f"copy_group_{task['name']}"):
                            copy_to_clipboard(cmd)
                            st.success("命令已复制")
                    
                    st.markdown("---")
    
    # 批量操作部分
    render_batch_operations(current_taskfile, view_key="group")

def render_batch_operations(current_taskfile, view_key=""):
    """渲染批量操作区域"""
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    st.markdown("### 批量操作")
    
    batch_col1, batch_col2, batch_col3 = st.columns(3)
    
    # 显示已选择的任务
    selected_tasks = st.session_state.selected_tasks
    st.markdown(f"**已选择 {len(selected_tasks)} 个任务：**")
    if selected_tasks:
        for task in selected_tasks:
            st.markdown(f"- {task}")
    
    # 并行执行选项
    with batch_col1:
        if 'run_parallel' not in st.session_state:
            st.session_state.run_parallel = False
        
        parallel_checkbox = st.checkbox(
            "并行执行任务", 
            value=st.session_state.run_parallel,
            key=f"parallel_{view_key}"
        )
        st.session_state.run_parallel = parallel_checkbox
    
    # 批量运行按钮
    with batch_col2:
        if st.button("运行选中的任务", key=f"run_batch_{view_key}"):
            if not selected_tasks:
                st.warning("请先选择要运行的任务")
            else:
                with st.spinner(f"正在启动 {len(selected_tasks)} 个任务..."):
                    result_msgs = run_multiple_tasks(
                        selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.run_parallel
                    )
                
                for msg in result_msgs:
                    st.success(msg)
    
    # 复制命令按钮
    with batch_col3:
        if st.button("复制所有命令", key=f"copy_batch_{view_key}"):
            if not selected_tasks:
                st.warning("请先选择要复制命令的任务")
            else:
                commands = []
                for task in selected_tasks:
                    cmd = get_task_command(task, current_taskfile)
                    commands.append(f"{task}: {cmd}")
                
                all_commands = "\n".join(commands)
                copy_to_clipboard(all_commands)
                st.success(f"已复制 {len(selected_tasks)} 个命令到剪贴板")
    
    # 清除选择按钮
    if st.button("清除选择", key=f"clear_{view_key}"):
        st.session_state.selected_tasks = []
        st.experimental_rerun()

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    with st.sidebar:
        st.title("任务管理器")
        
        # 视图选择
        st.markdown("## 视图设置")
        view_options = ["表格视图", "卡片视图", "分组视图"]
        
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "表格视图"
        
        selected_view = st.radio(
            "选择视图",
            options=view_options,
            index=view_options.index(st.session_state.current_view),
            key="view_selector"
        )
        
        st.session_state.current_view = selected_view
        
        # 添加任务过滤
        st.markdown("## 过滤任务")
        
        # 按名称搜索
        search_term = st.text_input("搜索任务名称:", key="search_task")
        
        # 按标签过滤
        tags_filter = st.multiselect(
            "按标签过滤:",
            options=get_all_tags(current_taskfile),
            key="tags_filter"
        )
        
        # 添加并行执行模式选项
        st.markdown("## 执行设置")
        
        if 'run_parallel' not in st.session_state:
            st.session_state.run_parallel = False
            
        parallel_mode = st.checkbox(
            "并行执行任务", 
            value=st.session_state.run_parallel,
            help="选中时，多个任务将同时启动"
        )
        
        st.session_state.run_parallel = parallel_mode
        
        # 显示已选任务数量
        if 'selected_tasks' in st.session_state and st.session_state.selected_tasks:
            st.markdown(f"## 已选择 {len(st.session_state.selected_tasks)} 个任务")
        
        # 添加关于部分
        with st.expander("关于"):
            st.markdown("""
            ### 任务管理器
            
            这个工具可以帮助您管理和运行各种任务。
            
            **功能**:
            - 支持多种视图模式
            - 可以同时运行多个任务
            - 支持文件浏览和打开
            - 可以复制命令到剪贴板
            
            **使用方法**:
            1. 选择您喜欢的视图模式
            2. 筛选您想要的任务
            3. 选择任务并执行操作
            """)

def get_all_tags(taskfile_path):
    """获取所有可用的标签"""
    try:
        from .taskfile import read_taskfile
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return []

def render_tag_filters(all_tags):
    """
    渲染标签过滤器
    
    参数:
        all_tags: 所有可用标签集合
        
    返回:
        selected_tags: 用户选择的标签列表
        search_term: 用户输入的搜索词
    """
    # 快速标签过滤器 - 横向显示在主区域
    st.markdown("### 🏷️ 快速标签筛选")
    
    # 管理收藏标签
    with st.expander("管理常用标签"):
        # 显示所有标签
        all_tag_cols = st.columns(5)
        for i, tag in enumerate(sorted(all_tags)):
            with all_tag_cols[i % 5]:
                if st.checkbox(tag, value=tag in st.session_state.favorite_tags, key=f"fav_{tag}"):
                    if tag not in st.session_state.favorite_tags:
                        st.session_state.favorite_tags.append(tag)
                else:
                    if tag in st.session_state.favorite_tags:
                        st.session_state.favorite_tags.remove(tag)
    
    # 显示收藏标签作为快速过滤器
    active_tags = []
    if st.session_state.favorite_tags:
        quick_filter_cols = st.columns(min(10, len(st.session_state.favorite_tags) + 2))
        
        # 添加"全部"和"清除"按钮
        with quick_filter_cols[0]:
            if st.button("🔍 全部", key="show_all"):
                active_tags = []
        
        with quick_filter_cols[1]:
            if st.button("❌ 清除", key="clear_filters"):
                active_tags = []
        
        # 显示收藏标签按钮
        for i, tag in enumerate(sorted(st.session_state.favorite_tags)):
            with quick_filter_cols[i + 2]:
                if st.button(f"#{tag}", key=f"quick_{tag}"):
                    active_tags.append(tag)
    
    # 搜索和过滤选项
    with st.sidebar:
        # 使用多选进行更复杂的标签过滤
        selected_tags = st.multiselect(
            "按标签过滤",
            options=sorted(list(all_tags)),
            default=active_tags
        )
        
        search_term = st.text_input("搜索任务")
    
    return selected_tags, search_term 