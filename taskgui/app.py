import streamlit as st
import pandas as pd
import os
import sys
import traceback
import tempfile
import time
import gc
from code_editor import code_editor

# 首先执行配置文件迁移
from .config.migrate_config import migrate_config_file
migrate_config_file()

# 导入自定义模块
from taskgui.utils.session_utils import init_session_state, setup_css
from taskgui.services.taskfile import load_taskfile, read_taskfile
from taskgui.services.dataframe import prepare_dataframe, filter_tasks
from taskgui.components.tag_filters import get_all_tags, render_tag_filters
from taskgui.views.table.table_view import render_table_view
from taskgui.views.card.card_view import render_card_view
from taskgui.components.sidebar import render_sidebar, get_base64_encoded_image, set_background_image, set_sidebar_background
from taskgui.utils.file_utils import open_file, get_directory_files, find_taskfiles, get_nearest_taskfile, copy_to_clipboard, get_task_command
from taskgui.services.task_runner import run_task_via_cmd, run_multiple_tasks
from taskgui.components.preview_card import render_action_buttons
from taskgui.manage.state_manager import render_state_manager
from taskgui.tabs.dashboard import render_dashboard
from taskgui.utils.selection_utils import (
    get_global_state, update_global_state, 
    export_yaml_state as export_global_state_yaml, 
    import_global_state_yaml,
    save_global_state, register_task_file, register_tasks_from_df,
    update_task_runtime, record_task_run, init_global_state,
    display_yaml_in_ui, validate_yaml, get_selected_tasks,
    load_background_settings, save_background_settings,
    get_memory_usage, run_gc, clear_memory_cache
)

# 导入新的模块化组件
from taskgui.ui.config import setup_page_config
from taskgui.ui.styles import apply_custom_css, add_clipboard_js
from taskgui.tabs.settings import render_settings_tab, load_basic_settings
from taskgui.tabs.preview_tab import render_preview_tab

# 导入Pillow增强插件
try:
    import pillow_avif
    import pillow_jxl
    AVIF_JXL_SUPPORT = True
except ImportError:
    AVIF_JXL_SUPPORT = False
    print("提示：未找到AVIF或JXL支持库，建议安装：pip install pillow-avif-plugin pillow-jpegxl")

# 内存监控配置
MEMORY_MONITOR_INTERVAL = 300  # 内存监控间隔（秒）
last_memory_monitor_time = 0

def monitor_memory_usage():
    """监控内存使用情况"""
    global last_memory_monitor_time
    
    current_time = time.time()
    if current_time - last_memory_monitor_time < MEMORY_MONITOR_INTERVAL:
        return
    
    last_memory_monitor_time = current_time
    
    try:
        # 获取内存使用情况
        memory_usage = get_memory_usage()
        
        # 记录内存使用情况
        print(f"内存监控 - 使用: {memory_usage['rss']:.2f} MB ({memory_usage['percent']:.2f}%), 缓存: {memory_usage['cache_size']:.2f} KB")
        
        # 如果内存使用率超过80%，执行垃圾回收
        if memory_usage["percent"] > 80:
            print(f"内存使用率较高 ({memory_usage['percent']:.2f}%)，执行垃圾回收")
            run_gc()
            
            # 再次检查内存使用情况
            memory_usage = get_memory_usage()
            print(f"垃圾回收后内存使用: {memory_usage['rss']:.2f} MB ({memory_usage['percent']:.2f}%)")
    except Exception as e:
        print(f"监控内存使用情况时出错: {str(e)}")

def main():
    """主函数"""
    try:
        # 初始化会话状态
        init_session_state()
        
        # 设置CSS样式
        setup_css()
        
        # 初始化全局状态
        init_global_state()
        
        # 初始化AgGrid设置
        from taskgui.views.table.aggrid_config import init_aggrid_settings
        init_aggrid_settings()
        
        # 加载背景设置
        if 'background_settings' not in st.session_state:
            st.session_state.background_settings = load_background_settings()
            # 确保侧边栏横幅设置存在
            if 'sidebar_banner_enabled' not in st.session_state.background_settings:
                st.session_state.background_settings['sidebar_banner_enabled'] = False
            if 'sidebar_banner_path' not in st.session_state.background_settings:
                st.session_state.background_settings['sidebar_banner_path'] = ''
        
        # 获取任务文件管理器
        from taskgui.config.taskfile_manager import get_taskfile_manager
        taskfile_manager = get_taskfile_manager()
        
        # 确保st.session_state.taskfiles_config已初始化
        if not hasattr(st.session_state, 'taskfiles_config'):
            st.session_state.taskfiles_config = taskfile_manager.load_taskfiles_config()
            
        # 获取可用Taskfile列表
        taskfiles = find_taskfiles()
        if not taskfiles:
            st.error("未找到任务文件。请确保当前目录下有Taskfile.yml文件。")
            return
        
        # 获取当前活动Taskfile或默认Taskfile
        active_taskfile = taskfile_manager.get_active_taskfile()
        if not active_taskfile:
            # 如果没有活动任务文件，使用第一个可用的任务文件
            default_taskfile = taskfiles[0]
            
            # 设置为活动任务文件
            taskfile_manager.set_active_taskfile(default_taskfile)
            active_taskfile = default_taskfile
        
        # 确保活动任务文件存在
        if not os.path.exists(active_taskfile):
            # 如果活动任务文件不存在，重置为默认值
            default_taskfile = get_nearest_taskfile(prefer_config=True)
            if not default_taskfile:
                default_taskfile = taskfiles[0] if taskfiles else None
                
            if default_taskfile:
                # 设置为活动任务文件
                taskfile_manager.set_active_taskfile(default_taskfile)
                active_taskfile = default_taskfile
            else:
                st.error("未找到有效的Taskfile，请添加或创建一个。")
                active_taskfile = None
        
        # 注册任务文件
        register_task_file(active_taskfile)
        
        # 加载任务文件
        tasks_df = load_taskfile(active_taskfile)
        if tasks_df is None or tasks_df.empty:
            st.error("无法加载任务文件或任务文件为空。")
            return
        
        # 注册所有任务
        register_tasks_from_df(tasks_df, active_taskfile)
        
        # 准备数据框
        tasks_df = prepare_dataframe(tasks_df)
        
        # 获取所有标签
        all_tags = get_all_tags(tasks_df)
        
        # 从全局状态获取选中的任务
        selected_tasks = get_selected_tasks()
        
        # 监控内存使用情况
        monitor_memory_usage()
        
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
            
            # 渲染侧边栏
            render_sidebar(active_taskfile)
        
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
        
        # 加载基本设置以确定要显示哪些标签页
        if 'basic_settings' not in st.session_state:
            st.session_state.basic_settings = load_basic_settings()
        
        # 使用字典存储页签标题和索引的映射，便于动态管理
        all_tab_names = ["🗂️ 卡片", "📊 表格", "🔍 预览", "📈 仪表盘", "⚙️ 设置", "🔧 状态"]
        all_tab_features = ["show_card_tab", "show_table_tab", "show_preview_tab", "show_dashboard_tab", "show_settings_tab", "show_state_tab"]
        
        # 根据设置决定要显示哪些标签页
        tab_names = []
        for i, tab_name in enumerate(all_tab_names):
            feature_name = all_tab_features[i]
            if st.session_state.basic_settings.get(feature_name, True):
                tab_names.append(tab_name)
        
        # 如果没有启用任何标签页，默认至少启用设置页
        if len(tab_names) == 0:
            tab_names = ["⚙️ 设置"]
        
        # 创建索引映射
        tab_indices = {name: idx for idx, name in enumerate(tab_names)}
        
        # 创建页签
        tabs = st.tabs(tab_names)
        
        # 表格视图
        if "📊 表格" in tab_indices:
            with tabs[tab_indices["📊 表格"]]:
                render_table_view(filtered_df, active_taskfile, show_sidebar=False)  # 关闭右侧预览
        
        # 卡片视图
        if "🗂️ 卡片" in tab_indices:
            with tabs[tab_indices["🗂️ 卡片"]]:
                render_card_view(filtered_df, active_taskfile)
        
        # 预览页签
        if "🔍 预览" in tab_indices:
            with tabs[tab_indices["🔍 预览"]]:
                render_preview_tab(filtered_df, active_taskfile)
        
        # 仪表盘页签
        if "📈 仪表盘" in tab_indices:
            with tabs[tab_indices["📈 仪表盘"]]:
                render_dashboard()
            
        # 设置页签
        if "⚙️ 设置" in tab_indices:
            with tabs[tab_indices["⚙️ 设置"]]:
                render_settings_tab()
        
        # 状态管理页签
        if "🔧 状态" in tab_indices:
            with tabs[tab_indices["🔧 状态"]]:
                render_state_manager()
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc())