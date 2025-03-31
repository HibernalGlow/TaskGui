import streamlit as st
import pandas as pd
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard
from ..services.task_runner import run_task_via_cmd, run_tasks_via_cmd
from ..utils.selection_utils import get_selected_tasks, clear_all_selections, get_global_state, record_task_run, get_task_runtime
from .task_card import render_task_card

def render_shared_preview(filtered_df, current_taskfile):
    """渲染共享任务预览区域
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
    """
    # 获取全局状态
    global_state = get_global_state()
    
    # 从全局状态获取选中的任务
    selected_tasks = get_selected_tasks()
    
    # 如果没有选中任务，显示提示信息
    if not selected_tasks:
        st.info("没有选中的任务。请从表格中选择要操作的任务。")
        return
    
    # 显示选中的任务数量
    st.markdown(f"**已选择 {len(selected_tasks)} 个任务**")
    
    # 获取选中任务的详细信息
    selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)].copy()
    
    # 添加操作按钮
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 清除选择按钮
        if st.button("清除选择", key="preview_clear_selection"):
            clear_all_selections()
            st.rerun()
    
    with col2:
        # 复制所有命令
        if st.button("复制所有命令", key="preview_copy_all"):
            commands = []
            for task_name in selected_tasks:
                cmd = get_task_command(task_name, current_taskfile)
                commands.append(cmd)
            
            all_commands = "\n".join(commands)
            copy_to_clipboard(all_commands)
            st.success("所有命令已复制到剪贴板")
    
    with col3:
        # 运行方式选择
        run_parallel = st.checkbox("并行运行", value=st.session_state.get('run_parallel', False), key="preview_run_parallel")
        st.session_state.run_parallel = run_parallel
    
    with col4:
        # 运行所有选中任务
        if st.button("运行所有任务", key="preview_run_all"):
            with st.spinner("正在启动所有选中的任务..."):
                results = run_tasks_via_cmd(selected_tasks, current_taskfile, parallel=run_parallel)
                # 记录所有任务的运行状态
                for task_name in selected_tasks:
                    record_task_run(task_name, status="started")
            
            st.success(f"已启动 {len(selected_tasks)} 个任务")
    
    # 创建任务页签列表
    task_names = selected_df['name'].tolist()
    
    # 使用tabs来并列展示任务卡片
    if task_names:
        tabs = st.tabs([f"{task['emoji']} {task['name']}" for _, task in selected_df.iterrows()])
        
        # 在每个页签中渲染对应的任务卡片
        for idx, ((_, task), tab) in enumerate(zip(selected_df.iterrows(), tabs)):
            with tab:
                render_task_preview_in_tab(task, current_taskfile, idx)


def render_task_preview_in_tab(task, current_taskfile, idx=0):
    """在页签中渲染单个任务的预览卡片
    
    参数:
        task: 任务数据
        current_taskfile: 当前任务文件路径
        idx: 任务索引，用于生成唯一key
    """
    # 使用通用任务卡片渲染函数
    render_task_card(
        task=task, 
        current_taskfile=current_taskfile, 
        idx=idx, 
        view_type="preview", 
        show_checkbox=False
    )


