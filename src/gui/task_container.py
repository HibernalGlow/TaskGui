#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from src.models.task_model import Task
from src.gui.task_block import TaskBlockWidget

class TaskContainerWidget(QScrollArea):
    """任务块容器"""
    
    # 信号定义
    task_selection_changed = pyqtSignal()
    task_order_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置属性
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        
        # 创建内容窗口
        self.container = QWidget()
        self.setWidget(self.container)
        
        # 设置布局
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 初始化任务块列表
        self.task_blocks = []
        self.block_map = {}  # 任务名到小部件的映射
        
        # 添加提示标签
        self.empty_label = QLabel("没有任务，请打开Taskfile")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.empty_label)
    
    def set_tasks(self, tasks):
        """设置任务列表"""
        # 清除现有任务块
        self._clear_tasks()
        
        # 没有任务时显示提示
        if not tasks:
            self.empty_label.setVisible(True)
            return
        
        # 隐藏提示标签
        self.empty_label.setVisible(False)
        
        # 按照order排序任务
        sorted_tasks = sorted(tasks, key=lambda t: t.order)
        
        # 为每个任务创建任务块
        for task in sorted_tasks:
            self.add_task_block(task)
        
        # 更新排序
        self._update_task_orders()
    
    def add_task_block(self, task):
        """添加单个任务块"""
        task_block = TaskBlockWidget(task)
        task_block.selectionChanged.connect(self._on_selection_changed)
        
        self.layout.addWidget(task_block)
        self.task_blocks.append(task_block)
        self.block_map[task.name] = task_block
    
    def _clear_tasks(self):
        """清除所有任务块"""
        for block in self.task_blocks:
            self.layout.removeWidget(block)
            block.deleteLater()
        
        self.task_blocks = []
        self.block_map = {}
    
    def _update_task_orders(self):
        """更新任务顺序"""
        # 遍历所有任务块并更新顺序
        for i, block in enumerate(self.task_blocks):
            block.task.order = i
    
    @pyqtSlot(bool)
    def _on_selection_changed(self, selected):
        """任务选择变化处理"""
        self.task_selection_changed.emit()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件处理"""
        # 只接受来自任务块的拖拽
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放置事件处理"""
        if event.mimeData().hasText():
            # 获取拖拽的任务名
            task_name = event.mimeData().text()
            
            # 找到对应的任务块
            if task_name in self.block_map:
                # 获取落点位置
                drop_pos = event.position().y()
                
                # 找到落点对应的索引
                drop_index = self._find_drop_index(drop_pos)
                
                # 移动任务块
                self._move_task_block(task_name, drop_index)
                
                # 接受拖拽操作
                event.acceptProposedAction()
                
                # 发送顺序变化信号
                self.task_order_changed.emit()
    
    def _find_drop_index(self, y_pos):
        """根据Y坐标找到对应的插入索引"""
        # 遍历所有任务块
        for i, block in enumerate(self.task_blocks):
            # 获取块的位置
            block_top = block.mapToParent(block.rect().topLeft()).y()
            block_bottom = block_top + block.height()
            
            # 如果落在块的上半部分，返回该块的索引
            if block_top <= y_pos <= (block_top + block_bottom) / 2:
                return i
            
            # 如果落在块的下半部分，返回下一个索引
            if (block_top + block_bottom) / 2 < y_pos <= block_bottom:
                return i + 1
        
        # 如果落在所有块的下方，返回最后一个索引
        return len(self.task_blocks)
    
    def _move_task_block(self, task_name, new_index):
        """移动任务块到新位置"""
        # 找到要移动的任务块
        block = self.block_map.get(task_name)
        if not block:
            return
        
        # 获取当前索引
        current_index = self.task_blocks.index(block)
        
        # 如果索引未变，不执行操作
        if current_index == new_index or current_index + 1 == new_index:
            return
        
        # 从布局中移除
        self.layout.removeWidget(block)
        
        # 从列表中移除
        self.task_blocks.pop(current_index)
        
        # 调整目标索引（如果当前索引小于目标索引）
        if current_index < new_index:
            new_index -= 1
        
        # 插入到新位置
        self.task_blocks.insert(new_index, block)
        
        # 重新添加所有任务块
        for i, task_block in enumerate(self.task_blocks):
            self.layout.insertWidget(i, task_block)
        
        # 更新任务顺序
        self._update_task_orders()