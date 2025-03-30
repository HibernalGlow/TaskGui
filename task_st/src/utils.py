import pyperclip
import streamlit as st
import os
import glob
import subprocess

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
    """将文本复制到剪贴板"""
    pyperclip.copy(text)

# 生成task命令文本
def get_task_command(task_name, taskfile_path=None):
    """生成task命令字符串"""
    if taskfile_path and os.path.exists(taskfile_path):
        return f'task --taskfile "{taskfile_path}" {task_name}'
    else:
        return f'task {task_name}'

# 查找Taskfile文件
def find_taskfiles(root_dir):
    """在指定目录递归查找Taskfile.yml文件"""
    if os.path.exists(os.path.dirname(root_dir)):
        return glob.glob(f"{root_dir}/**/*Taskfile.yml", recursive=True)
    else:
        return glob.glob(f"D:/**/*Taskfile.yml", recursive=True)

# 打开文件
def open_file(file_path):
    """使用默认程序打开文件"""
    try:
        if os.path.exists(file_path):
            subprocess.Popen(['start', '', file_path], shell=True)
            return True
        return False
    except Exception as e:
        st.error(f"无法打开文件: {str(e)}")
        return False

# 获取目录下的文件
def get_directory_files(directory, max_files=5):
    """获取目录下的文件列表"""
    if not directory or not os.path.exists(directory) or not os.path.isdir(directory):
        return []
    
    try:
        # 只查找特定类型的文件
        extensions = ['.py', '.js', '.html', '.css', '.txt', '.md', '.json', '.yml', '.yaml', '.bat', '.sh', '.cmd', '.ps1']
        files = []
        for ext in extensions:
            files.extend([f for f in os.listdir(directory) if f.endswith(ext)])
        return files[:max_files]  # 限制文件数量
    except:
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