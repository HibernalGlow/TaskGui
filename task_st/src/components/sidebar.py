import streamlit as st
from src.services.taskfile import read_taskfile
from streamlit_tags import st_tags
from src.utils.selection_utils import save_favorite_tags, save_background_settings, load_background_settings, get_selected_tasks, get_card_view_settings
import os
import sys
import subprocess
import base64
from src.components.preview_card import render_action_buttons

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

def render_filter_tasks_expander(current_taskfile):
    """渲染过滤任务expander"""
    with st.expander("🔍 过滤任务", expanded=True):
        # 获取任务列表用于过滤
        try:
            tasks_df = read_taskfile(current_taskfile)
            task_names = tasks_df["name"].tolist()
            
            # 使用多选组件进行任务筛选
            filtered_tasks = st.multiselect(
                "搜索任务名称:",
                options=sorted(task_names),
                default=[],
                key="search_task_multiselect",
                help="输入关键词搜索或直接选择要过滤的任务"
            )
            
            # 将选定的任务存储到session中供其他组件使用
            if 'filtered_tasks' not in st.session_state:
                st.session_state.filtered_tasks = []
            
            # 只有当选择发生变化时才更新
            if set(filtered_tasks) != set(st.session_state.filtered_tasks):
                st.session_state.filtered_tasks = filtered_tasks
        except Exception as e:
            st.error(f"加载任务失败: {str(e)}")
            st.session_state.filtered_tasks = []

def render_edit_task_expander(current_taskfile):
    """渲染编辑任务expander"""
    # 确保编辑expander状态存在
    if 'edit_task_expander_state' not in st.session_state:
        st.session_state.edit_task_expander_state = {}
    
    # 确保edit_task_in_sidebar存在于session_state中
    if 'edit_task_in_sidebar' not in st.session_state:
        st.session_state.edit_task_in_sidebar = None
    
    # 确定编辑任务expander的初始展开状态
    edit_expander_key = "✏️ 编辑任务"
    edit_expander_expanded = st.session_state.edit_task_expander_state.get(edit_expander_key, False)
    
    # 添加任务编辑expander
    with st.expander(edit_expander_key, expanded=edit_expander_expanded):
        # 获取当前expander展开状态，如果已折叠但有编辑中的任务，则清除
        if not st.session_state.edit_task_expander_state.get(edit_expander_key, False) and st.session_state.edit_task_in_sidebar is not None:
            st.session_state.edit_task_in_sidebar = None
        
        # 更新expander状态（这个必须在每次渲染时都更新）
        st.session_state.edit_task_expander_state[edit_expander_key] = True
        
        # 如果没有选中要编辑的任务，显示任务选择
        if st.session_state.edit_task_in_sidebar is None:
            # 检查是否有任务被选中，优先从已选任务中选择
            selected_tasks = get_selected_tasks()
            
            # 添加一个小标题
            st.markdown("<div style='font-size:1rem; font-weight:bold; margin-bottom:0.5rem;'>选择要编辑的任务</div>", unsafe_allow_html=True)
            
            if selected_tasks:
                st.markdown("<div style='font-size:0.9rem; margin-bottom:0.5rem;'>从已选任务中选择:</div>", unsafe_allow_html=True)
                
                # 确定每行显示的按钮数量
                buttons_per_row = min(3, len(selected_tasks))
                
                # 为每个选中的任务创建一个按钮
                for i in range(0, len(selected_tasks), buttons_per_row):
                    selected_task_cols = st.columns(buttons_per_row)
                    for j in range(buttons_per_row):
                        col_index = j
                        task_index = i + j
                        
                        if task_index < len(selected_tasks):
                            task_name = selected_tasks[task_index]
                            with selected_task_cols[col_index]:
                                if st.button(f"✏️ {task_name}", key=f"edit_btn_{task_name}", help=f"编辑任务 {task_name}"):
                                    # 查找任务数据
                                    try:
                                        tasks_df = read_taskfile(current_taskfile)
                                        task_row = tasks_df[tasks_df["name"] == task_name].iloc[0]
                                        st.session_state.edit_task_in_sidebar = task_row.to_dict()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"加载任务数据失败: {str(e)}")
                
                st.markdown("<hr style='margin:0.8rem 0;'>", unsafe_allow_html=True)
            
            # 从当前taskfile获取所有任务
            try:
                tasks_df = read_taskfile(current_taskfile)
                task_names = tasks_df["name"].tolist()
                
                # 合并搜索和选择为一个多选组件
                selected_tasks_to_edit = st.multiselect(
                    "搜索并选择要编辑的任务:",
                    options=sorted(task_names),
                    default=[],
                    key="edit_tasks_multiselect",
                    help="输入关键词筛选或直接从列表中选择一个任务进行编辑"
                )
                
                # 当选择了任务时
                if selected_tasks_to_edit:
                    # 取第一个选择的任务进行编辑
                    selected_task = selected_tasks_to_edit[0]
                    
                    # 如果选择了多个任务，提示用户
                    if len(selected_tasks_to_edit) > 1:
                        st.info(f"将编辑第一个选择的任务: {selected_task}")
                    
                    # 设置要编辑的任务
                    task_row = tasks_df[tasks_df["name"] == selected_task].iloc[0]
                    st.session_state.edit_task_in_sidebar = task_row.to_dict()
                    st.rerun()
            except Exception as e:
                st.error(f"加载任务列表失败: {str(e)}")
        else:
            # 显示当前正在编辑的任务名称
            st.markdown(f"<div style='font-size:1rem; font-weight:bold; margin-bottom:0.5rem;'>当前编辑: {st.session_state.edit_task_in_sidebar.get('name', '')}</div>", unsafe_allow_html=True)
            
            # 使用task_card_editor中的函数渲染编辑表单
            from src.views.card.task_card_editor import render_task_edit_form
            
            # 定义保存后的回调函数
            def on_save_callback():
                # 获取最新的任务名称（可能已更改）
                task_name = st.session_state.edit_task_in_sidebar.get('name', '')
                st.session_state.edit_task_in_sidebar = None
                st.success(f"任务 '{task_name}' 已保存")
                st.rerun()
            
            # 定义返回按钮回调
            def back_button_callback():
                st.session_state.edit_task_in_sidebar = None
                st.rerun()
            
            # 渲染编辑表单
            render_task_edit_form(
                task=st.session_state.edit_task_in_sidebar,
                taskfile_path=current_taskfile,
                on_save_callback=on_save_callback,
                with_back_button=True,
                back_button_callback=back_button_callback
            )

def render_tag_filters_expander(current_taskfile):
    """渲染标签筛选expander"""
    all_tags = get_all_tags(current_taskfile)
    
    with st.expander("🏷️ 标签筛选", expanded=True):
        # 添加一个多选组件，用于快速选择标签
        if all_tags:
            # 转换现有标签过滤器为集合，方便比较
            current_tags_set = set(st.session_state.tags_filter)
            
            # 获取收藏的标签并排序
            favorite_tags = sorted(st.session_state.favorite_tags)
            
            # 创建一个包含所有标签的列表，但将收藏标签置顶
            other_tags = sorted([tag for tag in all_tags if tag not in set(favorite_tags)])
            
            # 如果有收藏标签，添加一个分隔符
            sorted_tags = []
            if favorite_tags:
                # 添加收藏标签（标记为收藏）
                sorted_tags.extend([f"⭐ {tag}" for tag in favorite_tags])
                # 添加其他标签
                sorted_tags.extend(other_tags)
            else:
                sorted_tags = other_tags
            
            # 转换当前已选择的标签以匹配格式
            default_tags = []
            for tag in sorted(list(current_tags_set)):
                if tag in favorite_tags:
                    default_tags.append(f"⭐ {tag}")
                else:
                    default_tags.append(tag)
            
            # 使用多选组件替代下拉框
            selected_tags = st.multiselect(
                "选择要筛选的标签:",
                options=sorted_tags,
                default=default_tags,
                key="tags_multiselect"
            )
            
            # 转换选中的标签（移除星号前缀）
            processed_tags = [tag.replace("⭐ ", "") if tag.startswith("⭐ ") else tag for tag in selected_tags]
            
            # 更新标签过滤器
            if set(processed_tags) != current_tags_set:
                # 清空当前标签筛选
                st.session_state.tags_filter = []
                
                # 添加选中的标签
                if processed_tags:
                    st.session_state.tags_filter.extend(processed_tags)
                
                # 增加key值以强制刷新st_tags组件
                st.session_state.tags_widget_key += 1
                st.rerun()
        
        # 标签管理部分 - 使用multiselect代替checkbox
        if all_tags:
            # 获取当前收藏的标签
            favorite_tags = st.session_state.favorite_tags
            
            # 使用multiselect组件，预选中已收藏的标签
            selected_favorite_tags = st.multiselect(
                "选择收藏的标签:",
                options=sorted(all_tags),
                default=sorted(favorite_tags),
                key="favorite_tags_multiselect",
                help="选择要添加到收藏的标签，方便快速筛选"
            )
            
            # 检测是否发生变化
            if set(selected_favorite_tags) != set(favorite_tags):
                # 更新收藏标签
                st.session_state.favorite_tags = selected_favorite_tags
                
                # 保存到本地
                save_favorite_tags(selected_favorite_tags)
                st.success("常用标签已更新")
        else:
            st.info("没有找到标签")

def render_system_expander(current_taskfile):
    """渲染系统expander"""
    with st.expander("系统", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 重启", help="重新启动任务管理器"):
                restart_application()
        
        with col2:
            if st.button("❌ 退出", help="完全关闭任务管理器"):
                exit_application()
                
        with col3:
            if st.button("⏳ 刷新", help="刷新当前页面"):
                st.rerun()

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    # 移除with st.sidebar:包装，直接渲染侧边栏内容
    # st.title("任务管理器")
    
    # 加载卡片设置
    card_settings = get_card_view_settings()
    
    # 获取侧边栏设置
    sidebar_settings = card_settings.get("sidebar_settings", {})
    
    # 确保use_sidebar_editor在session_state中
    if 'use_sidebar_editor' not in st.session_state:
        st.session_state.use_sidebar_editor = sidebar_settings.get("use_sidebar_editor", True)
    
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
    
    # 定义expander组件
    expander_components = {
        "filter_tasks": {
            "name": "🔍 任务过滤",
            "function": render_filter_tasks_expander,
            "enabled": sidebar_settings.get("filter_tasks_enabled", True)
        },
        "edit_task": {
            "name": "✏️ 任务编辑",
            "function": render_edit_task_expander,
            "enabled": sidebar_settings.get("edit_task_enabled", True)
        },
        "tag_filters": {
            "name": "🏷️ 标签筛选",
            "function": render_tag_filters_expander,
            "enabled": sidebar_settings.get("tag_filters_enabled", True)
        },
        "system": {
            "name": "🔄 系统控制",
            "function": render_system_expander,
            "enabled": sidebar_settings.get("system_enabled", True)
        }
    }
    
    # 默认expander顺序
    default_order = ["filter_tasks", "edit_task", "tag_filters", "system"]
    
    # 获取用户设置的顺序
    expander_order = sidebar_settings.get("expander_order", default_order)
    
    # 获取选中的任务
    selected_tasks = get_selected_tasks()
    
    # 渲染action按钮（保持在固定位置）
    render_action_buttons(selected_tasks, current_taskfile, key_prefix="sidebar", is_sidebar=True)
    
    # 按配置的顺序渲染各个expander
    for expander_id in expander_order:
        if expander_id in expander_components and expander_components[expander_id]["enabled"]:
            expander_components[expander_id]["function"](current_taskfile)