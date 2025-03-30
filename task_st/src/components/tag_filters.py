import streamlit as st

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

def get_all_tags(taskfile_path):
    """获取所有可用的标签"""
    try:
        from ..services.taskfile import read_taskfile
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return [] 