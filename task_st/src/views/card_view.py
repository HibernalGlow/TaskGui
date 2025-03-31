import streamlit as st
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..components.batch_operations import render_batch_operations
from ..utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, record_task_run

def render_card_view(filtered_df, current_taskfile):
    """渲染卡片视图"""
    # 确保全局状态已初始化
    init_global_state()
    
    st.markdown("### 任务卡片")
    
    # 每行显示的卡片数量
    cards_per_row = 3
    
    # 创建行
    for i in range(0, len(filtered_df), cards_per_row):
        cols = st.columns(cards_per_row)
        # 获取当前行的任务
        row_tasks = filtered_df.iloc[i:min(i+cards_per_row, len(filtered_df))]
        
        # 为每个列填充卡片
        for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
            with cols[col_idx]:
                with st.container():
                    # 卡片标题
                    st.markdown(f"### {task['emoji']} {task['name']}")
                    
                    # 描述
                    st.markdown(f"**描述**: {task['description']}")
                    
                    # 标签
                    tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
                    st.markdown(f"**标签**: {tags_str}")
                    
                    # 目录
                    st.markdown(f"**目录**: `{task['directory']}`")
                    
                    # 命令
                    cmd = get_task_command(task['name'], current_taskfile)
                    st.code(cmd, language="bash")
                    
                    # 获取当前选择状态，直接从全局状态获取
                    is_selected = get_task_selection_state(task['name'])
                    
                    # 渲染勾选框，使用值变化模式而不是重复检查状态
                    checkbox_value = st.checkbox("选择此任务", value=is_selected, key=f"card_{task['name']}")
                    
                    # 如果勾选状态与记录的状态不同，更新状态
                    if checkbox_value != is_selected:
                        update_task_selection(task['name'], checkbox_value)
                        st.rerun()  # 立即刷新以更新预览
                    
                    # 操作按钮
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("运行", key=f"run_card_{task['name']}"):
                            with st.spinner(f"正在启动任务 {task['name']}..."):
                                result = run_task_via_cmd(task['name'], current_taskfile)
                                # 记录任务运行
                                record_task_run(task['name'], status="started")
                            st.success(f"任务 {task['name']} 已在新窗口启动")
                    
                    with col2:
                        # 文件按钮
                        if st.button("文件", key=f"file_card_{task['name']}"):
                            if task['directory'] and os.path.exists(task['directory']):
                                files = get_directory_files(task['directory'])
                                if files:
                                    st.markdown("##### 文件列表")
                                    for i, file in enumerate(files):
                                        file_path = os.path.join(task['directory'], file)
                                        if st.button(file, key=f"file_card_{task['name']}_{i}"):
                                            if open_file(file_path):
                                                st.success(f"已打开: {file}")
                                else:
                                    st.info("没有找到文件")
                    
                    with col3:
                        # 复制命令按钮
                        if st.button("复制", key=f"copy_card_{task['name']}"):
                            copy_to_clipboard(cmd)
                            st.success("命令已复制")
                    
                    st.markdown("---")
    
    # 批量操作部分
    # render_batch_operations(current_taskfile, view_key="card")