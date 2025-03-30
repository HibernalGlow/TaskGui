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
        """清空所有任务的选择状态，但保留顺序信息"""
        for task in self.tasks.values():
            task.is_selected = False
            # 移除这行代码，保留任务顺序信息
            # task.order = 0 