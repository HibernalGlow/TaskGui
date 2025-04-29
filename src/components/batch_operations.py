import streamlit as st
from src.utils.file_utils import get_task_command, copy_to_clipboard
from src.services.task_runner import run_multiple_tasks

def render_batch_operations(current_taskfile, view_key="default"):
    """
    渲染批量操作组件
    
    参数:
        current_taskfile: 当前任务文件路径
        view_key: 视图类型的唯一键值，用于防止不同视图的按钮key冲突
    """
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    st.markdown("### 批量操作")
    
    batch_col1, batch_col2, batch_col3 = st.columns(3)
    
    # 显示已选择的任务
    selected_tasks = st.session_state.selected_tasks
    st.markdown(f"**已选择 {len(selected_tasks)} 个任务：**")
    if selected_tasks:
        for task in selected_tasks:
            st.markdown(f"- {task}")
    
    # 并行执行选项
    with batch_col1:
        if 'run_parallel' not in st.session_state:
            st.session_state.run_parallel = False
        
        parallel_checkbox = st.checkbox(
            "并行执行任务", 
            value=st.session_state.run_parallel,
            key=f"parallel_{view_key}"
        )
        st.session_state.run_parallel = parallel_checkbox
    
    # 批量运行按钮
    with batch_col2:
        if st.button("运行选中的任务", key=f"run_batch_{view_key}"):
            if not selected_tasks:
                st.warning("请先选择要运行的任务")
            else:
                with st.spinner(f"正在启动 {len(selected_tasks)} 个任务..."):
                    result_msgs = run_multiple_tasks(
                        selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.run_parallel
                    )
                
                for msg in result_msgs:
                    st.success(msg)
    
    # 复制命令按钮
    with batch_col3:
        if st.button("复制所有命令", key=f"copy_batch_{view_key}"):
            if not selected_tasks:
                st.warning("请先选择要复制命令的任务")
            else:
                commands = []
                for task in selected_tasks:
                    cmd = get_task_command(task, current_taskfile)
                    commands.append(f"{task}: {cmd}")
                
                all_commands = "\n".join(commands)
                copy_to_clipboard(all_commands)
                st.success(f"已复制 {len(selected_tasks)} 个命令到剪贴板")
    
    # 清除选择按钮
    if st.button("清除选择", key=f"clear_{view_key}"):
        st.session_state.selected_tasks = []
        # 如果有selected状态，也要清除
        if 'selected' in st.session_state:
            for task in st.session_state.selected:
                st.session_state.selected[task] = False
        st.experimental_rerun()