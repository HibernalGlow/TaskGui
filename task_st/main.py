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
    
    功能说明:
    1. 支持排序和过滤任务
    2. 支持打开任务相关文件（使用默认程序）
    3. 显示任务命令和复制功能
    4. 表格视图支持AgGrid（如果安装）或标准表格
    
    安装AgGrid（更好的表格体验）:
    pip install streamlit-aggrid
    """
    try:
        st.title("🧰 GlowToolBox 任务管理器")
        
        # 初始化会话状态
        init_session_state()
        
        # 设置CSS样式
        setup_css()
        
        # 渲染侧边栏
        sidebar_data = render_sidebar(st.session_state.last_taskfile_path)
        
        # 加载任务
        tasks, current_taskfile = load_taskfile(st.session_state.last_taskfile_path)
        if not tasks:
            st.warning(f"未能加载任务或Taskfile为空: {current_taskfile}")
            return
            
        df = prepare_dataframe(tasks)
        
        if df.empty:
            st.warning(f"任务DataFrame为空: {current_taskfile}")
            return
        
        # 显示当前Taskfile路径
        st.markdown(f"**当前Taskfile**: `{current_taskfile}`")
        
        # 提取所有标签并渲染标签过滤器
        all_tags = get_all_tags(df)
        selected_tags, search_term = render_tag_filters(all_tags)
        
        # 应用过滤器
        filtered_df = filter_tasks(df, selected_tags, search_term)
        
        if filtered_df.empty:
            st.info("没有匹配的任务，请调整过滤条件")
            return
            
        # 根据视图类型渲染不同的视图
        view_type = sidebar_data["view_type"]
        if view_type == "表格视图":
            render_table_view(filtered_df, current_taskfile)
        elif view_type == "卡片视图":
            render_card_view(filtered_df, current_taskfile)
        elif view_type == "分组视图":
            render_group_view(filtered_df, current_taskfile)
    
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.info("如果是关于st-aggrid的错误，请尝试安装: pip install streamlit-aggrid")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()