import streamlit as st
import json
import yaml
from datetime import datetime
import os

# 全局状态文件路径
GLOBAL_STATE_FILE = "task_state.yaml"

# 初始化全局任务状态
def init_global_state():
    """
    初始化全局任务状态YAML
    """
    if 'global_task_state' not in st.session_state:
        # 尝试从文件加载状态
        if os.path.exists(GLOBAL_STATE_FILE):
            try:
                with open(GLOBAL_STATE_FILE, 'r', encoding='utf-8') as f:
                    st.session_state.global_task_state = yaml.safe_load(f)
                # 确保基本结构存在
                ensure_state_structure(st.session_state.global_task_state)
            except Exception as e:
                print(f"加载全局状态失败: {str(e)}")
                create_default_state()
        else:
            create_default_state()
    
    # 兼容旧的会话状态
    sync_session_state()

def create_default_state():
    """创建默认的全局状态结构"""
    current_time = datetime.now().isoformat()
    st.session_state.global_task_state = {
        "version": "1.0",
        "last_updated": current_time,
        "task_files": {},
        "tasks": {},
        "user_preferences": {
            "default_view": "aggrid",
            "last_filter": {
                "tags": [],
                "directory": None,
                "search_term": ""
            },
            "ui_settings": {
                "theme": "light",
                "aggrid_group_by": None
            }
        }
    }

def ensure_state_structure(state):
    """确保状态包含所有必要的字段"""
    if "version" not in state:
        state["version"] = "1.0"
    
    if "last_updated" not in state:
        state["last_updated"] = datetime.now().isoformat()
    
    if "task_files" not in state:
        state["task_files"] = {}
    
    if "tasks" not in state:
        state["tasks"] = {}
    
    if "user_preferences" not in state:
        state["user_preferences"] = {
            "default_view": "aggrid",
            "last_filter": {
                "tags": [],
                "directory": None,
                "search_term": ""
            },
            "ui_settings": {
                "theme": "light",
                "aggrid_group_by": None
            }
        }

def sync_session_state():
    """同步全局状态与会话状态的兼容层"""
    # 构建选中状态字典
    selected = {}
    selected_tasks = []
    
    for task_name, task_info in st.session_state.global_task_state.get("tasks", {}).items():
        is_selected = task_info.get("selected", False)
        selected[task_name] = is_selected
        if is_selected:
            selected_tasks.append(task_name)
    
    # 更新会话状态
    st.session_state.selected = selected
    st.session_state.selected_tasks = selected_tasks

# 获取全局状态
def get_global_state():
    """
    获取全局任务状态
    """
    init_global_state()
    return st.session_state.global_task_state

# 保存全局状态到文件
def save_global_state():
    """保存全局状态到YAML文件"""
    try:
        with open(GLOBAL_STATE_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(st.session_state.global_task_state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"保存全局状态失败: {str(e)}")
        return False

# 更新全局状态
def update_global_state(state_dict, save_to_file=True):
    """
    直接更新全局状态
    
    参数:
        state_dict: 新的状态字典
        save_to_file: 是否保存到文件
    """
    init_global_state()
    st.session_state.global_task_state = state_dict
    
    # 更新时间戳
    st.session_state.global_task_state["last_updated"] = datetime.now().isoformat()
    
    # 同步会话状态兼容层
    sync_session_state()
    
    # 保存到文件
    if save_to_file:
        save_global_state()

def register_task_file(file_path, meta=None):
    """
    注册任务文件
    
    参数:
        file_path: 任务文件路径
        meta: 元数据字典
    """
    global_state = get_global_state()
    
    if "task_files" not in global_state:
        global_state["task_files"] = {}
    
    current_time = datetime.now().isoformat()
    
    if file_path not in global_state["task_files"]:
        global_state["task_files"][file_path] = {
            "last_loaded": current_time,
            "meta": meta or {
                "description": "任务文件",
                "created_at": current_time
            }
        }
    else:
        global_state["task_files"][file_path]["last_loaded"] = current_time
        if meta:
            global_state["task_files"][file_path]["meta"].update(meta)
    
    update_global_state(global_state)

def register_tasks_from_df(tasks_df, source_file):
    """
    从DataFrame注册任务
    
    参数:
        tasks_df: 任务数据框
        source_file: 来源文件路径
    """
    for _, row in tasks_df.iterrows():
        task_name = row['name']
        task_data = row.to_dict()
        register_task(task_name, task_data, source_file)

def register_task(task_name, task_data, source_file, runtime_data=None):
    """
    注册单个任务
    
    参数:
        task_name: 任务名称
        task_data: 任务数据
        source_file: 来源文件
        runtime_data: 运行时数据
    """
    global_state = get_global_state()
    
    if "tasks" not in global_state:
        global_state["tasks"] = {}
    
    # 如果任务已存在，保留选中状态
    selected = False
    last_selected = None
    if task_name in global_state["tasks"]:
        selected = global_state["tasks"][task_name].get("selected", False)
        last_selected = global_state["tasks"][task_name].get("last_selected")
    
    # 创建或更新任务信息
    global_state["tasks"][task_name] = {
        "selected": selected,
        "last_selected": last_selected,
        "source_file": source_file,
        "data": task_data,
        "runtime": runtime_data or {
            "last_run": None,
            "run_count": 0,
            "last_status": None,
            "custom_flags": {}
        }
    }
    
    update_global_state(global_state)

def update_task_selection(task_name, is_selected, rerun=True):
    """
    更新任务选中状态
    
    参数:
        task_name: 任务名称
        is_selected: 是否选中
        rerun: 是否执行rerun刷新页面
    """
    global_state = get_global_state()
    
    if "tasks" in global_state and task_name in global_state["tasks"]:
        # 更新选中状态
        global_state["tasks"][task_name]["selected"] = is_selected
        
        # 如果被选中，记录选中时间
        if is_selected:
            global_state["tasks"][task_name]["last_selected"] = datetime.now().isoformat()
        
        # 更新全局状态
        update_global_state(global_state)
        
        # 同步会话状态
        sync_session_state()
        
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
    global_state = get_global_state()
    
    if "tasks" in global_state and task_name in global_state["tasks"]:
        # 获取当前状态并切换
        current_state = global_state["tasks"][task_name].get("selected", False)
        update_task_selection(task_name, not current_state, rerun)

def get_task_selection_state(task_name):
    """
    获取任务的选中状态
    
    参数:
        task_name: 任务名称
    返回:
        bool: 任务是否被选中
    """
    global_state = get_global_state()
    
    if "tasks" in global_state and task_name in global_state["tasks"]:
        return global_state["tasks"][task_name].get("selected", False)
    
    return False

def clear_all_selections(rerun=True):
    """
    清除所有选中状态
    
    参数:
        rerun: 是否执行rerun刷新页面
    """
    global_state = get_global_state()
    
    if "tasks" in global_state:
        for task_name in global_state["tasks"]:
            global_state["tasks"][task_name]["selected"] = False
    
    # 更新全局状态
    update_global_state(global_state)
    
    # 根据需要重新运行应用
    if rerun:
        st.rerun()

def update_task_runtime(task_name, runtime_data):
    """
    更新任务运行时数据
    
    参数:
        task_name: 任务名称
        runtime_data: 运行时数据字典
    """
    global_state = get_global_state()
    
    if "tasks" in global_state and task_name in global_state["tasks"]:
        # 获取当前运行时数据
        current_runtime = global_state["tasks"][task_name].get("runtime", {})
        
        # 更新运行时数据
        current_runtime.update(runtime_data)
        global_state["tasks"][task_name]["runtime"] = current_runtime
        
        # 更新全局状态
        update_global_state(global_state)
        return True
    
    return False

def record_task_run(task_name, status="success"):
    """
    记录任务运行
    
    参数:
        task_name: 任务名称
        status: 运行状态
    """
    global_state = get_global_state()
    
    if "tasks" in global_state and task_name in global_state["tasks"]:
        
        # 更新运行时数据
        runtime = global_state["tasks"][task_name]["runtime"]
        runtime["last_run"] = datetime.now().isoformat()
        runtime["run_count"] = runtime.get("run_count", 0) + 1
        runtime["last_status"] = status
        
        update_global_state(global_state)

def export_yaml_state():
    """
    导出全局状态为YAML字符串
    """
    global_state = get_global_state()
    return yaml.dump(global_state, default_flow_style=False, allow_unicode=True, sort_keys=False)

# 提供与main.py中使用的名称一致的别名
export_global_state_yaml = export_yaml_state

def import_global_state_yaml(yaml_str, rerun=True):
    """
    从YAML字符串导入全局状态
    """
    try:
        state_dict = yaml.safe_load(yaml_str)
        update_global_state(state_dict)
        if rerun:
            st.rerun()
        return True
    except Exception as e:
        print(f"导入状态失败: {str(e)}")
        return False

# 获取选中的任务列表
def get_selected_tasks():
    """获取选中的任务列表"""
    global_state = get_global_state()
    selected_tasks = []
    
    if "tasks" in global_state:
        for task_name, task_info in global_state["tasks"].items():
            if task_info.get("selected", False):
                selected_tasks.append(task_name)
    
    return selected_tasks

# 获取用户偏好设置
def get_user_preferences():
    """获取用户偏好设置"""
    global_state = get_global_state()
    return global_state.get("user_preferences", {})

# 更新用户偏好设置
def update_user_preferences(preferences):
    """更新用户偏好设置"""
    global_state = get_global_state()
    
    if "user_preferences" not in global_state:
        global_state["user_preferences"] = {}
    
    global_state["user_preferences"].update(preferences)
    update_global_state(global_state)

# 兼容旧方法 - 保留以确保兼容性
def export_global_state_json():
    """
    导出全局状态为JSON字符串 (兼容旧版本)
    """
    global_state = get_global_state()
    return json.dumps(global_state, indent=2, ensure_ascii=False)

def import_global_state_json(json_str, rerun=True):
    """
    从JSON字符串导入全局状态 (兼容旧版本)
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
