import streamlit as st
from .utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .task_runner import run_task_via_cmd, run_multiple_tasks
import os
import pandas as pd

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
    # 准备表格数据 - 只保留显示需要的列
    table_df = filtered_df.copy()
    
    # 确保标签字段是字符串
    table_df['tags_str'] = table_df['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # 只保留需要显示的列
    display_cols = ['emoji', 'name', 'description', 'tags_str', 'directory']
    table_df = table_df[display_cols]
    
    # 添加操作列
    table_df['操作'] = '运行'
    
    # 设置表格选项
    gb = GridOptionsBuilder.from_dataframe(table_df)
    gb.configure_column('emoji', header_name="", width=70)
    gb.configure_column('name', header_name="任务名称", width=150)
    gb.configure_column('description', header_name="描述", width=300)
    gb.configure_column('tags_str', header_name="标签", width=150)
    gb.configure_column('directory', header_name="目录", width=200)
    gb.configure_column('操作', header_name="操作", width=100)
    
    # 配置选择模式
    gb.configure_selection(selection_mode='single', use_checkbox=True)
    gb.configure_default_column(sortable=True, filterable=True)
    
    grid_options = gb.build()
    
    # 显示表格
    grid_response = AgGrid(
        table_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        columns_auto_size_mode="FIT_CONTENTS",
        height=500,
        allow_unsafe_jscode=True
    )
    
    # 处理选中行 - 修复错误处理
    selected_rows = grid_response.get('selected_rows', [])
    if selected_rows and len(selected_rows) > 0:
        selected_task = selected_rows[0]
        st.write(f"选中任务: **{selected_task['name']}**")
        
        # 显示任务命令
        cmd = get_task_command(selected_task['name'], current_taskfile)
        st.subheader("命令")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.code(cmd, language="bash")
        with col2:
            if st.button("复制命令", key="copy_aggrid_cmd"):
                copy_to_clipboard(cmd)
                st.success("命令已复制")
        
        # 任务目录下的文件
        if selected_task['directory'] and os.path.exists(selected_task['directory']):
            files = get_directory_files(selected_task['directory'])
            if files:
                st.subheader("相关文件")
                file_cols = st.columns(min(5, len(files)))
                for i, file in enumerate(files):
                    with file_cols[i % len(file_cols)]:
                        file_path = os.path.join(selected_task['directory'], file)
                        if st.button(f"打开 {file}", key=f"open_{selected_task['name']}_{file}"):
                            if open_file(file_path):
                                st.success(f"已打开: {file}")
        
        # 运行按钮
        if st.button(f"运行任务: {selected_task['name']}", type="primary", key="run_aggrid_task"):
            with st.spinner(f"正在启动任务窗口 {selected_task['name']}..."):
                result = run_task_via_cmd(selected_task['name'], current_taskfile)
            st.success("任务已在新窗口中启动")

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

def render_card_view(filtered_df, current_taskfile):
    """
    渲染卡片视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    cols = st.columns(3)
    
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 3]:
            with st.expander(f"{row['emoji']} {row['name']}", expanded=False):
                # 添加命令显示
                cmd = get_task_command(row['name'], current_taskfile)
                st.code(cmd, language="bash")
                if st.button("复制命令", key=f"copy_card_{row['name']}"):
                    copy_to_clipboard(cmd)
                    st.success("命令已复制")
                
                # 添加勾选框
                is_selected = row['name'] in st.session_state.selected_tasks
                task_selected = st.checkbox("选择此任务", value=is_selected, key=f"card_select_{row['name']}")
                if task_selected and row['name'] not in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.append(row['name'])
                elif not task_selected and row['name'] in st.session_state.selected_tasks:
                    st.session_state.selected_tasks.remove(row['name'])
                
                st.markdown(f"**描述**: {row['description']}")
                
                # 标签更美观显示
                if row['tags']:
                    st.markdown("**标签**: " + " ".join([f'`#{tag}`' for tag in row['tags']]))
                else:
                    st.markdown("**标签**: -")
                    
                st.markdown(f"**目录**: `{row['directory']}`")
                
                # 添加文件打开功能
                if row['directory'] and os.path.exists(row['directory']):
                    files = get_directory_files(row['directory'])
                    if files:
                        selected_file = st.selectbox(
                            "文件",
                            options=["选择文件..."] + files,
                            key=f"card_file_{row['name']}"
                        )
                        
                        if selected_file != "选择文件...":
                            file_path = os.path.join(row['directory'], selected_file)
                            if st.button("打开文件", key=f"card_open_{row['name']}"):
                                if open_file(file_path):
                                    st.success(f"已打开文件: {file_path}")
                
                # 运行按钮
                if st.button(f"运行任务", key=f"run_{row['name']}", type="primary"):
                    with st.spinner(f"正在启动任务窗口 {row['name']}..."):
                        result = run_task_via_cmd(row['name'], current_taskfile)
                    st.success("任务已在新窗口中启动")
    
    # 批量操作
    render_batch_operations(current_taskfile, view_key="card")

def render_group_view(filtered_df, current_taskfile):
    """
    渲染分组视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    # 按标签分组
    if not filtered_df.empty:
        # 获取第一个标签作为主标签
        filtered_df = filtered_df.copy()
        filtered_df['primary_tag'] = filtered_df['tags'].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else "未分类"
        )
        
        # 按主标签分组
        groups = filtered_df.groupby('primary_tag')
        
        for group_name, group_df in groups:
            st.subheader(f"📂 {group_name}")
            
            cols = st.columns(3)
            for i, (_, row) in enumerate(group_df.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"**{row['emoji']} {row['name']}**")
                    
                    # 添加命令显示
                    cmd = get_task_command(row['name'], current_taskfile)
                    st.code(cmd, language="bash")
                    if st.button("复制", key=f"copy_group_{row['name']}"):
                        copy_to_clipboard(cmd)
                        st.success("命令已复制")
                    
                    # 添加勾选框
                    is_selected = row['name'] in st.session_state.selected_tasks
                    task_selected = st.checkbox("选择", value=is_selected, key=f"group_select_{row['name']}")
                    if task_selected and row['name'] not in st.session_state.selected_tasks:
                        st.session_state.selected_tasks.append(row['name'])
                    elif not task_selected and row['name'] in st.session_state.selected_tasks:
                        st.session_state.selected_tasks.remove(row['name'])
                    
                    st.markdown(f"{row['description']}")
                    
                    # 添加文件打开功能
                    if row['directory'] and os.path.exists(row['directory']):
                        files = get_directory_files(row['directory'])
                        if files:
                            selected_file = st.selectbox(
                                "文件",
                                options=["选择文件..."] + files,
                                key=f"group_file_{row['name']}"
                            )
                            
                            if selected_file != "选择文件...":
                                file_path = os.path.join(row['directory'], selected_file)
                                if st.button("打开文件", key=f"group_open_{row['name']}"):
                                    if open_file(file_path):
                                        st.success(f"已打开文件: {file_path}")
                    
                    if st.button(f"运行", key=f"group_run_{row['name']}", type="primary"):
                        with st.spinner(f"正在启动任务窗口 {row['name']}..."):
                            result = run_task_via_cmd(row['name'], current_taskfile)
                        st.success("任务已在新窗口中启动")
                    
                    st.markdown("---")
        
        # 批量操作
        render_batch_operations(current_taskfile, view_key="group")

def render_batch_operations(current_taskfile, view_key=""):
    """
    渲染批量操作按钮
    
    参数:
        current_taskfile: 当前Taskfile路径
        view_key: 视图类型，用于生成唯一键值
    """
    if st.session_state.selected_tasks and len(st.session_state.selected_tasks) > 0:
        st.markdown("---")
        st.markdown("### 批量操作")
        
        # 展示当前选中的任务
        st.markdown(f"已选择 **{len(st.session_state.selected_tasks)}** 个任务: " + 
                  ", ".join([f"`{task}`" for task in st.session_state.selected_tasks]))
        
        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("取消所有选择", key=f"clear_{view_key}"):
                st.session_state.selected_tasks = []
                st.rerun()
        
        with cols[1]:
            mode_text = "并行" if st.session_state.parallel_mode else "顺序"
            if st.button(f"{mode_text}运行所有选中任务", key=f"run_selected_{view_key}", type="primary"):
                with st.spinner(f"正在{mode_text}启动任务窗口..."):
                    result = run_multiple_tasks(
                        st.session_state.selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.parallel_mode
                    )
                st.success(result)
        
        with cols[2]:
            if st.button("复制所有命令", key=f"copy_commands_{view_key}"):
                commands = [get_task_command(task, current_taskfile) for task in st.session_state.selected_tasks]
                copy_to_clipboard("\n".join(commands))
                st.success("所有命令已复制到剪贴板")

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