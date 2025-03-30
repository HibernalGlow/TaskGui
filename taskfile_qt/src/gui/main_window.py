#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QTextEdit, QMessageBox, QCheckBox, QScrollArea,
                            QGridLayout, QComboBox, QSizePolicy, QToolBar, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from src.gui.components.task_card import TaskCardWidget
from src.core.parser import TaskfileParser
from src.core.config import ConfigManager
from src.utils.command import CommandGenerator

class MainWindow(QMainWindow):
    """主窗口类"""
    
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
        
        # 任务卡片字典，key为任务名称，value为卡片组件
        self.task_cards = {}
        
        # 排序方式
        self.sort_mode = "name"  # 默认按名称排序
        
        # 设置窗口属性
        self.setWindowTitle("任务文件解析器")
        self.setMinimumSize(700, 500)
        
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
        
        # 任务卡片部分
        tasks_layout = QVBoxLayout()
        
        # 任务列表标题和工具栏
        tasks_header_layout = QHBoxLayout()
        tasks_label = QLabel("可用任务:")
        
        # 排序选择
        sort_label = QLabel("排序方式:")
        self.sort_combobox = QComboBox()
        self.sort_combobox.addItem("按名称排序", "name")
        self.sort_combobox.addItem("按描述排序", "description")
        self.sort_combobox.addItem("默认顺序", "default")
        self.sort_combobox.setCurrentIndex(0)
        self.sort_combobox.currentIndexChanged.connect(self.change_sort_mode)
        
        # 清空选择按钮
        self.clear_selection_button = QPushButton("清空选择")
        self.clear_selection_button.clicked.connect(self.clear_selection)
        self.clear_selection_button.setEnabled(False)
        
        # 全选按钮
        self.select_all_button = QPushButton("全选")
        self.select_all_button.clicked.connect(self.select_all_tasks)
        self.select_all_button.setEnabled(False)
        
        tasks_header_layout.addWidget(tasks_label)
        tasks_header_layout.addStretch()
        tasks_header_layout.addWidget(sort_label)
        tasks_header_layout.addWidget(self.sort_combobox)
        tasks_header_layout.addWidget(self.select_all_button)
        tasks_header_layout.addWidget(self.clear_selection_button)
        
        tasks_layout.addLayout(tasks_header_layout)
        
        # 创建滚动区域和网格布局用于显示任务卡片
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.task_container = QWidget()
        self.task_grid = QGridLayout(self.task_container)
        self.task_grid.setSpacing(10)
        
        self.scroll_area.setWidget(self.task_container)
        tasks_layout.addWidget(self.scroll_area)
        
        content_layout.addLayout(tasks_layout)
        
        # 命令预览
        command_layout = QVBoxLayout()
        command_label = QLabel("命令预览:")
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_preview)
        
        content_layout.addLayout(command_layout)
        content_layout.setStretch(0, 2)  # 任务列表占比更大
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
        # 加载排序模式
        sort_mode = self.config_manager.get("sort_mode", "name")
        self.sort_mode = sort_mode
        index = self.sort_combobox.findData(sort_mode)
        if index >= 0:
            self.sort_combobox.setCurrentIndex(index)
        
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
        # 保存排序模式
        self.config_manager.set("sort_mode", self.sort_mode)
        
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
            self.populate_task_cards()
            self.update_command()
            self.execute_button.setEnabled(False)
            self.copy_button.setEnabled(False)
            self.clear_selection_button.setEnabled(False)
            self.select_all_button.setEnabled(True)
            
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
    
    def change_sort_mode(self, index):
        """切换排序模式"""
        self.sort_mode = self.sort_combobox.currentData()
        self.config_manager.set("sort_mode", self.sort_mode)
        if self.task_collection:
            self.sort_task_cards()
    
    def sort_task_cards(self):
        """根据当前排序模式对任务卡片进行排序"""
        # 清除当前的网格布局中的所有卡片
        self._clear_task_grid()
        
        # 获取所有任务
        tasks = self.task_collection.get_all_tasks()
        
        # 根据排序模式排序
        if self.sort_mode == "name":
            tasks = sorted(tasks, key=lambda t: t.name.lower())
        elif self.sort_mode == "description":
            tasks = sorted(tasks, key=lambda t: t.description.lower())
        # 默认模式不排序，使用原有顺序
        
        # 将排序后的卡片重新添加到网格布局
        cards_per_row = 2  # 一行显示的卡片数
        for i, task in enumerate(tasks):
            row = i // cards_per_row
            col = i % cards_per_row
            card = self.task_cards.get(task.name)
            if card:
                self.task_grid.addWidget(card, row, col)
        
        # 更新命令预览
        self.update_command()
    
    def _clear_task_grid(self):
        """清除任务网格布局中的所有卡片"""
        # 移除但不删除卡片
        for i in reversed(range(self.task_grid.count())):
            item = self.task_grid.itemAt(i)
            if item.widget():
                self.task_grid.removeWidget(item.widget())
    
    def populate_task_cards(self):
        """填充任务卡片"""
        # 先清除现有卡片
        self.task_cards.clear()
        self._clear_task_grid()
        
        if not self.task_collection:
            return
        
        # 创建卡片
        for task in self.task_collection.get_all_tasks():
            card = TaskCardWidget(task.name, task.description)
            card.checkbox.toggled.connect(lambda checked, t=task.name: self.task_card_selection_changed(t, checked))
            self.task_cards[task.name] = card
        
        # 按当前排序模式排序并显示
        self.sort_task_cards()
    
    def task_card_selection_changed(self, task_name, is_selected):
        """当任务卡片选择状态变化时更新命令预览"""
        if not self.task_collection:
            return
        
        task = self.task_collection.get_task(task_name)
        if task:
            task.is_selected = is_selected
            
            # 如果是选中操作，更新order为当前最大order + 1
            # 这样确保任务执行顺序与用户选择顺序一致
            if is_selected:
                # 获取当前最大order值
                max_order = -1
                for t in self.task_collection.get_all_tasks():
                    if t.is_selected and t.order > max_order:
                        max_order = t.order
                
                # 设置当前任务的order为最大值+1
                task.order = max_order + 1
                print(f"设置任务 {task.name} 的顺序为 {task.order}")
        
        # 更新命令预览
        self.update_command()
    
    def select_all_tasks(self):
        """选择所有任务"""
        if not self.task_collection:
            return
        
        # 选中所有卡片
        for card in self.task_cards.values():
            card.set_selected(True)
        
        # 选中所有任务模型
        for task in self.task_collection.get_all_tasks():
            task.is_selected = True
        
        # 更新UI状态
        self.update_command()
        self.statusBar().showMessage("已选择所有任务", 3000)
    
    def clear_selection(self):
        """清空选择"""
        if not self.task_collection:
            return
        
        # 取消所有卡片的选择
        for card in self.task_cards.values():
            card.set_selected(False)
        
        # 清空任务模型中的选择状态
        self.task_collection.clear_selection()
        
        # 更新UI状态
        self.update_command()
        self.statusBar().showMessage("已清空选择", 3000)
    
    def update_command(self):
        """更新命令预览"""
        if not self.task_collection or not self.command_generator:
            return
        
        # 更新命令生成器的并行模式设置
        self.command_generator.parallel_mode = self.parallel_mode
        
        # 更新任务顺序
        self._update_task_order()
        
        # 生成命令
        command = self.command_generator.generate_command()
        self.command_preview.setText(command)
        
        # 更新按钮状态
        has_tasks = bool(self.task_collection.get_selected_tasks())
        self.copy_button.setEnabled(has_tasks)
        self.execute_button.setEnabled(has_tasks)
        self.clear_selection_button.setEnabled(has_tasks)
    
    def _update_task_order(self):
        """更新任务执行顺序（仅影响UI显示，不影响执行顺序）"""
        # 获取所有选中的任务
        selected_tasks = []
        for task in self.task_collection.get_all_tasks():
            if task.is_selected:
                selected_tasks.append(task)
                
        # 打印当前任务选择顺序（调试用）
        print("当前选中的任务顺序:")
        for task in selected_tasks:
            print(f"  任务: {task.name}, 顺序: {task.order}")
        
        # 排序模式现在只影响UI显示，不再重新分配order值
        # 这样保证命令执行时按照点击顺序执行
        
        # 对于UI排序，我们创建一个副本并进行排序
        ui_sorted_tasks = list(selected_tasks)
        if self.sort_mode == "name":
            ui_sorted_tasks = sorted(ui_sorted_tasks, key=lambda t: t.name.lower())
        elif self.sort_mode == "description":
            ui_sorted_tasks = sorted(ui_sorted_tasks, key=lambda t: t.description.lower())
        
        # 更新UI上的显示顺序，但不改变实际的task.order值
        # 仅用于UI显示，代码中不做任何更改
    
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
        
        # 不再清空选择状态
        # for card in self.task_cards.values():
        #     card.set_selected(False)
        
        # 更新UI状态 - 继续更新命令预览
        self.update_command()
        
        # 显示结果
        if success:
            self.statusBar().showMessage(f"已启动任务: {output}", 5000)
        else:
            self.statusBar().showMessage("任务启动失败", 3000)
            QMessageBox.critical(self, "错误", "任务执行失败:\n" + output)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存当前会话设置
        self.save_session()
        event.accept() 