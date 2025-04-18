#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLabel, QApplication, QMessageBox,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal

from src.utils.command import CommandGenerator

class CommandPanel(QWidget):
    """命令面板组件，用于显示和执行命令"""
    
    commandExecuted = pyqtSignal(bool, str)  # 命令执行信号，参数为成功状态和输出
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.task_collection = None
        self.taskfile_path = None
        self.command_generator = None
        self.parallel_mode = False
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("命令预览:")
        title_label.setStyleSheet("font-weight: bold;")
        
        # 模式切换
        self.parallel_checkbox = QCheckBox("并行模式")
        self.parallel_checkbox.setToolTip("启用并行模式将同时执行多个任务，而不是按顺序执行")
        self.parallel_checkbox.toggled.connect(self._on_parallel_mode_changed)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.parallel_checkbox)
        
        main_layout.addLayout(title_layout)
        
        # 命令预览区域
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        self.command_preview.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-family: monospace;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.command_preview)
        
        # 操作按钮区域
        buttons_layout = QHBoxLayout()
        
        self.copy_button = QPushButton("复制命令")
        self.copy_button.clicked.connect(self._copy_command)
        self.copy_button.setEnabled(False)
        
        self.execute_button = QPushButton("执行任务")
        self.execute_button.clicked.connect(self._execute_command)
        self.execute_button.setEnabled(False)
        self.execute_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: 1px solid #27ae60;
                border-radius: 3px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                border: 1px solid #7f8c8d;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.execute_button)
        
        main_layout.addLayout(buttons_layout)
    
    def set_task_data(self, task_collection, taskfile_path):
        """设置任务数据"""
        self.task_collection = task_collection
        self.taskfile_path = taskfile_path
        self.command_generator = CommandGenerator(
            self.task_collection,
            self.taskfile_path,
            self.parallel_mode
        )
        
        # 更新命令预览
        self.update_command()
    
    def update_command(self):
        """更新命令预览"""
        if not self.task_collection or not self.command_generator:
            return
        
        # 生成命令
        command = self.command_generator.generate_command()
        self.command_preview.setText(command)
        
        # 更新按钮状态
        has_tasks = bool(self.task_collection.get_selected_tasks())
        self.copy_button.setEnabled(has_tasks)
        self.execute_button.setEnabled(has_tasks)
    
    def _on_parallel_mode_changed(self, checked):
        """并行模式改变"""
        self.parallel_mode = checked
        
        if self.command_generator:
            self.command_generator.parallel_mode = checked
            self.update_command()
    
    def _copy_command(self):
        """复制命令到剪贴板"""
        if not self.command_generator:
            return
        
        # 检查是否有选中的任务
        if not self.task_collection.get_selected_tasks():
            QMessageBox.information(self, "提示", "没有选择任何任务")
            return
        
        # 获取命令
        command = self.command_generator.generate_command()
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(command)
        
        # 发出信号
        self.commandExecuted.emit(True, "命令已复制到剪贴板")
    
    def _execute_command(self):
        """执行命令"""
        if not self.command_generator:
            return
        
        # 检查是否有选中的任务
        if not self.task_collection.get_selected_tasks():
            QMessageBox.information(self, "提示", "没有选择任何任务")
            return
        
        # 执行命令
        success, output = self.command_generator.execute_command()
        
        # 发出信号
        self.commandExecuted.emit(success, output) 