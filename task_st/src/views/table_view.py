import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .selected_tasks_view import render_selected_tasks_section
from .aggrid_table import render_aggrid_table
from .standard_table import render_edit_table
from .task_editor import render_edit_controls

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    st.markdown("### 任务列表")
    
    # 初始化编辑模式状态
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    # 渲染编辑模式控制按钮
    edit_mode_enabled = render_edit_controls(filtered_df, current_taskfile)
    
    # 根据编辑模式状态选择渲染表格还是编辑器
    if edit_mode_enabled:
        # 在编辑模式下，使用专门的编辑器视图
        from .task_editor import render_task_editor
        render_task_editor(filtered_df, current_taskfile)
    else:
        # 正常表格视图
        render_aggrid_table(filtered_df, current_taskfile)
        # 显示已选择的任务操作区域
        render_selected_tasks_section(filtered_df, current_taskfile)

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用标准data_editor，这里重定向到新函数
    render_edit_table(filtered_df, current_taskfile)