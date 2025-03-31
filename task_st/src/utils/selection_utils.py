import streamlit as st
import json
from datetime import datetime

# 全局内存缓存
_MEMORY_CACHE = None  # 内存缓存

# 初始化全局任务状态
def init_global_state():
    """
    初始化全局任务状态 - 仅使用内存
    """
    global _MEMORY_CACHE
    
    if 'global_task_state' not in st.session_state:
        # 优先从内存缓存加载
        if _MEMORY_CACHE is not None:
            st.session_state.global_task_state = _MEMORY_CACHE
            return
        else:
            # 如果内存缓存为空，创建默认状态
            create_default_state()
    
    # 兼容旧的会话状态
    sync_session_state()

def create_default_state():
    """创建默认的全局状态结构"""
    global _MEMORY_CACHE
    current_time = datetime.now().isoformat()
    st.session_state.global_task_state = {
        "version": "1.0",
        "last_updated": current_time,
        "task_files": {},
        "tasks": {},  # 保留tasks键但只存储基本信息
        "select": {},  # 新增select键，用于存储所有任务的选中状态
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
    # 更新内存缓存
    _MEMORY_CACHE = st.session_state.global_task_state.copy()

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
    
    if "select" not in state:
        state["select"] = {}
    
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
    
    # 从新的select键获取选中状态
    for task_name, is_selected in st.session_state.global_task_state.get("select", {}).items():
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

# 更新内存缓存
def update_memory_cache():
    """更新内存缓存"""
    global _MEMORY_CACHE
    if 'global_task_state' in st.session_state:
        _MEMORY_CACHE = st.session_state.global_task_state.copy()

# 更新全局状态
def update_global_state(state_dict, save_to_file=False):
    """
    直接更新全局状态
    
    参数:
        state_dict: 新的状态字典
        save_to_file: 此参数已废弃，保留参数签名以兼容旧代码
    """
    global _MEMORY_CACHE
    init_global_state()
    st.session_state.global_task_state = state_dict
    
    # 更新时间戳
    st.session_state.global_task_state["last_updated"] = datetime.now().isoformat()
    
    # 同步会话状态兼容层
    sync_session_state()
    
    # 更新内存缓存
    update_memory_cache()

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
            },
            "task_state": {}  # 添加task_state字段，用于存储任务状态
        }
    else:
        global_state["task_files"][file_path]["last_loaded"] = current_time
        if meta:
            global_state["task_files"][file_path]["meta"].update(meta)
        # 确保task_state字段存在
        if "task_state" not in global_state["task_files"][file_path]:
            global_state["task_files"][file_path]["task_state"] = {}
    
    update_global_state(global_state)  # 更新内存状态

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
    
    # 更新内存缓存
    update_memory_cache()

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
    
    # 确保task_files和source_file存在
    if "task_files" not in global_state:
        global_state["task_files"] = {}
    
    if source_file not in global_state["task_files"]:
        register_task_file(source_file)
    
    # 确保task_state字段存在
    if "task_state" not in global_state["task_files"][source_file]:
        global_state["task_files"][source_file]["task_state"] = {}
    
    # 保存任务基本信息到tasks（不包含选中状态和运行时数据）
    if "tasks" not in global_state:
        global_state["tasks"] = {}
    
    global_state["tasks"][task_name] = {
        "source_file": source_file,
        "data": task_data
    }
    
    # 获取现有的选中状态和运行时数据（如果有）
    selected = False
    last_selected = None
    task_runtime = runtime_data or {
        "last_run": None,
        "run_count": 0,
        "last_status": None,
        "custom_flags": {}
    }
    
    # 如果任务已存在于task_state中，保留选中状态和运行时数据
    if task_name in global_state["task_files"][source_file]["task_state"]:
        task_state = global_state["task_files"][source_file]["task_state"][task_name]
        selected = task_state.get("selected", False)
        last_selected = task_state.get("last_selected")
        if "runtime" in task_state:
            # 只使用提供的runtime_data覆盖，否则保留原有数据
            if runtime_data is None:
                task_runtime = task_state["runtime"]
    
    # 更新task_state
    global_state["task_files"][source_file]["task_state"][task_name] = {
        "selected": selected,
        "last_selected": last_selected,
        "runtime": task_runtime
    }
    
    # 同步选中状态到select键
    if "select" not in global_state:
        global_state["select"] = {}
    global_state["select"][task_name] = selected
    
    update_global_state(global_state)  # 更新内存状态

def update_task_selection(task_name, is_selected, rerun=True):
    """
    更新任务选中状态
    
    参数:
        task_name: 任务名称
        is_selected: 是否选中
        rerun: 是否执行rerun刷新页面
    """
    global_state = get_global_state()
    
    # 查找任务所属的文件
    source_file = None
    if "tasks" in global_state and task_name in global_state["tasks"]:
        source_file = global_state["tasks"][task_name].get("source_file")
    
    if source_file and source_file in global_state["task_files"]:
        # 确保task_state结构存在
        if "task_state" not in global_state["task_files"][source_file]:
            global_state["task_files"][source_file]["task_state"] = {}
        
        # 确保任务在task_state中存在
        if task_name not in global_state["task_files"][source_file]["task_state"]:
            global_state["task_files"][source_file]["task_state"][task_name] = {
                "selected": False,
                "runtime": {
                    "last_run": None,
                    "run_count": 0,
                    "last_status": None,
                    "custom_flags": {}
                }
            }
        
        # 更新选中状态
        global_state["task_files"][source_file]["task_state"][task_name]["selected"] = is_selected
        
        # 如果被选中，记录选中时间
        if is_selected:
            global_state["task_files"][source_file]["task_state"][task_name]["last_selected"] = datetime.now().isoformat()
        
        # 同步选中状态到select键
        if "select" not in global_state:
            global_state["select"] = {}
        global_state["select"][task_name] = is_selected
        
        # 更新全局状态
        update_global_state(global_state)
        
        # 同步会话状态
        sync_session_state()
        
        # 根据需要重新运行应用
        if rerun:
            # 更新内存缓存
            update_memory_cache()
            st.rerun()

def toggle_task_selection(task_name, rerun=True):
    """
    切换任务的选中状态
    
    参数:
        task_name: 任务名称
        rerun: 是否执行rerun刷新页面
    """
    # 获取当前选中状态
    current_state = get_task_selection_state(task_name)
    
    # 更新为相反状态
    update_task_selection(task_name, not current_state, rerun)

def get_task_selection_state(task_name, task_file=None):
    """
    获取任务的选择状态
    
    参数:
        task_name: 任务名称
        task_file: 任务文件路径（如果为None，则搜索所有任务文件）
    
    返回:
        bool: 任务是否被选中
    """
    init_global_state()
    
    # 兼容旧的选择状态(方法1: 直接从selected字典获取)
    if 'selected' in st.session_state and task_name in st.session_state.selected:
        return st.session_state.selected[task_name]
    
    # 方法2: 从选中任务列表获取
    if 'selected_tasks' in st.session_state and task_name in st.session_state.selected_tasks:
        return True
    
    # 方法3: 从全局状态获取
    global_state = st.session_state.global_task_state
    
    # 优先从select键获取选中状态
    if "select" in global_state and task_name in global_state["select"]:
        return global_state["select"][task_name]
    
    # 如果select键中没有，则从task_state中获取
    if task_file and task_file in global_state.get("task_files", {}):
        file_state = global_state["task_files"][task_file]
        if "task_state" in file_state and task_name in file_state["task_state"]:
            return file_state["task_state"][task_name].get("selected", False)
    else:
        # 遍历所有任务文件查找任务状态
        for file_path, file_info in global_state.get("task_files", {}).items():
            if "task_state" in file_info and task_name in file_info["task_state"]:
                return file_info["task_state"][task_name].get("selected", False)
    
    # 如果找不到任务，默认为未选中
    return False

def clear_all_selections(rerun=True):
    """
    清除所有选中状态
    
    参数:
        rerun: 是否执行rerun刷新页面
    """
    global_state = get_global_state()
    
    # 遍历所有任务文件和任务状态
    for file_path in global_state.get("task_files", {}):
        if "task_state" in global_state["task_files"][file_path]:
            for task_name in global_state["task_files"][file_path]["task_state"]:
                # 设置选中状态为False
                global_state["task_files"][file_path]["task_state"][task_name]["selected"] = False
    
    # 清空select键
    global_state["select"] = {}
    
    # 更新全局状态
    update_global_state(global_state)
    
    # 根据需要重新运行应用
    if rerun:
        # 更新内存缓存
        update_memory_cache()
        st.rerun()

def update_task_runtime(task_name, runtime_data):
    """
    更新任务运行时数据
    
    参数:
        task_name: 任务名称
        runtime_data: 运行时数据字典
    """
    global_state = get_global_state()
    
    # 查找任务所属的文件
    source_file = None
    if "tasks" in global_state and task_name in global_state["tasks"]:
        source_file = global_state["tasks"][task_name].get("source_file")
    
    if source_file and source_file in global_state["task_files"]:
        # 确保task_state结构存在
        if "task_state" not in global_state["task_files"][source_file]:
            global_state["task_files"][source_file]["task_state"] = {}
        
        # 确保任务在task_state中存在
        if task_name not in global_state["task_files"][source_file]["task_state"]:
            global_state["task_files"][source_file]["task_state"][task_name] = {
                "selected": False,
                "runtime": {
                    "last_run": None,
                    "run_count": 0,
                    "last_status": None,
                    "custom_flags": {}
                }
            }
        
        # 确保runtime字段存在
        if "runtime" not in global_state["task_files"][source_file]["task_state"][task_name]:
            global_state["task_files"][source_file]["task_state"][task_name]["runtime"] = {
                "last_run": None,
                "run_count": 0,
                "last_status": None,
                "custom_flags": {}
            }
        
        # 更新运行时数据
        global_state["task_files"][source_file]["task_state"][task_name]["runtime"].update(runtime_data)
        
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
    
    # 查找任务所属的文件
    source_file = None
    if "tasks" in global_state and task_name in global_state["tasks"]:
        source_file = global_state["tasks"][task_name].get("source_file")
    
    if source_file and source_file in global_state["task_files"]:
        # 确保task_state结构存在
        if "task_state" not in global_state["task_files"][source_file]:
            global_state["task_files"][source_file]["task_state"] = {}
        
        # 确保任务在task_state中存在
        if task_name not in global_state["task_files"][source_file]["task_state"]:
            global_state["task_files"][source_file]["task_state"][task_name] = {
                "selected": False,
                "runtime": {
                    "last_run": None,
                    "run_count": 0,
                    "last_status": None,
                    "custom_flags": {}
                }
            }
        
        # 确保runtime字段存在
        if "runtime" not in global_state["task_files"][source_file]["task_state"][task_name]:
            global_state["task_files"][source_file]["task_state"][task_name]["runtime"] = {
                "last_run": None,
                "run_count": 0,
                "last_status": None,
                "custom_flags": {}
            }
        
        # 更新运行时数据
        runtime = global_state["task_files"][source_file]["task_state"][task_name]["runtime"]
        runtime["last_run"] = datetime.now().isoformat()
        runtime["run_count"] = runtime.get("run_count", 0) + 1
        runtime["last_status"] = status
        
        update_global_state(global_state)

def get_task_runtime(task_name):
    """
    获取任务运行时数据
    
    参数:
        task_name: 任务名称
    返回:
        dict: 任务运行时数据
    """
    global_state = get_global_state()
    
    # 查找任务所属的文件
    source_file = None
    if "tasks" in global_state and task_name in global_state["tasks"]:
        source_file = global_state["tasks"][task_name].get("source_file")
    
    if source_file and source_file in global_state["task_files"]:
        # 获取运行时数据
        if "task_state" in global_state["task_files"][source_file] and \
           task_name in global_state["task_files"][source_file]["task_state"] and \
           "runtime" in global_state["task_files"][source_file]["task_state"][task_name]:
            return global_state["task_files"][source_file]["task_state"][task_name]["runtime"]
    
    # 返回默认运行时数据
    return {
        "last_run": None,
        "run_count": 0,
        "last_status": None,
        "custom_flags": {}
    }

# 导出全局状态为字典 - 提供接口以备需要
def export_state_as_dict():
    """导出全局状态为字典"""
    return get_global_state().copy()

# 导入字典作为全局状态 - 提供接口以备需要
def import_state_from_dict(state_dict, rerun=True):
    """从字典导入全局状态"""
    try:
        update_global_state(state_dict)
        if rerun:
            st.rerun()
        return True
    except Exception as e:
        print(f"导入状态失败: {str(e)}")
        return False

# 强制保存当前状态到内存
def force_save_state():
    """强制保存当前状态到内存"""
    init_global_state()
    
    # 同步会话状态兼容层
    sync_session_state()
    
    # 更新内存缓存
    update_memory_cache()
    return True

# 兼容旧方法 - 为了保持接口一致而保留，但改为内存操作
def export_yaml_state():
    """导出全局状态 (兼容旧接口)"""
    return export_state_as_dict()

def export_global_state_yaml():
    """导出全局状态为YAML字符串"""
    try:
        import yaml
        state_dict = get_global_state()
        # 使用dump而不是dumps，并设置正确的格式化选项
        yaml_str = yaml.dump(
            state_dict,
            default_flow_style=False,  # 使用块样式而不是流样式
            sort_keys=False,  # 保持键的顺序
            allow_unicode=True,  # 允许Unicode字符
            width=80,  # 设置行宽
            indent=2,  # 设置缩进
            line_break='\n'  # 使用换行符
        )
        return yaml_str
    except Exception as e:
        print(f"导出状态失败: {str(e)}")
        return ""

def import_global_state_yaml(yaml_str, rerun=True):
    """从YAML导入全局状态 (兼容旧接口)"""
    # 由于现在不使用yaml，这个函数简化为接受一个字典并导入
    try:
        if isinstance(yaml_str, dict):
            state_dict = yaml_str
        else:
            # 为兼容性保留，但不鼓励使用
            import yaml
            state_dict = yaml.safe_load(yaml_str)
        
        update_global_state(state_dict)
        if rerun:
            st.rerun()
        return True
    except Exception as e:
        print(f"导入状态失败: {str(e)}")
        return False

def save_global_state(force=False):
    """仅更新内存缓存 (兼容旧接口)"""
    update_memory_cache()
    return True

# 获取选中的任务列表
def get_selected_tasks():
    """获取选中的任务列表"""
    global_state = get_global_state()
    selected_tasks = []
    
    # 从新的select键获取选中状态
    for task_name, is_selected in global_state.get("select", {}).items():
        if is_selected:
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
