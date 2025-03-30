import os
import streamlit as st
from .utils import (
    load_task_data, 
    apply_filters, 
    set_page_config, 
    get_task_command, 
    setup_css,
    initialize_session_state
)
from .views import (
    render_table_view, 
    render_card_view,
    render_group_view,
    render_settings_view,
    render_aggrid_table
)

def main():
    # 设置页面配置
    set_page_config("任务管理器", "🚀")
    
    # 初始化会话状态
    initialize_session_state()
    
    # 设置CSS样式
    setup_css()
    
    # 侧边栏 - 任务文件选择
    st.sidebar.title("任务管理器")
    
    # 获取可用的任务文件
    task_files_dir = os.path.abspath("../")
    available_files = [f for f in os.listdir(task_files_dir) 
                      if f.endswith('.json') and "task" in f.lower()]
    
    if not available_files:
        st.error("未找到任何任务文件。请确保目录中存在至少一个任务JSON文件。")
        return
    
    # 任务文件选择器
    current_taskfile = st.sidebar.selectbox(
        "选择任务文件",
        options=available_files,
        index=0,
        help="选择要加载的任务文件"
    )
    
    # 视图选择
    view_options = {
        "card": "卡片视图 🪪", 
        "table": "表格视图 📋", 
        "aggrid": "高级表格 📊", 
        "group": "分组视图 📑",
        "settings": "设置 ⚙️"
    }
    
    current_view = st.sidebar.radio(
        "选择视图",
        options=list(view_options.keys()),
        format_func=lambda x: view_options.get(x, x),
        index=list(view_options.keys()).index(st.session_state.current_view)
    )
    
    # 更新会话状态中的当前视图
    st.session_state.current_view = current_view
    
    # 批量模式选项
    st.sidebar.subheader("批量操作选项")
    st.session_state.parallel_mode = st.sidebar.checkbox(
        "启用并行模式", 
        value=st.session_state.parallel_mode,
        help="启用后，选中的任务将并行运行，而不是按顺序运行"
    )
    
    # 加载选定的任务文件
    if current_taskfile:
        taskfile_path = os.path.join(task_files_dir, current_taskfile)
        task_data = load_task_data(taskfile_path)
        
        if not task_data:
            st.error(f"无法加载任务文件: {current_taskfile}")
            return
        
        # 过滤选项（放在侧边栏中）
        st.sidebar.subheader("过滤选项")
        show_filter = st.sidebar.checkbox(
            "显示过滤选项", 
            value=st.session_state.show_filter,
            help="显示更多高级过滤选项"
        )
        st.session_state.show_filter = show_filter
        
        # 将任务数据转换为DataFrame
        df = task_data.copy()
        
        # 如果有过滤选项，应用过滤器
        filtered_df = df
        if show_filter:
            # 获取所有可用的标签列表
            all_tags = []
            for tags in df['tags']:
                if isinstance(tags, list):
                    all_tags.extend(tags)
            unique_tags = sorted(list(set(all_tags)))
            
            # 按标签过滤
            selected_tags = st.sidebar.multiselect("按标签过滤", unique_tags)
            
            # 按名称或描述搜索
            search_text = st.sidebar.text_input("搜索任务名称或描述")
            
            # 应用过滤器
            filtered_df = apply_filters(df, selected_tags, search_text)
        
        # 主内容区域
        
        # 根据选择的视图渲染不同的界面
        if current_view == "table":
            render_table_view(filtered_df, current_taskfile)
        elif current_view == "card":
            render_card_view(filtered_df, current_taskfile)
        elif current_view == "group":
            render_group_view(filtered_df, current_taskfile)
        elif current_view == "aggrid":
            render_aggrid_table(filtered_df, current_taskfile)
        elif current_view == "settings":
            render_settings_view(current_taskfile)

if __name__ == "__main__":
    main() 