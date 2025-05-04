import streamlit as st
from src.utils.selection_utils import get_selected_tasks
from src.views.card.card_view import render_card_view

def render_preview_tab(filtered_df, default_taskfile):
    """渲染预览标签页"""
    # 获取选中的任务
    selected_tasks = get_selected_tasks()
    if not selected_tasks:
        st.info("没有选中的任务。请从表格中选择要操作的任务。")
    else:
        # 筛选出选中的任务数据
        selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)].copy()
        # 使用卡片视图函数显示
        # st.markdown(f"## 已选择 {len(selected_tasks)} 个任务")
        render_card_view(selected_df, default_taskfile, key_prefix="preview_view") 