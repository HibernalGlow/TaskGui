import streamlit as st
import os
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..components.batch_operations import render_batch_operations
from ..utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, record_task_run
from ..components.task_card import render_task_card

def render_card_view(filtered_df, current_taskfile):
    """渲染卡片视图"""
    # 确保全局状态已初始化
    init_global_state()
    
    st.markdown("### 任务卡片")
    
    # 每行显示的卡片数量
    cards_per_row = 3
    
    # 创建行
    for i in range(0, len(filtered_df), cards_per_row):
        cols = st.columns(cards_per_row)
        # 获取当前行的任务
        row_tasks = filtered_df.iloc[i:min(i+cards_per_row, len(filtered_df))]
        
        # 为每个列填充卡片
        for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
            with cols[col_idx]:
                with st.container():
                    # 使用通用任务卡片渲染函数
                    render_task_card(
                        task=task,
                        current_taskfile=current_taskfile,
                        idx=i + col_idx,
                        view_type="card",
                        show_checkbox=True
                    )
    
    # 批量操作部分
    # render_batch_operations(current_taskfile, view_key="card")