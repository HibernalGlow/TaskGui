import streamlit as st
import pandas as pd
import os
import sys
import traceback
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
from src.taskfile import read_taskfile
from src.utils import find_taskfiles, get_nearest_taskfile, open_file, get_directory_files

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置页面配置
st.set_page_config(
    page_title="任务管理器",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加自定义CSS
st.markdown("""
<style>
    .tag {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 2px 8px;
        margin: 2px;
        display: inline-block;
        font-size: 0.8em;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    try:
        # 初始化会话状态
        if 'selected_tasks' not in st.session_state:
            st.session_state.selected_tasks = []
        
        if 'current_view' not in st.session_state:
            st.session_state.current_view = "表格视图"
        
        if 'run_parallel' not in st.session_state:
            st.session_state.run_parallel = False
        
        # 加载任务文件
        default_taskfile = get_nearest_taskfile()
        
        # 检查任务文件是否存在
        if not os.path.exists(default_taskfile):
            taskfiles = find_taskfiles(os.path.dirname(os.path.abspath(__file__)))
            if taskfiles:
                default_taskfile = taskfiles[0]
            else:
                st.error("找不到任务文件，请创建一个任务文件或指定正确的路径")
                return
        
        # 读取任务文件
        tasks_df = read_taskfile(default_taskfile)
        
        # 渲染侧边栏
        render_sidebar(default_taskfile)
        
        # 主内容区
        st.title("任务管理器")
        st.write(f"当前任务文件: `{default_taskfile}`")
        
        # 检查数据帧是否为空
        if tasks_df.empty:
            st.warning("任务文件中没有找到任务。请确保任务文件格式正确。")
            return
        
        # 应用过滤器
        filtered_df = filter_tasks(tasks_df)
        
        # 显示任务
        current_view = st.session_state.current_view
        
        if current_view == "表格视图":
            render_table_view(filtered_df, default_taskfile)
        elif current_view == "卡片视图":
            render_card_view(filtered_df, default_taskfile)
        elif current_view == "分组视图":
            render_group_view(filtered_df, default_taskfile)
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.error("如果错误与st-aggrid相关，请确保已安装: `pip install streamlit-aggrid`")
        st.code(traceback.format_exc())

def filter_tasks(tasks_df):
    """根据过滤条件过滤任务"""
    filtered_df = tasks_df.copy()
    
    # 应用搜索过滤
    if 'search_task' in st.session_state and st.session_state.search_task:
        search_term = st.session_state.search_task.lower()
        # 过滤名称或描述包含搜索词的任务
        mask = filtered_df['name'].str.lower().str.contains(search_term, na=False) | \
               filtered_df['description'].str.lower().str.contains(search_term, na=False)
        filtered_df = filtered_df[mask]
    
    # 应用标签过滤
    if 'tags_filter' in st.session_state and st.session_state.tags_filter:
        tags_to_filter = st.session_state.tags_filter
        # 过滤包含所选标签的任务
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: any(tag in x for tag in tags_to_filter) if isinstance(x, list) else False
        )]
    
    return filtered_df

if __name__ == "__main__":
    main()