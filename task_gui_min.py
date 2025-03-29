#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QListWidget, QListWidgetItem, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard

from task_parser_min import TaskfileParser, CommandGenerator

class TaskGUIMin(QMainWindow):
    """最小功能实现的任务GUI界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化解析器
        self.parser = TaskfileParser()
        self.task_collection = None
        self.command_generator = None
        self.current_taskfile_path = None
        
        # 设置窗口属性
        self.setWindowTitle("任务文件解析器")
        self.setMinimumSize(600, 400)
        
        # 初始化界面
        self._init_ui()
        
    def _init_ui(self):
        """初始化界面"""
        # 创建中央小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 文件选择布局
        file_layout = QHBoxLayout()
        file_label = QLabel("任务文件:")
        self.file_path_label = QLabel("未选择文件")
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_button)
        
        main_layout.addLayout(file_layout)
        
        # 任务列表和命令预览
        content_layout = QHBoxLayout()
        
        # 任务列表
        tasks_layout = QVBoxLayout()
        tasks_label = QLabel("可用任务:")
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.task_list.itemSelectionChanged.connect(self.update_command)
        
        tasks_layout.addWidget(tasks_label)
        tasks_layout.addWidget(self.task_list)
        
        content_layout.addLayout(tasks_layout)
        
        # 命令预览
        command_layout = QVBoxLayout()
        command_label = QLabel("命令预览:")
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_preview)
        
        content_layout.addLayout(command_layout)
        content_layout.setStretch(0, 1)  # 任务列表
        content_layout.setStretch(1, 1)  # 命令预览
        
        main_layout.addLayout(content_layout)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        
        # 复制命令按钮
        self.copy_button = QPushButton("复制命令")
        self.copy_button.clicked.connect(self.copy_command)
        self.copy_button.setEnabled(False)
        
        # 执行按钮
        self.execute_button = QPushButton("执行任务")
        self.execute_button.clicked.connect(self.execute_command)
        self.execute_button.setEnabled(False)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.execute_button)
        
        main_layout.addLayout(buttons_layout)
    
    def browse_file(self):
        """浏览并打开任务文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择任务文件", 
            "", 
            "YAML Files (*.yml *.yaml);;All Files (*)"
        )
        
        if file_path:
            try:
                # 解析任务文件
                self.task_collection = self.parser.parse_file(file_path)
                self.current_taskfile_path = file_path
                self.command_generator = CommandGenerator(self.task_collection, self.current_taskfile_path)
                
                # 更新界面
                self.file_path_label.setText(os.path.basename(file_path))
                self.populate_task_list()
                self.update_command()
                self.execute_button.setEnabled(True)
                self.copy_button.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法解析任务文件: {str(e)}")
    
    def populate_task_list(self):
        """填充任务列表"""
        self.task_list.clear()
        
        if not self.task_collection:
            return
        
        for task in self.task_collection.get_all_tasks():
            item = QListWidgetItem(f"{task.name} - {task.description}")
            item.setData(Qt.ItemDataRole.UserRole, task.name)
            self.task_list.addItem(item)
    
    def update_command(self):
        """更新命令预览"""
        if not self.task_collection or not self.command_generator:
            return
        
        # 更新任务选择状态
        for task in self.task_collection.get_all_tasks():
            task.is_selected = False
            task.order = 0
        
        # 获取选中项
        selected_items = self.task_list.selectedItems()
        for i, item in enumerate(selected_items):
            task_name = item.data(Qt.ItemDataRole.UserRole)
            task = self.task_collection.get_task(task_name)
            if task:
                task.is_selected = True
                task.order = i
        
        # 生成命令
        command = self.command_generator.generate_command()
        self.command_preview.setText(command)
        
        # 更新复制按钮状态
        has_tasks = bool(self.task_collection.get_selected_tasks())
        self.copy_button.setEnabled(has_tasks)
    
    def copy_command(self):
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
        
        # 显示提示
        self.statusBar().showMessage("命令已复制到剪贴板", 3000)
    
    def execute_command(self):
        """执行命令"""
        if not self.command_generator:
            return
        
        # 检查是否有选中的任务
        if not self.task_collection.get_selected_tasks():
            QMessageBox.information(self, "提示", "没有选择任何任务")
            return
        
        # 执行命令
        success, output = self.command_generator.execute_command()
        
        # 显示结果
        if success:
            QMessageBox.information(self, "成功", "任务执行成功:\n" + output)
        else:
            QMessageBox.critical(self, "错误", "任务执行失败:\n" + output)

def main():
    app = QApplication(sys.argv)
    window = TaskGUIMin()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 