import streamlit as st
import os
from src.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from src.services.task_runner import run_task_via_cmd
from src.utils.selection_utils import update_task_selection, get_task_selection_state, record_task_run, get_task_runtime
from src.views.card.task_card_editor import render_task_edit_form
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
    # 生成唯一前缀，用于区分不同视图的组件key
    prefix = f"{view_type}_{idx}_{task['name']}"
    
    # 初始化编辑状态
    edit_key = f"edit_state_{prefix}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False
    
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
                taskfile_path=current_taskfile, 
                on_save_callback=lambda: setattr(st.session_state, edit_key, False),
                with_back_button=True,
                back_button_callback=back_button_callback
            )
        else:
            # 描述
            st.markdown(f"**描述**: {task['description']}")
            
            # 显示标签（使用优化的标签样式）
            if isinstance(task['tags'], list) and task['tags']:
                st.write("**标签**:")
                render_tags(task['tags'])
            
            # 显示目录
            st.markdown(f"**目录**: `{task['directory']}`")
            
            # 显示命令
            cmd = get_task_command(task['name'], current_taskfile)
            st.code(cmd, language="bash")
            
            # 如果需要显示选择框
            if show_checkbox:
                # 获取当前选择状态
                is_selected = get_task_selection_state(task['name'])
                
                # 渲染勾选框
                checkbox_value = st.checkbox("选择此任务", value=is_selected, key=f"select_{prefix}")
                
                # 如果勾选状态与记录的状态不同，更新状态
                if checkbox_value != is_selected:
                    update_task_selection(task['name'], checkbox_value)
                    st.rerun()  # 立即刷新以更新预览
            
            # 操作按钮 - 使用4列布局，增加编辑按钮
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # 运行按钮
                if st.button("运行", key=f"run_{prefix}"):
                    with st.spinner(f"正在启动任务 {task['name']}..."):
                        result = run_task_via_cmd(task['name'], current_taskfile)
                        # 记录任务运行
                        record_task_run(task['name'], status="started")
                    st.success(f"任务 {task['name']} 已在新窗口启动")
            
            with col2:
                # 文件按钮
                if st.button("文件", key=f"file_{prefix}"):
                    if task['directory'] and os.path.exists(task['directory']):
                        files = get_directory_files(task['directory'])
                        if files:
                            st.markdown("##### 文件列表")
                            for i, file in enumerate(files):
                                file_path = os.path.join(task['directory'], file)
                                if st.button(file, key=f"file_{prefix}_{i}"):
                                    if open_file(file_path):
                                        st.success(f"已打开: {file}")
                        else:
                            st.info("没有找到文件")
            
            with col3:
                # 复制命令按钮
                if st.button("复制", key=f"copy_{prefix}"):
                    cmd = get_task_command(task['name'], current_taskfile)
                    copy_to_clipboard(cmd)
                    st.success("命令已复制")
                    
            with col4:
                # 编辑按钮
                if st.button("编辑", key=f"edit_{prefix}"):
                    st.session_state[edit_key] = True
                    st.rerun()
            
            # 获取任务运行时数据
            runtime = get_task_runtime(task['name'])
            
            # 如果有运行记录，显示运行信息
            if runtime.get("run_count", 0) > 0:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"**运行次数**: {runtime.get('run_count', 0)}")
                with col_b:
                    st.markdown(f"**最后运行**: {runtime.get('last_run', 'N/A')}")
                with col_c:
                    st.markdown(f"**最后状态**: {runtime.get('last_status', 'N/A')}")