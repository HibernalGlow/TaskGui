#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List, Dict, Optional

class Task:
    """任务数据模型"""
    
    def __init__(self, name: str, command: List[str], description: str = "", 
                 depends: Optional[List[str]] = None, vars: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command if command else []
        self.description = description
        self.depends = depends if depends else []
        self.vars = vars if vars else {}
        self.is_selected = False
        self.order = 0  # 用于排序
    
    def __str__(self) -> str:
        return f"Task({self.name})"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "depends": self.depends,
            "vars": self.vars,
            "is_selected": self.is_selected,
            "order": self.order
        }

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
        selected = [task for task in self.tasks.values() if task.is_selected]
        # 调试输出，可以在实际修复后删除
        print(f"选中的任务数量: {len(selected)}")
        for task in selected:
            print(f"任务名: {task.name}, 是否选中: {task.is_selected}")
        return selected    
    def reorder_tasks(self, order_map: Dict[str, int]) -> None:
        """重新排序任务"""
        for task_name, order in order_map.items():
            if task_name in self.tasks:
                self.tasks[task_name].order = order
    
    def __len__(self) -> int:
        return len(self.tasks)