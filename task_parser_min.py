#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import subprocess
import threading
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
    
    def __init__(self, task_collection, taskfile_path=None, parallel_mode=False):
        self.task_collection = task_collection
        self.taskfile_path = taskfile_path
        self.parallel_mode = parallel_mode
    
    def generate_command(self) -> str:
        """生成使用task命令行工具的命令"""
        selected_tasks = self.task_collection.get_selected_tasks()
        
        if not selected_tasks:
            return "# 未选择任何任务"
        
        # 对任务进行排序
        sorted_tasks = sorted(selected_tasks, key=lambda t: t.order)
        
        # 构建命令 - 使用task工具
        task_names = [task.name for task in sorted_tasks]
        
        if self.parallel_mode:
            # 并行模式：返回多行命令，每行运行一个任务
            commands = []
            for task_name in task_names:
                cmd = "task"
                if self.taskfile_path:
                    cmd += f" --taskfile {self.taskfile_path}"
                cmd += f" {task_name}"
                commands.append(cmd)
            return "\n".join(commands)
        else:
            # 串行模式：一条命令运行所有任务
            command = "task"
            if self.taskfile_path:
                command += f" --taskfile {self.taskfile_path}"
            command += " " + " ".join(task_names)
            return command
    
    def execute_command(self) -> tuple:
        """
        执行生成的命令
        返回: (成功标志, 输出内容)
        """
        selected_tasks = self.task_collection.get_selected_tasks()
        
        if not selected_tasks:
            return False, "没有选择任务，无法执行"
        
        # 对任务进行排序
        sorted_tasks = sorted(selected_tasks, key=lambda t: t.order)
        task_names = [task.name for task in sorted_tasks]
        
        if self.parallel_mode and len(task_names) > 1:
            # 并行模式：同时执行多个任务
            return self._execute_parallel(task_names)
        else:
            # 串行模式：执行单个命令
            command = self.generate_command()
            return self._execute_single_command(command)
    
    def _execute_single_command(self, command: str) -> tuple:
        """执行单个命令"""
        try:
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
    
    def _execute_parallel(self, task_names: List[str]) -> tuple:
        """并行执行多个任务"""
        results = []
        success_count = 0
        error_messages = []
        
        # 定义执行单个任务的函数
        def execute_task(task_name):
            nonlocal success_count, error_messages
            cmd = "task"
            if self.taskfile_path:
                cmd += f" --taskfile {self.taskfile_path}"
            cmd += f" {task_name}"
            
            try:
                process = subprocess.Popen(
                    cmd, 
                    shell=True, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    results.append((task_name, True, stdout))
                    success_count += 1
                else:
                    results.append((task_name, False, stderr))
                    error_messages.append(f"{task_name}: {stderr}")
            except Exception as e:
                results.append((task_name, False, str(e)))
                error_messages.append(f"{task_name}: {str(e)}")
        
        # 创建并启动线程
        threads = []
        for task_name in task_names:
            thread = threading.Thread(target=execute_task, args=(task_name,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 构建输出
        output = []
        for task_name, success, result in sorted(results, key=lambda x: task_names.index(x[0])):
            status = "成功" if success else "失败"
            output.append(f"任务 {task_name}: {status}")
            output.append(result)
            output.append("-" * 40)
        
        # 确定整体成功/失败状态
        all_success = success_count == len(task_names)
        
        if all_success:
            return True, "\n".join(output)
        else:
            return False, "\n".join([f"部分任务执行失败 ({success_count}/{len(task_names)} 成功)"] + error_messages + ["", "详细信息:"] + output)

def parse_and_execute_taskfile(filepath, selected_task_names=None, parallel_mode=False):
    """
    解析Taskfile并执行选定的任务
    
    Args:
        filepath: Taskfile的路径
        selected_task_names: 选定的任务名称列表
        parallel_mode: 是否并行执行任务
    
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
    command_generator = CommandGenerator(task_collection, filepath, parallel_mode)
    command = command_generator.generate_command()
    
    # 执行命令
    result = None
    if not command.startswith('#'):
        result = command_generator.execute_command()
    
    return command, result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python task_parser_min.py <taskfile_path> [task1 task2 ...] [--parallel]")
        sys.exit(1)
    
    taskfile_path = sys.argv[1]
    parallel_mode = "--parallel" in sys.argv
    
    # 过滤掉--parallel参数
    task_args = [arg for arg in sys.argv[2:] if arg != "--parallel"]
    selected_tasks = task_args if task_args else None
    
    try:
        command, result = parse_and_execute_taskfile(taskfile_path, selected_tasks, parallel_mode)
        
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