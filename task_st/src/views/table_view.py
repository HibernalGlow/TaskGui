import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .selected_tasks_view import render_selected_tasks_section, render_selected_tasks_sidebar
from .aggrid_table import render_aggrid_table

def render_table_view(filtered_df, current_taskfile, show_sidebar=False):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
        show_sidebar: 是否显示右侧预览侧边栏
    """
    # 初始化侧边栏状态
    if 'show_right_sidebar' not in st.session_state:
        st.session_state.show_right_sidebar = show_sidebar
    
    # 创建主布局
    st.markdown("### 任务列表")
    
    # 正常表格视图 - 使用原始的AgGrid实现
    render_aggrid_table(filtered_df, current_taskfile)