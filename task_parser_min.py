#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import subprocess
from typing import List, Dict, Optional

class Task:
    """任务数据模型"""
    
    def __init__(self, name: str, command: List[str], description: str = "", dir: str = ""):
        self.name = name
        self.command = command if command else []
        self.description = description
        self.dir = dir
        self.is_selected = False
        self.order = 0
    
    def __str__(self) -> str:
        return f"Task({self.name})"

class TaskCollection:
    """任务集合管理"""
    
    def __init__(self):
        self.tasks = {}  # 使用字典存储任务，键为任务名
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.name] = task
    
    def get_task(self, name: str) -> Optional[Task]:
        """根据名称获取任务"""
        return self.tasks.get(name)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_selected_tasks(self) -> List[Task]:
        """获取已选择的任务"""
        return [task for task in self.tasks.values() if task.is_selected]

class TaskfileParser:
    """Taskfile解析器"""
    
    def parse_file(self, filepath):
        """解析Taskfile并返回任务集合"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Taskfile不存在: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                return self._process_taskfile(data)
            except yaml.YAMLError as e:
                raise ValueError(f"Taskfile解析错误: {e}")
    
    def _process_taskfile(self, data):
        """处理Taskfile数据"""
        task_collection = TaskCollection()
        
        # 处理tasks部分
        tasks_data = data.get('tasks', {})
        for task_name, task_info in tasks_data.items():
            # 处理命令，可能是字符串或列表
            command = task_info.get('cmds', [])
            if isinstance(command, str):
                command = [command]
            
            # 处理描述
            desc = task_info.get('desc', '')
            
            # 处理目录
            dir_path = task_info.get('dir', '')
            
            # 创建任务对象
            task = Task(
                name=task_name,
                command=command,
                description=desc,
                dir=dir_path
            )
            
            # 添加到集合
            task_collection.add_task(task)
        
        return task_collection

class CommandGenerator:
    """命令生成器"""
    
    def __init__(self, task_collection, taskfile_path=None):
        self.task_collection = task_collection
        self.taskfile_path = taskfile_path
    
    def generate_command(self) -> str:
        """生成使用task命令行工具的命令"""
        selected_tasks = self.task_collection.get_selected_tasks()
        
        if not selected_tasks:
            return "# 未选择任何任务"
        
        # 对任务进行排序
        sorted_tasks = sorted(selected_tasks, key=lambda t: t.order)
        
        # 构建命令 - 使用task工具
        task_names = [task.name for task in sorted_tasks]
        
        # 基本命令
        command = "task"
        
        # 如果有指定taskfile路径，添加--taskfile参数
        if self.taskfile_path:
            command += f" --taskfile {self.taskfile_path}"
        
        # 添加任务名称
        command += " " + " ".join(task_names)
        
        return command
    
    def execute_command(self) -> tuple:
        """
        执行生成的命令
        返回: (成功标志, 输出内容)
        """
        command = self.generate_command()
        
        if command.startswith('#'):
            return False, "没有选择任务，无法执行"
        
        try:
            # 执行命令
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return True, stdout
            else:
                return False, f"错误: {stderr}"
        except Exception as e:
            return False, f"执行错误: {str(e)}"

def parse_and_execute_taskfile(filepath, selected_task_names=None):
    """
    解析Taskfile并执行选定的任务
    
    Args:
        filepath: Taskfile的路径
        selected_task_names: 选定的任务名称列表
    
    Returns:
        (命令字符串, 执行结果元组)
    """
    # 解析Taskfile
    parser = TaskfileParser()
    task_collection = parser.parse_file(filepath)
    
    # 选择任务
    if selected_task_names:
        for task_name in selected_task_names:
            task = task_collection.get_task(task_name)
            if task:
                task.is_selected = True
                # 设置顺序为列表中的索引
                task.order = selected_task_names.index(task_name)
    
    # 生成命令
    command_generator = CommandGenerator(task_collection, filepath)
    command = command_generator.generate_command()
    
    # 执行命令
    result = None
    if not command.startswith('#'):
        result = command_generator.execute_command()
    
    return command, result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python task_parser_min.py <taskfile_path> [task1 task2 ...]")
        sys.exit(1)
    
    taskfile_path = sys.argv[1]
    selected_tasks = sys.argv[2:] if len(sys.argv) > 2 else None
    
    try:
        command, result = parse_and_execute_taskfile(taskfile_path, selected_tasks)
        
        print(f"生成的命令: {command}")
        
        if result:
            success, output = result
            if success:
                print(f"执行成功: {output}")
            else:
                print(f"执行失败: {output}")
    
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1) 