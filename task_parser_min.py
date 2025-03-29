#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import subprocess
import threading
import platform
import shlex
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
    
    def clear_selection(self) -> None:
        """清空所有任务的选择状态"""
        for task in self.tasks.values():
            task.is_selected = False
            task.order = 0

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
        
        result = None
        if self.parallel_mode and len(task_names) > 1:
            # 并行模式：同时执行多个任务
            result = self._execute_parallel_in_wt(task_names)
        else:
            # 串行模式：执行单个命令
            command = self.generate_command()
            result = self._execute_in_wt(command)
        
        # 清空选择
        self.task_collection.clear_selection()
        
        return result
    
    def _execute_in_wt(self, command: str) -> tuple:
        """在Windows Terminal中执行命令"""
        try:
            # Windows平台使用wt.exe启动PowerShell
            if platform.system() == 'Windows':
                # 转义PowerShell命令中的引号
                ps_command = command.replace('"', '`"')
                # 构造wt.exe命令
                wt_command = f'wt.exe powershell -NoExit -Command "{ps_command}"'
                subprocess.Popen(wt_command, shell=True)
                return True, f"已在Windows Terminal中启动PowerShell执行命令: {command}"
            # Linux/Mac平台
            else:
                # 根据不同的终端模拟器调整命令
                if os.path.exists('/usr/bin/gnome-terminal'):
                    full_command = f'gnome-terminal -- bash -c "{command}; exec bash"'
                elif os.path.exists('/usr/bin/xterm'):
                    full_command = f'xterm -e "{command}; bash"'
                elif os.path.exists('/usr/bin/konsole'):
                    full_command = f'konsole -e "{command}; bash"'
                elif os.path.exists('/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal'):
                    full_command = f'open -a Terminal "{command}"'
                else:
                    full_command = f'x-terminal-emulator -e "{command}; bash"'
                
                subprocess.Popen(full_command, shell=True)
                return True, f"已在终端窗口中启动命令: {command}"
        except Exception as e:
            return False, f"启动命令窗口失败: {str(e)}"
    
    def _execute_parallel_in_wt(self, task_names: List[str]) -> tuple:
        """在多个Windows Terminal标签页中并行执行任务"""
        try:
            if platform.system() == 'Windows':
                # 构造wt.exe命令，为每个任务创建一个新标签页
                wt_args = []
                first_tab = True
                
                for task_name in task_names:
                    cmd = "task"
                    if self.taskfile_path:
                        cmd += f" --taskfile {self.taskfile_path}"
                    cmd += f" {task_name}"
                    
                    # 转义PowerShell命令中的引号
                    ps_command = cmd.replace('"', '`"')
                    
                    if first_tab:
                        # 第一个标签页使用不同的语法
                        wt_args.append(f'powershell -NoExit -Command "{ps_command}"')
                        first_tab = False
                    else:
                        # 后续标签页使用new-tab
                        wt_args.append(f'--tab "powershell -NoExit -Command \'{ps_command}\'"')
                
                # 构造完整的wt命令
                wt_command = "wt.exe " + " ".join(wt_args)
                subprocess.Popen(wt_command, shell=True)
                
                return True, f"已在Windows Terminal的{len(task_names)}个标签页中启动任务"
            else:
                # 在Linux/Mac上还是使用多个窗口
                for task_name in task_names:
                    cmd = "task"
                    if self.taskfile_path:
                        cmd += f" --taskfile {self.taskfile_path}"
                    cmd += f" {task_name}"
                    
                    # 根据不同的终端模拟器调整命令
                    if os.path.exists('/usr/bin/gnome-terminal'):
                        full_command = f'gnome-terminal -- bash -c "{cmd}; exec bash"'
                    elif os.path.exists('/usr/bin/xterm'):
                        full_command = f'xterm -e "{cmd}; bash"'
                    elif os.path.exists('/usr/bin/konsole'):
                        full_command = f'konsole -e "{cmd}; bash"'
                    elif os.path.exists('/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal'):
                        full_command = f'open -a Terminal "{cmd}"'
                    else:
                        full_command = f'x-terminal-emulator -e "{cmd}; bash"'
                    
                    subprocess.Popen(full_command, shell=True)
                
                return True, f"已在{len(task_names)}个独立窗口中启动任务"
        except Exception as e:
            return False, f"启动命令窗口失败: {str(e)}"

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