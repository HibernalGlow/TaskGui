#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import platform
import shlex
from typing import List, Dict, Optional, Tuple

from src.models.task import TaskCollection

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
    from src.core.parser import TaskfileParser
    
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