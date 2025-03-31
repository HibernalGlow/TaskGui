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
    
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
    
    # 更新选中状态字典
    st.session_state.selected[task_name] = is_selected
    
    # 根据字典重建选中任务列表
    st.session_state.selected_tasks = [
        task for task, is_selected in st.session_state.selected.items() 
        if is_selected
    ]
    
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
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
    
    # 获取当前状态
    current_state = st.session_state.selected.get(task_name, False)
    
    # 更新为相反状态
    update_task_selection(task_name, not current_state, rerun)

def get_task_selection_state(task_name):
    """
    获取任务的选中状态
    
    参数:
        task_name: 任务名称
    返回:
        bool: 任务是否被选中
    """
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
    
    return st.session_state.selected.get(task_name, False)

def init_selection_state(task_names):
    """
    初始化任务选择状态
    
    参数:
        task_names: 所有任务名称列表
    """
    # 确保会话状态初始化
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
        
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 确保所有任务都有选择状态
    for task in task_names:
        if task not in st.session_state.selected:
            st.session_state.selected[task] = False

def clear_all_selections(rerun=True):
    """
    清除所有选中状态
    
    参数:
        rerun: 是否执行rerun刷新页面
    """
    if 'selected' in st.session_state:
        for task in st.session_state.selected:
            st.session_state.selected[task] = False
    
    if 'selected_tasks' in st.session_state:
        st.session_state.selected_tasks = []
    
    if rerun:
        st.rerun()
