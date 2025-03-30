import streamlit as st
import pandas as pd

def render_edit_table(filtered_df, current_taskfile):
    """标准表格实现 - 使用Streamlit原生data_editor"""
    
    # 准备表格数据
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
        
    if 'selected' not in st.session_state:
        st.session_state.selected = {task: False for task in filtered_df_copy['name']}
    
    # 更新选择状态 - 确保所有新任务都被添加到选择状态中
    for task in filtered_df_copy['name']:
        if task not in st.session_state.selected:
            st.session_state.selected[task] = False
    
    # 设置已选择的任务状态
    for task in st.session_state.selected_tasks:
        if task in st.session_state.selected:
            st.session_state.selected[task] = True
    
    # 创建勾选框列
    filtered_df_copy['选择'] = filtered_df_copy['name'].apply(
        lambda x: st.session_state.selected.get(x, False)
    )
    
    # 准备要显示的列 - 现在包含选择列
    display_df = filtered_df_copy[['选择', 'name', '显示名称', 'description', 'tags_str', 'directory']]
    display_df = display_df.rename(columns={
        'description': '描述',
        'tags_str': '标签',
        'directory': '目录'
    })
    
    # 定义编辑器回调函数，减少页面刷新
    def on_change():
        if "edited_rows" in st.session_state.task_editor:
            has_changes = False
            for idx, changes in st.session_state.task_editor["edited_rows"].items():
                if "选择" in changes:
                    idx = int(idx)
                    if idx < len(filtered_df_copy):
                        task_name = filtered_df_copy.iloc[idx]['name']
                        if st.session_state.selected.get(task_name) != changes["选择"]:
                            st.session_state.selected[task_name] = changes["选择"]
                            has_changes = True
            
            # 只有当有变化时才更新选中的任务列表
            if has_changes:
                st.session_state.selected_tasks = [
                    task for task, is_selected in st.session_state.selected.items() 
                    if is_selected
                ]
    
    # 使用标准data_editor显示表格，使用on_change回调减少刷新
    edited_df = st.data_editor(
        display_df,
        column_config={
            "name": None,  # 隐藏name列，但保留数据
            "选择": st.column_config.CheckboxColumn(
                "选择",
                help="选择要操作的任务",
                default=False,
                width="small"
            ),
            "显示名称": st.column_config.TextColumn(
                "任务名称",
                help="任务的名称和图标",
                width="medium"
            ),
            "描述": st.column_config.TextColumn(
                "任务描述",
                width="large"
            ),
            "标签": st.column_config.TextColumn(
                "标签",
                width="medium"
            ),
            "目录": st.column_config.TextColumn(
                "任务目录",
                width="medium"
            )
        },
        hide_index=True,
        width=None,
        height=400,
        use_container_width=True,
        disabled=["显示名称", "描述", "标签", "目录"],  # 只允许编辑勾选框
        key="task_editor",
        on_change=on_change
    )
