import pyperclip
import streamlit as st
import os
import glob
import subprocess
import platform

# 常量
DEFAULT_TASKFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Taskfile.yml')

# 初始化会话状态
def init_session_state():
    """初始化Streamlit会话状态变量"""
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    if 'last_taskfile_path' not in st.session_state:
        st.session_state.last_taskfile_path = None
    if 'taskfile_history' not in st.session_state:
        st.session_state.taskfile_history = []
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
    if 'parallel_mode' not in st.session_state:
        st.session_state.parallel_mode = False
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = '名称'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = '升序'

# 复制命令到剪贴板
def copy_to_clipboard(text):
    """
    将文本复制到剪贴板
    
    参数:
        text: 要复制的文本
        
    返回:
        布尔值，表示是否成功复制
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"复制到剪贴板时出错: {str(e)}")
        return False

# 生成task命令文本
def get_task_command(task_name, taskfile_path=None):
    """
    获取任务的命令
    
    参数:
        task_name: 任务名称
        taskfile_path: 可选的Taskfile路径
        
    返回:
        命令字符串
    """
    if taskfile_path and os.path.exists(taskfile_path):
        return f'task --taskfile "{taskfile_path}" {task_name}'
    else:
        return f'task {task_name}'

# 查找Taskfile文件
def find_taskfiles(start_dir=None):
    """
    在指定目录及其父目录中寻找Taskfile
    
    参数:
        start_dir: 起始目录
        
    返回:
        Taskfile路径列表
    """
    if not start_dir:
        start_dir = os.getcwd()
    
    # 支持的Taskfile名称
    taskfile_patterns = [
        'Taskfile.y*ml',
        'taskfile.y*ml',
        '.taskfile.y*ml',
        'task.y*ml',
        '.task.y*ml'
    ]
    
    taskfiles = []
    
    # 在当前目录及子目录中查找
    for pattern in taskfile_patterns:
        search_pattern = os.path.join(start_dir, '**', pattern)
        taskfiles.extend(glob.glob(search_pattern, recursive=True))
    
    # 添加当前目录的匹配
    for pattern in taskfile_patterns:
        search_pattern = os.path.join(start_dir, pattern)
        taskfiles.extend(glob.glob(search_pattern))
    
    return sorted(list(set(taskfiles)))

# 获取最近的Taskfile
def get_nearest_taskfile(start_dir=None):
    """
    获取最近的Taskfile
    
    参数:
        start_dir: 起始目录
        
    返回:
        Taskfile的完整路径，如果没有找到则返回None
    """
    if not start_dir:
        start_dir = os.getcwd()
    
    # 支持的Taskfile名称模式
    taskfile_names = [
        'Taskfile.yml',
        'Taskfile.yaml',
        'taskfile.yml',
        'taskfile.yaml',
        '.taskfile.yml',
        '.taskfile.yaml',
        'task.yml',
        'task.yaml',
        '.task.yml',
        '.task.yaml'
    ]
    
    # 首先检查当前目录
    for name in taskfile_names:
        file_path = os.path.join(start_dir, name)
        if os.path.exists(file_path):
            return file_path
    
    # 如果当前目录没有，查找父目录
    current_dir = start_dir
    max_levels = 5  # 最多向上查找的层数
    
    for _ in range(max_levels):
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # 已到达根目录
            break
        
        for name in taskfile_names:
            file_path = os.path.join(parent_dir, name)
            if os.path.exists(file_path):
                return file_path
        
        current_dir = parent_dir
    
    # 如果还没找到，则返回已找到的第一个Taskfile
    taskfiles = find_taskfiles(start_dir)
    return taskfiles[0] if taskfiles else None

# 打开文件
def open_file(file_path):
    """
    使用系统默认程序打开文件
    
    参数:
        file_path: 文件路径
        
    返回:
        布尔值，表示是否成功打开
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f"打开文件时出错: {str(e)}")
        return False

# 获取目录下的文件
def get_directory_files(directory):
    """
    获取目录中的所有文件
    
    参数:
        directory: 目录路径
        
    返回:
        文件名列表
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return []
    
    try:
        # 只返回文件，不包括目录
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        print(f"获取目录文件时出错: {str(e)}")
        return []

# 定义CSS样式
def setup_css():
    """设置应用的CSS样式"""
    st.markdown("""
    <style>
    .copy-btn {
        display: inline-block;
        padding: 2px 8px;
        background-color: #f0f2f6;
        color: #31333F;
        border: 1px solid #ddd;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        margin-left: 10px;
    }
    .copy-btn:hover {
        background-color: #ddd;
    }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 12px;
        margin-right: 5px;
        font-size: 12px;
    }
    .run-btn {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True) 