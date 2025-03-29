#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QListWidget, QListWidgetItem, QTextEdit, QMessageBox,
                            QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard

from task_parser_min import TaskfileParser, CommandGenerator
from config_manager import ConfigManager

class TaskGUIMin(QMainWindow):
    """最小功能实现的任务GUI界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化解析器
        self.parser = TaskfileParser()
        self.task_collection = None
        self.command_generator = None
        self.current_taskfile_path = None
        self.parallel_mode = False
        
        # 设置窗口属性
        self.setWindowTitle("任务文件解析器")
        self.setMinimumSize(600, 400)
        
        # 初始化界面
        self._init_ui()
        
        # 加载上次打开的文件和并行模式设置
        self.load_last_session()
        
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
        
        # 模式选择布局
        mode_layout = QHBoxLayout()
        self.parallel_checkbox = QCheckBox("并行模式")
        self.parallel_checkbox.setToolTip("启用并行模式将同时执行多个任务，而不是按顺序执行")
        self.parallel_checkbox.stateChanged.connect(self.toggle_parallel_mode)
        
        mode_layout.addWidget(self.parallel_checkbox)
        mode_layout.addStretch()
        
        main_layout.addLayout(mode_layout)
        
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
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def load_last_session(self):
        """加载上次会话的设置"""
        # 加载并行模式设置
        parallel_mode = self.config_manager.get("parallel_mode", False)
        self.parallel_mode = parallel_mode
        self.parallel_checkbox.setChecked(parallel_mode)
        
        # 加载上次打开的文件
        last_file = self.config_manager.get("last_file")
        if last_file and os.path.exists(last_file):
            self.load_taskfile(last_file)
            self.statusBar().showMessage(f"已加载上次打开的文件: {os.path.basename(last_file)}", 3000)
    
    def save_session(self):
        """保存当前会话设置"""
        # 保存并行模式设置
        self.config_manager.set("parallel_mode", self.parallel_mode)
        
        # 保存当前文件路径
        if self.current_taskfile_path:
            self.config_manager.set("last_file", self.current_taskfile_path)
    
    def toggle_parallel_mode(self, state):
        """切换并行/串行模式"""
        self.parallel_mode = (state == Qt.CheckState.Checked.value)
        self.update_command()
        
        # 保存设置
        self.config_manager.set("parallel_mode", self.parallel_mode)
        
        if self.parallel_mode:
            self.statusBar().showMessage("并行模式：将同时执行多个任务", 3000)
        else:
            self.statusBar().showMessage("串行模式：将按顺序执行所有任务", 3000)
    
    def load_taskfile(self, file_path):
        """加载指定的任务文件"""
        try:
            # 解析任务文件
            self.task_collection = self.parser.parse_file(file_path)
            self.current_taskfile_path = file_path
            self.command_generator = CommandGenerator(
                self.task_collection, 
                self.current_taskfile_path,
                self.parallel_mode
            )
            
            # 更新界面
            self.file_path_label.setText(os.path.basename(file_path))
            self.populate_task_list()
            self.update_command()
            self.execute_button.setEnabled(True)
            self.copy_button.setEnabled(True)
            
            # 保存到配置
            self.config_manager.set("last_file", file_path)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法解析任务文件: {str(e)}")
            return False
    
    def browse_file(self):
        """浏览并打开任务文件"""
        # 获取上次打开的目录作为起始目录
        start_dir = ""
        if self.current_taskfile_path:
            start_dir = os.path.dirname(self.current_taskfile_path)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择任务文件", 
            start_dir, 
            "YAML Files (*.yml *.yaml);;All Files (*)"
        )
        
        if file_path:
            self.load_taskfile(file_path)
    
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
        if not self.task_collection:
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
        
        # 更新命令生成器的并行模式设置
        if self.command_generator:
            self.command_generator.parallel_mode = self.parallel_mode
        
        # 生成命令
        if self.command_generator:
            command = self.command_generator.generate_command()
            self.command_preview.setText(command)
        
        # 更新复制按钮状态
        has_tasks = self.task_collection and bool(self.task_collection.get_selected_tasks())
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
        self.statusBar().showMessage(f"正在执行任务，请稍候...", 0)
        QApplication.processEvents()  # 刷新界面
        
        success, output = self.command_generator.execute_command()
        
        # 显示结果
        self.statusBar().showMessage("就绪")
        if success:
            QMessageBox.information(self, "成功", "任务执行成功:\n" + output)
        else:
            QMessageBox.critical(self, "错误", "任务执行失败:\n" + output)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存当前会话设置
        self.save_session()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TaskGUIMin()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 