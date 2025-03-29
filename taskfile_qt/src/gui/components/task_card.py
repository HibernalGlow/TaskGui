#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QFrame, QLabel, QCheckBox, QVBoxLayout, 
                            QHBoxLayout, QSizePolicy)

class TaskCardWidget(QFrame):
    """任务卡片组件"""
    
    def __init__(self, task_name, description, parent=None):
        super().__init__(parent)
        self.task_name = task_name
        self.description = description
        self.is_selected = False
        
        # 设置卡片样式
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 设置卡片布局
        self._init_ui()
    
    def _init_ui(self):
        """初始化卡片UI"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 名称和选择框
        header_layout = QHBoxLayout()
        self.name_label = QLabel(f"<b>{self.task_name}</b>")
        self.name_label.setWordWrap(True)
        self.checkbox = QCheckBox("选择")
        self.checkbox.toggled.connect(self.toggle_selection)
        
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.checkbox)
        layout.addLayout(header_layout)
        
        # 描述
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setWordWrap(True)
            layout.addWidget(self.desc_label)
        
        # 设置最小高度
        self.setMinimumHeight(50)
        
    def toggle_selection(self, checked):
        """切换选择状态"""
        self.is_selected = checked
        self.update_style()
    
    def update_style(self):
        """根据选择状态更新样式"""
        if self.is_selected:
            self.setStyleSheet("background-color: #e0f0ff; border: 1px solid #b0d0f0;")
        else:
            self.setStyleSheet("")
    
    def set_selected(self, selected):
        """设置选择状态"""
        self.is_selected = selected
        self.checkbox.setChecked(selected)
        self.update_style()
    
    def get_selected(self):
        """获取选择状态"""
        return self.is_selected 