import streamlit as st
from streamlit_elements import elements, mui, html, dashboard
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..components.batch_operations import render_batch_operations
from ..utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, record_task_run, get_global_state
import pandas as pd
from datetime import datetime
import os

def render_card_view(filtered_df, current_taskfile):
    """渲染卡片视图
    
    Args:
        filtered_df (pd.DataFrame): 过滤后的任务数据框
        current_taskfile (str): 当前任务文件路径
    """
    # 获取全局状态
    global_state = get_global_state()
    tasks = global_state.get('tasks', {})
    
    # 获取用户偏好
    user_prefs = global_state.get('user_preferences', {})
    theme = user_prefs.get('ui_settings', {}).get('theme', 'light')
    
    # 创建任务卡片数据
    task_cards = []
    for task_name, task_info in tasks.items():
        # 获取任务数据
        task_data = task_info.get('data', {})
        
        # 获取任务状态
        is_selected = get_task_selection_state(task_name)
        
        # 获取任务运行时数据
        runtime = {}
        source_file = task_info.get('source_file')
        if source_file and source_file in global_state.get('task_files', {}):
            if 'task_state' in global_state['task_files'][source_file]:
                if task_name in global_state['task_files'][source_file]['task_state']:
                    if 'runtime' in global_state['task_files'][source_file]['task_state'][task_name]:
                        runtime = global_state['task_files'][source_file]['task_state'][task_name]['runtime']
        
        # 构建卡片数据
        card_data = {
            'name': task_name,
            'description': task_data.get('description', ''),
            'tags': task_data.get('tags', []),
            'status': task_data.get('status', 'pending'),
            'priority': task_data.get('priority', 'normal'),
            'is_selected': is_selected,
            'runtime': runtime,
            'source_file': source_file
        }
        task_cards.append(card_data)
    
    # 使用streamlit-elements创建Material UI布局
    with elements("task_cards"):
        # 创建网格布局
        with mui.Grid(container=True, spacing=2):
            for i, card_data in enumerate(task_cards):
                with mui.Grid(item=True, xs=12, sm=6, md=4):
                    with mui.Card(
                        sx={
                            "maxWidth": "100%",
                            "height": "100%",
                            "display": "flex",
                            "flexDirection": "column",
                            "margin": "8px",
                            "cursor": "pointer",
                            "transition": "all 0.2s",
                            "&:hover": {
                                "boxShadow": 3,
                                "transform": "translateY(-2px)",
                            }
                        },
                        onClick=lambda e, name=card_data['name']: update_task_selection(name, not card_data['is_selected'])
                    ):
                        # 卡片内容
                        with mui.CardContent(sx={"flexGrow": 1}):
                            # 卡片头部
                            with mui.Box(sx={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "mb": 1}):
                                # 任务名称
                                mui.Typography(
                                    card_data['name'],
                                    variant="h6",
                                    sx={
                                        "fontWeight": "bold",
                                        "color": "primary.main",
                                        "flex": 1,
                                        "mr": 1
                                    }
                                )
                                
                                # 选中状态指示器
                                mui.Icon(
                                    "check_circle" if card_data['is_selected'] else "radio_button_unchecked",
                                    sx={
                                        "color": "primary.main" if card_data['is_selected'] else "action.disabled",
                                        "cursor": "pointer"
                                    }
                                )
                            
                            # 任务描述
                            if card_data['description']:
                                mui.Typography(
                                    card_data['description'],
                                    variant="body2",
                                    sx={"color": "text.secondary", "mb": 1}
                                )
                            
                            # 标签
                            if card_data['tags']:
                                with mui.Box(sx={"display": "flex", "flexWrap": "wrap", "gap": "4px", "mb": 1}):
                                    for tag in card_data['tags']:
                                        mui.Chip(
                                            label=tag,
                                            size="small",
                                            sx={
                                                "bgcolor": "primary.light",
                                                "color": "primary.contrastText",
                                                "fontSize": "0.75rem"
                                            }
                                        )
                            
                            # 状态和优先级
                            with mui.Box(sx={"display": "flex", "justifyContent": "space-between", "mt": "auto"}):
                                # 状态
                                status_color = {
                                    'pending': 'warning.main',
                                    'running': 'info.main',
                                    'completed': 'success.main',
                                    'failed': 'error.main'
                                }.get(card_data['status'], 'text.secondary')
                                
                                mui.Typography(
                                    str(card_data['status']).upper(),
                                    variant="caption",
                                    sx={"color": status_color}
                                )
                                
                                # 优先级
                                priority = card_data['priority']
                                if isinstance(priority, int):
                                    priority_map = {
                                        1: 'high',
                                        2: 'medium',
                                        3: 'low',
                                        4: 'normal'
                                    }
                                    priority = priority_map.get(priority, 'normal')
                                
                                priority_color = {
                                    'high': 'error.main',
                                    'medium': 'warning.main',
                                    'low': 'success.main',
                                    'normal': 'text.secondary'
                                }.get(priority, 'text.secondary')
                                
                                mui.Typography(
                                    str(priority).upper(),
                                    variant="caption",
                                    sx={"color": priority_color}
                                )
                            
                            # 运行时信息
                            if card_data['runtime']:
                                with mui.Box(sx={"mt": 1, "display": "flex", "gap": 1}):
                                    if card_data['runtime'].get('last_run'):
                                        last_run = datetime.fromisoformat(card_data['runtime']['last_run'])
                                        mui.Typography(
                                            f"上次运行: {last_run.strftime('%Y-%m-%d %H:%M')}",
                                            variant="caption",
                                            sx={"color": "text.secondary"}
                                        )
                                    
                                    if card_data['runtime'].get('run_count'):
                                        mui.Typography(
                                            f"运行次数: {card_data['runtime']['run_count']}",
                                            variant="caption",
                                            sx={"color": "text.secondary"}
                                        )
                        
                        # 卡片操作区
                        with mui.CardActions:
                            mui.Button(
                                "运行",
                                size="small",
                                variant="contained",
                                onClick=lambda e, name=card_data['name']: run_task_via_cmd(name, card_data['source_file'])
                            )
                            mui.Button(
                                "查看",
                                size="small",
                                onClick=lambda e, name=card_data['name']: open_file(card_data['source_file'])
                            )
                            mui.Button(
                                "复制",
                                size="small",
                                onClick=lambda e, name=card_data['name']: copy_to_clipboard(get_task_command(name, card_data['source_file']))
                            )

    # 批量操作部分
    render_batch_operations(current_taskfile, view_key="card")