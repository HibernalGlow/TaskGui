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

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    # 移除with st.sidebar:包装，直接渲染侧边栏内容
    # st.title("任务管理器")
    
    # 加载卡片设置
    card_settings = get_card_view_settings()
    
    # 确保use_sidebar_editor在session_state中
    if 'use_sidebar_editor' not in st.session_state:
        st.session_state.use_sidebar_editor = card_settings.get("use_sidebar_editor", True)
    
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
    

    
    # 将搜索框放入expander中
    with st.expander("🔍 过滤任务", expanded=True):
        # 按名称搜索
        search_term = st.text_input("搜索任务名称:", key="search_task", placeholder="输入关键词...")
        
    # 获取选中的任务
    selected_tasks = get_selected_tasks()
    
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
            st.markdown("<div style='font-size:0.9rem; margin-bottom:0.5rem;'>或从所有任务中选择:</div>", unsafe_allow_html=True)
            try:
                tasks_df = read_taskfile(current_taskfile)
                task_names = tasks_df["name"].tolist()
                
                # 添加搜索框来过滤任务
                search_key = "task_editor_search"
                if search_key not in st.session_state:
                    st.session_state[search_key] = ""
                    
                search_term = st.text_input("搜索任务:", 
                                         value=st.session_state[search_key], 
                                         key=search_key+"_input", 
                                         placeholder="输入关键词过滤任务...")
                
                # 过滤任务列表
                filtered_tasks = []
                if search_term:
                    filtered_tasks = [name for name in task_names if search_term.lower() in name.lower()]
                else:
                    filtered_tasks = task_names
                
                # 下拉选择要编辑的任务
                selected_task = st.selectbox("选择要编辑的任务:", 
                                        options=[""] + filtered_tasks, 
                                        index=0,
                                        help="从下拉列表中选择一个任务进行编辑")
                
                if selected_task:
                    # 设置要编辑的任务
                    task_row = tasks_df[tasks_df["name"] == selected_task].iloc[0]
                    st.session_state.edit_task_in_sidebar = task_row.to_dict()
                    st.rerun()
            except Exception as e:
                st.error(f"加载任务列表失败: {str(e)}")
        else:
            # 显示当前正在编辑的任务名称
            st.markdown(f"<div style='font-size:1rem; font-weight:bold; color:#1E88E5; margin-bottom:0.5rem;'>当前编辑: {st.session_state.edit_task_in_sidebar.get('name', '')}</div>", unsafe_allow_html=True)
            
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
    
    # 如果有选中的任务，显示任务操作按钮
    # if selected_tasks:
    render_action_buttons(selected_tasks, current_taskfile, key_prefix="sidebar", is_sidebar=True)
    
    # 将常用标签和标签筛选放入同一个expander中
    with st.expander("🏷️ 标签筛选", expanded=True):
        # 显示收藏标签作为快速过滤器按钮
        if st.session_state.favorite_tags:
            # st.markdown("#### 常用标签")
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
        
        # 标签过滤器部分
        # st.markdown("### 从列表选择标签")
        
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
            
        # 使用分隔线和标题替代嵌套的expander
        # st.markdown("---")
        # st.markdown("#### 管理常用标签")
        
        # 添加一个折叠按钮来模拟expander功能
        if 'show_tag_manager' not in st.session_state:
            st.session_state.show_tag_manager = False
            
        show_manager = st.checkbox("显示/隐藏标签管理", value=st.session_state.show_tag_manager, key="show_tag_manager_toggle")
        st.session_state.show_tag_manager = show_manager
        
        # 只有当选择显示时才显示标签管理内容
        if st.session_state.show_tag_manager:
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
    with st.expander("系统", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重启", help="重新启动任务管理器"):
                restart_application()
        
        with col2:
            if st.button("❌ 退出", help="完全关闭任务管理器"):
                exit_application()
    
    # 背景设置部分已移动到主界面设置标签页

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