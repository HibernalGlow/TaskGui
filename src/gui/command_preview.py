#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal

class CommandPreviewWidget(QWidget):
    """命令预览面板"""
    
    # 信号定义
    run_command = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 添加标题
        title_label = QLabel("命令预览")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)
        
        # 添加命令文本框
        self.command_text = QTextEdit()
        self.command_text.setReadOnly(True)
        self.command_text.setMinimumHeight(100)
        main_layout.addWidget(self.command_text)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # 添加复制按钮
        self.copy_button = QPushButton("复制命令")
        self.copy_button.clicked.connect(self._copy_command)
        button_layout.addWidget(self.copy_button)
        
        # 添加运行按钮
        self.run_button = QPushButton("运行命令")
        self.run_button.clicked.connect(self._run_command)
        button_layout.addWidget(self.run_button)
        
        # 初始禁用按钮
        self._update_buttons_state("")
    
    def update_command(self, command):
        """更新命令预览"""
        self.command_text.setText(command)
        self._update_buttons_state(command)
    
    def _update_buttons_state(self, command):
        """更新按钮状态"""
        has_command = bool(command and not command.startswith("#"))
        
        self.copy_button.setEnabled(has_command)
        self.run_button.setEnabled(has_command)
    
    def _copy_command(self):
        """复制命令到剪贴板"""
        QApplication.clipboard().setText(self.command_text.toPlainText())
    
    def _run_command(self):
        """发出运行命令信号"""
        self.run_command.emit()