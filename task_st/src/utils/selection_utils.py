import streamlit as st
import json

# 初始化全局任务状态
def init_global_state():
    """
    初始化全局任务状态JSON
    """
    if 'global_task_state' not in st.session_state:
        st.session_state.global_task_state = {
            "selected": {},      # 选中状态字典
            "selected_tasks": [], # 选中的任务列表
            "last_updated": None,  # 最后更新时间
            "version": "1.0"      # 状态版本
        }

# 获取全局状态
def get_global_state():
    """
    获取全局任务状态JSON
    """
    init_global_state()
    return st.session_state.global_task_state

# 更新全局状态
def update_global_state(state_dict):
    """
    直接更新全局状态
    """
    init_global_state()
    st.session_state.global_task_state = state_dict
    # 更新会话状态兼容层
    st.session_state.selected = state_dict["selected"]
    st.session_state.selected_tasks = state_dict["selected_tasks"]

def update_task_selection(task_name, is_selected, rerun=True):
    """
    统一的任务选中状态更新函数
    
    参数:
        task_name: 任务名称
        is_selected: 是否选中
        rerun: 是否执行rerun刷新页面
    """
    # 初始化全局状态
    init_global_state()
    global_state = get_global_state()
    
    # 更新选中状态字典
    global_state["selected"][task_name] = is_selected
    
    # 根据字典重建选中任务列表
    global_state["selected_tasks"] = [
        task for task, is_selected in global_state["selected"].items() 
        if is_selected
    ]
    
    # 更新最后修改时间
    from datetime import datetime
    global_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 更新全局状态
    update_global_state(global_state)
    
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
    # 获取全局状态
    global_state = get_global_state()
    
    # 获取当前状态
    current_state = global_state["selected"].get(task_name, False)
    
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
    # 获取全局状态
    global_state = get_global_state()
    
    # 返回任务选中状态
    return global_state["selected"].get(task_name, False)

def init_selection_state(task_names):
    """
    初始化任务选择状态
    
    参数:
        task_names: 所有任务名称列表
    """
    # 获取全局状态
    global_state = get_global_state()
    
    # 确保所有任务都有选择状态
    for task in task_names:
        if task not in global_state["selected"]:
            global_state["selected"][task] = False
    
    # 更新全局状态
    update_global_state(global_state)

def clear_all_selections(rerun=True):
    """
    清除所有选中状态
    
    参数:
        rerun: 是否执行rerun刷新页面
    """
    # 获取全局状态
    global_state = get_global_state()
    
    # 清除所有选中状态
    for task in global_state["selected"]:
        global_state["selected"][task] = False
    
    # 清空选中任务列表
    global_state["selected_tasks"] = []
    
    # 更新全局状态
    update_global_state(global_state)
    
    # 根据需要重新运行应用
    if rerun:
        st.rerun()

def export_global_state_json():
    """
    导出全局状态为JSON字符串
    """
    global_state = get_global_state()
    return json.dumps(global_state, indent=2)

def import_global_state_json(json_str, rerun=True):
    """
    从JSON字符串导入全局状态
    """
    try:
        state_dict = json.loads(json_str)
        update_global_state(state_dict)
        if rerun:
            st.rerun()
        return True
    except Exception as e:
        print(f"导入状态失败: {str(e)}")
        return False
