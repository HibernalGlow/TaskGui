import streamlit as st
import os
from taskgui.utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from taskgui.services.task_runner import run_task_via_cmd
from taskgui.components.batch_operations import render_batch_operations
from taskgui.utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, record_task_run, load_local_config
from taskgui.views.card.task_card import render_task_card

def group_tasks_by_first_tag(tasks_df):
    """按第一个标签对任务进行分组
    
    参数:
        tasks_df: 任务数据框
        
    返回:
        dict: 按标签分组的任务字典
    """
    grouped_tasks = {}
    
    for _, task in tasks_df.iterrows():
        # 获取第一个标签，如果没有标签则使用"未分类"
        first_tag = task['tags'][0] if isinstance(task['tags'], list) and task['tags'] else "未分类"
        
        # 将任务添加到对应标签组
        if first_tag not in grouped_tasks:
            grouped_tasks[first_tag] = []
        grouped_tasks[first_tag].append(task)
    
    return grouped_tasks

def sort_grouped_tasks(grouped_tasks, pinned_tags):
    """对分组后的任务进行排序，置顶标签优先显示
    
    参数:
        grouped_tasks: 按标签分组的任务字典
        pinned_tags: 置顶标签列表
        
    返回:
        list: 排序后的(标签, 任务列表)元组列表
    """
    # 将分组转换为列表以便排序
    groups = list(grouped_tasks.items())
    
    # 定义排序函数
    def sort_key(item):
        tag = item[0]
        if tag in pinned_tags:
            # 置顶标签按其在pinned_tags中的顺序排序
            return (0, pinned_tags.index(tag))
        elif tag == "未分类":
            # 未分类放在最后
            return (2, 0)
        else:
            # 其他标签按字母顺序排序
            return (1, tag)
    
    # 排序并返回
    return sorted(groups, key=sort_key)

def render_card_view(filtered_df, current_taskfile, key_prefix="card_view"):
    """渲染卡片视图
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
        key_prefix: 组件key前缀，用于区分不同视图
    """
    # 确保全局状态已初始化
    init_global_state()
    
    # 加载设置
    config = load_local_config()
    group_by_tag = config.get('card_group_by_tag', False)
    pinned_tags = config.get('pinned_tags', [])
    
    # 添加每行卡片数量的滑动条
    cards_per_row = st.slider(
        "每行显示卡片数量", 
        min_value=1, 
        max_value=4, 
        value=3, 
        step=1,
        key=f"{key_prefix}_cards_per_row"
    )
    
    if group_by_tag:
        # 按标签分组显示
        grouped_tasks = group_tasks_by_first_tag(filtered_df)
        
        # 对分组进行排序
        sorted_groups = sort_grouped_tasks(grouped_tasks, pinned_tags)
        
        # 遍历每个标签组
        for tag, tasks in sorted_groups:
            # 创建标签锚点ID
            tag_id = tag.replace(" ", "_").lower()
            
            # 创建锚点和标题
            st.markdown(f'<div id="tag_{tag_id}"></div>', unsafe_allow_html=True)
            
            # 显示带样式的标签标题
            if tag in pinned_tags:
                st.markdown(f"### ⭐ {tag}")
            else:
                st.markdown(f"### {tag}")
            
            # 创建行
            for i in range(0, len(tasks), cards_per_row):
                cols = st.columns(cards_per_row)
                # 获取当前行的任务
                row_tasks = tasks[i:min(i+cards_per_row, len(tasks))]
                
                # 为每个列填充卡片
                for col_idx, task in enumerate(row_tasks):
                    with cols[col_idx]:
                        with st.container():
                            # 使用通用任务卡片渲染函数
                            render_task_card(
                                task=task,
                                current_taskfile=current_taskfile,
                                idx=i + col_idx,
                                view_type=key_prefix,
                                show_checkbox=True
                            )
    else:
        # 原有的不分组显示逻辑
        for i in range(0, len(filtered_df), cards_per_row):
            cols = st.columns(cards_per_row)
            # 获取当前行的任务
            row_tasks = filtered_df.iloc[i:min(i+cards_per_row, len(filtered_df))]
            
            # 为每个列填充卡片
            for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
                with cols[col_idx]:
                    with st.container():
                        # 使用通用任务卡片渲染函数
                        render_task_card(
                            task=task,
                            current_taskfile=current_taskfile,
                            idx=i + col_idx,
                            view_type=key_prefix,
                            show_checkbox=True
                        )
    
    # 批量操作部分
    # render_batch_operations(current_taskfile, view_key="card")