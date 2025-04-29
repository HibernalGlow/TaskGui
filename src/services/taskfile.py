import os
import yaml
import json
import pandas as pd
import streamlit as st

def read_taskfile(file_path):
    """
    读取Taskfile并返回DataFrame
    
    参数:
        file_path: Taskfile路径
        
    返回:
        包含任务信息的DataFrame
    """
    if not os.path.exists(file_path):
        st.error(f"找不到Taskfile: {file_path}")
        return pd.DataFrame()
    
    try:
        # 读取YAML文件
        with open(file_path, 'r', encoding='utf-8') as f:
            taskfile_data = yaml.safe_load(f)
        
        # 提取任务
        tasks_dict = taskfile_data.get('tasks', {})
        
        # 将任务转换为DataFrame
        tasks = []
        for task_name, task_info in tasks_dict.items():
            # 基本信息
            task_data = {
                'name': task_name,
                'description': task_info.get('desc', ''),
                'directory': task_info.get('dir', ''),
                'emoji': task_info.get('emoji', ''),
                'tags': task_info.get('tags', []),
                'group': task_info.get('group', '默认'),
                'priority': task_info.get('priority', 5),
                'vars': task_info.get('vars', {}),
                'deps': task_info.get('deps', []),
                'cmds': task_info.get('cmds', [])
            }
            tasks.append(task_data)
        
        # 创建DataFrame
        tasks_df = pd.DataFrame(tasks)
        
        # 确保所有必要的列都存在
        required_columns = ['name', 'description', 'directory', 'emoji', 'tags', 'group', 'priority']
        for col in required_columns:
            if col not in tasks_df.columns:
                tasks_df[col] = ''
        
        return tasks_df
    
    except Exception as e:
        st.error(f"读取Taskfile时出错: {str(e)}")
        return pd.DataFrame()

def load_taskfile(file_path):
    """
    加载Taskfile并更新会话状态
    
    参数:
        file_path: Taskfile路径
        
    返回:
        包含任务信息的DataFrame
    """
    # 添加到历史记录
    if 'taskfile_history' not in st.session_state:
        st.session_state.taskfile_history = []
    
    # 如果是新的Taskfile，添加到历史记录
    if file_path not in st.session_state.taskfile_history:
        st.session_state.taskfile_history.append(file_path)
        # 限制历史记录长度
        if len(st.session_state.taskfile_history) > 10:
            st.session_state.taskfile_history.pop(0)
    
    # 设置当前Taskfile路径
    st.session_state.last_taskfile_path = file_path
    
    # 读取任务数据
    return read_taskfile(file_path)

def prepare_dataframe(df):
    """
    准备DataFrame以供显示
    
    参数:
        df: 原始DataFrame
        
    返回:
        处理后的DataFrame
    """
    if df.empty:
        return df
    
    # 确保所有必要的列都存在
    required_columns = ['name', 'description', 'directory', 'emoji', 'tags', 'group', 'priority']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # 处理排序
    if 'sort_by' in st.session_state and 'sort_order' in st.session_state:
        sort_by = st.session_state.sort_by
        sort_order = st.session_state.sort_order
        
        # 映射UI显示名称到DataFrame列名
        sort_column_map = {
            '名称': 'name',
            '描述': 'description',
            '目录': 'directory',
            '组': 'group',
            '优先级': 'priority'
        }
        
        if sort_by in sort_column_map:
            column = sort_column_map[sort_by]
            ascending = (sort_order == '升序')
            df = df.sort_values(by=column, ascending=ascending)
    
    return df

def filter_tasks(tasks_df):
    """
    根据过滤条件过滤任务
    
    参数:
        tasks_df: 包含所有任务的DataFrame
        
    返回:
        过滤后的DataFrame
    """
    if tasks_df.empty:
        return tasks_df
    
    filtered_df = tasks_df.copy()
    
    # 应用搜索过滤
    if 'search_task' in st.session_state and st.session_state.search_task:
        search_term = st.session_state.search_task.lower()
        # 过滤名称或描述包含搜索词的任务
        mask = filtered_df['name'].str.lower().str.contains(search_term, na=False) | \
               filtered_df['description'].str.lower().str.contains(search_term, na=False)
        filtered_df = filtered_df[mask]
    
    # 应用标签过滤
    if 'tags_filter' in st.session_state and st.session_state.tags_filter:
        tags_to_filter = st.session_state.tags_filter
        # 过滤包含所选标签的任务
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: any(tag in x for tag in tags_to_filter) if isinstance(x, list) else False
        )]
    
    return filtered_df 