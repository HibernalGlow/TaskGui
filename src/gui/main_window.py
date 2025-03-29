#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QSplitter, 
                             QMessageBox, QStatusBar, QToolBar)
from PyQt6.QtCore import Qt, pyqtSlot, QEvent
from PyQt6.QtGui import QIcon, QAction, QCloseEvent

from src.core.parser import TaskfileParser
from src.core.command_generator import CommandGenerator
from src.models.task_model import TaskCollection
from src.gui.task_container import TaskContainerWidget
from src.gui.command_preview import CommandPreviewWidget
from src.utils.file_watcher import FileWatcher
from src.utils.config_manager import ConfigManager

class MainWindow(QMainWindow):
    """应用主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化组件
        self.parser = TaskfileParser()
        self.task_collection = TaskCollection()
        self.command_generator = CommandGenerator(self.task_collection)
        self.file_watcher = None
        self.current_file = None
        self.config_manager = ConfigManager()
        
        # 设置窗口属性
        self.setWindowTitle("Taskfile GUI")
        self.setMinimumSize(800, 600)
        
        # 初始化界面
        self._init_ui()
        
        # 加载上次打开的文件
        self.load_last_file()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建中央小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建任务容器
        self.task_container = TaskContainerWidget()
        # 确保这里的信号名称匹配 TaskContainerWidget 中的信号
        self.task_container.task_selection_changed.connect(self._on_task_selection_changed)
        self.task_container.task_order_changed.connect(self._on_task_order_changed)
        splitter.addWidget(self.task_container)
        
        # 创建命令预览区域
        self.command_preview = CommandPreviewWidget()
        self.command_preview.run_command.connect(self._on_run_command)
        splitter.addWidget(self.command_preview)
        
        # 设置分割器比例
        splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 打开文件动作
        open_action = QAction("打开Taskfile", self)
        open_action.triggered.connect(self.open_taskfile)
        toolbar.addAction(open_action)
        
        # 刷新动作
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_taskfile)
        toolbar.addAction(refresh_action)
    
    def load_last_file(self):
        """加载上次打开的文件"""
        last_file = self.config_manager.get("last_file")
        if last_file and os.path.exists(last_file):
            self.load_taskfile(last_file)
    
    def load_taskfile(self, file_path):
        """加载指定的Taskfile"""
        try:
            # 解析Taskfile
            self.task_collection = self.parser.parse_file(file_path)
            self.command_generator = CommandGenerator(self.task_collection)
            
            # 更新任务容器
            self.task_container.set_tasks(self.task_collection.get_all_tasks())
            
            # 更新命令预览
            self.command_preview.update_command("")
            
            # 设置当前文件并启动文件监控
            self.current_file = file_path
            if self.file_watcher:
                self.file_watcher.stop()
            self.file_watcher = FileWatcher(file_path)
            self.file_watcher.file_changed.connect(self.refresh_taskfile)
            self.file_watcher.start()
            
            # 保存到最近使用文件
            self.config_manager.set("last_file", file_path)
            
            # 更新窗口标题
            self.setWindowTitle(f"Taskfile GUI - {os.path.basename(file_path)}")
            
            # 更新状态栏
            self.status_bar.showMessage(f"已加载: {os.path.basename(file_path)}")
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法解析Taskfile: {str(e)}")
            return False
    
    @pyqtSlot()
    def open_taskfile(self):
        """打开Taskfile"""
        # 获取上次打开的目录
        last_dir = os.path.dirname(self.current_file) if self.current_file else ""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Taskfile", 
            last_dir, 
            "YAML Files (*.yml *.yaml);;All Files (*)"
        )
        
        if file_path:
            self.load_taskfile(file_path)
    
    @pyqtSlot()
    def refresh_taskfile(self):
        """刷新当前Taskfile"""
        if not self.current_file:
            return
        
        try:
            # 保存当前选择状态
            selected_tasks = {task.name: task.is_selected for task in self.task_collection.get_all_tasks()}
            task_orders = {task.name: task.order for task in self.task_collection.get_all_tasks()}
            
            # 重新解析文件
            self.task_collection = self.parser.parse_file(self.current_file)
            self.command_generator = CommandGenerator(self.task_collection)
            
            # 恢复选择状态
            for task in self.task_collection.get_all_tasks():
                if task.name in selected_tasks:
                    task.is_selected = selected_tasks[task.name]
                if task.name in task_orders:
                    task.order = task_orders[task.name]
            
            # 更新任务容器
            self.task_container.set_tasks(self.task_collection.get_all_tasks())
            
            # 更新命令预览
            self._update_command_preview()
            
            # 更新状态栏
            self.status_bar.showMessage(f"已刷新: {os.path.basename(self.current_file)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新Taskfile失败: {str(e)}")
    
    @pyqtSlot()
    def _on_task_selection_changed(self):
        """当任务选择变化时更新命令预览"""
        self._update_command_preview()
    
    @pyqtSlot()
    def _on_task_order_changed(self):
        """当任务顺序变化时更新命令预览"""
        self._update_command_preview()
    
    def _update_command_preview(self):
        """更新命令预览"""
        command = self.command_generator.generate_command()
        print(f"生成的命令: {command}")
        self.command_preview.update_command(command)  
          
    @pyqtSlot()
    def _on_run_command(self):
        """运行命令"""
        if not self.task_collection.get_selected_tasks():
            QMessageBox.information(self, "提示", "没有选择任何任务")
            return
        
        success, output = self.command_generator.execute_command()
        
        if success:
            QMessageBox.information(self, "成功", "命令执行成功:\n" + output)
        else:
            QMessageBox.critical(self, "错误", "命令执行失败:\n" + output)
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        # 保存当前文件路径
        if self.current_file:
            self.config_manager.set("last_file", self.current_file)
        
        # 停止文件监控
        if self.file_watcher:
            self.file_watcher.stop()
        
        # 接受关闭事件
        event.accept()