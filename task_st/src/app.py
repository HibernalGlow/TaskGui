import streamlit as st
import pandas as pd
import os
import sys
import traceback
import tempfile
from code_editor import code_editor

# 导入自定义模块
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

# 导入新的模块化组件
from src.ui.config import setup_page_config
from src.ui.styles import apply_custom_css, add_clipboard_js
from src.tabs.settings import render_settings_tab
from src.tabs.preview_tab import render_preview_tab

# 导入Pillow增强插件
try:
    import pillow_avif
    import pillow_jxl
    AVIF_JXL_SUPPORT = True
except ImportError:
    AVIF_JXL_SUPPORT = False
    print("提示：未找到AVIF或JXL支持库，建议安装：pip install pillow-avif-plugin pillow-jpegxl")

def main():
    """主函数"""
    try:
        # 初始化会话状态
        init_session_state()
        
        # 设置CSS样式
        setup_css()
        
        # 初始化全局状态
        init_global_state()
        
        # 加载背景设置
        if 'background_settings' not in st.session_state:
            st.session_state.background_settings = load_background_settings()
            # 确保侧边栏横幅设置存在
            if 'sidebar_banner_enabled' not in st.session_state.background_settings:
                st.session_state.background_settings['sidebar_banner_enabled'] = False
            if 'sidebar_banner_path' not in st.session_state.background_settings:
                st.session_state.background_settings['sidebar_banner_path'] = ''
        
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
            # 显示侧边栏横幅图片
            try:
                if st.session_state.background_settings.get('sidebar_banner_enabled', False):
                    sidebar_banner_path = st.session_state.background_settings.get('sidebar_banner_path', '')
                    if sidebar_banner_path and os.path.isfile(sidebar_banner_path):
                        st.image(sidebar_banner_path, use_container_width=True)
                    else:
                        # 如果文件不存在但设置为启用，则重置此设置
                        st.session_state.background_settings['sidebar_banner_enabled'] = False
                        save_background_settings(st.session_state.background_settings)
            except Exception as e:
                # 出现任何异常，禁用横幅并继续
                print(f"显示侧边栏横幅时出错：{str(e)}")
            
            # 在侧边栏顶部渲染操作按钮
            # render_action_buttons(selected_tasks, default_taskfile, key_prefix="sidebar", is_sidebar=True)
            
            # 渲染侧边栏
            render_sidebar(default_taskfile)
        
        # 渲染标签过滤器 - 代码已移至侧边栏，仅保留调用以保持兼容性
        render_tag_filters(all_tags)
        
        # 过滤任务
        filtered_df = filter_tasks(tasks_df)
        
        # 显示顶部横幅图片
        if 'background_settings' not in st.session_state:
            st.session_state.background_settings = load_background_settings()
            
        # 如果启用了顶部横幅图片，则显示，增加更严格的错误处理
        try:
            if st.session_state.background_settings.get('header_banner_enabled', False):
                banner_path = st.session_state.background_settings.get('header_banner_path', '')
                if banner_path and os.path.isfile(banner_path):
                    st.image(banner_path, use_container_width=True)
                else:
                    # 如果文件不存在但设置为启用，则重置此设置
                    st.session_state.background_settings['header_banner_enabled'] = False
                    save_background_settings(st.session_state.background_settings)
        except Exception as e:
            # 出现任何异常，禁用横幅并继续
            st.session_state.background_settings['header_banner_enabled'] = False
            save_background_settings(st.session_state.background_settings)
            print(f"显示顶部横幅时出错：{str(e)}")
        
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
            render_preview_tab(filtered_df, default_taskfile)
        
        # 仪表盘页签
        with tabs[tab_indices["📈 仪表盘"]]:
            render_dashboard()
            
        # 设置页签
        with tabs[tab_indices["⚙️ 设置"]]:
            render_settings_tab()
        
        # 状态管理页签
        with tabs[tab_indices["🔧 状态"]]:
            render_state_manager()
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc()) 