import streamlit as st
import os
import pandas as pd
from taskgui.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from taskgui.views.table.aggrid_table import render_aggrid_table
from taskgui.components.batch_operations import render_batch_operations
from taskgui.utils.selection_utils import force_save_state

def render_table_view(filtered_df, current_taskfile, show_sidebar=True):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
        show_sidebar: 不再使用，保留参数兼容旧接口
    """
    # 添加表格标题和控制按钮
    col1, col2, col3 = st.columns([3, 1, 1])
    # with col1:
    #     st.markdown("### 任务表格")
    
    # with col2:
    #     # 保存表格变更按钮 - 用于手动触发保存
    #     if st.button("保存变更", key="save_table_changes"):
    #         with st.spinner("正在保存表格变更..."):
    #             force_save_state()
    #         st.success("变更已保存")
    
    # with col3:
    #     # 刷新表格按钮 - 用于手动刷新视图
    #     if st.button("刷新表格", key="refresh_table"):
    #         st.session_state._force_refresh_aggrid = True
    #         st.rerun()
    
    # 使用AgGrid渲染表格
    # st.info("提示: 在表格中选中行后，可以在上方预览卡片中查看详情。点击'保存变更'按钮应用更改。")
    
    # 渲染AgGrid表格
    result = render_aggrid_table(filtered_df, current_taskfile)
    
    # 检查是否有选中的任务
    has_selected_tasks = len(st.session_state.selected_tasks) > 0 if 'selected_tasks' in st.session_state else False
    
    # 批量操作 - 使用可折叠卡片
    batch_expander = st.expander("批量操作", expanded=has_selected_tasks)
    # with batch_expander:
    #     render_batch_operations(current_taskfile, view_key="table")