import streamlit as st
import os
from src.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from src.services.task_runner import run_task_via_cmd
from src.utils.selection_utils import update_task_selection, get_task_selection_state, record_task_run, get_task_runtime

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
    
    # 显示标题 (两种视图都显示)
    if view_type != "preview":  # 预览模式下不显示标题，因为已经在tab上显示了
        st.markdown(f"### {task['emoji']} {task['name']}")
    
    # 描述
    st.markdown(f"**描述**: {task['description']}")
    
    # 显示标签
    if isinstance(task['tags'], list) and task['tags']:
        tags_str = ', '.join([f"#{tag}" for tag in task['tags']])
        st.markdown(f"**标签**: {tags_str}")
    
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
    
    # 操作按钮 - 统一使用3列布局
    col1, col2, col3 = st.columns(3)
    
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
    
    # 添加分隔线
    st.markdown("---")