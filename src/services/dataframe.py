import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    准备数据框，确保所有必要的列都存在和格式正确
    
    参数:
        df: 原始数据框
        
    返回:
        处理后的数据框
    """
    # 复制数据框，避免修改原始数据
    tasks_df = df.copy()
    
    # 确保所有必需的列都存在
    required_columns = ['name', 'description', 'cmd', 'tags']
    for col in required_columns:
        if col not in tasks_df.columns:
            tasks_df[col] = ""
    
    # 确保标签列是列表类型
    tasks_df['tags'] = tasks_df['tags'].apply(lambda x: x if isinstance(x, list) else [])
    
    # 添加文本搜索列，用于更好的搜索
    tasks_df['search_text'] = tasks_df.apply(
        lambda row: f"{row['name']} {row['description']} {' '.join(row['tags'])}", 
        axis=1
    ).str.lower()
    
    return tasks_df

def filter_tasks(df: pd.DataFrame) -> pd.DataFrame:
    """
    根据用户的筛选条件过滤任务
    
    参数:
        df: 要过滤的数据框
        
    返回:
        过滤后的数据框
    """
    # 复制数据框，避免修改原始数据
    filtered_df = df.copy()
    
    # 应用搜索过滤
    if 'search_task' in st.session_state and st.session_state.search_task:
        search_term = st.session_state.search_task.lower()
        # 过滤名称或描述包含搜索词的任务
        mask = filtered_df['search_text'].str.contains(search_term, na=False)
        filtered_df = filtered_df[mask]
    
    # 应用过滤任务名称
    if 'filtered_tasks' in st.session_state and st.session_state.filtered_tasks:
        filtered_task_names = st.session_state.filtered_tasks
        if filtered_task_names:
            filtered_df = filtered_df[filtered_df['name'].isin(filtered_task_names)]
    
    # 应用标签过滤
    if 'tags_filter' in st.session_state and st.session_state.tags_filter:
        tags_to_filter = st.session_state.tags_filter
        
        # 确保tags_to_filter是列表
        if not isinstance(tags_to_filter, list):
            tags_to_filter = list(tags_to_filter)
            
        # 如果标签列表不为空，应用过滤
        if tags_to_filter:
            # 过滤包含所选标签的任务
            filtered_df = filtered_df[filtered_df['tags'].apply(
                lambda x: any(tag in x for tag in tags_to_filter) if isinstance(x, list) else False
            )]
    
    return filtered_df

def get_all_tags(df: pd.DataFrame) -> List[str]:
    """
    从数据框获取所有唯一标签
    
    参数:
        df: 任务数据框
        
    返回:
        所有唯一标签的列表
    """
    all_tags = []
    for tags in df["tags"]:
        if isinstance(tags, list):
            all_tags.extend(tags)
    
    # 移除重复项并排序
    return sorted(list(set(all_tags))) 