import streamlit as st
import json
import yaml
import os
import gc
import psutil
import time
from datetime import datetime
from pathlib import Path

# 全局内存缓存
_MEMORY_CACHE = None  # 内存缓存
_MEMORY_CACHE_TIMESTAMP = None  # 内存缓存时间戳
_MEMORY_CACHE_SIZE = 0  # 内存缓存大小（字节）
_MEMORY_CACHE_MAX_SIZE = 50 * 1024 * 1024  # 最大缓存大小（50MB）
_MEMORY_CACHE_MAX_AGE = 3600  # 最大缓存年龄（秒）
_LAST_GC_TIME = 0  # 上次垃圾回收时间
_GC_INTERVAL = 300  # 垃圾回收间隔（秒）

# 本地配置文件路径
# LOCAL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".glowtoolbox")
# LOCAL_CONFIG_FILE = os.path.join(LOCAL_CONFIG_DIR, "local_config.yaml")

# 修改为脚本目录
LOCAL_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOCAL_CONFIG_FILE = os.path.join(LOCAL_CONFIG_DIR, "config.yaml")

# 确保配置目录存在
def ensure_config_dir():
    """确保配置目录存在"""
    if not os.path.exists(LOCAL_CONFIG_DIR):
        try:
            os.makedirs(LOCAL_CONFIG_DIR)
        except Exception as e:
            print(f"创建配置目录失败: {str(e)}")
            return False
    return True

# 加载本地配置
def load_local_config():
    """从本地文件加载配置"""
    if not os.path.exists(LOCAL_CONFIG_FILE):
        return {}
    
    try:
        with open(LOCAL_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return {}

# 保存本地配置
def save_local_config(config):
    """保存配置到本地文件"""
    if not ensure_config_dir():
        return False
    
    try:
        with open(LOCAL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, sort_keys=False, allow_unicode=True, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")
        return False

# 初始化全局任务状态
def init_global_state():
    """
    初始化全局任务状态 - 仅使用内存
    """
    global _MEMORY_CACHE, _MEMORY_CACHE_TIMESTAMP
    
    # 检查是否需要执行垃圾回收
    check_and_run_gc()
    
    if 'global_task_state' not in st.session_state:
        # 优先从内存缓存加载
        if _MEMORY_CACHE is not None and _MEMORY_CACHE_TIMESTAMP is not None:
            # 检查缓存是否过期
            current_time = time.time()
            if current_time - _MEMORY_CACHE_TIMESTAMP < _MEMORY_CACHE_MAX_AGE:
                st.session_state.global_task_state = _MEMORY_CACHE
                return
            else:
                # 缓存过期，清除缓存
                clear_memory_cache()
        
        # 如果内存缓存为空或已过期，创建默认状态
        create_default_state()
    
    # 添加本地配置信息
    load_local_data()
    
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
                "aggrid_group_by": None,
                "card_view": {  # 添加卡片视图设置
                    "show_description": True,
                    "show_tags": True,
                    "show_directory": True,
                    "show_command": True,
                    "use_sidebar_editor": True
                }
            }
        },
        "local": {  # 添加local键，用于存储本地配置
            "favorite_tags": []
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
    
    # 确保local键存在
    if "local" not in state:
        state["local"] = {
            "favorite_tags": []
        }
    elif "favorite_tags" not in state["local"]:
        state["local"]["favorite_tags"] = []

# 加载本地数据并同步到全局状态
def load_local_data():
    """从本地配置加载数据并同步到全局状态"""
    global_state = st.session_state.global_task_state
    
    # 确保结构完整
    ensure_state_structure(global_state)
    
    # 加载本地配置
    local_config = load_local_config()
    
    # 更新常用标签
    if "favorite_tags" in local_config:
        global_state["local"]["favorite_tags"] = local_config["favorite_tags"]
    
    # 确保会话状态中有常用标签
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = global_state["local"]["favorite_tags"].copy()

# 保存常用标签到本地
def save_favorite_tags(tags):
    """保存常用标签到本地配置"""
    global_state = get_global_state()
    
    # 确保结构完整
    ensure_state_structure(global_state)
    
    # 更新全局状态中的常用标签
    global_state["local"]["favorite_tags"] = tags
    
    # 更新会话状态
    st.session_state.favorite_tags = tags.copy()
    
    # 更新全局状态
    update_global_state(global_state)
    
    # 保存到本地文件
    local_config = load_local_config()
    local_config["favorite_tags"] = tags
    save_local_config(local_config)

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
    
    # 同步常用标签
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
        
    # 从全局状态更新常用标签
    if "local" in st.session_state.global_task_state and "favorite_tags" in st.session_state.global_task_state["local"]:
        st.session_state.favorite_tags = st.session_state.global_task_state["local"]["favorite_tags"].copy()

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
    global _MEMORY_CACHE, _MEMORY_CACHE_TIMESTAMP, _MEMORY_CACHE_SIZE
    
    if 'global_task_state' in st.session_state:
        # 创建深拷贝以避免引用问题
        _MEMORY_CACHE = json.loads(json.dumps(st.session_state.global_task_state))
        _MEMORY_CACHE_TIMESTAMP = time.time()
        
        # 估算内存缓存大小
        try:
            _MEMORY_CACHE_SIZE = len(json.dumps(_MEMORY_CACHE).encode('utf-8'))
            
            # 如果缓存大小超过限制，执行清理
            if _MEMORY_CACHE_SIZE > _MEMORY_CACHE_MAX_SIZE:
                optimize_memory_cache()
        except Exception as e:
            print(f"估算内存缓存大小时出错: {str(e)}")
            _MEMORY_CACHE_SIZE = 0

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
    """导出全局状态为YAML格式的字符串"""
    global_state = get_global_state()
    return yaml.dump(global_state, sort_keys=False, allow_unicode=True, indent=2)

def export_global_state_yaml():
    """导出全局状态为YAML格式的字符串"""
    global_state = get_global_state()
    return yaml.dump(global_state, sort_keys=False, allow_unicode=True, indent=2)

def import_global_state_yaml(yaml_str, rerun=True):
    """从YAML导入全局状态"""
    try:
        if isinstance(yaml_str, dict):
            state_dict = yaml_str
        else:
            state_dict = yaml.safe_load(yaml_str)
        
        update_global_state(state_dict)
        if rerun:
            st.rerun()
        return True
    except Exception as e:
        print(f"导入状态失败: {str(e)}")
        return False

def save_global_state(force=False):
    """更新内存缓存并执行内存优化 (兼容旧接口)"""
    update_memory_cache()
    
    # 如果强制保存或缓存大小超过限制，执行内存优化
    if force or _MEMORY_CACHE_SIZE > _MEMORY_CACHE_MAX_SIZE:
        optimize_memory_cache()
    
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

# 导出全局状态为字典 - 提供接口以备需要
def export_global_state_json():
    """
    导出全局状态为JSON字符串
    """
    global_state = get_global_state()
    return json.dumps(global_state, indent=2, ensure_ascii=False)

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

# 添加辅助函数用于验证YAML格式
def validate_yaml(yaml_str):
    """
    验证YAML字符串的格式是否正确
    
    参数:
        yaml_str: 要验证的YAML字符串
    
    返回:
        tuple: (是否有效, 错误信息)
    """
    try:
        yaml.safe_load(yaml_str)
        return True, None
    except Exception as e:
        return False, str(e)

# 添加辅助函数用于在UI中显示YAML
def display_yaml_in_ui(yaml_str):
    """
    在UI中显示YAML字符串为格式化的代码块
    
    参数:
        yaml_str: YAML格式的字符串
    """
    # 构建markdown代码块
    markdown_yaml = f"```yaml\n{yaml_str}\n```"
    
    # 添加到UI
    st.markdown(markdown_yaml)

def load_background_settings():
    """从本地配置加载背景设置，确保所有必要的键都存在"""
    try:
        local_config = load_local_config()
        if "background_settings" not in local_config:
            return {
                'enabled': False,
                'sidebar_enabled': False,
                'header_banner_enabled': False, 
                'sidebar_banner_enabled': False,  # 侧边栏横幅开关
                'image_path': '',
                'sidebar_image_path': '',
                'header_banner_path': '',
                'sidebar_banner_path': '',  # 侧边栏横幅路径
                'opacity': 0.5,
                'blur': 0
            }
        
        # 获取基本设置
        settings = local_config["background_settings"]
        
        # 确保所有必要的字段存在
        default_settings = {
            'enabled': False,
            'sidebar_enabled': False,
            'header_banner_enabled': False,
            'sidebar_banner_enabled': False,  # 侧边栏横幅开关
            'image_path': '',
            'sidebar_image_path': '',
            'header_banner_path': '',
            'sidebar_banner_path': '',  # 侧边栏横幅路径
            'opacity': 0.5,
            'blur': 0
        }
        
        # 使用默认值填充缺失的键
        for key, default_value in default_settings.items():
            if key not in settings:
                settings[key] = default_value
        
        # 删除所有base64编码的图片数据
        if 'image_base64' in settings:
            del settings['image_base64']
        if 'sidebar_image_base64' in settings:
            del settings['sidebar_image_base64']
        if 'header_banner_base64' in settings:
            del settings['header_banner_base64']
        if 'sidebar_banner_base64' in settings:
            del settings['sidebar_banner_base64']
        
        # 验证所有路径，确保它们是有效的文件
        for path_key in ['image_path', 'sidebar_image_path', 'header_banner_path', 'sidebar_banner_path']:
            if settings[path_key] and not os.path.isfile(settings[path_key]):
                # 如果路径无效，重置相关设置
                related_enabled_key = 'enabled' if path_key == 'image_path' else \
                                     'sidebar_enabled' if path_key == 'sidebar_image_path' else \
                                     'header_banner_enabled' if path_key == 'header_banner_path' else \
                                     'sidebar_banner_enabled'
                settings[path_key] = ''
                settings[related_enabled_key] = False
        
        return settings
    except Exception as e:
        print(f"加载背景设置时出错: {str(e)}")
        # 出现任何错误时返回默认设置
        return {
            'enabled': False,
            'sidebar_enabled': False,
            'header_banner_enabled': False, 
            'sidebar_banner_enabled': False,  # 侧边栏横幅开关
            'image_path': '',
            'sidebar_image_path': '',
            'header_banner_path': '',
            'sidebar_banner_path': '',  # 侧边栏横幅路径
            'opacity': 0.5,
            'blur': 0
        }

def save_background_settings(settings):
    """保存背景设置到本地配置，增加错误处理"""
    try:
        # 确保设置中包含所有必要的键
        default_settings = {
            'enabled': False,
            'sidebar_enabled': False,
            'header_banner_enabled': False,
            'sidebar_banner_enabled': False,
            'image_path': '',
            'sidebar_image_path': '',
            'header_banner_path': '',
            'sidebar_banner_path': '',
            'opacity': 0.5,
            'blur': 0
        }
        
        # 使用默认值填充缺失的键
        for key, default_value in default_settings.items():
            if key not in settings:
                settings[key] = default_value
        
        # 删除所有base64编码的图片数据，不保存到配置文件
        settings_copy = settings.copy()
        if 'image_base64' in settings_copy:
            del settings_copy['image_base64']
        if 'sidebar_image_base64' in settings_copy:
            del settings_copy['sidebar_image_base64']
        if 'header_banner_base64' in settings_copy:
            del settings_copy['header_banner_base64']
        if 'sidebar_banner_base64' in settings_copy:
            del settings_copy['sidebar_banner_base64']
        if 'image_format' in settings_copy:
            del settings_copy['image_format']
        if 'sidebar_image_format' in settings_copy:
            del settings_copy['sidebar_image_format']
        if 'header_banner_format' in settings_copy:
            del settings_copy['header_banner_format']
        if 'sidebar_banner_format' in settings_copy:
            del settings_copy['sidebar_banner_format']
        
        # 验证所有路径
        for path_key in ['image_path', 'sidebar_image_path', 'header_banner_path', 'sidebar_banner_path']:
            if settings_copy[path_key] and not os.path.isfile(settings_copy[path_key]):
                # 如果路径无效，记录警告但不阻止保存
                print(f"警告: 保存的路径无效 {path_key}={settings_copy[path_key]}")
        
        # 加载现有配置并更新
        local_config = load_local_config()
        local_config["background_settings"] = settings_copy
        return save_local_config(local_config)
    except Exception as e:
        print(f"保存背景设置时出错: {str(e)}")
        return False

def get_card_view_settings():
    """获取卡片视图显示设置
    
    返回:
        dict: 卡片视图设置字典
    """
    # 尝试从本地配置加载设置
    local_config = load_local_config()
    local_card_settings = None
    
    # 如果本地配置中有卡片视图设置，则使用它
    if ("user_preferences" in local_config and 
            "ui_settings" in local_config["user_preferences"] and 
            "card_view" in local_config["user_preferences"]["ui_settings"]):
        local_card_settings = local_config["user_preferences"]["ui_settings"]["card_view"]
    
    # 如果本地配置有效，直接返回本地设置
    if local_card_settings:
        # 确保use_sidebar_editor选项存在
        if "use_sidebar_editor" not in local_card_settings:
            local_card_settings["use_sidebar_editor"] = True
            
        # 同时更新全局状态以保持一致
        global_state = get_global_state()
        if "user_preferences" not in global_state:
            global_state["user_preferences"] = {}
        if "ui_settings" not in global_state["user_preferences"]:
            global_state["user_preferences"]["ui_settings"] = {}
        
        global_state["user_preferences"]["ui_settings"]["card_view"] = local_card_settings
        update_global_state(global_state)
        
        return local_card_settings
    
    # 如果本地配置无效，从全局状态获取
    global_state = get_global_state()
    
    # 确保设置存在
    if "user_preferences" not in global_state:
        global_state["user_preferences"] = {}
    if "ui_settings" not in global_state["user_preferences"]:
        global_state["user_preferences"]["ui_settings"] = {}
    if "card_view" not in global_state["user_preferences"]["ui_settings"]:
        global_state["user_preferences"]["ui_settings"]["card_view"] = {
            "show_description": True,
            "show_tags": True,
            "show_directory": True,
            "show_command": True,
            "use_sidebar_editor": True
        }
        
        # 更新全局状态
        update_global_state(global_state)
        
        # 同时保存到本地配置
        local_config = load_local_config()
        if "user_preferences" not in local_config:
            local_config["user_preferences"] = {}
        if "ui_settings" not in local_config["user_preferences"]:
            local_config["user_preferences"]["ui_settings"] = {}
        
        local_config["user_preferences"]["ui_settings"]["card_view"] = global_state["user_preferences"]["ui_settings"]["card_view"]
        save_local_config(local_config)
    else:
        # 确保use_sidebar_editor选项存在
        if "use_sidebar_editor" not in global_state["user_preferences"]["ui_settings"]["card_view"]:
            global_state["user_preferences"]["ui_settings"]["card_view"]["use_sidebar_editor"] = True
            update_global_state(global_state)
    
    return global_state["user_preferences"]["ui_settings"]["card_view"]

def update_card_view_settings(settings):
    """更新卡片视图显示设置
    
    参数:
        settings (dict): 新的卡片视图设置
    """
    global_state = get_global_state()
    
    # 确保设置路径存在
    if "user_preferences" not in global_state:
        global_state["user_preferences"] = {}
    if "ui_settings" not in global_state["user_preferences"]:
        global_state["user_preferences"]["ui_settings"] = {}
    
    # 更新设置
    global_state["user_preferences"]["ui_settings"]["card_view"] = settings
    
    # 保存更新后的全局状态
    update_global_state(global_state)
    
    # 同时保存到本地配置文件
    local_config = load_local_config()
    if "user_preferences" not in local_config:
        local_config["user_preferences"] = {}
    if "ui_settings" not in local_config["user_preferences"]:
        local_config["user_preferences"]["ui_settings"] = {}
    
    # 更新本地配置
    local_config["user_preferences"]["ui_settings"]["card_view"] = settings
    
    # 保存到本地文件
    save_local_config(local_config)

# 新增内存管理函数

def check_and_run_gc():
    """检查是否需要执行垃圾回收"""
    global _LAST_GC_TIME
    
    current_time = time.time()
    if current_time - _LAST_GC_TIME > _GC_INTERVAL:
        run_gc()
        _LAST_GC_TIME = current_time

def run_gc():
    """执行垃圾回收"""
    try:
        # 强制垃圾回收
        gc.collect()
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        
        # 获取内存使用情况
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # 如果内存使用率超过80%，执行更激进的清理
        if memory_percent > 80:
            # 清理内存缓存
            clear_memory_cache()
            
            # 再次强制垃圾回收
            gc.collect(2)  # 使用更激进的垃圾回收
            
            # 记录内存使用情况
            print(f"内存使用率过高 ({memory_percent:.2f}%)，已执行内存清理")
            print(f"当前内存使用: {memory_info.rss / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"执行垃圾回收时出错: {str(e)}")

def clear_memory_cache():
    """清除内存缓存"""
    global _MEMORY_CACHE, _MEMORY_CACHE_TIMESTAMP, _MEMORY_CACHE_SIZE
    
    _MEMORY_CACHE = None
    _MEMORY_CACHE_TIMESTAMP = None
    _MEMORY_CACHE_SIZE = 0
    
    # 强制垃圾回收
    gc.collect()

def optimize_memory_cache():
    """优化内存缓存，减少内存使用"""
    global _MEMORY_CACHE, _MEMORY_CACHE_SIZE
    
    if _MEMORY_CACHE is None:
        return
    
    try:
        # 创建优化后的缓存
        optimized_cache = {
            "version": _MEMORY_CACHE.get("version", "1.0"),
            "last_updated": _MEMORY_CACHE.get("last_updated", datetime.now().isoformat()),
            "task_files": {},
            "tasks": {},
            "select": _MEMORY_CACHE.get("select", {}),
            "user_preferences": _MEMORY_CACHE.get("user_preferences", {})
        }
        
        # 只保留必要的任务文件信息
        for file_path, file_info in _MEMORY_CACHE.get("task_files", {}).items():
            optimized_cache["task_files"][file_path] = {
                "path": file_info.get("path", ""),
                "last_modified": file_info.get("last_modified", ""),
                "task_count": file_info.get("task_count", 0)
            }
        
        # 只保留必要的任务信息
        for task_name, task_info in _MEMORY_CACHE.get("tasks", {}).items():
            optimized_cache["tasks"][task_name] = {
                "name": task_info.get("name", task_name),
                "source_file": task_info.get("source_file", ""),
                "last_run": task_info.get("last_run", ""),
                "run_count": task_info.get("run_count", 0)
            }
        
        # 更新缓存
        _MEMORY_CACHE = optimized_cache
        
        # 重新计算缓存大小
        _MEMORY_CACHE_SIZE = len(json.dumps(_MEMORY_CACHE).encode('utf-8'))
        
        print(f"内存缓存已优化，当前大小: {_MEMORY_CACHE_SIZE / 1024:.2f} KB")
    except Exception as e:
        print(f"优化内存缓存时出错: {str(e)}")

def get_memory_usage():
    """获取当前内存使用情况"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": memory_percent,
            "cache_size": _MEMORY_CACHE_SIZE / 1024 if _MEMORY_CACHE_SIZE > 0 else 0  # KB
        }
    except Exception as e:
        print(f"获取内存使用情况时出错: {str(e)}")
        return {
            "rss": 0,
            "vms": 0,
            "percent": 0,
            "cache_size": 0
        }
