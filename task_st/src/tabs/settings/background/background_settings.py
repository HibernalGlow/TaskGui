import streamlit as st
import os
import re
from src.utils.selection_utils import load_background_settings, save_background_settings
from src.components.sidebar import set_background_image, set_sidebar_background
from src.ui.styles import reset_background_css

def load_background_color_settings():
    """从config.toml文件加载背景色设置，包括RGB值和透明度设置"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), ".streamlit", "config.toml")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()
            
            # 使用正则表达式提取背景色RGB值和透明度
            import re
            # 提取主背景色
            main_bg_match = re.search(r'backgroundColor\s*=\s*"rgba\(([^,]+),([^,]+),([^,]+),\s*([0-9.]+)\)"', config_content)
            if main_bg_match:
                main_r = int(main_bg_match.group(1).strip())
                main_g = int(main_bg_match.group(2).strip())
                main_b = int(main_bg_match.group(3).strip())
                main_bg_alpha = float(main_bg_match.group(4))
            else:
                main_r, main_g, main_b = 240, 242, 246
                main_bg_alpha = 1.0
            
            # 提取次要背景色
            sec_bg_match = re.search(r'secondaryBackgroundColor\s*=\s*"rgba\(([^,]+),([^,]+),([^,]+),\s*([0-9.]+)\)"', config_content)
            if sec_bg_match:
                sec_r = int(sec_bg_match.group(1).strip())
                sec_g = int(sec_bg_match.group(2).strip())
                sec_b = int(sec_bg_match.group(3).strip())
                sec_bg_alpha = float(sec_bg_match.group(4))
            else:
                sec_r, sec_g, sec_b = 240, 242, 246
                sec_bg_alpha = 1.0
            
            return {
                'main_r': main_r,
                'main_g': main_g,
                'main_b': main_b,
                'main_bg_alpha': main_bg_alpha,
                'sec_r': sec_r,
                'sec_g': sec_g,
                'sec_b': sec_b,
                'secondary_bg_alpha': sec_bg_alpha
            }
        
        return {
            'main_r': 240,
            'main_g': 242,
            'main_b': 246,
            'main_bg_alpha': 1.0,
            'sec_r': 240,
            'sec_g': 242,
            'sec_b': 246,
            'secondary_bg_alpha': 1.0
        }
    except Exception as e:
        print(f"读取背景色设置时出错: {str(e)}")
        return {
            'main_r': 240,
            'main_g': 242,
            'main_b': 246,
            'main_bg_alpha': 1.0,
            'sec_r': 240,
            'sec_g': 242,
            'sec_b': 246,
            'secondary_bg_alpha': 1.0
        }

def render_background_settings():
    """渲染背景设置"""
    st.subheader("🎨 背景设置")
    
    # 初始化背景设置
    if 'background_settings' not in st.session_state:
        st.session_state.background_settings = load_background_settings()
    
    # 添加背景色透明度快速调整部分
    st.write("### 背景色透明度快速调整")
    
    # 如果不存在toml设置，从config.toml文件加载
    if 'toml_bg_settings' not in st.session_state:
        st.session_state.toml_bg_settings = load_background_color_settings()
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 在第一列显示预览和主背景透明度滑块
    with col1:
        st.markdown("#### 主背景色透明度")
        main_alpha = st.slider(
            "主背景透明度", 
            min_value=0.0, 
            max_value=1.0, 
            value=st.session_state.toml_bg_settings.get('main_bg_alpha', 0.7),
            step=0.1,
            key="main_bg_alpha"
        )
        st.session_state.toml_bg_settings['main_bg_alpha'] = main_alpha
        
        # 主背景色预览
        r = st.session_state.toml_bg_settings.get('main_r', 240)
        g = st.session_state.toml_bg_settings.get('main_g', 242)
        b = st.session_state.toml_bg_settings.get('main_b', 246)
        st.markdown(
            f"""
            <div style="
                background-color: rgba({r}, {g}, {b}, {main_alpha}); 
                padding: 20px; 
                border-radius: 5px; 
                text-align: center;
                border: 1px solid #ddd;
                margin-top: 10px;
            ">
                主背景色预览 (透明度: {main_alpha})
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 在第二列显示预览和次要背景透明度滑块
    with col2:
        st.markdown("#### 次要背景色透明度")
        secondary_alpha = st.slider(
            "次要背景透明度", 
            min_value=0.0, 
            max_value=1.0,
            value=st.session_state.toml_bg_settings.get('secondary_bg_alpha', 0.7),
            step=0.1,
            key="secondary_bg_alpha"
        )
        st.session_state.toml_bg_settings['secondary_bg_alpha'] = secondary_alpha
        
        # 次要背景色预览
        r = st.session_state.toml_bg_settings.get('sec_r', 240)
        g = st.session_state.toml_bg_settings.get('sec_g', 242)
        b = st.session_state.toml_bg_settings.get('sec_b', 246)
        st.markdown(
            f"""
            <div style="
                background-color: rgba({r}, {g}, {b}, {secondary_alpha}); 
                padding: 20px; 
                border-radius: 5px; 
                text-align: center;
                border: 1px solid #ddd;
                margin-top: 10px;
            ">
                次要背景色预览 (透明度: {secondary_alpha})
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 添加应用按钮
    if st.button("应用背景色透明度", key="apply_bg_alpha"):
        try:
            # 读取当前的config.toml文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), ".streamlit", "config.toml")
            
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_content = f.read()
                
                # 获取RGB值
                main_r = st.session_state.toml_bg_settings.get('main_r', 240)
                main_g = st.session_state.toml_bg_settings.get('main_g', 242)
                main_b = st.session_state.toml_bg_settings.get('main_b', 246)
                sec_r = st.session_state.toml_bg_settings.get('sec_r', 240)
                sec_g = st.session_state.toml_bg_settings.get('sec_g', 242)
                sec_b = st.session_state.toml_bg_settings.get('sec_b', 246)
                
                # 使用正则表达式替换背景色设置
                # 替换主背景色
                config_content = re.sub(
                    r'backgroundColor\s*=\s*"[^"]*"', 
                    f'backgroundColor = "rgba({main_r}, {main_g}, {main_b}, {main_alpha})"', 
                    config_content
                )
                # 替换次要背景色
                config_content = re.sub(
                    r'secondaryBackgroundColor\s*=\s*"[^"]*"', 
                    f'secondaryBackgroundColor = "rgba({sec_r}, {sec_g}, {sec_b}, {secondary_alpha})"', 
                    config_content
                )
                
                # 保存更新后的配置文件
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(config_content)
                
                st.success("背景色透明度设置已应用，请刷新页面查看效果")
                # 添加刷新按钮
                if st.button("刷新页面", key="refresh_after_bg_change"):
                    st.rerun()
            else:
                st.error("无法找到配置文件：.streamlit/config.toml")
        except Exception as e:
            st.error(f"应用背景色透明度时出错: {str(e)}")
    
    st.markdown("---")
    
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
    
    # 重置背景色透明度
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), ".streamlit", "config.toml")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()
            
            # 使用正则表达式替换背景色设置为默认值
            # 替换主背景色
            config_content = re.sub(
                r'backgroundColor\s*=\s*"[^"]*"', 
                'backgroundColor = "rgba(255, 255, 255, 1.0)"', 
                config_content
            )
            # 替换次要背景色
            config_content = re.sub(
                r'secondaryBackgroundColor\s*=\s*"[^"]*"', 
                'secondaryBackgroundColor = "rgba(240, 242, 246, 1.0)"', 
                config_content
            )
            
            # 保存更新后的配置文件
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_content)
                
            # 重置toml背景色设置
            if 'toml_bg_settings' in st.session_state:
                st.session_state.toml_bg_settings = {
                    'main_bg_alpha': 1.0,
                    'secondary_bg_alpha': 1.0
                }
    except Exception as e:
        st.error(f"重置背景色透明度时出错: {str(e)}")
    
    # 重置CSS
    reset_background_css()
    
    st.success("所有背景设置已重置")
    
    # 提示用户刷新页面
    st.info("请刷新页面以查看变更效果")
    if st.button("刷新页面", key="refresh_after_reset"):
        st.rerun() 