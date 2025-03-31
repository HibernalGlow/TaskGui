import streamlit as st

def update_task_selection(task_name, is_selected, rerun=True):
    """
    统一的任务选中状态更新函数
    
    参数:
        task_name: 任务名称
        is_selected: 是否选中
        rerun: 是否执行rerun刷新页面
    """
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 更新选中状态
    if is_selected and task_name not in st.session_state.selected_tasks:
        st.session_state.selected_tasks.append(task_name)
    elif not is_selected and task_name in st.session_state.selected_tasks:
        st.session_state.selected_tasks.remove(task_name)
    
    # 同步更新selected字典状态
    if 'selected' in st.session_state:
        st.session_state.selected[task_name] = is_selected
    
    # 根据需要重新运行应用
    if rerun:
        st.rerun()

def toggle_task_selection(task_name, rerun=True):
    """
    切换任务的选中状态
    
    参数:
        task_name: 任务名称
        rerun: 是否执行rerun刷新页面
    """
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 切换选中状态
    is_currently_selected = task_name in st.session_state.selected_tasks
    
    if is_currently_selected:
        st.session_state.selected_tasks.remove(task_name)
    else:
        st.session_state.selected_tasks.append(task_name)
    
    # 同步更新selected字典状态
    if 'selected' in st.session_state:
        st.session_state.selected[task_name] = not is_currently_selected
    
    # 根据需要重新运行应用
    if rerun:
        st.rerun()
