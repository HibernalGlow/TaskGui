import streamlit as st
import os
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from .standard_table import render_edit_table
from .aggrid_table import render_aggrid_table
from ..components.preview_card import render_shared_preview
from ..components.batch_operations import render_batch_operations
from ..utils.selection_utils import force_save_state

def render_table_view(filtered_df, current_taskfile, show_sidebar=True):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
        show_sidebar: 是否显示右侧预览，默认显示
    """
    # 记录原始状态，用于比较变动
    initial_state = st.session_state.selected_tasks.copy() if 'selected_tasks' in st.session_state else []
    
    # 侧边栏状态控制
    if 'sidebar_visible' not in st.session_state:
        st.session_state.sidebar_visible = show_sidebar
    
    # 根据侧边栏显示状态创建布局
    if st.session_state.sidebar_visible:
        # 双列布局：主内容 + 预览侧边栏
        main_col, preview_col = st.columns([3, 1])
        
        # 主列内容
        with main_col:
            render_main_content(filtered_df, current_taskfile)
        
        # 预览列内容
        with preview_col:
            st.markdown("### 任务预览")
            render_shared_preview(filtered_df, current_taskfile, location="sidebar")
    else:
        # 单列布局：只有主内容
        render_main_content(filtered_df, current_taskfile)
        
        # 如果没有侧边栏但有选中任务，则在主内容下方展示预览卡片
        if len(st.session_state.selected_tasks) > 0:
            st.markdown("### 选中任务预览")
            render_shared_preview(filtered_df, current_taskfile, location="main")
    
    # 添加批量操作
    render_batch_operations(current_taskfile, view_key="table")

def render_main_content(filtered_df, current_taskfile):
    """渲染主内容区域"""
    # 添加表格标题和控制按钮
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown("### 任务表格")
    
    with col2:
        # 保存表格变更按钮 - 用于手动触发保存
        if st.button("保存变更", key="save_table_changes"):
            with st.spinner("正在保存表格变更..."):
                force_save_state()
            st.success("变更已保存")
    
    with col3:
        # 刷新表格按钮 - 用于手动刷新视图
        if st.button("刷新表格", key="refresh_table"):
            st.session_state._force_refresh_aggrid = True
            st.rerun()
            
    with col4:
        # 切换侧边栏显示状态
        sidebar_label = "隐藏预览" if st.session_state.sidebar_visible else "显示预览"
        if st.button(sidebar_label, key="toggle_sidebar"):
            st.session_state.sidebar_visible = not st.session_state.sidebar_visible
            st.rerun()
    
    # 使用标签页选择不同的表格视图
    tab1, tab2 = st.tabs(["高级表格(AgGrid)", "标准表格"])
    
    with tab1:
        st.info("提示: 选中表格行后可编辑数据，编辑完成后点击'保存变更'按钮应用更改。")
        
        # 使用AgGrid渲染表格
        result = render_aggrid_table(filtered_df, current_taskfile)
        
        # 添加警告信息
        if '_aggrid_selection_state' in st.session_state and len(st.session_state._aggrid_selection_state) > 0:
            st.info("✅ 表格选中状态已临时保存，点击'保存变更'按钮或'刷新表格'按钮以应用到全局状态。")
    
    with tab2:
        # 使用标准表格渲染 - 使用正确的函数
        render_edit_table(filtered_df, current_taskfile)