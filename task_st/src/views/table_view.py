import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .selected_tasks_view import render_selected_tasks_section, render_selected_tasks_sidebar
from .aggrid_table import render_aggrid_table
from .standard_table import render_edit_table

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    # 初始化侧边栏状态
    if 'show_right_sidebar' not in st.session_state:
        st.session_state.show_right_sidebar = True
    
    # 创建主布局
    main_cols = st.columns([3, 1] if st.session_state.show_right_sidebar else [1])
    
    # 主要内容区(左侧)
    with main_cols[0]:
        st.markdown("### 任务列表")
        
        # 正常表格视图
        render_aggrid_table(filtered_df, current_taskfile)
    
    # 右侧边栏(如果启用)
    if st.session_state.show_right_sidebar:
        with main_cols[1]:
            # 切换侧边栏按钮
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("⬅️"):
                    st.session_state.show_right_sidebar = False
                    st.rerun()
            
            # 显示已选择的任务操作区域
            render_selected_tasks_sidebar(filtered_df, current_taskfile)
    else:
        # 显示打开侧边栏的按钮
        st.sidebar.markdown("---")
        if st.sidebar.button("显示任务栏 ➡️"):
            st.session_state.show_right_sidebar = True
            st.rerun()

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用标准data_editor，这里重定向到新函数
    render_edit_table(filtered_df, current_taskfile)