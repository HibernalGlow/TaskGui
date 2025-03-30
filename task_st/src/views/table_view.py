import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .selected_tasks_view import render_selected_tasks_sidebar
from .aggrid_table import render_aggrid_table
from .standard_table import render_edit_table

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图 - 使用三列布局
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    # 初始化列宽设置
    if 'column_widths' not in st.session_state:
        st.session_state.column_widths = [3, 1, 2]  # 默认宽度比例 [左侧, 中间, 右侧]
    
    # 初始化侧边栏状态
    if 'show_right_sidebar' not in st.session_state:
        st.session_state.show_right_sidebar = True
    
    # 设置三列布局
    left_col_width, middle_col_width, right_col_width = st.session_state.column_widths
    
    # 创建三列布局 - 使用现有的Streamlit列
    left_col, middle_col, right_col = st.columns([left_col_width, middle_col_width, right_col_width])
    
    # 左边栏 - 显示主表格
    with left_col:
        st.markdown("### 任务列表")
        # 正常表格视图
        render_aggrid_table(filtered_df, current_taskfile)
    
    # 中间栏 - 用于列宽调整
    with middle_col:
        st.markdown("### 布局控制")
        
        # 添加列宽调整控件
        st.markdown("调整列宽比例")
        left_width = st.slider("左侧表格宽度", 1, 6, st.session_state.column_widths[0], key="left_width_slider")
        middle_width = st.slider("中间控制栏宽度", 1, 3, st.session_state.column_widths[1], key="middle_width_slider")
        right_width = st.slider("右侧任务栏宽度", 1, 6, st.session_state.column_widths[2], key="right_width_slider")
        
        # 保存按钮
        if st.button("应用列宽设置"):
            st.session_state.column_widths = [left_width, middle_width, right_width]
            st.rerun()
        
        # 可折叠边栏控制
        sidebar_status = "隐藏" if st.session_state.show_right_sidebar else "显示"
        if st.button(f"{sidebar_status}右侧任务栏"):
            st.session_state.show_right_sidebar = not st.session_state.show_right_sidebar
            st.rerun()
        
        # 重置按钮
        if st.button("重置布局"):
            st.session_state.column_widths = [3, 1, 2]
            st.session_state.show_right_sidebar = True
            st.rerun()
    
    # 右边栏 - 显示已选择的任务
    with right_col:
        if st.session_state.show_right_sidebar:
            render_selected_tasks_sidebar(filtered_df, current_taskfile)
        else:
            st.markdown("### 任务面板 (已折叠)")

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用标准data_editor，这里重定向到新函数
    render_edit_table(filtered_df, current_taskfile)