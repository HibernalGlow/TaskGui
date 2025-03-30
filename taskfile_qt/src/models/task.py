from typing import List, Dict, Optional, Set

class Task:
    """任务数据模型"""
    
    def __init__(self, name: str, command: List[str], description: str = "", dir: str = "", tags: List[str] = None):
        self.name = name
        self.command = command if command else []
        self.description = description
        self.dir = dir
        self.tags = tags if tags else []  # 标签列表
        self.is_selected = False
        self.order = 0
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """检查是否包含指定标签"""
        return tag in self.tags
    
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
    
    def get_all_tags(self) -> Set[str]:
        """获取所有任务的标签集合"""
        tags = set()
        for task in self.tasks.values():
            tags.update(task.tags)
        return tags
    
    def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """获取包含指定标签的所有任务"""
        return [task for task in self.tasks.values() if task.has_tag(tag)]
    
    def clear_selection(self) -> None:
        """清空所有任务的选择状态，但保留顺序信息"""
        for task in self.tasks.values():
            task.is_selected = False
            # 移除这行代码，保留任务顺序信息
            # task.order = 0 