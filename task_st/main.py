import streamlit as st
import os
from src import (
    init_session_state, 
    setup_css,
    load_taskfile, 
    prepare_dataframe, 
    get_all_tags, 
    filter_tasks,
    render_table_view,
    render_card_view,
    render_group_view,
    render_sidebar,
    render_tag_filters
)

# 设置页面配置
st.set_page_config(
    page_title="GlowToolBox 任务管理器",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """
    主应用程序入口
    """
    st.title("🧰 GlowToolBox 任务管理器")
    
    # 初始化会话状态
    init_session_state()
    
    # 设置CSS样式
    setup_css()
    
    # 渲染侧边栏
    sidebar_data = render_sidebar(st.session_state.last_taskfile_path)
    
    # 加载任务
    tasks, current_taskfile = load_taskfile(st.session_state.last_taskfile_path)
    df = prepare_dataframe(tasks)
    
    if df.empty:
        st.warning(f"未找到任务或Taskfile为空: {current_taskfile}")
        return
    
    # 显示当前Taskfile路径
    st.markdown(f"**当前Taskfile**: `{current_taskfile}`")
    
    # 提取所有标签并渲染标签过滤器
    all_tags = get_all_tags(df)
    selected_tags, search_term = render_tag_filters(all_tags)
    
    # 应用过滤器
    filtered_df = filter_tasks(df, selected_tags, search_term)
    
    # 根据视图类型渲染不同的视图
    view_type = sidebar_data["view_type"]
    if view_type == "表格视图":
        render_table_view(filtered_df, current_taskfile)
    elif view_type == "卡片视图":
        render_card_view(filtered_df, current_taskfile)
    elif view_type == "分组视图":
        render_group_view(filtered_df, current_taskfile)

if __name__ == "__main__":
    main()