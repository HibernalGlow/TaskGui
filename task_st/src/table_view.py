import streamlit as st
import os
import json
import pandas as pd
from .utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .task_runner import run_task_via_cmd
from .common import render_batch_operations
from .card_view import render_card_view

# 尝试导入AgGrid
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    st.error("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    st.markdown("### 任务列表")
    
    # 使用自定义表格渲染，避免data_editor的闪烁问题
    render_custom_table(filtered_df, current_taskfile)
    
    # 显示已选择的任务操作区域
    render_selected_tasks_section(filtered_df, current_taskfile)

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
    
    with col2:
        # 清除选择按钮 - 直接更新状态，不使用回调
        if st.button("清除选择", key="clear_table_selection"):
            # 清空选中任务列表
            st.session_state.selected_tasks = []
    
    with col3:
        if st.button("运行选中的任务", key="run_selected_tasks"):
            if not selected_tasks:
                st.warning("请先选择要运行的任务")
            else:
                from .task_runner import run_multiple_tasks
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
        
        # 使用卡片视图显示选中的任务
        with st.container():
            # 每行显示的卡片数量
            cards_per_row = 3
            
            # 创建行
            for i in range(0, len(selected_df), cards_per_row):
                cols = st.columns(cards_per_row)
                # 获取当前行的任务
                row_tasks = selected_df.iloc[i:min(i+cards_per_row, len(selected_df))]
                
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
                            
                            # 操作按钮，不包含选择框（已经在表格中选择了）
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("运行", key=f"run_selected_{task['name']}"):
                                    with st.spinner(f"正在启动任务 {task['name']}..."):
                                        result = run_task_via_cmd(task['name'], current_taskfile)
                                    st.success(f"任务 {task['name']} 已在新窗口启动")
                            
                            with col2:
                                # 文件按钮
                                if st.button("文件", key=f"file_selected_{task['name']}"):
                                    if task['directory'] and os.path.exists(task['directory']):
                                        files = get_directory_files(task['directory'])
                                        if files:
                                            st.markdown("##### 文件列表")
                                            for j, file in enumerate(files):
                                                file_path = os.path.join(task['directory'], file)
                                                if st.button(file, key=f"file_selected_{task['name']}_{j}"):
                                                    if open_file(file_path):
                                                        st.success(f"已打开: {file}")
                                    else:
                                        st.info("没有找到文件")
                            
                            with col3:
                                # 复制命令按钮
                                if st.button("复制", key=f"copy_selected_{task['name']}"):
                                    copy_to_clipboard(cmd)
                                    st.success("命令已复制")
                            
                            st.markdown("---")

def render_custom_table(filtered_df, current_taskfile):
    """自定义表格实现 - 使用手动创建的复选框和列，避免data_editor的闪烁问题"""
    
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 为每一行创建一个唯一的选择键
    def toggle_task(task_name):
        if task_name in st.session_state.selected_tasks:
            st.session_state.selected_tasks.remove(task_name)
        else:
            st.session_state.selected_tasks.append(task_name)
    
    # 创建表头
    header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([1, 3, 8, 3, 4])
    with header_col1:
        st.markdown("**选择**")
    with header_col2:
        st.markdown("**任务名称**")
    with header_col3:
        st.markdown("**描述**")
    with header_col4:
        st.markdown("**标签**")
    with header_col5:
        st.markdown("**目录**")
    
    # 创建表格主体 - 使用容器包装以获得更好的样式
    with st.container():
        for _, task in filtered_df.iterrows():
            task_name = task['name']
            
            # 判断此任务是否已选中
            is_selected = task_name in st.session_state.selected_tasks
            
            # 创建行
            col1, col2, col3, col4, col5 = st.columns([1, 3, 8, 3, 4])
            
            # 选择列 - 使用复选框
            with col1:
                # 创建一个唯一键的复选框
                if st.checkbox("", value=is_selected, key=f"check_{task_name}", 
                               on_change=toggle_task, args=(task_name,)):
                    # 复选框的处理由on_change回调函数处理
                    pass
            
            # 任务名称列
            with col2:
                st.markdown(f"{task['emoji']} {task_name}")
            
            # 描述列 - 截断过长的描述
            with col3:
                description = task['description']
                if len(description) > 80:
                    description = description[:80] + "..."
                st.markdown(description)
            
            # 标签列
            with col4:
                tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
                st.markdown(tags_str)
            
            # 目录列
            with col5:
                st.markdown(f"`{task['directory']}`")
            
            # 添加分隔线
            st.markdown("---")

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格 - 保留但不使用"""
    st.warning("AgGrid表格存在选择状态问题，已改为使用自定义表格。")
    render_custom_table(filtered_df, current_taskfile)

def render_edit_table(filtered_df, current_taskfile):
    """标准表格实现 - 保留但重定向到自定义表格"""
    # 由于data_editor的闪烁问题，重定向到自定义表格实现
    render_custom_table(filtered_df, current_taskfile)

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用自定义表格，这里重定向到新函数
    render_custom_table(filtered_df, current_taskfile)