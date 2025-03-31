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
    render_tag_filters,
    find_taskfiles,
    get_nearest_taskfile
)
from src.services.taskfile import read_taskfile
from src.utils.file_utils import open_file, get_directory_files
from src.views.styles import apply_custom_styles
from src.components.preview_card import render_shared_preview
from src.utils.selection_utils import get_global_state, update_global_state, export_global_state_json, import_global_state_json

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
    
    /* 添加页签样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0 0;
    }
    
    /* 主要页签样式 */
    .main-tabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    
    /* 预览区域样式 */
    .preview-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
        border: 1px solid #e6e6e6;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    try:
        # 初始化会话状态
        if 'selected_tasks' not in st.session_state:
            st.session_state.selected_tasks = []
        
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
        
        # 应用自定义样式 - 在st.title之前添加
        apply_custom_styles()
        
        # 主内容区
        st.title("任务管理器")
        st.write(f"当前任务文件: `{default_taskfile}`")
        
        # 检查数据帧是否为空
        if tasks_df.empty:
            st.warning("任务文件中没有找到任务。请确保任务文件格式正确。")
            return
        
        # 应用过滤器
        filtered_df = filter_tasks(tasks_df)
        
        # 共享预览区域 - 放在页签上方
        preview_expander = st.expander("📌 选中任务预览", expanded=True)
        with preview_expander:
            render_shared_preview(filtered_df, default_taskfile)
        
        # 使用单层页签 - 将所有页签放在一排
        tabs = st.tabs(["📊 表格视图", "🗂️ 卡片视图", "📁 分组视图", "📈 仪表盘", "⚙️ 设置", "🔍 状态管理"])
        
        # 表格视图
        with tabs[0]:
            render_table_view(filtered_df, default_taskfile, show_sidebar=False)  # 关闭右侧预览
        
        # 卡片视图
        with tabs[1]:
            render_card_view(filtered_df, default_taskfile)
        
        # 分组视图
        with tabs[2]:
            render_group_view(filtered_df, default_taskfile)
        
        # 仪表盘页签
        with tabs[3]:
            st.markdown("## 📊 任务仪表盘")
            st.info("仪表盘功能正在开发中...")
            
            # 占位内容
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总任务数", len(tasks_df))
            with col2:
                st.metric("选中任务", len(st.session_state.selected_tasks))
            
            # 示例图表
            st.subheader("标签分布")
            st.write("此处将显示任务标签的分布统计")
        
        # 设置页签
        with tabs[4]:
            st.markdown("## ⚙️ 系统设置")
            st.info("设置功能正在开发中...")
            
            # 示例设置选项
            st.subheader("界面设置")
            st.checkbox("启用深色模式", value=False, disabled=True)
            st.checkbox("自动加载最近的任务文件", value=True, disabled=True)
            
            st.subheader("任务执行")
            st.radio("默认运行模式", options=["顺序执行", "并行执行"], index=0, disabled=True)
        
        # 状态管理页签
        with tabs[5]:
            render_state_manager()
        
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

def render_state_manager():
    """渲染状态管理器页面"""
    st.markdown("## 🔍 全局状态管理")
    st.info("在这里您可以查看和修改系统的全局状态数据")
    
    # 获取当前状态
    global_state = get_global_state()
    
    # 创建两列布局
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("当前状态")
        
        # 显示基本状态信息
        st.write(f"版本: {global_state.get('version', 'N/A')}")
        st.write(f"最后更新: {global_state.get('last_updated', 'N/A')}")
        st.write(f"选中任务数: {len(global_state.get('selected_tasks', []))}")
        
        # 导出为JSON字符串
        json_str = export_global_state_json()
        
        # 添加编辑区域
        edited_json = st.text_area("编辑状态JSON", json_str, height=400)
        
        # 保存修改按钮
        if st.button("保存修改"):
            if import_global_state_json(edited_json):
                st.success("状态已更新")
            else:
                st.error("无法更新状态，JSON格式可能有误")
    
    with col2:
        st.subheader("选中任务列表")
        
        # 显示选中的任务
        selected_tasks = global_state.get('selected_tasks', [])
        if selected_tasks:
            for i, task in enumerate(selected_tasks):
                st.write(f"{i+1}. {task}")
                # 添加移除按钮
                if st.button("移除", key=f"remove_{i}"):
                    if task in global_state['selected']:
                        global_state['selected'][task] = False
                    global_state['selected_tasks'].remove(task)
                    update_global_state(global_state)
                    st.rerun()
        else:
            st.info("没有选中的任务")
        
        st.subheader("选择状态")
        
        # 显示所有任务的选择状态
        st.write("任务选择状态预览:")
        
        # 创建表格展示所有任务的状态
        task_states = []
        for task, is_selected in global_state.get('selected', {}).items():
            task_states.append({"任务名称": task, "已选中": is_selected})
        
        if task_states:
            tasks_df = pd.DataFrame(task_states)
            st.dataframe(tasks_df, use_container_width=True)
        else:
            st.info("没有任务状态信息")

if __name__ == "__main__":
    main()