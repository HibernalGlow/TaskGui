import streamlit as st
from .utils import get_task_command, copy_to_clipboard
from .task_runner import run_multiple_tasks

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
    
    # 初始化常用标签
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
    
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