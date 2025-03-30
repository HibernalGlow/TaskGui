import streamlit as st
import os
import yaml
import shutil
from datetime import datetime
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from .task_card_editor import render_task_edit_form

def render_selected_tasks_section(filtered_df, current_taskfile):
    """渲染已选择任务的区域，包括清除选择按钮和卡片视图"""
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 获取选中的任务列表
    selected_tasks = st.session_state.selected_tasks
    
    # 显示已选择的任务数量和操作按钮
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 已选择 {len(selected_tasks)} 个任务")
    
    # 定义清除选择的回调函数
    def clear_selection():
        st.session_state.selected_tasks = []
        if 'selected' in st.session_state:
            for task in st.session_state.selected:
                st.session_state.selected[task] = False
    
    with col2:
        if st.button("清除选择", key="clear_table_selection", on_click=clear_selection):
            pass  # 清除选择的动作由回调函数处理，避免刷新
    
    with col3:
        if st.button("运行选中的任务", key="run_selected_tasks"):
            if not selected_tasks:
                st.warning("请先选择要运行的任务")
            else:
                from ..services.task_runner import run_multiple_tasks
                with st.spinner(f"正在启动 {len(selected_tasks)} 个任务..."):
                    result_msgs = run_multiple_tasks(
                        selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.get('run_parallel', False)
                    )
                
                for msg in result_msgs:
                    st.success(msg)
    
    # 如果有选中的任务，显示卡片视图
    if selected_tasks:
        # 过滤出选中的任务数据
        selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)]
        render_task_cards(selected_df, current_taskfile)

def render_task_cards(selected_df, current_taskfile):
    """渲染可编辑的任务卡片"""
    # 使用卡片视图显示选中的任务
    with st.container():
        # 每行显示的卡片数量
        cards_per_row = 2  # 改为2列以便有更多空间显示编辑控件
        
        # 创建行
        for i in range(0, len(selected_df), cards_per_row):
            cols = st.columns(cards_per_row)
            # 获取当前行的任务
            row_tasks = selected_df.iloc[i:min(i+cards_per_row, len(selected_df))]
            
            # 为每个列填充卡片
            for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
                with cols[col_idx]:
                    render_task_card(task, current_taskfile)

def render_task_card(task, current_taskfile):
    """渲染单个任务卡片，增加编辑功能"""
    task_name = task['name']
    
    # 初始化卡片编辑状态
    card_edit_key = f"card_edit_{task_name}"
    if card_edit_key not in st.session_state:
        st.session_state[card_edit_key] = False
    
    with st.container():
        # 卡片标题和编辑按钮
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### {task['emoji']} {task_name}")
        with col2:
            if st.button("编辑", key=f"edit_btn_{task_name}"):
                st.session_state[card_edit_key] = not st.session_state[card_edit_key]
                st.rerun()
        
        # 根据编辑状态显示不同内容
        if st.session_state[card_edit_key]:
            # 编辑模式
            render_task_edit_form(task, current_taskfile, on_save_callback=lambda: 
                setattr(st.session_state, card_edit_key, False))
        else:
            # 显示模式
            # 描述
            st.markdown(f"**描述**: {task['description']}")
            
            # 标签
            tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
            st.markdown(f"**标签**: {tags_str}")
            
            # 目录
            st.markdown(f"**目录**: `{task['directory']}`")
            
            # 命令
            cmd = get_task_command(task_name, current_taskfile)
            st.code(cmd, language="bash")
            
            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("运行", key=f"run_selected_{task_name}"):
                    with st.spinner(f"正在启动任务 {task_name}..."):
                        result = run_task_via_cmd(task_name, current_taskfile)
                    st.success(f"任务 {task_name} 已在新窗口启动")
            
            with col2:
                # 文件按钮
                if st.button("文件", key=f"file_selected_{task_name}"):
                    if task['directory'] and os.path.exists(task['directory']):
                        files = get_directory_files(task['directory'])
                        if files:
                            st.markdown("##### 文件列表")
                            for j, file in enumerate(files):
                                file_path = os.path.join(task['directory'], file)
                                if st.button(file, key=f"file_selected_{task_name}_{j}"):
                                    if open_file(file_path):
                                        st.success(f"已打开: {file}")
                    else:
                        st.info("没有找到文件")
            
            with col3:
                # 复制命令按钮
                if st.button("复制", key=f"copy_selected_{task_name}"):
                    copy_to_clipboard(cmd)
                    st.success("命令已复制")
        
        st.markdown("---")
