import streamlit as st
from src.services.taskfile import read_taskfile
from streamlit_tags import st_tags
from src.utils.selection_utils import save_favorite_tags, save_background_settings, load_background_settings
import os
import sys
import subprocess
import base64

def get_base64_encoded_image(image_path):
    """获取图片的base64编码"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def set_background_image(image_path, opacity=0.5, blur=0):
    """设置背景图片"""
    try:
        # 获取图片格式
        img_format = image_path.split('.')[-1].lower()
        if img_format not in ['png', 'jpg', 'jpeg', 'gif']:
            img_format = 'png'  # 默认使用png格式
        
        # 获取图片的base64编码
        img_base64 = get_base64_encoded_image(image_path)
        
        # 应用CSS样式
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/{img_format};base64,{img_base64});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .stApp::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: inherit;
                filter: blur({blur}px) brightness({1 - opacity});
                z-index: -1;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        return True
    except Exception as e:
        st.error(f"设置背景图片失败: {str(e)}")
        return False

def set_sidebar_background(image_path):
    """设置侧边栏背景图片"""
    try:
        # 获取图片格式
        img_format = image_path.split('.')[-1].lower()
        if img_format not in ['png', 'jpg', 'jpeg', 'gif']:
            img_format = 'png'  # 默认使用png格式
        
        # 获取图片的base64编码
        img_base64 = get_base64_encoded_image(image_path)
        
        # 应用CSS样式
        st.markdown(
            f"""
            <style>
            [data-testid="stSidebar"] > div:first-child {{
                background-image: url(data:image/{img_format};base64,{img_base64});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        return True
    except Exception as e:
        st.error(f"设置侧边栏背景失败: {str(e)}")
        return False

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    with st.sidebar:
        st.title("任务管理器")
        
        # 添加任务过滤
        st.markdown("## 过滤任务")
        
        # 按名称搜索
        search_term = st.text_input("搜索任务名称:", key="search_task")
        
        # 获取所有标签
        all_tags = get_all_tags(current_taskfile)
        
        # 初始化常用标签和筛选状态
        if 'favorite_tags' not in st.session_state:
            st.session_state.favorite_tags = []
            
        # 确保tags_filter存在于session_state中
        if 'tags_filter' not in st.session_state:
            st.session_state.tags_filter = []
        
        # 确保tags_widget_key存在，用于控制st_tags组件的刷新
        if 'tags_widget_key' not in st.session_state:
            st.session_state.tags_widget_key = 0
        
        # 显示收藏标签作为快速过滤器按钮
        if st.session_state.favorite_tags:
            st.markdown("#### 常用标签")
            # 使用更紧凑的布局显示常用标签
            cols_per_row = 2
            for i in range(0, len(st.session_state.favorite_tags), cols_per_row):
                fav_tag_cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(st.session_state.favorite_tags):
                        tag = sorted(st.session_state.favorite_tags)[i + j]
                        with fav_tag_cols[j]:
                            # 创建按钮，点击时添加或移除该标签的过滤
                            is_active = tag in st.session_state.tags_filter
                            btn_label = f"✓ #{tag}" if is_active else f"#{tag}"
                            btn_type = "primary" if is_active else "secondary"
                            
                            if st.button(btn_label, key=f"quick_{tag}", type=btn_type):
                                # 切换标签的状态
                                if tag in st.session_state.tags_filter:
                                    # 移除标签
                                    st.session_state.tags_filter.remove(tag)
                                else:
                                    # 添加标签
                                    st.session_state.tags_filter.append(tag)
                                # 增加key值以强制刷新st_tags组件
                                st.session_state.tags_widget_key += 1
                                st.rerun()
            
        # 快速标签过滤器
        st.markdown("### 🏷️ 标签筛选")
        
        # 添加一个下拉框，用于快速选择标签
        if all_tags:
            tag_dropdown = st.selectbox(
                "从列表选择标签:",
                options=[""] + sorted(all_tags),  # 添加空选项作为默认值
                index=0,  # 默认选择第一个（空选项）
                key="tag_dropdown"
            )
            
            # 如果用户从下拉框选择了一个非空标签，添加到标签过滤器中
            if tag_dropdown and tag_dropdown not in st.session_state.tags_filter:
                st.session_state.tags_filter.append(tag_dropdown)
                # 增加key值以强制刷新st_tags组件
                st.session_state.tags_widget_key += 1
                st.rerun()
        
        # 常用标签管理
        with st.expander("管理常用标签", expanded=False):
            st.markdown("选择要保存为常用标签的标签:")
            
            # 初始化标记，用于检测常用标签是否有变化
            tags_changed = False
            
            # 创建一个多列布局，用于显示所有标签的checkbox
            if all_tags:
                all_tag_cols = st.columns(3)
                for i, tag in enumerate(sorted(all_tags)):
                    with all_tag_cols[i % 3]:
                        # 创建checkbox来添加/移除收藏标签
                        was_selected = tag in st.session_state.favorite_tags
                        is_selected = st.checkbox(tag, value=was_selected, key=f"fav_{tag}")
                        
                        # 检测是否发生变化
                        if was_selected != is_selected:
                            tags_changed = True
                            
                            if is_selected and tag not in st.session_state.favorite_tags:
                                st.session_state.favorite_tags.append(tag)
                            elif not is_selected and tag in st.session_state.favorite_tags:
                                st.session_state.favorite_tags.remove(tag)
            else:
                st.info("没有找到标签")
            
            # 如果常用标签有变化，保存到本地
            if tags_changed:
                save_favorite_tags(st.session_state.favorite_tags)
                st.success("常用标签已保存")
        
        # 显示已选任务数量
        # if 'selected_tasks' in st.session_state and st.session_state.selected_tasks:
        #     st.markdown(f"## 已选择 {len(st.session_state.selected_tasks)} 个任务")
        
        # 添加系统操作部分
        with st.expander("系统"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重启", help="重新启动任务管理器"):
                    restart_application()
            
            with col2:
                if st.button("❌ 退出", help="完全关闭任务管理器"):
                    exit_application()
                
        # 添加背景设置部分
        with st.expander("🎨 背景设置"):
            # 初始化背景设置
            if 'background_settings' not in st.session_state:
                st.session_state.background_settings = load_background_settings()
            
            # 拆分为主背景和侧边栏背景设置
            tabs = st.tabs(["主界面背景", "侧边栏背景"])
            
            with tabs[0]:  # 主界面背景设置
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
                        import tempfile
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
            
            with tabs[1]:  # 侧边栏背景设置
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
                        import tempfile
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
            
            # 重置背景设置
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

def get_all_tags(taskfile_path):
    """获取所有可用的标签"""
    try:
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return []

def restart_application():
    """重启应用程序"""
    run_script = "run_task_manager.py"
    
    # 启动新实例
    if os.path.exists(run_script):
        subprocess.Popen([sys.executable, run_script])
    else:
        st.error(f"找不到启动脚本: {run_script}")
        return
        
    # 退出当前实例
    os._exit(0)

def exit_application():
    """完全退出应用程序"""
    os._exit(0)