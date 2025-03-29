#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import shlex
from typing import List
import os

class CommandGenerator:
    """命令生成器"""
    
    def __init__(self, task_collection):
        self.task_collection = task_collection
    
    def generate_command(self) -> str:
        """生成命令行命令"""
        selected_tasks = self.task_collection.get_selected_tasks()
        
        if not selected_tasks:
            return "# 未选择任何任务"
        
        # 对任务进行排序
        sorted_tasks = sorted(selected_tasks, key=lambda t: t.order)
        
        # 构建命令
        commands = []
        for task in sorted_tasks:
            # 获取任务的完整命令
            task_cmd = task.command
            if isinstance(task_cmd, list):
                task_cmd = " && ".join(task_cmd)
            
            # 如果有目录设置，添加目录切换
            if hasattr(task, 'dir') and task.dir:
                commands.append(f"cd {task.dir} && {task_cmd}")
            else:
                commands.append(task_cmd)
        
        # 使用 && 连接多个命令
        return " && ".join(commands)    
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