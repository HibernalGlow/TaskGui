import yaml
import os
import streamlit as st
import pandas as pd
from .utils import DEFAULT_TASKFILE_PATH

def load_taskfile(file_path=None):
    """
    加载Taskfile.yml文件并解析任务
    
    参数:
        file_path: Taskfile的路径，如果为空则使用默认值
        
    返回:
        tasks: 任务列表
        file_path: 实际使用的Taskfile路径
    """
    if not file_path:
        # 尝试使用上次的路径
        if st.session_state.last_taskfile_path and os.path.exists(st.session_state.last_taskfile_path):
            file_path = st.session_state.last_taskfile_path
        else:
            file_path = DEFAULT_TASKFILE_PATH
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        
        # 更新会话状态
        if file_path != st.session_state.last_taskfile_path:
            if st.session_state.last_taskfile_path and st.session_state.last_taskfile_path not in st.session_state.taskfile_history:
                st.session_state.taskfile_history.append(st.session_state.last_taskfile_path)
            st.session_state.last_taskfile_path = file_path
            # 限制历史记录数量
            if len(st.session_state.taskfile_history) > 10:
                st.session_state.taskfile_history = st.session_state.taskfile_history[-10:]
        
        tasks = []
        for task_name, task_info in data.get('tasks', {}).items():
            # 跳过分组命令
            if isinstance(task_info, dict) and task_info.get('cmds'):
                if task_name in ['comic', 'filter', 'folder'] and 'findstr' in task_info['cmds'][0]:
                    continue
                
                task = {
                    'name': task_name,
                    'description': task_info.get('desc', ''),
                    'tags': task_info.get('tags', []) if task_info.get('tags') else [],
                    'directory': task_info.get('dir', ''),
                    'commands': task_info.get('cmds', []),
                    'emoji': task_info.get('desc', '').split(' ')[0] if task_info.get('desc') else ''
                }
                tasks.append(task)
        
        return tasks, file_path
    except Exception as e:
        st.error(f"加载Taskfile失败: {str(e)}")
        return [], file_path

def prepare_dataframe(tasks):
    """
    将任务列表转换为DataFrame并进行必要的处理
    
    参数:
        tasks: 任务列表
        
    返回:
        df: 处理后的DataFrame
    """
    df = pd.DataFrame(tasks)
    
    if df.empty:
        return df
    
    # 添加选择列
    df['selected'] = False
    
    # 修正标签显示
    df['tags_str'] = df['tags'].apply(lambda x: ', '.join(x) if x else '')
    
    return df

def get_all_tags(df):
    """
    从任务DataFrame中提取所有唯一标签
    
    参数:
        df: 任务DataFrame
        
    返回:
        all_tags: 所有唯一标签的集合
    """
    all_tags = set()
    for tags in df['tags']:
        if tags:
            all_tags.update(tags)
    return all_tags

def filter_tasks(df, selected_tags=None, search_term=None):
    """
    根据标签和搜索词过滤任务
    
    参数:
        df: 任务DataFrame
        selected_tags: 选中的标签列表
        search_term: 搜索词
        
    返回:
        filtered_df: 过滤后的DataFrame
    """
    filtered_df = df.copy()
    
    if selected_tags:
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: any(tag in x for tag in selected_tags) if x else False
        )]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['description'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered_df 