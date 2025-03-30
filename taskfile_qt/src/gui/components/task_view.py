#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                             QPushButton, QLabel, QGridLayout, QMenu, QFrame,
                             QSizePolicy, QApplication, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal

from src.gui.components.notion_card import NotionTaskCard
from src.gui.components.tag_editor import NotionStyleTagEditor, DIALOG_ACCEPTED

class TaskView(QWidget):
    """任务视图组件，负责展示和管理任务卡片"""
    
    selectionChanged = pyqtSignal()  # 任务选择变化信号
    tagEdited = pyqtSignal()         # 标签编辑完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.task_collection = None
        self.current_filter_tag = None
        self.task_cards = {}  # 存储任务卡片的引用
        self.sort_mode = "name"  # 默认排序模式
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 工具栏区域
        toolbar_layout = QHBoxLayout()
        
        # 左侧区域
        left_layout = QHBoxLayout()
        self.tasks_label = QLabel("可用任务:")
        self.tasks_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.tasks_label)
        
        toolbar_layout.addLayout(left_layout)
        toolbar_layout.addStretch()
        
        # 右侧区域
        right_layout = QHBoxLayout()
        
        # 排序选择
        sort_label = QLabel("排序:")
        
        self.sort_by_name_btn = QPushButton("按名称")
        self.sort_by_name_btn.setCheckable(True)
        self.sort_by_name_btn.setChecked(True)
        self.sort_by_name_btn.clicked.connect(lambda: self.change_sort_mode("name"))
        
        self.sort_by_desc_btn = QPushButton("按描述")
        self.sort_by_desc_btn.setCheckable(True)
        self.sort_by_desc_btn.clicked.connect(lambda: self.change_sort_mode("description"))
        
        self.sort_default_btn = QPushButton("默认")
        self.sort_default_btn.setCheckable(True)
        self.sort_default_btn.clicked.connect(lambda: self.change_sort_mode("default"))
        
        # 组织成按钮组
        self.sort_buttons = [self.sort_by_name_btn, self.sort_by_desc_btn, self.sort_default_btn]
        for btn in self.sort_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 4px 8px;
                    background-color: #f8f8f8;
                    border: 1px solid #d0d0d0;
                    border-radius: 0px;
                }
                QPushButton:checked {
                    background-color: #2980b9;
                    color: white;
                    border: 1px solid #2573a7;
                }
                QPushButton:hover:!checked {
                    background-color: #e8e8e8;
                }
            """)
        
        # 设置按钮连接左右边框
        self.sort_by_name_btn.setStyleSheet(self.sort_by_name_btn.styleSheet() + """
            QPushButton {
                border-top-left-radius: 3px;
                border-bottom-left-radius: 3px;
                border-right: none;
            }
        """)
        
        self.sort_default_btn.setStyleSheet(self.sort_default_btn.styleSheet() + """
            QPushButton {
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                border-left: none;
            }
        """)
        
        # 操作按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_visible)
        
        self.clear_btn = QPushButton("清空选择")
        self.clear_btn.clicked.connect(self.clear_selection)
        
        right_layout.addWidget(sort_label)
        right_layout.addWidget(self.sort_by_name_btn)
        right_layout.addWidget(self.sort_by_desc_btn)
        right_layout.addWidget(self.sort_default_btn)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.select_all_btn)
        right_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addLayout(right_layout)
        
        main_layout.addLayout(toolbar_layout)
        
        # 任务卡片区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # 任务卡片容器
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: #f5f5f5;
            border-radius: 4px;
        """)
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)
        
        scroll_area.setWidget(self.container)
        main_layout.addWidget(scroll_area)
    
    def set_task_collection(self, task_collection):
        """设置任务集合"""
        self.task_collection = task_collection
        self.populate_tasks()
    
    def filter_by_tag(self, tag):
        """按标签筛选任务"""
        self.current_filter_tag = tag
        self.populate_tasks()
    
    def change_sort_mode(self, mode):
        """改变排序模式"""
        # 更新按钮状态
        for btn in self.sort_buttons:
            btn.setChecked(False)
        
        if mode == "name":
            self.sort_by_name_btn.setChecked(True)
        elif mode == "description":
            self.sort_by_desc_btn.setChecked(True)
        else:  # default
            self.sort_default_btn.setChecked(True)
        
        self.sort_mode = mode
        self.refresh_layout()
    
    def populate_tasks(self):
        """填充所有任务卡片"""
        if not self.task_collection:
            return
        
        # 清除现有卡片
        self.clear_cards()
        
        # 创建任务卡片
        for task in self.task_collection.get_all_tasks():
            # 根据当前筛选标签过滤
            if self.current_filter_tag and not task.has_tag(self.current_filter_tag):
                continue
                
            card = NotionTaskCard(task)
            card.checkStateChanged.connect(self._on_card_selection_changed)
            card.rightClicked.connect(lambda pos, t=task: self._show_context_menu(pos, t))
            
            self.task_cards[task.name] = card
        
        # 更新UI布局
        self.refresh_layout()
    
    def refresh_layout(self):
        """刷新布局"""
        # 清除网格布局中的所有卡片
        self._clear_grid()
        
        # 获取应该显示的任务卡片
        visible_cards = list(self.task_cards.values())
        
        # 根据排序模式排序
        if self.sort_mode == "name":
            visible_cards.sort(key=lambda card: card.task.name.lower())
        elif self.sort_mode == "description":
            visible_cards.sort(key=lambda card: card.task.description.lower())
        # 默认不排序
        
        # 重新添加到网格布局
        cards_per_row = 2  # 一行显示的卡片数
        for i, card in enumerate(visible_cards):
            row = i // cards_per_row
            col = i % cards_per_row
            self.grid_layout.addWidget(card, row, col)
    
    def _clear_grid(self):
        """清除网格布局"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                self.grid_layout.removeWidget(item.widget())
    
    def clear_cards(self):
        """清除所有卡片"""
        # 删除字典中的所有卡片
        for card in self.task_cards.values():
            card.deleteLater()
        
        self.task_cards.clear()
        self._clear_grid()
    
    def _on_card_selection_changed(self, checked):
        """当卡片选择状态改变时"""
        if checked:
            # 如果选中，更新任务的order值为当前最大值+1
            max_order = -1
            for task in self.task_collection.get_all_tasks():
                if task.is_selected and task.order > max_order:
                    max_order = task.order
            
            # 找到对应的任务并更新order值
            sender_card = self.sender()
            if sender_card and hasattr(sender_card, 'task'):
                sender_card.task.order = max_order + 1
        
        # 发出选择变化信号
        self.selectionChanged.emit()
    
    def _show_context_menu(self, position, task):
        """显示右键菜单"""
        menu = QMenu()
        edit_tags_action = menu.addAction("编辑标签")
        
        # 获取点击的卡片
        sender = self.sender()
        if not sender:
            return
        
        # 显示菜单
        action = menu.exec(sender.mapToGlobal(position))
        
        # 处理菜单动作
        if action == edit_tags_action:
            self._edit_task_tags(task)
    
    def _edit_task_tags(self, task):
        """编辑任务标签"""
        # 获取所有标签
        all_tags = self.task_collection.get_all_tags()
        
        # 创建并显示标签编辑对话框
        dialog = NotionStyleTagEditor(task, all_tags, self)
        if dialog.exec() == DIALOG_ACCEPTED:
            # 更新任务卡片显示
            card = self.task_cards.get(task.name)
            if card:
                card.update_tags()
            
            # 发出标签编辑完成信号
            self.tagEdited.emit()
    
    def select_all_visible(self):
        """选择所有可见任务"""
        for card in self.task_cards.values():
            card.set_selected(True)
        
        # 发出选择变化信号
        self.selectionChanged.emit()
    
    def clear_selection(self):
        """清空选择"""
        for card in self.task_cards.values():
            card.set_selected(False)
        
        # 清空任务模型中的选择状态
        if self.task_collection:
            self.task_collection.clear_selection()
        
        # 发出选择变化信号
        self.selectionChanged.emit() 