import streamlit as st
import os
from src.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from src.services.task_runner import run_task_via_cmd
from src.components.batch_operations import render_batch_operations
from src.utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, record_task_run
from src.views.card.task_card import render_task_card

def render_card_view(filtered_df, current_taskfile, key_prefix="card_view"):
    """渲染卡片视图
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
        key_prefix: 组件key前缀，用于区分不同视图
    """
    # 确保全局状态已初始化
    init_global_state()
    
    st.markdown("### 任务卡片")
    
    # 添加每行卡片数量的滑动条
    cards_per_row = st.slider(
        "每行显示卡片数量", 
        min_value=1, 
        max_value=4, 
        value=3, 
        step=1,
        key=f"{key_prefix}_cards_per_row"
    )
    
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
                        view_type=key_prefix,  # 使用key_prefix作为视图类型
                        show_checkbox=True
                    )
    
    # 批量操作部分
    # render_batch_operations(current_taskfile, view_key="card")