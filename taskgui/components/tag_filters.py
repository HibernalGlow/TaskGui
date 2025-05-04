import streamlit as st

def render_tag_filters(all_tags):
    """
    渲染标签过滤器
    
    参数:
        all_tags: 所有可用标签集合
    """
    # 初始化常用标签
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
    
    # 初始化标签过滤器状态
    if 'tags_filter' not in st.session_state:
        st.session_state.tags_filter = []
        
    # 所有逻辑已移到sidebar.py，这里仅保留函数以保持兼容性
    pass

def get_all_tags(taskfile_path):
    """获取所有可用的标签"""
    try:
        from taskgui.services.taskfile import read_taskfile
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return []