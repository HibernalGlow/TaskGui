import streamlit as st
import os
from taskst.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from taskst.services.task_runner import run_task_via_cmd
from taskst.utils.selection_utils import update_task_selection, get_task_selection_state, record_task_run, get_task_runtime, get_card_view_settings
from taskst.views.card.task_card_editor import render_task_edit_form
import hashlib

def get_tag_color(tag):
    """为标签生成一致的颜色
    
    参数:
        tag: 标签文本
        
    返回:
        str: 十六进制颜色代码
    """
    # 使用标签文本的哈希值生成颜色
    hash_obj = hashlib.md5(tag.encode())
    hash_value = int(hash_obj.hexdigest(), 16)
    
    # 生成柔和的颜色（调整亮度和饱和度）
    hue = hash_value % 360  # 0-359 色相
    
    # 返回HSL格式的颜色
    return f"hsl({hue}, 70%, 85%)"

def render_tags(tags):
    """使用Notion风格渲染标签
    
    参数:
        tags: 标签列表
    """
    if not isinstance(tags, list) or not tags:
        return
    
    # 创建一个完整的HTML字符串，一次性渲染所有标签
    tags_container = '<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;">'
    
    # 添加每个标签的HTML
    for tag in tags:
        bg_color = get_tag_color(tag)
        tags_container += f'<span style="display: inline-block; background-color: {bg_color}; color: #333; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;">#{tag}</span>'
    
    # 关闭容器
    tags_container += '</div>'
    
    # 一次性渲染整个容器
    st.markdown(tags_container, unsafe_allow_html=True)

def render_task_card(task, current_taskfile, idx=0, view_type="preview", show_checkbox=False):
    """通用的任务卡片渲染函数，可在不同视图中复用
    
    参数:
        task: 任务数据
        current_taskfile: 当前任务文件路径
        idx: 任务索引，用于生成唯一key
        view_type: 视图类型，"preview"或"card"
        show_checkbox: 是否显示选择框
    """
    # 获取卡片视图设置
    card_settings = get_card_view_settings()
    
    # 生成唯一前缀，用于区分不同视图的组件key
    prefix = f"{view_type}_{idx}_{task['name']}"
    
    # 初始化编辑状态
    edit_key = f"edit_state_{prefix}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False
    
    # 获取任务的实际源文件路径（合并模式下可能与current_taskfile不同）
    taskfile_path = task.get('source_file', current_taskfile)
    
    # 在expander中显示卡片内容
    with st.expander(f"{task['emoji']} {task['name']}", expanded=True):
        # 如果是编辑模式，显示编辑表单
        if st.session_state[edit_key]:
            # 定义返回按钮回调
            def back_button_callback():
                st.session_state[edit_key] = False
                st.rerun()
            
            # 渲染编辑表单
            render_task_edit_form(
                task=task, 
                taskfile_path=taskfile_path, 
                on_save_callback=lambda: setattr(st.session_state, edit_key, False),
                with_back_button=True,
                back_button_callback=back_button_callback
            )
        else:
            # 描述 - 根据设置显示
            if card_settings.get("show_description", True):
                st.markdown(f"**描述**: {task['description']}")
            
            # 显示标签 - 根据设置显示
            if card_settings.get("show_tags", True) and isinstance(task['tags'], list) and task['tags']:
                # st.write("**标签**:")
                render_tags(task['tags'])
            
            # 显示目录 - 根据设置显示
            if card_settings.get("show_directory", True):
                st.markdown(f"**目录**: `{task['directory']}`")
            
            # 显示命令 - 根据设置显示
            if card_settings.get("show_command", True):
                cmd = get_task_command(task['name'], taskfile_path)
                st.code(cmd, language="bash")
            
            # 在合并模式下显示来源文件
            if 'source_file' in task and task['source_file'] != current_taskfile:
                st.markdown(f"**来源**: `{os.path.basename(task['source_file'])}`")
            
            # 如果需要显示选择框
            if show_checkbox:
                # 获取当前选择状态
                is_selected = get_task_selection_state(task['name'])
                
                # 操作按钮 - 使用动态列布局
                # 定义按钮配置列表
                button_configs = [
                    {
                        "icon": "☑️",
                        "key": f"select_{prefix}",
                        "help": "选择/取消选择此任务",
                        "type": "primary" if is_selected else "secondary"
                    },
                    {
                        "icon": "▶️",
                        "key": f"run_{prefix}",
                        "help": "运行此任务"
                    },
                    {
                        "icon": "📋",
                        "key": f"copy_{prefix}",
                        "help": "复制任务命令"
                    },
                    {
                        "icon": "✏️",
                        "key": f"edit_{prefix}",
                        "help": "编辑任务"
                    }
                ]
                
                # 创建动态列布局
                button_columns = st.columns(len(button_configs))
                
                # 动态渲染按钮
                for idx, (col, config) in enumerate(zip(button_columns, button_configs)):
                    with col:
                        # 获取按钮类型（如果有定义）
                        button_type = config.get("type", "secondary")
                        btn_key = config.get("key")
                        
                        # 选择按钮特殊处理
                        if "select_" in btn_key:
                            # 检查按钮状态变化
                            if st.button(config["icon"], key=btn_key, help=config["help"], type=button_type):
                                # 直接更新全局选择状态
                                update_task_selection(task['name'], not is_selected)
                                
                        # 运行按钮
                        elif "run_" in btn_key:
                            if st.button(config["icon"], key=btn_key, help=config["help"], type=button_type):
                                with st.spinner(f"正在启动任务 {task['name']}..."):
                                    # 使用任务的源文件路径，而不是当前默认的任务文件路径
                                    run_task_via_cmd(task['name'], taskfile_path)
                                    record_task_run(task['name'], status="started")
                                    
                        # 复制命令按钮
                        elif "copy_" in btn_key:
                            if st.button(config["icon"], key=btn_key, help=config["help"], type=button_type):
                                # 使用任务的源文件路径生成命令
                                cmd = get_task_command(task['name'], taskfile_path)
                                copy_to_clipboard(cmd)
                                
                        # 编辑按钮
                        elif "edit_" in btn_key:
                            if st.button(config["icon"], key=btn_key, help=config["help"], type=button_type):
                                # 修改：检查是否启用侧边栏编辑
                                if 'use_sidebar_editor' in st.session_state and st.session_state.use_sidebar_editor:
                                    # 将任务设置到侧边栏编辑状态
                                    st.session_state.edit_task_in_sidebar = task.copy()
                                    
                                    # 设置编辑expander为展开状态
                                    if 'edit_task_expander_state' not in st.session_state:
                                        st.session_state.edit_task_expander_state = {}
                                    
                                    # 将编辑expander标记为展开
                                    st.session_state.edit_task_expander_state["✏️ 编辑任务"] = True
                                    
                                    st.rerun()
                                else:
                                    # 使用原来的内联编辑模式
                                    st.session_state[edit_key] = True
                                    st.rerun() # 编辑模式需要重新加载
            
            # 获取任务运行时数据
            runtime = get_task_runtime(task['name'])
            
            # 如果有运行记录，显示运行信息
            # if runtime.get("run_count", 0) > 0:
            #     col_a, col_b, col_c = st.columns(3)
            #     with col_a:
            #         st.markdown(f"**运行次数**: {runtime.get('run_count', 0)}")
            #     with col_b:
            #         st.markdown(f"**最后运行**: {runtime.get('last_run', 'N/A')}")
            #     with col_c:
            #         st.markdown(f"**最后状态**: {runtime.get('last_status', 'N/A')}")