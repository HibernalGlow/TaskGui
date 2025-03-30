import pyperclip
import streamlit as st
import os
import glob
import subprocess
import re
import sys
import json
import time
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# 常量
DEFAULT_TASKFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Taskfile.yml')

# 设置页面配置
def set_page_config(title="任务管理器", icon="📋"):
    """设置Streamlit页面配置"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )

# 加载任务数据
def load_task_data(task_file_path):
    """从JSON文件加载任务数据"""
    try:
        if not os.path.exists(task_file_path):
            return None
        
        with open(task_file_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
        
        # 将任务数据转换为DataFrame
        task_list = []
        for task_name, task_info in task_data.items():
            # 确保包含所有必要字段
            task_info['name'] = task_name
            if 'tags' not in task_info:
                task_info['tags'] = []
            if 'description' not in task_info:
                task_info['description'] = ""
            if 'emoji' not in task_info:
                task_info['emoji'] = "🚀"
            if 'directory' not in task_info:
                task_info['directory'] = ""
            
            task_list.append(task_info)
        
        # 创建DataFrame
        df = pd.DataFrame(task_list)
        return df
    
    except Exception as e:
        st.error(f"加载任务文件时出错: {str(e)}")
        return None

# 应用过滤器
def apply_filters(df, selected_tags=None, search_text=None):
    """应用过滤器到任务DataFrame"""
    filtered_df = df.copy()
    
    # 应用标签过滤
    if selected_tags and len(selected_tags) > 0:
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: isinstance(x, list) and any(tag in x for tag in selected_tags)
        )]
    
    # 应用搜索文本过滤
    if search_text and search_text.strip():
        search_lower = search_text.lower()
        filtered_df = filtered_df[
            filtered_df['name'].str.lower().str.contains(search_lower, na=False) |
            filtered_df['description'].str.lower().str.contains(search_lower, na=False)
        ]
    
    return filtered_df

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
    .task-card {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ddd;
        background-color: #fff;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .task-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .task-emoji {
        font-size: 24px;
        margin-right: 10px;
    }
    .task-title {
        margin: 0;
        font-size: 18px;
    }
    .task-description {
        margin-bottom: 10px;
        color: #555;
    }
    .task-tags {
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 设置session state中的初始值
def initialize_session_state():
    """初始化各种会话状态变量"""
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'card'  # 默认视图模式
    
    if 'show_filter' not in st.session_state:
        st.session_state.show_filter = False
    
    if 'parallel_mode' not in st.session_state:
        st.session_state.parallel_mode = False
        
    if 'task_to_run' not in st.session_state:
        st.session_state.task_to_run = ''
        
    # 初始化运行状态跟踪
    if 'running_tasks' not in st.session_state:
        st.session_state.running_tasks = {}
    
    # 添加其他初始状态
    if 'last_taskfile_path' not in st.session_state:
        st.session_state.last_taskfile_path = None
    if 'taskfile_history' not in st.session_state:
        st.session_state.taskfile_history = []
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
        
def update_running_task_status(task_name, status, output=None):
    """更新任务运行状态"""
    if 'running_tasks' not in st.session_state:
        st.session_state.running_tasks = {}
    
    if status == 'running':
        st.session_state.running_tasks[task_name] = {
            'status': 'running',
            'start_time': datetime.now(),
            'output': []
        }
    elif status == 'completed':
        if task_name in st.session_state.running_tasks:
            st.session_state.running_tasks[task_name]['status'] = 'completed'
            st.session_state.running_tasks[task_name]['end_time'] = datetime.now()
            if output:
                st.session_state.running_tasks[task_name]['output'] = output
    elif status == 'failed':
        if task_name in st.session_state.running_tasks:
            st.session_state.running_tasks[task_name]['status'] = 'failed'
            st.session_state.running_tasks[task_name]['end_time'] = datetime.now()
            if output:
                st.session_state.running_tasks[task_name]['output'] = output

def get_task_status(task_name):
    """获取任务状态"""
    if 'running_tasks' in st.session_state and task_name in st.session_state.running_tasks:
        return st.session_state.running_tasks[task_name]['status']
    return None 