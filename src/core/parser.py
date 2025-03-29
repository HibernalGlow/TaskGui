#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
from src.models.task_model import Task, TaskCollection

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
        
        # 提取全局变量
        global_vars = data.get('vars', {})
        
        # 处理tasks部分
        tasks_data = data.get('tasks', {})
        for task_name, task_info in tasks_data.items():
            # 处理命令，可能是字符串或列表
            command = task_info.get('cmds', [])
            if isinstance(command, str):
                command = [command]
            
            # 处理依赖
            depends = task_info.get('deps', [])
            if isinstance(depends, str):
                depends = [depends]
            
            # 处理描述
            desc = task_info.get('desc', '')
            
            # 处理目录
            dir_path = task_info.get('dir', '')
            
            # 处理任务特有变量
            task_vars = task_info.get('vars', {})
            # 合并全局变量和任务变量
            vars_dict = {**global_vars, **task_vars}
            
            # 创建任务对象
            task = Task(
                name=task_name,
                command=command,
                description=desc,
                depends=depends,
                vars=vars_dict
            )
            
            # 添加目录属性
            if dir_path:
                task.dir = dir_path
            
            # 添加到集合
            task_collection.add_task(task)
        
        # 解析依赖关系
        self._resolve_dependencies(task_collection)
        
        return task_collection    
    def _resolve_dependencies(self, task_collection):
        """解析任务之间的依赖关系"""
        # 此处可以添加依赖解析的详细逻辑
        # 例如检查循环依赖等
        pass