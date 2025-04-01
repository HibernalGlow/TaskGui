import streamlit as st
import pandas as pd
import os
from src.utils.file_utils import get_task_command, copy_to_clipboard
from src.services.task_runner import run_task_via_cmd, run_multiple_tasks as run_tasks_via_cmd
from src.utils.selection_utils import get_selected_tasks, clear_all_selections, get_global_state, record_task_run, get_task_runtime
from src.views.card.task_card import render_task_card

try:
    from streamlit_pills import pills
    PILLS_AVAILABLE = True
except ImportError:
    PILLS_AVAILABLE = False

def render_action_buttons(selected_tasks, current_taskfile, key_prefix="preview", is_sidebar=False):
    """渲染任务操作按钮卡片
    
    参数:
        selected_tasks: 选中的任务列表
        current_taskfile: 当前任务文件路径
        key_prefix: 按钮key前缀，用于区分不同位置的按钮
        is_sidebar: 是否在侧边栏中渲染（已由调用函数处理）
    """
    # 使用当前上下文，不再创建新的sidebar.container
    container = st.container()
    
    with container:
        # 创建expander，在侧边栏或主界面中显示，使用更简洁的标题
        with st.expander("📌 任务操作", expanded=True):
            # 显示已选择的任务数量，更简洁的显示
            # st.markdown(f"### **选中{len(selected_tasks)}个任务**")
            
            with st.container():
                # 使用响应式布局，在宽屏幕上单行显示，在窄屏上自适应折行
                cols = st.columns([1, 1, 1, 1])
                
                with cols[0]:
                    # 清除选择按钮，使用emoji代替文本
                    if st.button("🗑️", key=f"{key_prefix}_clear_selection", use_container_width=True, help="清除选择"):
                        clear_all_selections()
                        st.rerun()
                
                with cols[1]:
                    # 复制所有命令，使用emoji代替文本
                    if st.button("📋", key=f"{key_prefix}_copy_all", use_container_width=True, help="复制所有命令"):
                        commands = []
                        for task_name in selected_tasks:
                            cmd = get_task_command(task_name, current_taskfile)
                            commands.append(cmd)
                        
                        all_commands = "\n".join(commands)
                        copy_to_clipboard(all_commands)
                        st.success("已复制")
                
                with cols[2]:
                    # 运行方式选择，使用按钮代替复选框，通过颜色变化表示选中状态
                    btn_type = "primary" if st.session_state.get('run_parallel', False) else "secondary"
                    if st.button("⚡", key=f"{key_prefix}_run_parallel", type=btn_type, use_container_width=True, help="切换并行/顺序运行"):
                        # 切换状态
                        st.session_state.run_parallel = not st.session_state.get('run_parallel', False)
                        st.rerun()
                
                with cols[3]:
                    # 运行所有选中任务，使用emoji代替文本
                    if st.button("▶️", key=f"{key_prefix}_run_all", use_container_width=True, help="运行所有任务"):
                        with st.spinner("正在启动所有选中的任务..."):
                            results = run_tasks_via_cmd(selected_tasks, current_taskfile, parallel=st.session_state.get('run_parallel', False))
                            # 记录所有任务的运行状态
                            for task_name in selected_tasks:
                                record_task_run(task_name, status="started")
                        
                st.success(f"已选中{len(selected_tasks)}个任务")

def render_preview_tab_content(filtered_df, current_taskfile):
    """渲染预览页签的内容
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
    """
    # 从全局状态获取选中的任务
    selected_tasks = get_selected_tasks()
    
    # 如果没有选中任务，显示提示信息
    if not selected_tasks:
        st.info("没有选中的任务。请从表格中选择要操作的任务。")
        return
    
    # 获取选中任务的详细信息
    selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)].copy()
    
    # 添加每行卡片数量的滑动条
    cards_per_row = st.slider(
        "每行显示卡片数量", 
        min_value=1, 
        max_value=4, 
        value=2, 
        step=1,
        key="preview_view_cards_per_row"
    )
    
    # 使用网格布局显示卡片
    for i in range(0, len(selected_df), cards_per_row):
        cols = st.columns(cards_per_row)
        # 获取当前行的任务
        row_tasks = selected_df.iloc[i:min(i+cards_per_row, len(selected_df))]
        
        # 为每个列填充卡片
        for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
            with cols[col_idx]:
                with st.container():
                    st.markdown(f"### {task['emoji']} {task['name']}")
                    render_task_card(
                        task=task,
                        current_taskfile=current_taskfile,
                        idx=i + col_idx,
                        view_type="preview",
                        show_checkbox=False
                    )

def render_shared_preview(filtered_df, current_taskfile):
    """渲染共享任务预览区域
    
    参数:
        filtered_df: 过滤后的任务数据框
        current_taskfile: 当前任务文件路径
    """
    # 获取全局状态
    global_state = get_global_state()
    
    # 从全局状态获取选中的任务
    selected_tasks = get_selected_tasks()
    
    # 如果没有选中任务，显示提示信息
    if not selected_tasks:
        st.info("没有选中的任务。请从表格中选择要操作的任务。")
        return
    
    # 在侧边栏中渲染操作按钮卡片 - 现在已包含expander
    render_action_buttons(selected_tasks, current_taskfile, key_prefix="sidebar", is_sidebar=True)
    
    # 不再在主界面直接显示预览内容，而是通过外部的Tab系统显示

def render_task_preview_in_tab(task, current_taskfile, idx=0):
    """在页签中渲染单个任务的预览卡片
    
    参数:
        task: 任务数据
        current_taskfile: 当前任务文件路径
        idx: 任务索引，用于生成唯一key
    """
    # 使用通用任务卡片渲染函数
    render_task_card(
        task=task, 
        current_taskfile=current_taskfile, 
        idx=idx, 
        view_type="preview", 
        show_checkbox=False
    )


