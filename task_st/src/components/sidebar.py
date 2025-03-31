import streamlit as st
from ..services.taskfile import read_taskfile

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    with st.sidebar:
        st.title("任务管理器")
        
        # 移除视图选择部分
        
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
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return []