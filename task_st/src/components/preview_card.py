import streamlit as st
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..utils.selection_utils import update_task_selection

def render_shared_preview(filtered_df, current_taskfile):
    """
    渲染共享的预览卡片区域，显示当前选中的任务
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    # 检查是否有选中的任务
    if 'selected_tasks' not in st.session_state or not st.session_state.selected_tasks:
        st.info("请在下方视图中选择任务以查看预览")
        return
    
    # 过滤出选中的任务
    selected_tasks = st.session_state.selected_tasks
    selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)]
    
    if selected_df.empty:
        st.info("没有找到选中的任务")
        return
    
    # 创建预览卡片区域
    with st.container():
        # 顶部操作栏
        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
        with col1:
            st.markdown(f"### 已选择 {len(selected_tasks)} 个任务")
        
        # 清除选择按钮 - 使用统一的方式清除选择
        with col2:
            if st.button("🗑️ 清除选择", key="clear_preview_selection"):
                # 使用统一的更新函数来清除
                for task_name in selected_tasks.copy():
                    update_task_selection(task_name, False, rerun=False)
                st.rerun()
        
        # 复制所有命令按钮
        with col3:
            if st.button("📋 复制所有命令", key="copy_all_commands"):
                if not selected_tasks:
                    st.warning("请先选择要复制的任务")
                else:
                    commands = []
                    for task in selected_tasks:
                        cmd = get_task_command(task, current_taskfile)
                        commands.append(f"{task}: {cmd}")
                    
                    all_commands = "\n".join(commands)
                    copy_to_clipboard(all_commands)
                    st.success(f"已复制 {len(selected_tasks)} 个命令到剪贴板")
        
        # 批量运行按钮
        with col4:
            run_btn = st.button("▶️ 运行选中任务", key="run_preview_tasks")
            if run_btn:
                from ..services.task_runner import run_multiple_tasks
                with st.spinner(f"正在启动 {len(selected_tasks)} 个任务..."):
                    result_msgs = run_multiple_tasks(
                        selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.get('run_parallel', False)
                    )
                
                for msg in result_msgs:
                    st.success(msg)
        
        # 使用标签页显示每个选中的任务
        if len(selected_tasks) > 0:
            # 创建标签页
            task_tabs = st.tabs([f"{task[:15]}..." if len(task) > 15 else task for task in selected_tasks])
            
            # 为每个标签页填充内容
            for i, task_name in enumerate(selected_tasks):
                task_data = selected_df[selected_df['name'] == task_name].iloc[0]
                with task_tabs[i]:
                    render_task_preview(task_data, current_taskfile)

def render_task_preview(task, current_taskfile):
    """
    渲染单个任务的预览卡片
    
    参数:
        task: 任务数据
        current_taskfile: 当前Taskfile路径
    """
    # 标题
    st.markdown(f"## {task['emoji']} {task['name']}")
    
    # 任务详情
    st.markdown(f"**描述**: {task['description']}")
    
    # 标签
    tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
    st.markdown(f"**标签**: {tags_str}")
    
    # 目录
    st.markdown(f"**目录**: `{task['directory']}`")
    
    # 命令
    cmd = get_task_command(task['name'], current_taskfile)
    st.code(cmd, language="bash")
    
    # 操作按钮
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("运行", key=f"run_preview_{task['name']}"):
            with st.spinner(f"正在启动任务 {task['name']}..."):
                result = run_task_via_cmd(task['name'], current_taskfile)
            st.success(f"任务 {task['name']} 已在新窗口启动")
    
    with col2:
        # 文件按钮
        if st.button("查看文件", key=f"file_preview_{task['name']}"):
            if task['directory'] and os.path.exists(task['directory']):
                files = get_directory_files(task['directory'])
                if files:
                    st.markdown("##### 文件列表")
                    for i, file in enumerate(files[:10]):  # 限制显示10个文件
                        file_path = os.path.join(task['directory'], file)
                        if st.button(file, key=f"file_preview_{task['name']}_{i}"):
                            if open_file(file_path):
                                st.success(f"已打开: {file}")
                    
                    if len(files) > 10:
                        st.info(f"还有 {len(files) - 10} 个文件未显示")
                else:
                    st.info("目录中没有找到文件")
            else:
                st.warning("目录不存在")
    
    with col3:
        # 复制命令按钮
        if st.button("复制命令", key=f"copy_preview_{task['name']}"):
            copy_to_clipboard(cmd)
            st.success("命令已复制到剪贴板")
