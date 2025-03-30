import os
import json
import time
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
from .utils import (
    get_task_command, 
    copy_to_clipboard, 
    get_directory_files, 
    open_file, 
    set_page_config, 
    setup_css
)
from .task_runner import run_task_via_cmd, run_multiple_tasks

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
        # 只有标准表格视图需要在这里添加批量操作
        render_batch_operations(current_taskfile, view_key="table")

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格"""
    # 准备表格数据 - 只保留显示需要的列
    table_df = filtered_df.copy()
    
    # 确保标签字段是字符串
    table_df['tags_str'] = table_df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # 添加运行按钮列 - 使用JSCode渲染一个真正的按钮
    button_renderer = JsCode("""
    function(params) {
        return '<button onclick="window.runTask(\'' + params.data.name + '\')" style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">运行</button>';
    }
    """)
    
    # 注册运行任务的JS函数
    st.markdown("""
    <script>
    if (typeof window.runTask !== 'function') {
        window.runTask = function(taskName) {
            // 创建一个隐藏的输入框来存储任务名
            var input = document.createElement('input');
            input.setAttribute('type', 'hidden');
            input.setAttribute('id', 'task-to-run');
            input.setAttribute('value', taskName);
            document.body.appendChild(input);
            
            // 触发一个自定义事件
            document.dispatchEvent(new CustomEvent('run_selected_task'));
        };
        
        // 监听自定义事件
        document.addEventListener('run_selected_task', function() {
            // 模拟点击"运行单个任务"按钮
            setTimeout(function() {
                const buttons = Array.from(document.querySelectorAll('button'));
                for (let btn of buttons) {
                    if (btn.innerText === '运行单个任务') {
                        btn.click();
                        break;
                    }
                }
            }, 100);
        });
    }
    </script>
    """, unsafe_allow_html=True)
    
    # 配置表格选项
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_column('emoji', header_name="", width=50)
    gb.configure_column('name', header_name="任务名称", width=150)
    gb.configure_column('description', header_name="描述", width=300)
    gb.configure_column('tags_str', header_name="标签", width=150)
    gb.configure_column('directory', header_name="目录", width=200)
    
    # 添加操作列
    gb.configure_column(
        'run', 
        header_name='操作', 
        cellRenderer=button_renderer,
        width=100
    )
    
    # 配置多选功能
    gb.configure_selection(selection_mode='multiple', use_checkbox=True)
    gb.configure_default_column(sortable=True, filterable=True)
    
    # 构建选项并显示表格
    grid_options = gb.build()
    grid_response = AgGrid(
        table_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        columns_auto_size_mode="FIT_CONTENTS",
        height=500,
        allow_unsafe_jscode=True,
        custom_css={
            ".ag-cell-value": {"padding": "10px !important"},
            ".ag-header-cell-text": {"font-weight": "bold"}
        }
    )
    
    # 处理选中行（支持多选）
    selected_rows = grid_response.get('selected_rows', [])
    
    # 清除之前的选择 
    st.session_state.selected_tasks = []
    
    # 添加当前选中的行到会话状态
    if selected_rows and len(selected_rows) > 0:
        for row in selected_rows:
            if row['name'] not in st.session_state.selected_tasks:
                st.session_state.selected_tasks.append(row['name'])
    
    # 获取JS设置的要运行的任务
    task_to_run = st.empty()
    if st.button("运行单个任务", key="run_js_task", type="primary", help="这个按钮由JavaScript自动触发，用于运行表格中的任务"):
        # 检查是否有任务需要运行
        task_name_from_js = st.session_state.get('task_to_run', '')
        if task_name_from_js:
            with st.spinner(f"正在启动任务 {task_name_from_js}..."):
                result = run_task_via_cmd(task_name_from_js, current_taskfile)
            st.success(f"已启动任务: {task_name_from_js}")
            # 清除会话状态
            st.session_state.task_to_run = ''
    
    # 显示选中的任务数量和批量操作按钮
    if st.session_state.selected_tasks:
        st.markdown(f"已选择 **{len(st.session_state.selected_tasks)}** 个任务")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("显示任务命令", key="show_commands"):
                st.code("\n".join([get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]), language="bash")
        
        with col2:
            if st.button("复制任务命令", key="copy_commands_aggrid"):
                commands = [get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]
                copy_to_clipboard("\n".join(commands))
                st.success("所有命令已复制到剪贴板")
        
        with col3:
            mode_text = "并行" if st.session_state.parallel_mode else "顺序"
            if st.button(f"{mode_text}运行所有选中", key="run_selected_aggrid", type="primary"):
                with st.spinner(f"正在{mode_text}启动任务窗口..."):
                    result = run_multiple_tasks(
                        st.session_state.selected_tasks, 
                        current_taskfile,
                        parallel=st.session_state.parallel_mode
                    )
                st.success(result)
    
    # 如果选择了单个任务，显示详细信息
    if len(st.session_state.selected_tasks) == 1:
        task_name = st.session_state.selected_tasks[0]
        st.subheader(f"任务详情: {task_name}")
        
        # 找到对应行
        task_row = None
        for _, row in filtered_df.iterrows():
            if row['name'] == task_name:
                task_row = row
                break
        
        if task_row is not None:
            # 显示任务命令
            cmd = get_task_command(task_name, current_taskfile)
            st.markdown("**命令:**")
            st.code(cmd, language="bash")
            
            # 显示相关文件（如果有）
            if task_row['directory'] and os.path.exists(task_row['directory']):
                files = get_directory_files(task_row['directory'])
                if files:
                    st.markdown("**相关文件:**")
                    file_cols = st.columns(min(4, len(files)))
                    for i, file in enumerate(files):
                        with file_cols[i % len(file_cols)]:
                            file_path = os.path.join(task_row['directory'], file)
                            if st.button(f"{file}", key=f"open_{task_name}_{file}"):
                                if open_file(file_path):
                                    st.success(f"已打开: {file}")
    
    # 显示批量操作
    render_batch_operations(current_taskfile, view_key="aggrid")

def render_standard_table(filtered_df, current_taskfile):
    """使用标准Streamlit组件渲染表格"""
    # 添加排序选项
    sort_col, order_col = st.columns([2, 1])
    with sort_col:
        sort_by = st.selectbox(
            "排序方式", 
            options=["名称", "描述", "标签"],
            index=0,
            key="sort_by_key"
        )
    
    with order_col:
        sort_order = st.radio(
            "顺序",
            options=["升序", "降序"],
            horizontal=True,
            index=0,
            key="sort_order_key"
        )
    
    # 应用排序
    sort_map = {
        "名称": "name",
        "描述": "description",
        "标签": "tags_str"
    }
    
    # 修正标签显示
    filtered_df = filtered_df.copy()
    filtered_df['tags_str'] = filtered_df['tags'].apply(lambda x: ', '.join(x) if x else '')
    
    ascending = sort_order == "升序"
    if sort_by in sort_map:
        filtered_df = filtered_df.sort_values(by=sort_map[sort_by], ascending=ascending)
    
    # 创建自定义表格
    cols = st.columns([0.3, 1.2, 2.5, 1.2, 1.5, 1.5, 1.5])
    with cols[0]:
        st.markdown("**选择**")
    with cols[1]:
        st.markdown("**图标/名称**")
    with cols[2]:
        st.markdown("**描述**")
    with cols[3]:
        st.markdown("**标签**")
    with cols[4]:
        st.markdown("**目录/文件**")
    with cols[5]:
        st.markdown("**命令**")
    with cols[6]:
        st.markdown("**操作**")
    
    st.markdown("---")
    
    # 显示每一行
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        cols = st.columns([0.3, 1.2, 2.5, 1.2, 1.5, 1.5, 1.5])
        
        # 复选框
        with cols[0]:
            is_selected = row['name'] in st.session_state.selected_tasks
            task_selected = st.checkbox("", value=is_selected, key=f"select_{row['name']}")
            if task_selected and row['name'] not in st.session_state.selected_tasks:
                st.session_state.selected_tasks.append(row['name'])
            elif not task_selected and row['name'] in st.session_state.selected_tasks:
                st.session_state.selected_tasks.remove(row['name'])
        
        # 图标和名称
        with cols[1]:
            st.markdown(f"{row['emoji']} **{row['name']}**")
        
        # 描述
        with cols[2]:
            st.markdown(row['description'])
        
        # 标签
        with cols[3]:
            # 更美观的标签显示
            if row['tags']:
                tags_html = "".join([f'<span class="tag">#{tag}</span>' for tag in row['tags']])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.markdown("-")
        
        # 目录和文件
        with cols[4]:
            st.markdown(f"`{row['directory']}`")
            
            # 添加文件打开按钮
            if row['directory'] and os.path.exists(row['directory']):
                files = get_directory_files(row['directory'])
                if files:
                    selected_file = st.selectbox(
                        "文件",
                        options=["选择文件..."] + files,
                        key=f"files_{row['name']}"
                    )
                    
                    if selected_file != "选择文件...":
                        file_path = os.path.join(row['directory'], selected_file)
                        if st.button("打开", key=f"open_file_{row['name']}"):
                            if open_file(file_path):
                                st.success(f"已打开文件: {file_path}")
        
        # 命令
        with cols[5]:
            cmd = get_task_command(row['name'], current_taskfile)
            st.code(cmd, language="bash")
            if st.button("复制", key=f"copy_cmd_{row['name']}"):
                copy_to_clipboard(cmd)
                st.success("命令已复制")
        
        # 运行按钮
        with cols[6]:
            if st.button("运行", key=f"run_table_{row['name']}"):
                with st.spinner(f"正在启动任务窗口 {row['name']}..."):
                    result = run_task_via_cmd(row['name'], current_taskfile)
                st.success("任务已在新窗口中启动")
    
    # 批量执行选定的任务
    render_batch_operations(current_taskfile, view_key="table")

def render_card_view(df, current_taskfile):
    """渲染卡片视图"""
    st.title("任务卡片视图")
    if df.empty:
        st.warning("没有可用的任务，或者所有任务都被过滤掉了")
        return
    
    # 创建3列布局
    col_count = 3
    rows = [st.columns(col_count) for _ in range((len(df) + col_count - 1) // col_count)]
    
    # 遍历每个任务
    for i, (_, row) in enumerate(df.iterrows()):
        with rows[i // col_count][i % col_count]:
            task_name = row['name']
            
            # 构建卡片
            st.markdown(f"""
            <div class="task-card">
                <div class="task-header">
                    <span class="task-emoji">{row['emoji'] if 'emoji' in row else '🚀'}</span>
                    <h3 class="task-title">{task_name}</h3>
                </div>
                <div class="task-description">{row['description']}</div>
                <div class="task-tags">{"".join([f'<span class="tag">{tag}</span>' for tag in row['tags']])}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 获取任务命令
            cmd = get_task_command(task_name, current_taskfile)
            st.code(cmd, language="bash")
            
            # 按钮操作区
            col1, col2 = st.columns(2)
            
            with col1:
                # 复制命令按钮
                if st.button("复制命令", key=f"copy_{i}", help="将命令复制到剪贴板"):
                    copy_to_clipboard(cmd)
                    st.success("已复制!")
            
            with col2:
                # 运行任务按钮
                if st.button("运行任务", key=f"run_{i}", type="primary", help="在新窗口中运行此任务"):
                    with st.spinner(f"正在启动任务 {task_name}..."):
                        result = run_task_via_cmd(task_name, current_taskfile)
                    st.success("已启动!")
            
            # 复选框 - 添加到批量任务
            is_selected = task_name in st.session_state.selected_tasks
            if st.checkbox("添加到批量任务", key=f"select_{i}", value=is_selected):
                if task_name not in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.append(task_name)
            else:
                if task_name in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.remove(task_name)
            
            # 相关文件部分
            if row['directory'] and os.path.exists(row['directory']):
                files = get_directory_files(row['directory'])
                if files:
                    st.markdown("**相关文件:**")
                    for file in files:
                        file_path = os.path.join(row['directory'], file)
                        if st.button(f"{file}", key=f"open_{i}_{file}"):
                            if open_file(file_path):
                                st.success(f"已打开: {file}")
    
    # 显示批量操作
    render_batch_operations(current_taskfile, view_key="card")

def render_group_view(df, current_taskfile):
    """渲染分组视图"""
    st.title("任务分组视图")
    if df.empty:
        st.warning("没有可用的任务，或者所有任务都被过滤掉了")
        return
    
    # 获取所有标签的集合
    all_tags = set()
    for tags in df['tags']:
        if isinstance(tags, list):
            all_tags.update(tags)
    
    # 将无标签的任务分组
    no_tag_tasks = df[df['tags'].apply(lambda x: not x or len(x) == 0)]
    
    # 先显示无标签任务
    if not no_tag_tasks.empty:
        with st.expander("📂 无标签任务", expanded=True):
            for _, row in no_tag_tasks.iterrows():
                task_name = row['name']
                
                # 任务信息行
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    # 选择复选框
                    is_selected = task_name in st.session_state.selected_tasks
                    if st.checkbox("", key=f"select_no_tag_{task_name}", value=is_selected):
                        if task_name not in st.session_state.selected_tasks:
                            st.session_state.selected_tasks.append(task_name)
                    else:
                        if task_name in st.session_state.selected_tasks:
                            st.session_state.selected_tasks.remove(task_name)
                
                with col2:
                    # 任务名称和描述
                    st.markdown(f"**{row['emoji'] if 'emoji' in row else '🚀'} {task_name}**")
                    st.markdown(f"{row['description']}")
                    
                    # 命令
                    cmd = get_task_command(task_name, current_taskfile)
                    st.code(cmd, language="bash")
                
                with col3:
                    # 复制和运行按钮
                    if st.button("复制", key=f"copy_no_tag_{task_name}"):
                        copy_to_clipboard(cmd)
                        st.success("已复制!")
                    
                    if st.button("运行", key=f"run_no_tag_{task_name}", type="primary"):
                        with st.spinner(f"正在启动任务 {task_name}..."):
                            result = run_task_via_cmd(task_name, current_taskfile)
                        st.success("已启动!")
                
                # 显示相关文件（如果有）
                if row['directory'] and os.path.exists(row['directory']):
                    files = get_directory_files(row['directory'])
                    if files:
                        st.markdown("**相关文件:**")
                        file_cols = st.columns(min(4, len(files)))
                        for i, file in enumerate(files):
                            with file_cols[i % len(file_cols)]:
                                file_path = os.path.join(row['directory'], file)
                                if st.button(f"{file}", key=f"open_no_tag_{task_name}_{i}"):
                                    if open_file(file_path):
                                        st.success(f"已打开: {file}")
                
                st.markdown("---")
    
    # 按标签分组显示
    for tag in sorted(all_tags):
        # 获取包含此标签的任务
        tag_tasks = df[df['tags'].apply(lambda x: isinstance(x, list) and tag in x)]
        
        if not tag_tasks.empty:
            with st.expander(f"🏷️ {tag} ({len(tag_tasks)})", expanded=False):
                for _, row in tag_tasks.iterrows():
                    task_name = row['name']
                    
                    # 任务信息行
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        # 选择复选框
                        is_selected = task_name in st.session_state.selected_tasks
                        if st.checkbox("", key=f"select_{tag}_{task_name}", value=is_selected):
                            if task_name not in st.session_state.selected_tasks:
                                st.session_state.selected_tasks.append(task_name)
                        else:
                            if task_name in st.session_state.selected_tasks:
                                st.session_state.selected_tasks.remove(task_name)
                    
                    with col2:
                        # 任务名称和描述
                        st.markdown(f"**{row['emoji'] if 'emoji' in row else '🚀'} {task_name}**")
                        st.markdown(f"{row['description']}")
                        
                        # 额外的标签显示（除了当前分组的标签）
                        other_tags = [t for t in row['tags'] if t != tag]
                        if other_tags:
                            st.markdown(" ".join([f"`{t}`" for t in other_tags]))
                        
                        # 命令
                        cmd = get_task_command(task_name, current_taskfile)
                        st.code(cmd, language="bash")
                    
                    with col3:
                        # 复制和运行按钮
                        if st.button("复制", key=f"copy_{tag}_{task_name}"):
                            copy_to_clipboard(cmd)
                            st.success("已复制!")
                        
                        if st.button("运行", key=f"run_{tag}_{task_name}", type="primary"):
                            with st.spinner(f"正在启动任务 {task_name}..."):
                                result = run_task_via_cmd(task_name, current_taskfile)
                            st.success("已启动!")
                    
                    # 显示相关文件（如果有）
                    if row['directory'] and os.path.exists(row['directory']):
                        files = get_directory_files(row['directory'])
                        if files:
                            st.markdown("**相关文件:**")
                            file_cols = st.columns(min(4, len(files)))
                            for i, file in enumerate(files):
                                with file_cols[i % len(file_cols)]:
                                    file_path = os.path.join(row['directory'], file)
                                    if st.button(f"{file}", key=f"open_{tag}_{task_name}_{i}"):
                                        if open_file(file_path):
                                            st.success(f"已打开: {file}")
                    
                    st.markdown("---")
    
    # 显示批量操作
    render_batch_operations(current_taskfile, view_key="group")

def render_batch_operations(current_taskfile, view_key="default"):
    """渲染批量操作部分"""
    # 如果有选中的任务，显示批量操作
    if st.session_state.selected_tasks:
        st.markdown("---")
        st.subheader(f"批量操作 ({len(st.session_state.selected_tasks)} 个任务)")
        
        # 显示选中的任务
        st.markdown("**选中的任务:**")
        st.write(", ".join(st.session_state.selected_tasks))
        
        # 命令显示和操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("显示所有命令", key=f"show_all_{view_key}"):
                commands = [get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]
                st.code("\n".join(commands), language="bash")
        
        with col2:
            if st.button("复制所有命令", key=f"copy_all_{view_key}"):
                commands = [get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]
                copy_to_clipboard("\n".join(commands))
                st.success("所有命令已复制到剪贴板")
        
        with col3:
            mode_text = "并行" if st.session_state.parallel_mode else "顺序"
            if st.button(f"{mode_text}运行所有", key=f"run_all_{view_key}", type="primary"):
                with st.spinner(f"正在{mode_text}启动选中的任务..."):
                    result = run_multiple_tasks(
                        st.session_state.selected_tasks, 
                        current_taskfile,
                        parallel=st.session_state.parallel_mode
                    )
                st.success(result)
        
        # 清除选择按钮
        if st.button("清除所有选择", key=f"clear_{view_key}"):
            st.session_state.selected_tasks = []
            st.experimental_rerun()

def render_sidebar(current_taskfile):
    """
    渲染侧边栏
    
    参数:
        current_taskfile: 当前Taskfile路径
        
    返回:
        sidebar_data: 包含侧边栏选项的字典
    """
    st.sidebar.subheader("Taskfile 设置")
    
    # 历史记录
    if st.session_state.taskfile_history:
        taskfile_history = ["当前文件"] + st.session_state.taskfile_history
        history_choice = st.sidebar.selectbox(
            "历史记录",
            options=taskfile_history,
            index=0
        )
        
        if history_choice != "当前文件":
            if st.sidebar.button("使用选中的历史文件"):
                st.session_state.last_taskfile_path = history_choice
                st.rerun()
    
    # 手动输入路径
    manual_path = st.sidebar.text_input(
        "Taskfile 路径",
        value=st.session_state.last_taskfile_path or ""
    )
    
    # 浏览文件
    if st.sidebar.button("浏览文件..."):
        # 使用路径预测来模拟文件浏览
        from .utils import find_taskfiles
        root_dir = os.path.dirname(manual_path) if os.path.exists(os.path.dirname(manual_path)) else "D:/"
        taskfiles = find_taskfiles(root_dir)
        if taskfiles:
            st.session_state.last_taskfile_path = taskfiles[0]
            st.rerun()
    
    # 载入指定文件
    if st.sidebar.button("加载文件"):
        st.session_state.last_taskfile_path = manual_path
        st.rerun()
    
    # 并行模式
    parallel_mode = st.sidebar.checkbox(
        "并行执行任务",
        value=st.session_state.parallel_mode,
        help="启用后，批量任务将同时运行，而不是等待前一个完成"
    )
    # 更新会话状态
    st.session_state.parallel_mode = parallel_mode
    
    # 高级过滤部分
    st.sidebar.subheader("高级过滤")
    
    # 视图选择
    view_type = st.sidebar.radio(
        "视图类型",
        options=["表格视图", "卡片视图", "分组视图"]
    )
    
    # 处理批量操作
    selected_count = len(st.session_state.selected_tasks)
    if selected_count > 0:
        st.sidebar.subheader(f"批量操作 ({selected_count} 个任务)")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.sidebar.button("清空选择", key="clear_selection_sidebar"):
                st.session_state.selected_tasks = []
                st.rerun()
        
        with col2:
            if st.sidebar.button("运行所有选中", key="run_all_sidebar", type="primary"):
                with st.spinner("正在启动任务..."):
                    result = run_multiple_tasks(
                        st.session_state.selected_tasks, 
                        current_taskfile,
                        parallel=st.session_state.parallel_mode
                    )
                st.success(result)
        
        # 复制所有命令
        if st.sidebar.button("复制所有命令", key="copy_all_cmd"):
            commands = [get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]
            copy_to_clipboard("\n".join(commands))
            st.sidebar.success("所有命令已复制到剪贴板")
    
    return {
        'manual_path': manual_path,
        'view_type': view_type
    }

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

def render_settings_view(current_taskfile):
    """渲染设置视图"""
    st.title("设置")
    
    # 显示当前任务文件信息
    st.subheader("当前任务文件")
    st.info(f"名称: {current_taskfile}")
    
    task_file_path = os.path.join(os.path.abspath("../"), current_taskfile)
    st.info(f"路径: {task_file_path}")
    
    # 显示统计信息
    df = load_task_data(task_file_path)
    if df is not None:
        st.subheader("统计信息")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("任务总数", len(df))
        
        # 统计标签数量
        all_tags = set()
        for tags in df['tags']:
            if isinstance(tags, list):
                all_tags.update(tags)
        
        with col2:
            st.metric("标签总数", len(all_tags))
        
        # 统计目录数量
        unique_dirs = df['directory'].unique()
        with col3:
            st.metric("相关目录数", len(unique_dirs))
        
        # 显示标签分布
        if all_tags:
            st.subheader("标签分布")
            
            tag_counts = {}
            for tags in df['tags']:
                if isinstance(tags, list):
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            tag_df = pd.DataFrame({
                '标签': list(tag_counts.keys()),
                '数量': list(tag_counts.values())
            }).sort_values('数量', ascending=False)
            
            st.bar_chart(tag_df.set_index('标签'))
        
        # 任务目录分布
        if len(unique_dirs) > 1:
            st.subheader("目录分布")
            
            dir_counts = df['directory'].value_counts().reset_index()
            dir_counts.columns = ['目录', '任务数量']
            
            st.dataframe(dir_counts)
    
    # 应用程序设置
    st.subheader("应用设置")
    
    # 主题选择
    theme = st.selectbox(
        "界面主题",
        options=["明亮", "暗黑"],
        index=0,
        help="选择应用程序的显示主题"
    )
    
    # 默认视图
    default_view = st.selectbox(
        "默认视图",
        options=["卡片视图", "表格视图", "分组视图", "高级表格"],
        index=0,
        help="选择应用程序启动时的默认视图模式"
    )
    
    # 自动刷新
    auto_refresh = st.checkbox(
        "启用自动刷新",
        value=False,
        help="定期刷新任务数据"
    )
    
    if auto_refresh:
        refresh_interval = st.slider(
            "刷新间隔(秒)",
            min_value=10,
            max_value=300,
            value=60,
            step=10
        )
    
    # 确认按钮
    if st.button("保存设置", type="primary"):
        st.session_state.theme = theme
        st.session_state.default_view = default_view
        st.session_state.auto_refresh = auto_refresh
        if auto_refresh:
            st.session_state.refresh_interval = refresh_interval
        
        st.success("设置已保存")
        st.info("部分设置可能需要重新启动应用后生效") 