import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .selected_tasks_view import render_selected_tasks_section
from .aggrid_table import render_aggrid_table
from .standard_table import render_edit_table

def render_table_view(filtered_df, current_taskfile, show_sidebar=False):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
        show_sidebar: 是否显示右侧预览侧边栏
    """
    # 不再初始化侧边栏状态，直接使用传入的参数
    
    # 创建主布局 - 移除侧边栏列
    st.markdown("### 任务列表")
    
    # 正常表格视图 - 不再分列
    render_aggrid_table(filtered_df, current_taskfile)
    
    # 右侧边栏(如果启用) - 但按照用户要求，我们不再显示这个侧边栏
    if show_sidebar:
        st.markdown("---")
        # 显示已选择的任务操作区域
        render_selected_tasks_sidebar(filtered_df, current_taskfile)

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用标准data_editor，这里重定向到新函数
    render_edit_table(filtered_df, current_taskfile)