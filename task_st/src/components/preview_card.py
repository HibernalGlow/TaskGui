import streamlit as st
import pandas as pd
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard
from ..services.task_runner import run_task_via_cmd, run_tasks_via_cmd
from ..utils.selection_utils import get_selected_tasks, clear_all_selections, get_global_state, record_task_run, get_task_runtime

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
    # 任务标题和描述
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**描述**: {task['description']}")
    
    with col2:
        # 添加操作按钮
        run_key = f"preview_run_{idx}_{task['name']}"
        if st.button("运行", key=run_key):
            with st.spinner(f"正在启动任务 {task['name']}..."):
                result = run_task_via_cmd(task['name'], current_taskfile)
                # 记录任务运行
                record_task_run(task['name'], status="started")
            st.success(f"任务 {task['name']} 已在新窗口启动")
        
        # 复制命令按钮
        copy_key = f"preview_copy_{idx}_{task['name']}"
        if st.button("复制命令", key=copy_key):
            cmd = get_task_command(task['name'], current_taskfile)
            copy_to_clipboard(cmd)
            st.success("命令已复制到剪贴板")
    
    # 显示标签
    if isinstance(task['tags'], list) and task['tags']:
        st.markdown("**标签**: " + " ".join([f"<span class='tag'>#{tag}</span>" for tag in task['tags']]), unsafe_allow_html=True)
    
    # 显示目录
    st.markdown(f"**目录**: `{task['directory']}`")
    
    # 显示命令
    cmd = get_task_command(task['name'], current_taskfile)
    st.code(cmd, language="bash")
    
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


# 保留原始的render_task_preview函数，以便在其他地方可能的调用
def render_task_preview(task, current_taskfile, idx=0):
    """渲染单个任务的预览卡片
    
    参数:
        task: 任务数据
        current_taskfile: 当前任务文件路径
        idx: 任务索引，用于生成唯一key
    """
    # 创建一个带边框的容器
    with st.container():
        st.markdown("---")
        
        # 任务标题和描述
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"#### {task['emoji']} {task['name']}")
            st.markdown(f"**描述**: {task['description']}")
        
        with col2:
            # 添加操作按钮
            run_key = f"preview_run_{idx}_{task['name']}"
            if st.button("运行", key=run_key):
                with st.spinner(f"正在启动任务 {task['name']}..."):
                    result = run_task_via_cmd(task['name'], current_taskfile)
                    # 记录任务运行
                    record_task_run(task['name'], status="started")
                st.success(f"任务 {task['name']} 已在新窗口启动")
            
            # 复制命令按钮
            copy_key = f"preview_copy_{idx}_{task['name']}"
            if st.button("复制命令", key=copy_key):
                cmd = get_task_command(task['name'], current_taskfile)
                copy_to_clipboard(cmd)
                st.success("命令已复制到剪贴板")
        
        # 显示标签
        if isinstance(task['tags'], list) and task['tags']:
            st.markdown("**标签**: " + " ".join([f"<span class='tag'>#{tag}</span>" for tag in task['tags']]), unsafe_allow_html=True)
        
        # 显示目录
        st.markdown(f"**目录**: `{task['directory']}`")
        
        # 显示命令
        cmd = get_task_command(task['name'], current_taskfile)
        st.code(cmd, language="bash")
        
        # 获取任务运行时数据
        runtime = get_task_runtime(task['name'])
        
        # 如果有运行记录，显示运行信息
        if runtime.get("run_count", 0) > 0:
            st.markdown(f"**运行次数**: {runtime.get('run_count', 0)}")
            st.markdown(f"**最后运行**: {runtime.get('last_run', 'N/A')}")
            st.markdown(f"**最后状态**: {runtime.get('last_status', 'N/A')}")
        
        st.markdown("---")
