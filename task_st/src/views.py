import streamlit as st
from .utils import get_task_command, copy_to_clipboard
from .task_runner import run_task_via_cmd, run_multiple_tasks
import os

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    st.markdown("### 任务列表")
    
    # 创建自定义表格
    cols = st.columns([0.4, 2, 5, 2, 2, 1.5])
    with cols[0]:
        st.markdown("**选择**")
    with cols[1]:
        st.markdown("**图标/名称**")
    with cols[2]:
        st.markdown("**描述**")
    with cols[3]:
        st.markdown("**标签**")
    with cols[4]:
        st.markdown("**目录**")
    with cols[5]:
        st.markdown("**操作**")
    
    st.markdown("---")
    
    # 显示每一行
    for i, (_, row) in enumerate(filtered_df.iterrows()):
        cols = st.columns([0.4, 2, 5, 2, 2, 1.5])
        
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
            # 添加复制命令按钮
            cmd = get_task_command(row['name'], current_taskfile)
            st.markdown(f"""
            <div>
                <code style="font-size:11px">{cmd}</code>
                <button class="copy-btn" 
                    onclick="navigator.clipboard.writeText('{cmd}'); this.innerText='已复制';">
                    复制
                </button>
            </div>
            """, unsafe_allow_html=True)
        
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
        
        # 目录
        with cols[4]:
            st.markdown(f"`{row['directory']}`")
        
        # 运行按钮
        with cols[5]:
            run_col, copy_col = st.columns(2)
            with run_col:
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
                # 添加复制命令按钮
                cmd = get_task_command(row['name'], current_taskfile)
                st.markdown(f"""
                <div>
                    <code style="font-size:12px">{cmd}</code>
                    <button class="copy-btn" 
                        onclick="navigator.clipboard.writeText('{cmd}'); this.innerText='已复制';">
                        复制
                    </button>
                </div>
                """, unsafe_allow_html=True)
                
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
                
                if st.button(f"运行", key=f"run_{row['name']}"):
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
        filtered_df['primary_tag'] = filtered_df['tags'].apply(
            lambda x: x[0] if x and len(x) > 0 else "未分类"
        )
        
        # 按主标签分组
        groups = filtered_df.groupby('primary_tag')
        
        for group_name, group_df in groups:
            st.subheader(f"📂 {group_name}")
            
            cols = st.columns(3)
            for i, (_, row) in enumerate(group_df.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"**{row['emoji']} {row['name']}**")
                    
                    # 添加复制命令按钮
                    cmd = get_task_command(row['name'], current_taskfile)
                    st.markdown(f"""
                    <div>
                        <code style="font-size:11px">{cmd}</code>
                        <button class="copy-btn" 
                            onclick="navigator.clipboard.writeText('{cmd}'); this.innerText='已复制';">
                            复制
                        </button>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 添加勾选框
                    is_selected = row['name'] in st.session_state.selected_tasks
                    task_selected = st.checkbox("选择", value=is_selected, key=f"group_select_{row['name']}")
                    if task_selected and row['name'] not in st.session_state.selected_tasks:
                        st.session_state.selected_tasks.append(row['name'])
                    elif not task_selected and row['name'] in st.session_state.selected_tasks:
                        st.session_state.selected_tasks.remove(row['name'])
                    
                    st.markdown(f"{row['description']}")
                    
                    if st.button(f"运行", key=f"group_run_{row['name']}"):
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
    if st.session_state.selected_tasks:
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
        manual_path: 用户输入的Taskfile路径
        selected_tags: 选择的标签
        search_term: 搜索词
        view_type: 视图类型
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
    st.session_state.parallel_mode = st.sidebar.checkbox(
        "并行执行任务",
        value=st.session_state.parallel_mode,
        help="启用后，批量任务将同时运行，而不是等待前一个完成"
    )
    
    # 处理批量操作
    selected_count = len(st.session_state.selected_tasks)
    if selected_count > 0:
        st.sidebar.subheader(f"批量操作 ({selected_count} 个任务)")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("清空选择", key="clear_selection_sidebar"):
                st.session_state.selected_tasks = []
                st.rerun()
        
        with col2:
            if st.button("运行所有选中", key="run_all_sidebar", type="primary"):
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
    
    # 高级过滤部分
    st.sidebar.subheader("高级过滤")
    
    # 视图选择
    view_type = st.sidebar.radio(
        "视图类型",
        options=["表格视图", "卡片视图", "分组视图"]
    )
    
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