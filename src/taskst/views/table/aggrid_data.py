import pandas as pd
import streamlit as st
from taskst.utils.selection_utils import update_task_selection, get_task_selection_state

def prepare_display_data(filtered_df):
    """准备表格显示数据"""
    filtered_df_copy = filtered_df.copy()
    
    # 处理标签
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    
    # 添加显示名称
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
    # 创建勾选列，从集中状态管理获取
    filtered_df_copy['选择'] = filtered_df_copy['name'].apply(
        lambda x: get_task_selection_state(x)
    )
    
    # 准备要显示的列
    display_df = filtered_df_copy[['选择', 'name', '显示名称', 'description', 'tags_str', 'directory']]
    display_df = display_df.rename(columns={
        'description': '描述',
        'tags_str': '标签',
        'directory': '目录'
    })
    
    return display_df, filtered_df_copy

def process_grid_selection_changes(grid_return):
    """处理表格勾选状态变化"""
    from taskst.utils.selection_utils import force_save_state, get_selected_tasks
    
    if 'data' not in grid_return:
        return False
    
    updated_df = pd.DataFrame(grid_return['data'])
    
    # 记录状态是否有变化
    has_changes = False
    
    # 检查每个任务的选择状态与全局状态是否一致
    for idx, row in updated_df.iterrows():
        task_name = row['name']
        if task_name and pd.notna(task_name):  # 确保任务名有效
            current_selection = bool(row['选择'])
            previous_selection = get_task_selection_state(task_name)
            
            # 如果状态有变化，更新全局状态
            if current_selection != previous_selection:
                has_changes = True
                update_task_selection(task_name, current_selection, rerun=False)
    
    # 如果有状态变化，强制更新内存缓存并更新会话状态
    if has_changes:
        # 更新内存缓存
        force_save_state()
        
        # 更新会话状态中的选中任务列表，确保预览卡能正确显示
        if 'selected_tasks' not in st.session_state:
            st.session_state.selected_tasks = []
        
        # 重新构建选中任务列表
        st.session_state.selected_tasks = list(updated_df[updated_df['选择'] == True]['name'].values)
    
    return has_changes 