import streamlit as st
import yaml
import os
import shutil
from datetime import datetime

def render_task_edit_form(task, taskfile_path, on_save_callback=None, with_back_button=False, back_button_callback=None):
    """
    渲染任务编辑表单
    
    参数:
        task: 要编辑的任务数据
        taskfile_path: 任务文件路径
        on_save_callback: 保存成功后的回调函数
        with_back_button: 是否显示返回按钮
        back_button_callback: 返回按钮回调函数
    """
    # 创建一个任务的可编辑副本
    edited_task = task.copy()
    
    # 转换标签列表为字符串方便编辑
    tags_str = ', '.join(edited_task.get('tags', [])) if isinstance(edited_task.get('tags'), list) else ''
    
    # 添加一些CSS样式，使表单更美观
    st.markdown("""
        <style>
        .task-edit-header {
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #1E88E5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 编辑表单
    with st.form(key=f"edit_form_{edited_task['name']}"):
        st.markdown(f"<div class='task-edit-header'>编辑任务</div>", unsafe_allow_html=True)
        
        # 添加任务名称字段
        original_name = edited_task['name']
        edited_task['name'] = st.text_input("任务名称", value=original_name, help="任务的唯一标识符，用于引用该任务")
        
        # 组织编辑字段
        col1, col2 = st.columns(2)
        
        with col1:
            edited_task['emoji'] = st.text_input("任务图标", value=edited_task.get('emoji', '📋'), help="用于显示的表情符号")
            edited_task['description'] = st.text_area("任务描述", value=edited_task.get('description', ''), help="任务的详细描述")
        
        with col2:
            edited_task['directory'] = st.text_input("任务目录", value=edited_task.get('directory', ''), help="任务执行的目录路径")
            new_tags_str = st.text_input("标签 (逗号分隔)", value=tags_str, help="使用逗号分隔的标签列表，用于分类和筛选")
            # 将标签字符串转换回列表
            edited_task['tags'] = [tag.strip() for tag in new_tags_str.split(',') if tag.strip()]
        
        # 命令编辑
        if 'cmds' in edited_task and isinstance(edited_task['cmds'], list) and len(edited_task['cmds']) > 0:
            # YAML格式的任务通常使用cmds列表存储命令
            command = edited_task['cmds'][0]
            new_command = st.text_area("命令", value=command, height=100, help="要执行的命令行")
            if new_command != command:
                edited_task['cmds'][0] = new_command
        elif 'command' in edited_task:
            # 适配可能使用command字段的情况
            edited_task['command'] = st.text_area("命令", value=edited_task.get('command', ''), height=100, help="要执行的命令行")
        
        # 创建一个校验状态进行检查
        is_valid = True
        validation_error = None
        
        # 检查任务名称是否为空
        if not edited_task['name']:
            is_valid = False
            validation_error = "任务名称不能为空"
        
        # 按钮区域 - 使用单行布局放置所有按钮
        # st.markdown("---")
        
        # 定义按钮配置
        button_configs = []
        
        # 添加保存按钮
        button_configs.append({
            "icon": "💾保存",
            "help": "保存对当前任务的修改",
            "key": "save_btn"
        })
        
        # 添加保存为新任务按钮
        button_configs.append({
            "icon": "➕新建",
            "help": "创建一个新的任务副本",
            "key": "save_as_new_btn"
        })
        
        # 如果需要返回按钮，添加到配置中
        if with_back_button:
            button_configs.append({
                "icon": "🔙返回",
                "help": "返回上一页面",
                "key": "back_btn"
            })
        
        # 设置是否为新任务的标志
        save_as_new = False
        submit = False
        back_clicked = False
        
        # 创建动态列布局
        button_columns = st.columns(len(button_configs))
        
        # 渲染按钮
        for idx, (col, config) in enumerate(zip(button_columns, button_configs)):
            with col:
                btn_key = config.get("key")
                btn_icon = config.get("icon")
                btn_help = config.get("help")
                
                # 创建按钮
                btn_clicked = st.form_submit_button(btn_icon, help=btn_help)
                
                # 处理按钮点击事件
                if btn_clicked:
                    if btn_key == "save_btn":
                        submit = True
                    elif btn_key == "save_as_new_btn":
                        save_as_new = True
                        submit = True
                    elif btn_key == "back_btn":
                        back_clicked = True
        
        # 调试信息
        # st.write(f"Submit: {submit}, Save as new: {save_as_new}, Back: {back_clicked}")
        
        # 返回按钮的处理逻辑
        if back_clicked and with_back_button and back_button_callback:
            back_button_callback()
            return
        
        if submit:
            # 先检查验证错误
            if not is_valid:
                st.error(validation_error)
            else:
                # 如果是保存为新任务，确保使用新名称
                if save_as_new and edited_task['name'] == original_name:
                    # 生成新名称，添加"_copy"后缀
                    edited_task['name'] = f"{original_name}_copy"
                
                # 保存修改
                success = save_task_to_yml(edited_task, taskfile_path, original_name, save_as_new)
                if success:
                    if save_as_new:
                        st.success(f"已创建新任务: {edited_task['name']}")
                    else:
                        st.success(f"任务 {edited_task['name']} 已保存")
                    if on_save_callback:
                        on_save_callback()
                else:
                    st.error("保存失败，请查看错误信息")

def save_task_to_yml(edited_task, taskfile_path, original_name=None, save_as_new=False):
    """
    将编辑后的任务保存到YAML文件
    
    参数:
        edited_task: 编辑后的任务数据
        taskfile_path: 任务文件路径
        original_name: 原始任务名称（如果已更改）
        save_as_new: 是否作为新任务保存
        
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
        
        # 如果没有指定原始名称，使用当前名称
        if original_name is None:
            original_name = task_name
        
        # 处理Taskfile.yml格式
        if 'tasks' in taskfile_data and isinstance(taskfile_data['tasks'], dict):
            # 确保任务数据格式正确 - 移除非YAML格式需要的字段
            if 'command' in edited_task:
                del edited_task['command']  # 移除command字段，Taskfile使用cmds
            
            # 准备任务数据
            task_data = {
                'desc': edited_task.get('description', ''),
                'dir': edited_task.get('directory', ''),
                'tags': edited_task.get('tags', []),
                'cmds': edited_task.get('cmds', [])
            }
            
            # 如果有emoji字段，添加到描述前面
            if 'emoji' in edited_task and edited_task['emoji']:
                task_data['desc'] = f"{edited_task['emoji']} {task_data['desc']}"
            
            # 如果是新任务或任务名称已更改，添加新任务
            if save_as_new or task_name != original_name:
                # 检查新名称是否已存在
                if task_name in taskfile_data['tasks'] and not save_as_new:
                    # 如果只是重命名，并且新名称已存在，返回错误
                    st.error(f"任务名称 '{task_name}' 已存在，请使用其他名称")
                    return False
                
                # 如果是新任务且使用了相同的名称，自动添加后缀
                if save_as_new and task_name == original_name:
                    task_name = f"{original_name}_copy"
                    edited_task['name'] = task_name
                
                # 添加新任务条目
                taskfile_data['tasks'][task_name] = task_data
                
                # 如果是重命名而非新任务，删除原任务
                if not save_as_new and task_name != original_name:
                    if original_name in taskfile_data['tasks']:
                        del taskfile_data['tasks'][original_name]
            else:
                # 更新现有任务
                taskfile_data['tasks'][task_name] = task_data
        
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
