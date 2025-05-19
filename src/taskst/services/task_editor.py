import streamlit as st
import pandas as pd
import os
import json
import shutil
from datetime import datetime

def render_edit_controls(filtered_df, current_taskfile):
    """
    渲染编辑模式控制按钮并返回当前编辑模式状态
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
        
    返回:
        bool: 是否处于编辑模式
    """
    col1, col2, col3 = st.columns([3, 1, 1])
    
    # 初始化编辑模式状态
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    with col1:
        # 显示当前模式
        mode_text = "当前模式: 编辑模式" if st.session_state.edit_mode else "当前模式: 查看模式"
        st.markdown(f"**{mode_text}**")
    
    with col2:
        # 编辑模式开关
        if st.button("切换编辑模式" if not st.session_state.edit_mode else "退出编辑模式"):
            st.session_state.edit_mode = not st.session_state.edit_mode
            # 如果退出编辑模式，清除编辑缓存
            if not st.session_state.edit_mode and 'edited_tasks' in st.session_state:
                del st.session_state.edited_tasks
            st.rerun()
    
    with col3:
        # 只在编辑模式下显示保存按钮
        if st.session_state.edit_mode:
            if st.button("保存更改", key="save_task_changes"):
                save_task_changes(filtered_df, current_taskfile)
                st.success("任务更改已保存到任务文件")
                st.rerun()
    
    return st.session_state.edit_mode

def render_task_editor(filtered_df, current_taskfile):
    """
    渲染任务编辑器
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    # 将数据初始化到编辑缓存
    if 'edited_tasks' not in st.session_state:
        st.session_state.edited_tasks = filtered_df.copy().to_dict('records')
    
    # 准备编辑用的数据
    edit_df = pd.DataFrame(st.session_state.edited_tasks)
    
    # 转换标签列表为字符串用于编辑
    if 'tags' in edit_df.columns:
        edit_df['tags_str'] = edit_df['tags'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else ''
        )
    
    # 创建任务编辑界面
    st.subheader("任务编辑器")
    
    # 添加任务按钮
    if st.button("添加新任务", key="add_new_task"):
        # 创建一个新的空任务
        new_task = {
            'name': f"new_task_{len(edit_df) + 1}",
            'emoji': "📋",
            'description': "新任务描述",
            'tags': [],
            'tags_str': '',
            'directory': "",
            'command': "echo 这是一个新任务"
        }
        st.session_state.edited_tasks.append(new_task)
        st.rerun()
    
    # 渲染每个任务的编辑面板
    for i, task in enumerate(st.session_state.edited_tasks):
        with st.expander(f"{task.get('emoji', '📋')} {task.get('name', f'任务_{i}')}"):
            # 任务基本信息编辑
            col1, col2 = st.columns(2)
            
            with col1:
                task['name'] = st.text_input("任务名称", value=task.get('name', ''), key=f"name_{i}")
                task['emoji'] = st.text_input("任务图标", value=task.get('emoji', '📋'), key=f"emoji_{i}")
                task['tags_str'] = st.text_input("标签 (逗号分隔)", value=task.get('tags_str', ''), key=f"tags_{i}")
                # 将标签字符串转换为列表
                task['tags'] = [tag.strip() for tag in task.get('tags_str', '').split(',') if tag.strip()]
            
            with col2:
                task['description'] = st.text_area("任务描述", value=task.get('description', ''), key=f"desc_{i}")
                task['directory'] = st.text_input("任务目录", value=task.get('directory', ''), key=f"dir_{i}")
            
            # 任务命令编辑
            task['command'] = st.text_area("任务命令", value=task.get('command', ''), height=100, key=f"cmd_{i}")
            
            # 操作按钮
            col1, col2 = st.columns([1, 6])
            with col1:
                if st.button("删除任务", key=f"delete_{i}"):
                    if len(st.session_state.edited_tasks) > 0:
                        st.session_state.edited_tasks.pop(i)
                        st.rerun()
            
            # 分隔线
            st.markdown("---")
    
    # 批量操作区域
    with st.expander("批量操作"):
        st.write("批量编辑多个任务的公共属性")
        
        # 选择要批量编辑的任务
        task_names = [task.get('name', f"任务_{i}") for i, task in enumerate(st.session_state.edited_tasks)]
        selected_tasks = st.multiselect("选择要批量编辑的任务", options=task_names)
        
        if selected_tasks:
            # 批量编辑界面
            st.subheader("批量编辑")
            
            # 添加共享标签
            shared_tags = st.text_input("添加共享标签 (逗号分隔)")
            if st.button("应用标签") and shared_tags:
                tags_to_add = [tag.strip() for tag in shared_tags.split(',') if tag.strip()]
                
                # 更新所选任务
                for task in st.session_state.edited_tasks:
                    if task.get('name') in selected_tasks:
                        task_tags = set(task.get('tags', []))
                        task_tags.update(tags_to_add)
                        task['tags'] = list(task_tags)
                        task['tags_str'] = ', '.join(task['tags'])
                
                st.success(f"已为选中的 {len(selected_tasks)} 个任务添加标签")
                st.rerun()
            
            # 设置共享目录
            shared_dir = st.text_input("设置共享目录路径")
            if st.button("应用目录") and shared_dir:
                # 更新所选任务
                for task in st.session_state.edited_tasks:
                    if task.get('name') in selected_tasks:
                        task['directory'] = shared_dir
                
                st.success(f"已为选中的 {len(selected_tasks)} 个任务设置目录")
                st.rerun()
    
    # 底部保存按钮区域
    save_col1, save_col2 = st.columns([5, 1])
    with save_col2:
        if st.button("保存所有更改", key="save_all_changes"):
            save_task_changes(filtered_df, current_taskfile)
            st.success("任务更改已保存到任务文件")
            st.session_state.edit_mode = False
            st.rerun()

def save_task_changes(original_df, taskfile_path):
    """
    保存编辑后的任务到任务文件
    
    参数:
        original_df: 原始任务DataFrame
        taskfile_path: 任务文件路径
    """
    if 'edited_tasks' not in st.session_state:
        st.warning("没有可保存的更改")
        return
    
    try:
        # 备份原文件
        backup_path = f"{taskfile_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(taskfile_path, backup_path)
        
        # 读取现有的taskfile文件
        with open(taskfile_path, 'r', encoding='utf-8') as f:
            taskfile_data = json.load(f)
        
        # 更新任务数据
        # 编辑后的任务
        edited_tasks = st.session_state.edited_tasks
        
        # 确保任务数据格式正确
        for task in edited_tasks:
            # 移除tags_str，这只是为了UI编辑
            if 'tags_str' in task:
                del task['tags_str']
        
        # 更新任务文件中的任务列表
        taskfile_data['tasks'] = edited_tasks
        
        # 写回任务文件
        with open(taskfile_path, 'w', encoding='utf-8') as f:
            json.dump(taskfile_data, f, ensure_ascii=False, indent=2)
        
        # 清理会话状态
        if 'edited_tasks' in st.session_state:
            del st.session_state.edited_tasks
        
        return True
    except Exception as e:
        st.error(f"保存任务失败: {str(e)}")
        return False
