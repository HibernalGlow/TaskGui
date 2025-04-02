import streamlit as st
import os
from src.utils.selection_utils import load_background_settings, save_background_settings, get_card_view_settings, update_card_view_settings
from src.components.sidebar import set_background_image, set_sidebar_background
from src.ui.styles import reset_background_css

def render_settings_tab():
    """渲染设置标签页"""
    st.markdown("## ⚙️ 系统设置")
    
    # 创建设置子标签页
    settings_tabs = st.tabs(["基本设置", "🎨 背景设置", "卡片设置"])
    
    # 基本设置标签页
    with settings_tabs[0]:
        render_basic_settings()
    
    # 背景设置标签页
    with settings_tabs[1]:
        render_background_settings()
        
    # 卡片设置标签页
    with settings_tabs[2]:
        render_card_settings()

def render_basic_settings():
    """渲染基本设置"""
    st.subheader("界面设置")
    st.checkbox("启用深色模式", value=False, disabled=True)
    st.checkbox("自动加载最近的任务文件", value=True, disabled=True)
    
    st.subheader("任务执行")
    st.radio("默认运行模式", options=["顺序执行", "并行执行"], index=0, disabled=True)

def render_card_settings():
    """渲染卡片设置"""
    st.subheader("卡片元素显示设置")
    
    # 获取当前卡片设置
    card_settings = get_card_view_settings()
    
    # 创建设置表单
    with st.form("card_view_settings_form"):
        st.write("选择要在任务卡片中显示的元素：")
        
        # 描述显示选项
        show_description = st.checkbox(
            "显示任务描述", 
            value=card_settings.get("show_description", True),
            help="显示任务的详细描述"
        )
        
        # 标签显示选项
        show_tags = st.checkbox(
            "显示任务标签", 
            value=card_settings.get("show_tags", True),
            help="显示任务的相关标签"
        )
        
        # 目录显示选项
        show_directory = st.checkbox(
            "显示任务目录", 
            value=card_settings.get("show_directory", True),
            help="显示任务相关的目录路径"
        )
        
        # 命令显示选项
        show_command = st.checkbox(
            "显示任务命令", 
            value=card_settings.get("show_command", True),
            help="显示执行任务的命令"
        )
        
        # 提交按钮
        submitted = st.form_submit_button("保存设置")
        
        if submitted:
            # 更新设置
            new_settings = {
                "show_description": show_description,
                "show_tags": show_tags,
                "show_directory": show_directory,
                "show_command": show_command
            }
            
            # 保存设置
            update_card_view_settings(new_settings)
            st.success("卡片显示设置已更新！")

def render_background_settings():
    """渲染背景设置"""
    st.subheader("🎨 背景设置")
    
    # 初始化背景设置
    if 'background_settings' not in st.session_state:
        st.session_state.background_settings = load_background_settings()
    
    # 拆分为主背景、侧边栏背景、顶部横幅和侧边栏横幅设置
    bg_tabs = st.tabs(["主界面背景", "侧边栏背景", "顶部横幅", "侧边栏横幅"])
    
    with bg_tabs[0]:  # 主界面背景设置
        render_main_background_settings()
    
    with bg_tabs[1]:  # 侧边栏背景设置
        render_sidebar_background_settings()
    
    with bg_tabs[2]:  # 顶部横幅设置
        render_header_banner_settings()
    
    with bg_tabs[3]:  # 侧边栏横幅设置
        render_sidebar_banner_settings()
    
    # 重置背景设置按钮
    if st.button("重置所有背景设置", key="reset_all_bg"):
        reset_all_background_settings()

def render_main_background_settings():
    """渲染主界面背景设置"""
    # 启用/禁用背景
    st.session_state.background_settings['enabled'] = st.checkbox(
        "启用背景图片",
        value=st.session_state.background_settings.get('enabled', False),
        key="main_bg_enabled"
    )
    
    if st.session_state.background_settings['enabled']:
        # 选择背景图片
        # 本地图片路径输入
        local_path = st.text_input(
            "输入本地图片路径",
            value=st.session_state.background_settings.get('image_path', ''),
            key="main_bg_local_path"
        )
        
        if local_path and os.path.isfile(local_path):
            try:
                st.session_state.background_settings['image_path'] = local_path
                # 预览图片
                st.image(local_path, caption="背景图片预览", width=300)
            except Exception as e:
                st.error(f"加载本地图片时出错: {str(e)}")
        elif local_path:
            st.warning("输入的文件路径不存在或不是有效的文件")
        
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
            if 'image_path' in st.session_state.background_settings and os.path.isfile(st.session_state.background_settings['image_path']):
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

def render_sidebar_background_settings():
    """渲染侧边栏背景设置"""
    # 启用/禁用侧边栏背景
    st.session_state.background_settings['sidebar_enabled'] = st.checkbox(
        "启用侧边栏背景",
        value=st.session_state.background_settings.get('sidebar_enabled', False),
        key="sidebar_bg_enabled"
    )
    
    if st.session_state.background_settings['sidebar_enabled']:
        # 本地图片路径输入
        sidebar_local_path = st.text_input(
            "输入本地图片路径",
            value=st.session_state.background_settings.get('sidebar_image_path', ''),
            key="sidebar_bg_local_path"
        )
        
        if sidebar_local_path and os.path.isfile(sidebar_local_path):
            try:
                st.session_state.background_settings['sidebar_image_path'] = sidebar_local_path
                # 预览图片
                st.image(sidebar_local_path, caption="侧边栏背景预览", width=250)
            except Exception as e:
                st.error(f"加载本地图片时出错: {str(e)}")
        elif sidebar_local_path:
            st.warning("输入的文件路径不存在或不是有效的文件")
        
        # 应用侧边栏背景设置
        if st.button("应用侧边栏背景", key="apply_sidebar_bg"):
            if 'sidebar_image_path' in st.session_state.background_settings and os.path.isfile(st.session_state.background_settings['sidebar_image_path']):
                # 应用侧边栏背景
                success = set_sidebar_background(st.session_state.background_settings['sidebar_image_path'])
                if success:
                    # 保存设置
                    save_background_settings(st.session_state.background_settings)
                    st.success("侧边栏背景设置已应用")
            else:
                st.error("请先选择有效的侧边栏背景图片")

def render_header_banner_settings():
    """渲染顶部横幅设置"""
    # 启用/禁用顶部横幅
    st.session_state.background_settings['header_banner_enabled'] = st.checkbox(
        "启用顶部横幅图片",
        value=st.session_state.background_settings.get('header_banner_enabled', False),
        key="header_banner_enabled"
    )
    
    if st.session_state.background_settings['header_banner_enabled']:
        # 本地图片路径输入
        banner_local_path = st.text_input(
            "输入本地图片路径",
            value=st.session_state.background_settings.get('header_banner_path', ''),
            key="header_banner_local_path"
        )
        
        if banner_local_path and os.path.isfile(banner_local_path):
            try:
                st.session_state.background_settings['header_banner_path'] = banner_local_path
                # 预览图片
                st.image(banner_local_path, caption="顶部横幅预览", use_container_width=True)
            except Exception as e:
                st.error(f"加载本地图片时出错: {str(e)}")
        elif banner_local_path:
            st.warning("输入的文件路径不存在或不是有效的文件")
        
        # 应用顶部横幅设置
        if st.button("应用顶部横幅设置", key="apply_header_banner"):
            # 验证横幅图片路径是否有效
            banner_path = st.session_state.background_settings.get('header_banner_path', '')
            if banner_path and os.path.isfile(banner_path):
                # 保存设置
                save_background_settings(st.session_state.background_settings)
                st.success("顶部横幅设置已应用")
            else:
                st.error("无法应用设置：请先选择有效的图片文件")
                # 如果路径无效，不启用横幅
                st.session_state.background_settings['header_banner_enabled'] = False

def render_sidebar_banner_settings():
    """渲染侧边栏横幅设置"""
    # 获取全局AVIF和JXL支持状态
    try:
        import pillow_avif
        import pillow_jxl
        AVIF_JXL_SUPPORT = True
    except ImportError:
        AVIF_JXL_SUPPORT = False
        
    # 启用/禁用侧边栏横幅
    st.session_state.background_settings['sidebar_banner_enabled'] = st.checkbox(
        "启用侧边栏横幅图片",
        value=st.session_state.background_settings.get('sidebar_banner_enabled', False),
        key="sidebar_banner_enabled"
    )
    
    if st.session_state.background_settings['sidebar_banner_enabled']:
        # 定义支持的图片格式
        SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'gif', 'webp']
        if AVIF_JXL_SUPPORT:
            SUPPORTED_FORMATS.extend(['avif', 'jxl'])
        
        # 本地图片路径输入
        sidebar_banner_local_path = st.text_input(
            f"输入本地图片路径 (支持{', '.join(SUPPORTED_FORMATS)}格式)",
            value=st.session_state.background_settings.get('sidebar_banner_path', ''),
            key="sidebar_banner_local_path"
        )
        
        if sidebar_banner_local_path and os.path.isfile(sidebar_banner_local_path):
            try:
                st.session_state.background_settings['sidebar_banner_path'] = sidebar_banner_local_path
                # 预览图片
                st.image(sidebar_banner_local_path, caption="侧边栏横幅预览", width=250)
            except Exception as e:
                st.error(f"加载本地图片时出错: {str(e)}")
        elif sidebar_banner_local_path:
            st.warning("输入的文件路径不存在或不是有效的文件")
        
        # 应用侧边栏横幅设置
        if st.button("应用侧边栏横幅设置", key="apply_sidebar_banner"):
            # 验证横幅图片路径是否有效
            banner_path = st.session_state.background_settings.get('sidebar_banner_path', '')
            if banner_path and os.path.isfile(banner_path):
                # 保存设置
                save_background_settings(st.session_state.background_settings)
                st.success("侧边栏横幅设置已应用")
            else:
                st.error("无法应用设置：请先选择有效的图片文件")
                # 如果路径无效，不启用横幅
                st.session_state.background_settings['sidebar_banner_enabled'] = False

def reset_all_background_settings():
    """重置所有背景设置"""
    st.session_state.background_settings = {
        'enabled': False,
        'sidebar_enabled': False,
        'header_banner_enabled': False,
        'sidebar_banner_enabled': False,
        'image_path': '',
        'sidebar_image_path': '',
        'header_banner_path': '',
        'sidebar_banner_path': '',
        'opacity': 0.5,
        'blur': 0
    }
    save_background_settings(st.session_state.background_settings)
    
    # 重置CSS
    reset_background_css()
    
    st.success("所有背景设置已重置") 