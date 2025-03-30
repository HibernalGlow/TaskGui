#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
from typing import List, Dict, Optional, Tuple

from src.models.task import Task, TaskCollection

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
            
            # 处理标签
            tags = task_info.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            
            # 创建任务对象
            task = Task(
                name=task_name,
                command=command,
                description=desc,
                dir=dir_path,
                tags=tags
            )
            
            # 添加到集合
            task_collection.add_task(task)
        
        return task_collection 