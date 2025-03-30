#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                            QTextEdit, QMessageBox, QCheckBox, QScrollArea,
                            QGridLayout, QComboBox, QSizePolicy, QToolBar, QApplication,
                            QListWidget, QDialog, QLineEdit, QListWidgetItem, QFrame,
                            QGroupBox, QRadioButton, QButtonGroup, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QCursor

from src.gui.components.task_card import TaskCardWidget
from src.core.parser import TaskfileParser
from src.core.config import ConfigManager
from src.utils.command import CommandGenerator

class TagDialog(QDialog):
    """标签编辑对话框"""
    
    def __init__(self, task, all_tags, parent=None):
        super().__init__(parent)
        self.task = task
        self.all_tags = all_tags
        self.setWindowTitle(f"编辑标签 - {task.name}")
        self.setMinimumSize(400, 300)
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 当前标签列表
        current_group = QGroupBox("当前标签")
        current_layout = QVBoxLayout()
        self.current_tags_list = QListWidget()
        self.current_tags_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._populate_current_tags()
        remove_button = QPushButton("移除选中的标签")
        remove_button.clicked.connect(self._remove_selected_tag)
        
        current_layout.addWidget(self.current_tags_list)
        current_layout.addWidget(remove_button)
        current_group.setLayout(current_layout)
        
        # 添加新标签
        add_group = QGroupBox("添加标签")
        add_layout = QVBoxLayout()
        
        # 输入新标签
        add_new_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("输入新标签名称...")
        add_new_button = QPushButton("添加")
        add_new_button.clicked.connect(self._add_new_tag)
        add_new_layout.addWidget(self.new_tag_input)
        add_new_layout.addWidget(add_new_button)
        
        # 从现有标签中选择
        existing_group = QGroupBox("从现有标签中选择")
        existing_layout = QVBoxLayout()
        self.existing_tags_list = QListWidget()
        self._populate_existing_tags()
        add_existing_button = QPushButton("添加选中的标签")
        add_existing_button.clicked.connect(self._add_existing_tag)
        
        existing_layout.addWidget(self.existing_tags_list)
        existing_layout.addWidget(add_existing_button)
        existing_group.setLayout(existing_layout)
        
        add_layout.addLayout(add_new_layout)
        add_layout.addWidget(existing_group)
        add_group.setLayout(add_layout)
        
        # 确定/取消按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addWidget(current_group)
        layout.addWidget(add_group)
        layout.addLayout(buttons_layout)
    
    def _populate_current_tags(self):
        """填充当前标签列表"""
        self.current_tags_list.clear()
        for tag in self.task.tags:
            self.current_tags_list.addItem(tag)
    
    def _populate_existing_tags(self):
        """填充现有标签列表，排除当前任务已有的标签"""
        self.existing_tags_list.clear()
        for tag in sorted(self.all_tags):
            if tag not in self.task.tags:
                self.existing_tags_list.addItem(tag)
    
    def _remove_selected_tag(self):
        """移除选中的标签"""
        selected_items = self.current_tags_list.selectedItems()
        if not selected_items:
            return
            
        tag = selected_items[0].text()
        self.task.remove_tag(tag)
        self._populate_current_tags()
        self._populate_existing_tags()
    
    def _add_new_tag(self):
        """添加新标签"""
        tag = self.new_tag_input.text().strip()
        if not tag:
            return
            
        self.task.add_tag(tag)
        self.new_tag_input.clear()
        self._populate_current_tags()
        self._populate_existing_tags()
    
    def _add_existing_tag(self):
        """添加选中的现有标签"""
        selected_items = self.existing_tags_list.selectedItems()
        if not selected_items:
            return
            
        tag = selected_items[0].text()
        self.task.add_tag(tag)
        self._populate_current_tags()
        self._populate_existing_tags()

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
        
        # 标签筛选
        self.active_tag_filter = None  # 当前激活的标签筛选
        
        # 设置窗口属性
        self.setWindowTitle("任务文件解析器")
        self.setMinimumSize(800, 600)
        
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
        
        # 标签工具栏 - 显示所有可用标签的按钮
        self.tags_toolbar = QFrame()
        self.tags_toolbar.setFrameShape(QFrame.Shape.StyledPanel)
        self.tags_toolbar_layout = QHBoxLayout(self.tags_toolbar)
        self.tags_toolbar_layout.setContentsMargins(5, 5, 5, 5)
        self.tags_toolbar_layout.setSpacing(5)
        
        # 添加标签标题
        toolbar_label = QLabel("快速标签筛选:")
        toolbar_label.setStyleSheet("font-weight: bold;")
        self.tags_toolbar_layout.addWidget(toolbar_label)
        
        # 添加"显示全部"按钮
        all_button = QPushButton("显示全部")
        all_button.setCheckable(True)
        all_button.setChecked(True)
        all_button.clicked.connect(lambda: self.quick_filter_by_tag(None))
        self.all_tags_button = all_button
        self.tags_toolbar_layout.addWidget(all_button)
        
        # 标签管理
        self.manage_tags_button = QPushButton("管理标签组")
        self.manage_tags_button.clicked.connect(self.manage_tag_groups)
        
        self.tags_toolbar_layout.addStretch()
        self.tags_toolbar_layout.addWidget(self.manage_tags_button)
        
        main_layout.addWidget(self.tags_toolbar)
        
        # 任务列表和命令预览
        content_layout = QHBoxLayout()
        
        # 侧边栏布局 - 用于标签筛选
        sidebar_layout = QVBoxLayout()
        tags_label = QLabel("按标签筛选:")
        self.tags_list = QListWidget()
        self.tags_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.tags_list.itemClicked.connect(self.filter_by_tag)
        
        # 添加"显示全部"选项
        self.show_all_item = QListWidgetItem("显示全部")
        self.show_all_item.setData(Qt.ItemDataRole.UserRole, "all")
        self.tags_list.addItem(self.show_all_item)
        
        # 添加分隔线
        separator_item = QListWidgetItem("")
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)
        separator_item.setBackground(QColor(200, 200, 200))
        self.tags_list.addItem(separator_item)
        
        sidebar_layout.addWidget(tags_label)
        sidebar_layout.addWidget(self.tags_list)
        
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
        
        # 将侧边栏和任务卡片区域放入水平布局
        tasks_container_layout = QHBoxLayout()
        tasks_container_layout.addLayout(sidebar_layout, 1)  # 侧边栏占比较小
        tasks_container_layout.addLayout(tasks_layout, 3)    # 任务卡片区域占比较大
        
        content_layout.addLayout(tasks_container_layout, 2)  # 任务部分占整体的2/3
        
        # 命令预览
        command_layout = QVBoxLayout()
        command_label = QLabel("命令预览:")
        self.command_preview = QTextEdit()
        self.command_preview.setReadOnly(True)
        
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_preview)
        
        content_layout.addLayout(command_layout, 1)  # 命令预览占整体的1/3
        
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
    
    def populate_tags_list(self):
        """填充标签列表"""
        # 保留"显示全部"和分隔线
        current_count = self.tags_list.count()
        for i in range(current_count - 2, -1, -1):
            self.tags_list.takeItem(2)
        
        if not self.task_collection:
            return
            
        # 获取所有标签并排序
        all_tags = sorted(self.task_collection.get_all_tags())
        
        # 添加标签到列表
        for tag in all_tags:
            item = QListWidgetItem(tag)
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tags_list.addItem(item)
        
        # 选中"显示全部"
        self.tags_list.setCurrentItem(self.show_all_item)
    
    def populate_tags_toolbar(self):
        """填充标签工具栏"""
        # 清除现有的标签按钮，保留标签标题和管理按钮
        for i in range(self.tags_toolbar_layout.count() - 1, 1, -1):
            item = self.tags_toolbar_layout.itemAt(i)
            if item.widget() and item.widget() != self.manage_tags_button:
                item.widget().deleteLater()
        
        if not self.task_collection:
            return
        
        # 获取所有标签
        all_tags = sorted(self.task_collection.get_all_tags())
        
        # 重置当前选中按钮
        self.all_tags_button.setChecked(self.active_tag_filter is None)
        
        # 添加标签按钮
        for tag in all_tags:
            tag_button = QPushButton(tag)
            tag_button.setCheckable(True)
            tag_button.setChecked(self.active_tag_filter == tag)
            tag_button.clicked.connect(lambda checked, t=tag: self.quick_filter_by_tag(t))
            
            # 在全部按钮和管理按钮之间插入新按钮
            self.tags_toolbar_layout.insertWidget(
                self.tags_toolbar_layout.count() - 2,  # 在倒数第二个位置插入
                tag_button
            )
    
    def quick_filter_by_tag(self, tag):
        """通过工具栏按钮快速筛选标签"""
        # 更新所有按钮状态
        for i in range(self.tags_toolbar_layout.count()):
            item = self.tags_toolbar_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton):
                button = item.widget()
                if button == self.all_tags_button:
                    button.setChecked(tag is None)
                elif button != self.manage_tags_button and button.text() == tag:
                    button.setChecked(True)
                elif button != self.manage_tags_button:
                    button.setChecked(False)
        
        # 更新当前标签筛选
        self.active_tag_filter = tag
        
        # 更新标签列表选择
        if tag is None:
            self.tags_list.setCurrentItem(self.show_all_item)
        else:
            for i in range(self.tags_list.count()):
                item = self.tags_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == tag:
                    self.tags_list.setCurrentItem(item)
                    break
        
        # 刷新任务卡片显示
        self.populate_task_cards()
        
        # 更新状态栏
        if tag is None:
            self.statusBar().showMessage("显示所有任务", 3000)
        else:
            self.statusBar().showMessage(f"筛选标签: {tag}", 3000)
    
    def manage_tag_groups(self):
        """管理标签组"""
        QMessageBox.information(self, "标签组管理", "此功能将在未来版本中提供，敬请期待！")
    
    def filter_by_tag(self, item):
        """根据标签筛选任务"""
        tag_data = item.data(Qt.ItemDataRole.UserRole)
        
        # 更新当前标签筛选
        if tag_data == "all":
            self.active_tag_filter = None
            self.statusBar().showMessage("显示所有任务", 3000)
        else:
            self.active_tag_filter = tag_data
            self.statusBar().showMessage(f"筛选标签: {tag_data}", 3000)
        
        # 更新工具栏按钮状态
        self.populate_tags_toolbar()
        
        # 刷新任务卡片显示
        self.populate_task_cards()
    
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
            self.populate_tags_list()
            self.populate_tags_toolbar()
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
        
        # 如果有标签筛选，先应用筛选
        if self.active_tag_filter:
            tasks = [task for task in tasks if task.has_tag(self.active_tag_filter)]
        
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
        
        # 获取任务列表
        tasks = self.task_collection.get_all_tasks()
        
        # 如果有标签筛选，应用筛选
        if self.active_tag_filter:
            tasks = [task for task in tasks if task.has_tag(self.active_tag_filter)]
        
        # 创建卡片
        for task in tasks:
            card = TaskCardWidget(task.name, task.description, task.tags)
            card.checkbox.toggled.connect(lambda checked, t=task.name: self.task_card_selection_changed(t, checked))
            
            # 添加右键菜单
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(lambda pos, t=task.name: self.show_task_context_menu(pos, t))
            
            self.task_cards[task.name] = card
        
        # 按当前排序模式排序并显示
        self.sort_task_cards()
    
    def show_task_context_menu(self, position, task_name):
        """显示任务卡片的右键菜单"""
        task = self.task_collection.get_task(task_name)
        if not task:
            return
        
        menu = QMenu()
        edit_tags_action = menu.addAction("编辑标签")
        
        # 显示标签菜单在卡片位置
        card = self.task_cards.get(task_name)
        if not card:
            return
            
        action = menu.exec(card.mapToGlobal(position))
        if action == edit_tags_action:
            self.edit_task_tags(task)
    
    def edit_task_tags(self, task):
        """编辑任务标签"""
        # 获取所有标签
        all_tags = self.task_collection.get_all_tags()
        
        # 创建并显示标签编辑对话框
        dialog = TagDialog(task, all_tags, self)
        result = dialog.exec()
        
        # 如果用户确认编辑，刷新相关界面并保存更改
        if result == QDialog.DialogCode.Accepted:
            # 重新填充标签列表
            self.populate_tags_list()
            # 更新工具栏
            self.populate_tags_toolbar()
            # 刷新任务卡片
            self.populate_task_cards()
            # 保存更改到Taskfile.yml
            self.save_taskfile()
    
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
        
        # 选中所有可见卡片 (考虑标签筛选)
        visible_tasks = set()
        for task_name, card in self.task_cards.items():
            card.set_selected(True)
            visible_tasks.add(task_name)
        
        # 选中所有可见任务模型
        for task in self.task_collection.get_all_tasks():
            if task.name in visible_tasks:
                task.is_selected = True
        
        # 更新UI状态
        self.update_command()
        self.statusBar().showMessage("已选择所有可见任务", 3000)
    
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
    
    def save_taskfile(self):
        """保存任务文件"""
        if not self.task_collection or not self.current_taskfile_path:
            return False
            
        try:
            # 读取原始文件
            with open(self.current_taskfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 逐个更新任务的标签
            for task in self.task_collection.get_all_tasks():
                # 准备标签字符串
                tag_strings = []
                for tag in task.tags:
                    tag_strings.append(f"'{tag}'")
                tags_str = f"tags: [{', '.join(tag_strings)}]"
                
                if task.tags:
                    # 查找任务定义区域
                    task_pattern = r'(' + re.escape(task.name) + r':.*?)\n(\s+)tags:.*?\n'
                    
                    # 如果找到现有的tags行，替换它
                    if re.search(task_pattern, content, re.DOTALL):
                        replacement = r'\1\n\2' + tags_str + r'\n'
                        content = re.sub(task_pattern, replacement, content)
                    else:
                        # 如果没找到，在desc行后添加
                        desc_pattern = r'(' + re.escape(task.name) + r':.*?\n(\s+)desc:.*?\n)'
                        match = re.search(desc_pattern, content, re.DOTALL)
                        if match:
                            indent = match.group(2)
                            replacement = r'\1' + indent + tags_str + r'\n'
                            content = re.sub(desc_pattern, replacement, content)
            
            # 写回文件
            with open(self.current_taskfile_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.statusBar().showMessage("标签已保存到Taskfile.yml", 3000)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
            return False 