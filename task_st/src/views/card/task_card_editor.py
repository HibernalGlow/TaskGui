import streamlit as st
import yaml
import os
import shutil
from datetime import datetime

def render_task_edit_form(task, taskfile_path, on_save_callback=None):
    """
    渲染任务编辑表单
    
    参数:
        task: 要编辑的任务数据
        taskfile_path: 任务文件路径
        on_save_callback: 保存成功后的回调函数
    """
    # 创建一个任务的可编辑副本
    edited_task = task.copy()
    
    # 转换标签列表为字符串方便编辑
    tags_str = ', '.join(edited_task.get('tags', [])) if isinstance(edited_task.get('tags'), list) else ''
    
    # 编辑表单
    with st.form(key=f"edit_form_{edited_task['name']}"):
        st.markdown(f"{edited_task['name']}")
        
        # 组织编辑字段
        col1, col2 = st.columns(2)
        
        with col1:
            edited_task['emoji'] = st.text_input("任务图标", value=edited_task.get('emoji', '📋'))
            edited_task['description'] = st.text_area("任务描述", value=edited_task.get('description', ''))
        
        with col2:
            edited_task['directory'] = st.text_input("任务目录", value=edited_task.get('directory', ''))
            new_tags_str = st.text_input("标签 (逗号分隔)", value=tags_str)
            # 将标签字符串转换回列表
            edited_task['tags'] = [tag.strip() for tag in new_tags_str.split(',') if tag.strip()]
        
        # 命令编辑
        if 'cmds' in edited_task and isinstance(edited_task['cmds'], list) and len(edited_task['cmds']) > 0:
            # YAML格式的任务通常使用cmds列表存储命令
            command = edited_task['cmds'][0]
            new_command = st.text_area("命令", value=command, height=100)
            if new_command != command:
                edited_task['cmds'][0] = new_command
        elif 'command' in edited_task:
            # 适配可能使用command字段的情况
            edited_task['command'] = st.text_area("命令", value=edited_task.get('command', ''), height=100)
        
        # 表单提交按钮
        submit = st.form_submit_button("保存修改")
        
        if submit:
            # 保存修改
            success = save_task_to_yml(edited_task, taskfile_path)
            if success:
                st.success(f"任务 {edited_task['name']} 已保存")
                if on_save_callback:
                    on_save_callback()
            else:
                st.error("保存失败，请查看错误信息")

def save_task_to_yml(edited_task, taskfile_path):
    """
    将编辑后的任务保存到YAML文件
    
    参数:
        edited_task: 编辑后的任务数据
        taskfile_path: 任务文件路径
        
    返回:
        bool: 是否保存成功
    """
    try:
        # 备份原文件
        backup_path = f"{taskfile_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(taskfile_path, backup_path)
        
        # 读取当前的YAML文件
        with open(taskfile_path, 'r', encoding='utf-8') as f:
            taskfile_data = yaml.safe_load(f)
        
        # 检查文件格式，更新对应的任务
        task_name = edited_task['name']
        
        # 处理Taskfile.yml格式
        if 'tasks' in taskfile_data and isinstance(taskfile_data['tasks'], dict):
            # 确保任务数据格式正确 - 移除非YAML格式需要的字段
            if 'command' in edited_task:
                del edited_task['command']  # 移除command字段，Taskfile使用cmds
            
            # 更新任务数据
            taskfile_data['tasks'][task_name] = {
                'desc': edited_task.get('description', ''),
                'dir': edited_task.get('directory', ''),
                'tags': edited_task.get('tags', []),
                'cmds': edited_task.get('cmds', [])
            }
            
            # 如果有emoji字段，添加到描述前面
            if 'emoji' in edited_task and edited_task['emoji']:
                taskfile_data['tasks'][task_name]['desc'] = f"{edited_task['emoji']} {taskfile_data['tasks'][task_name]['desc']}"
        
        # 写回YAML文件
        with open(taskfile_path, 'w', encoding='utf-8') as f:
            yaml.dump(taskfile_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        return True
    except Exception as e:
        st.error(f"保存任务失败: {str(e)}")
        return False

def load_task_from_yml(task_name, taskfile_path):
    """
    从YAML文件加载指定任务
    
    参数:
        task_name: 任务名称
        taskfile_path: 任务文件路径
        
    返回:
        dict: 任务数据
    """
    try:
        # 读取YAML文件
        with open(taskfile_path, 'r', encoding='utf-8') as f:
            taskfile_data = yaml.safe_load(f)
        
        # 检查文件格式，获取对应的任务
        if 'tasks' in taskfile_data and isinstance(taskfile_data['tasks'], dict):
            task_data = taskfile_data['tasks'].get(task_name)
            if task_data:
                # 解析描述中的emoji
                desc = task_data.get('desc', '')
                emoji = ''
                if desc and len(desc) > 1 and ord(desc[0]) > 127:  # 简单判断是否为emoji
                    emoji = desc[0]
                    desc = desc[2:] if len(desc) > 2 else ''
                
                # 构建任务数据
                return {
                    'name': task_name,
                    'emoji': emoji,
                    'description': desc,
                    'directory': task_data.get('dir', ''),
                    'tags': task_data.get('tags', []),
                    'cmds': task_data.get('cmds', [])
                }
        
        return None
    except Exception as e:
        st.error(f"加载任务失败: {str(e)}")
        return None
