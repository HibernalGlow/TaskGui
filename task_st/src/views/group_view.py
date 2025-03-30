import streamlit as st
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..components.batch_operations import render_batch_operations

def render_group_view(filtered_df, current_taskfile):
    """渲染分组视图"""
    st.markdown("### 任务分组")
    
    # 按主标签分组
    if filtered_df.empty or 'tags' not in filtered_df.columns:
        st.warning("没有任务可显示或任务没有标签")
        return
    
    # 获取每个任务的主标签（第一个标签）
    filtered_df['primary_tag'] = filtered_df['tags'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else '未分类'
    )
    
    # 获取所有主标签
    primary_tags = sorted(filtered_df['primary_tag'].unique())
    
    # 为每个标签创建一个部分
    for tag in primary_tags:
        with st.expander(f"📂 {tag} ({len(filtered_df[filtered_df['primary_tag'] == tag])})", expanded=True):
            tag_tasks = filtered_df[filtered_df['primary_tag'] == tag]
            
            # 为该标签下的每个任务创建一个容器
            for _, task in tag_tasks.iterrows():
                with st.container():
                    # 标题行
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {task['emoji']} {task['name']}")
                    with col2:
                        # 选择框
                        is_selected = task['name'] in st.session_state.selected_tasks if 'selected_tasks' in st.session_state else False
                        if st.checkbox("选择", value=is_selected, key=f"group_{task['name']}"):
                            if 'selected_tasks' not in st.session_state:
                                st.session_state.selected_tasks = []
                            if task['name'] not in st.session_state.selected_tasks:
                                st.session_state.selected_tasks.append(task['name'])
                        elif 'selected_tasks' in st.session_state and task['name'] in st.session_state.selected_tasks:
                            st.session_state.selected_tasks.remove(task['name'])
                    
                    # 任务信息
                    st.markdown(f"**描述**: {task['description']}")
                    
                    # 显示所有标签
                    tags_str = ', '.join([f"#{t}" for t in task['tags']]) if isinstance(task['tags'], list) else ''
                    st.markdown(f"**标签**: {tags_str}")
                    
                    # 目录
                    st.markdown(f"**目录**: `{task['directory']}`")
                    
                    # 命令
                    cmd = get_task_command(task['name'], current_taskfile)
                    st.code(cmd, language="bash")
                    
                    # 操作按钮
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("运行", key=f"run_group_{task['name']}"):
                            with st.spinner(f"正在启动任务 {task['name']}..."):
                                result = run_task_via_cmd(task['name'], current_taskfile)
                            st.success(f"任务 {task['name']} 已在新窗口启动")
                    
                    with col2:
                        # 文件按钮
                        if st.button("文件", key=f"file_group_{task['name']}"):
                            if task['directory'] and os.path.exists(task['directory']):
                                files = get_directory_files(task['directory'])
                                if files:
                                    st.markdown("##### 文件列表")
                                    for i, file in enumerate(files):
                                        file_path = os.path.join(task['directory'], file)
                                        if st.button(file, key=f"file_group_{task['name']}_{i}"):
                                            if open_file(file_path):
                                                st.success(f"已打开: {file}")
                                else:
                                    st.info("没有找到文件")
                    
                    with col3:
                        # 复制命令按钮
                        if st.button("复制", key=f"copy_group_{task['name']}"):
                            copy_to_clipboard(cmd)
                            st.success("命令已复制")
                    
                    st.markdown("---")
    
    # 批量操作部分
    render_batch_operations(current_taskfile, view_key="group") 