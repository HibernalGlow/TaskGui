import streamlit as st
import pandas as pd
import os
import sys
import traceback
import tempfile
from code_editor import code_editor
from src.utils.session_utils import init_session_state, setup_css
from src.services.taskfile import load_taskfile, read_taskfile
from src.services.dataframe import prepare_dataframe, filter_tasks
from src.components.tag_filters import get_all_tags, render_tag_filters
from src.views.table.table_view import render_table_view
from src.views.card.card_view import render_card_view
from src.components.sidebar import render_sidebar, get_base64_encoded_image, set_background_image, set_sidebar_background
from src.utils.file_utils import open_file, get_directory_files, find_taskfiles, get_nearest_taskfile, copy_to_clipboard, get_task_command
from src.services.task_runner import run_task_via_cmd, run_multiple_tasks
from src.components.preview_card import render_action_buttons
from src.manage.state_manager import render_state_manager
from src.tabs.dashboard import render_dashboard
from src.utils.selection_utils import (
    get_global_state, update_global_state, 
    export_yaml_state as export_global_state_yaml, 
    import_global_state_yaml,
    save_global_state, register_task_file, register_tasks_from_df,
    update_task_runtime, record_task_run, init_global_state,
    display_yaml_in_ui, validate_yaml, get_selected_tasks,
    load_background_settings, save_background_settings
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
        
        # 从全局状态获取选中的任务
        selected_tasks = get_selected_tasks()
        
        # 侧边栏内容
        with st.sidebar:
            # 在侧边栏顶部渲染操作按钮
            render_action_buttons(selected_tasks, default_taskfile, key_prefix="sidebar", is_sidebar=True)
            
            # 渲染侧边栏
            render_sidebar(default_taskfile)
        
        # 渲染标签过滤器 - 代码已移至侧边栏，仅保留调用以保持兼容性
        render_tag_filters(all_tags)
        
        # 过滤任务
        filtered_df = filter_tasks(tasks_df)
        
        # 渲染主界面操作按钮
        render_action_buttons(selected_tasks, default_taskfile, key_prefix="main_preview")
        
        # 使用字典存储页签标题和索引的映射，便于动态管理
        tab_names = ["📊 表格", "🗂️ 卡片", "🔍 预览", "📈 仪表盘", "⚙️ 设置", "🔧 状态"]
        tab_indices = {name: idx for idx, name in enumerate(tab_names)}
        
        # 创建页签
        tabs = st.tabs(tab_names)
        
        # 表格视图
        with tabs[tab_indices["📊 表格"]]:
            render_table_view(filtered_df, default_taskfile, show_sidebar=False)  # 关闭右侧预览
        
        # 卡片视图
        with tabs[tab_indices["🗂️ 卡片"]]:
            render_card_view(filtered_df, default_taskfile)
        
        # 预览页签
        with tabs[tab_indices["🔍 预览"]]:
            # 获取选中的任务
            selected_tasks = get_selected_tasks()
            if not selected_tasks:
                st.info("没有选中的任务。请从表格中选择要操作的任务。")
            else:
                # 筛选出选中的任务数据
                selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)].copy()
                # 使用卡片视图函数显示
                # st.markdown(f"## 已选择 {len(selected_tasks)} 个任务")
                render_card_view(selected_df, default_taskfile, key_prefix="preview_view")
        
        # 仪表盘页签
        with tabs[tab_indices["📈 仪表盘"]]:
            render_dashboard()
        # 设置页签
        with tabs[tab_indices["⚙️ 设置"]]:
            st.markdown("## ⚙️ 系统设置")
            
            # 创建设置子标签页
            settings_tabs = st.tabs(["基本设置", "🎨 背景设置"])
            
            # 基本设置标签页
            with settings_tabs[0]:
                st.subheader("界面设置")
                st.checkbox("启用深色模式", value=False, disabled=True)
                st.checkbox("自动加载最近的任务文件", value=True, disabled=True)
                
                st.subheader("任务执行")
                st.radio("默认运行模式", options=["顺序执行", "并行执行"], index=0, disabled=True)
            
            # 背景设置标签页
            with settings_tabs[1]:
                st.subheader("🎨 背景设置")
                
                # 初始化背景设置
                if 'background_settings' not in st.session_state:
                    st.session_state.background_settings = load_background_settings()
                
                # 拆分为主背景和侧边栏背景设置
                bg_tabs = st.tabs(["主界面背景", "侧边栏背景"])
                
                with bg_tabs[0]:  # 主界面背景设置
                    # 启用/禁用背景
                    st.session_state.background_settings['enabled'] = st.checkbox(
                        "启用背景图片",
                        value=st.session_state.background_settings.get('enabled', False),
                        key="main_bg_enabled"
                    )
                    
                    if st.session_state.background_settings['enabled']:
                        # 选择背景图片
                        uploaded_file = st.file_uploader(
                            "选择背景图片",
                            type=['png', 'jpg', 'jpeg', 'gif'],
                            key="main_background_image"
                        )
                        
                        if uploaded_file is not None:
                            # 保存图片到临时目录
                            temp_dir = tempfile.gettempdir()
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            st.session_state.background_settings['image_path'] = temp_path
                            # 存储base64编码的图片
                            st.session_state.background_settings['image_base64'] = get_base64_encoded_image(temp_path)
                            st.session_state.background_settings['image_format'] = uploaded_file.name.split('.')[-1].lower()
                        
                        # 透明度调节
                        st.session_state.background_settings['opacity'] = st.slider(
                            "背景透明度",
                            min_value=0.0,
                            max_value=1.0,
                            value=st.session_state.background_settings.get('opacity', 0.5),
                            step=0.1,
                            key="main_bg_opacity"
                        )
                        
                        # 模糊度调节
                        st.session_state.background_settings['blur'] = st.slider(
                            "背景模糊度",
                            min_value=0,
                            max_value=20,
                            value=st.session_state.background_settings.get('blur', 0),
                            step=1,
                            key="main_bg_blur"
                        )
                        
                        # 应用背景设置
                        if st.button("应用主界面背景", key="apply_main_bg"):
                            if 'image_path' in st.session_state.background_settings and os.path.exists(st.session_state.background_settings['image_path']):
                                # 应用背景
                                success = set_background_image(
                                    st.session_state.background_settings['image_path'],
                                    st.session_state.background_settings['opacity'],
                                    st.session_state.background_settings['blur']
                                )
                                if success:
                                    # 保存设置
                                    save_background_settings(st.session_state.background_settings)
                                    st.success("主界面背景设置已应用")
                            else:
                                st.error("请先选择有效的背景图片")
                
                with bg_tabs[1]:  # 侧边栏背景设置
                    # 启用/禁用侧边栏背景
                    st.session_state.background_settings['sidebar_enabled'] = st.checkbox(
                        "启用侧边栏背景",
                        value=st.session_state.background_settings.get('sidebar_enabled', False),
                        key="sidebar_bg_enabled"
                    )
                    
                    if st.session_state.background_settings['sidebar_enabled']:
                        # 选择侧边栏背景图片
                        sidebar_uploaded_file = st.file_uploader(
                            "选择侧边栏背景图片",
                            type=['png', 'jpg', 'jpeg', 'gif'],
                            key="sidebar_background_image"
                        )
                        
                        if sidebar_uploaded_file is not None:
                            # 保存图片到临时目录
                            temp_dir = tempfile.gettempdir()
                            sidebar_temp_path = os.path.join(temp_dir, sidebar_uploaded_file.name)
                            with open(sidebar_temp_path, "wb") as f:
                                f.write(sidebar_uploaded_file.getbuffer())
                            st.session_state.background_settings['sidebar_image_path'] = sidebar_temp_path
                            # 存储base64编码的图片
                            st.session_state.background_settings['sidebar_image_base64'] = get_base64_encoded_image(sidebar_temp_path)
                            st.session_state.background_settings['sidebar_image_format'] = sidebar_uploaded_file.name.split('.')[-1].lower()
                        
                        # 应用侧边栏背景设置
                        if st.button("应用侧边栏背景", key="apply_sidebar_bg"):
                            if 'sidebar_image_path' in st.session_state.background_settings and os.path.exists(st.session_state.background_settings['sidebar_image_path']):
                                # 应用侧边栏背景
                                success = set_sidebar_background(st.session_state.background_settings['sidebar_image_path'])
                                if success:
                                    # 保存设置
                                    save_background_settings(st.session_state.background_settings)
                                    st.success("侧边栏背景设置已应用")
                            else:
                                st.error("请先选择有效的侧边栏背景图片")
                
                # 重置背景设置按钮
                if st.button("重置所有背景设置", key="reset_all_bg"):
                    st.session_state.background_settings = {
                        'enabled': False,
                        'sidebar_enabled': False,
                        'image_path': '',
                        'sidebar_image_path': '',
                        'opacity': 0.5,
                        'blur': 0
                    }
                    save_background_settings(st.session_state.background_settings)
                    
                    # 重置CSS
                    st.markdown("""
                    <style>
                    .stApp {
                        background-image: none;
                    }
                    [data-testid="stSidebar"] > div:first-child {
                        background-image: none;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.success("所有背景设置已重置")
        
        # 状态管理页签
        with tabs[tab_indices["🔧 状态"]]:
            render_state_manager()
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()