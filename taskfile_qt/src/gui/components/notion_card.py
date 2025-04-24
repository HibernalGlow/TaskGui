#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                            QCheckBox, QSizePolicy, QWidget, QMenu, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

from src.gui.components.tag_editor import TagBadge

class NotionTaskCard(QFrame):
    """Notion风格的任务卡片"""
    
    checkStateChanged = pyqtSignal(bool)  # 选择状态改变信号
    rightClicked = pyqtSignal(object)     # 右键点击信号，传递点击位置
    
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.is_selected = False
        
        # 设置卡片样式和行为
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet("""
            NotionTaskCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            NotionTaskCard:hover {
                border: 1px solid #c0c0c0;
                background-color: #f9f9f9;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(80)
        
        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        
        # 顶部区域：任务名称和选择框
        top_layout = QHBoxLayout()
        
        # 选择框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.is_selected)
        self.checkbox.toggled.connect(self._on_selection_changed)
        
        # 任务名称
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        
        self.name_label = QLabel(self.task.name)
        self.name_label.setFont(name_font)
        self.name_label.setWordWrap(True)
        
        top_layout.addWidget(self.checkbox)
        top_layout.addWidget(self.name_label, 1)
        
        main_layout.addLayout(top_layout)
        
        # 中部区域：任务描述
        if self.task.description:
            desc_layout = QHBoxLayout()
            desc_layout.setContentsMargins(20, 0, 0, 0)  # 左侧缩进
            
            self.desc_label = QLabel(self.task.description)
            self.desc_label.setWordWrap(True)
            self.desc_label.setStyleSheet("color: #505050;")
            
            desc_layout.addWidget(self.desc_label)
            main_layout.addLayout(desc_layout)
        
        # 底部区域：标签
        if self.task.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setContentsMargins(20, 0, 0, 0)  # 左侧缩进
            
            # 创建标签容器
            tags_container = QWidget()
            tags_flow = QHBoxLayout(tags_container)
            tags_flow.setContentsMargins(0, 0, 0, 0)
            tags_flow.setSpacing(4)
            
            # 添加标签
            for tag in self.task.tags:
                tag_badge = TagBadge(tag)
                # 禁用删除按钮
                tag_badge.findChild(QPushButton).hide()
                tags_flow.addWidget(tag_badge)
            
            tags_flow.addStretch()
            tags_layout.addWidget(tags_container)
            main_layout.addLayout(tags_layout)
        
        # 更新选择状态
        self.set_selected(self.task.is_selected)
    
    def _on_selection_changed(self, checked):
        """当选择状态改变时"""
        self.is_selected = checked
        self.task.is_selected = checked
        self._update_style()
        self.checkStateChanged.emit(checked)
    
    def _update_style(self):
        """更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                NotionTaskCard {
                    background-color: #f0f7ff;
                    border: 1px solid #b3d9ff;
                    border-radius: 4px;
                }
                NotionTaskCard:hover {
                    border: 1px solid #80bfff;
                    background-color: #e5f0ff;
                }
            """)
        else:
            self.setStyleSheet("""
                NotionTaskCard {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }
                NotionTaskCard:hover {
                    border: 1px solid #c0c0c0;
                    background-color: #f9f9f9;
                }
            """)
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        self.rightClicked.emit(position)
    
    def set_selected(self, selected):
        """设置选择状态"""
        self.is_selected = selected
        self.task.is_selected = selected
        self.checkbox.setChecked(selected)
        self._update_style()
    
    def update_tags(self):
        """更新标签显示"""
        # 重新构建UI
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._init_ui() 