import streamlit as st
import pandas as pd
import os
import sys
import traceback
from code_editor import code_editor
from src.utils.session_utils import init_session_state, setup_css
from src.services.taskfile import load_taskfile, read_taskfile
from src.services.dataframe import prepare_dataframe, filter_tasks
from src.components.tag_filters import get_all_tags, render_tag_filters
from src.views.table.table_view import render_table_view
from src.views.card.card_view import render_card_view
from src.components.sidebar import render_sidebar
from src.utils.file_utils import open_file, get_directory_files, find_taskfiles, get_nearest_taskfile, copy_to_clipboard, get_task_command
from src.services.task_runner import run_task_via_cmd, run_multiple_tasks
from src.components.styles import apply_custom_styles
from src.components.preview_card import render_shared_preview
from src.manage.state_manager import render_state_manager
from src.utils.selection_utils import (
    get_global_state, update_global_state, 
    export_yaml_state as export_global_state_yaml, 
    import_global_state_yaml,
    save_global_state, register_task_file, register_tasks_from_df,
    update_task_runtime, record_task_run, init_global_state,
    display_yaml_in_ui, validate_yaml
)

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
    
    /* YAML编辑器样式 */
    .yaml-editor {
        font-family: monospace;
        border-radius: 4px;
        background-color: #282c34;
        color: #e6e6e6;
        padding: 16px;
        border: 1px solid #444;
        font-size: 14px;
        line-height: 1.5;
    }
    
    /* 自定义文本区域样式，使其看起来像代码编辑器 */
    .stTextArea textarea {
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
        padding: 12px !important;
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        border: 1px solid #3e3e3e !important;
        border-radius: 4px !important;
    }
    
    /* 字段标签隐藏 */
    .hide-label .stTextArea label {
        display: none;
    }
    
    /* 语法高亮区域 */
    .yaml-preview {
        background-color: #282c34;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
        border: 1px solid #444;
        overflow-x: auto;
    }
    
    /* 复制按钮样式 */
    .copy-button {
        position: absolute;
        top: 5px;
        right: 5px;
        padding: 5px 10px;
        background-color: #4a4a4a;
        color: white;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
    }
    
    .copy-button:hover {
        background-color: #616161;
    }
    
    /* markdown代码块样式增强 */
    pre {
        position: relative;
        background-color: #282c34 !important;
        padding: 15px !important;
        border-radius: 5px !important;
        margin-bottom: 15px !important;
    }
    
    code {
        font-family: 'Courier New', Courier, monospace !important;
        color: #d4d4d4 !important;
    }
</style>
""", unsafe_allow_html=True)

# 添加复制到剪贴板的JavaScript函数
st.markdown("""
<script>
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    alert('已复制到剪贴板!');
}
</script>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    try:
        # 初始化会话状态
        init_session_state()
        
        # 设置CSS样式
        setup_css()
        
        # 初始化全局状态
        init_global_state()
        
        # 获取任务文件列表
        taskfiles = find_taskfiles()
        if not taskfiles:
            st.error("未找到任务文件。请确保当前目录下有Taskfile.yml文件。")
            return
        
        # 获取默认任务文件
        default_taskfile = get_nearest_taskfile()
        if not default_taskfile:
            default_taskfile = taskfiles[0]
        
        # 注册任务文件
        register_task_file(default_taskfile)
        
        # 加载任务文件
        tasks_df = load_taskfile(default_taskfile)
        if tasks_df is None or tasks_df.empty:
            st.error("无法加载任务文件或任务文件为空。")
            return
        
        # 注册所有任务
        register_tasks_from_df(tasks_df, default_taskfile)
        
        # 准备数据框
        tasks_df = prepare_dataframe(tasks_df)
        
        # 获取所有标签
        all_tags = get_all_tags(tasks_df)
        
        # 渲染侧边栏
        render_sidebar(default_taskfile)
        
        # 渲染标签过滤器 - 代码已移至侧边栏，仅保留调用以保持兼容性
        render_tag_filters(all_tags)
        
        # 过滤任务
        filtered_df = filter_tasks(tasks_df)
        
        # 共享预览区域 - 放在页签上方
        preview_expander = st.expander("📌 选中任务预览", expanded=True)
        with preview_expander:
            render_shared_preview(filtered_df, default_taskfile)
        
        # 使用字典存储页签标题和索引的映射，便于动态管理
        tab_names = ["📊 表格视图", "🗂️ 卡片视图", "📈 仪表盘", "⚙️ 设置", "🔍 状态管理"]
        tab_indices = {name: idx for idx, name in enumerate(tab_names)}
        
        # 创建页签
        tabs = st.tabs(tab_names)
        
        # 表格视图
        with tabs[tab_indices["📊 表格视图"]]:
            render_table_view(filtered_df, default_taskfile, show_sidebar=False)  # 关闭右侧预览
        
        # 卡片视图
        with tabs[tab_indices["🗂️ 卡片视图"]]:
            render_card_view(filtered_df, default_taskfile)
        
        # 仪表盘页签
        with tabs[tab_indices["📈 仪表盘"]]:
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
        with tabs[tab_indices["⚙️ 设置"]]:
            st.markdown("## ⚙️ 系统设置")
            st.info("设置功能正在开发中...")
            
            # 示例设置选项
            st.subheader("界面设置")
            st.checkbox("启用深色模式", value=False, disabled=True)
            st.checkbox("自动加载最近的任务文件", value=True, disabled=True)
            
            st.subheader("任务执行")
            st.radio("默认运行模式", options=["顺序执行", "并行执行"], index=0, disabled=True)
        
        # 状态管理页签
        with tabs[tab_indices["🔍 状态管理"]]:
            render_state_manager()
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()