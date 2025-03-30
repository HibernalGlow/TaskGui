#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                             QPushButton, QLabel, QMenu, QInputDialog, QDialog,
                             QListWidget, QListWidgetItem, QCheckBox, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

from src.gui.components.tag_editor import TagBadge

class FavoriteTagsEditor(QDialog):
    """收藏标签编辑对话框"""
    
    def __init__(self, all_tags, favorite_tags, parent=None):
        super().__init__(parent)
        self.all_tags = sorted(all_tags)
        self.favorite_tags = list(favorite_tags)
        
        self.setWindowTitle("编辑快速筛选标签")
        self.setMinimumSize(400, 300)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 说明标签
        help_label = QLabel("选择要添加到快速筛选栏的标签:")
        layout.addWidget(help_label)
        
        # 标签列表
        self.tags_list = QListWidget()
        
        # 添加所有标签
        for tag in self.all_tags:
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if tag in self.favorite_tags:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.tags_list.addItem(item)
        
        layout.addWidget(self.tags_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def get_selected_tags(self):
        """获取选中的标签"""
        selected = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

class TagManager(QWidget):
    """标签管理器组件"""
    
    tagFilterChanged = pyqtSignal(str)  # 标签筛选变化信号，参数为标签名或None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.all_tags = set()
        self.favorite_tags = []  # 用户收藏的标签
        self.current_tag = None  # 当前筛选标签
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 快速筛选区域 (水平滚动)
        quick_filter_label = QLabel("快速筛选:")
        quick_filter_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(quick_filter_label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(50)  # 限制高度
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
        """)
        
        # 标签按钮容器
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(5, 5, 5, 5)
        self.tags_layout.setSpacing(8)
        
        # 添加"显示全部"按钮
        self.all_button = QPushButton("显示全部")
        self.all_button.setCheckable(True)
        self.all_button.setChecked(True)
        self.all_button.clicked.connect(lambda: self.filter_by_tag(None))
        self.all_button.setStyleSheet("""
            QPushButton {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:checked {
                background-color: #2980b9;
                color: white;
                border: 1px solid #2573a7;
            }
            QPushButton:hover:!checked {
                background-color: #d0d0d0;
            }
        """)
        
        self.tags_layout.addWidget(self.all_button)
        
        # 添加管理按钮
        self.manage_button = QPushButton("管理")
        self.manage_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f8f8;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.manage_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_button.clicked.connect(self._show_tag_management)
        
        # 添加空白占位
        self.tags_layout.addStretch()
        self.tags_layout.addWidget(self.manage_button)
        
        self.scroll_area.setWidget(self.tags_container)
        layout.addWidget(self.scroll_area)
        
        # 添加标签列表区域 (垂直滚动)
        all_tags_label = QLabel("所有标签:")
        all_tags_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(all_tags_label)
        
        self.all_tags_list = QListWidget()
        self.all_tags_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e5f0ff;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.all_tags_list.itemClicked.connect(self._on_tag_list_clicked)
        
        layout.addWidget(self.all_tags_list)
    
    def _on_tag_list_clicked(self, item):
        """当点击标签列表项时"""
        tag = item.data(Qt.ItemDataRole.UserRole)
        self.filter_by_tag(tag)
    
    def _show_tag_management(self):
        """显示标签管理对话框"""
        dialog = FavoriteTagsEditor(self.all_tags, self.favorite_tags, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.favorite_tags = dialog.get_selected_tags()
            self._update_quick_filter_buttons()
    
    def _update_quick_filter_buttons(self):
        """更新快速筛选按钮"""
        # 清除当前按钮（保留显示全部和管理按钮）
        for i in reversed(range(1, self.tags_layout.count() - 2)):
            item = self.tags_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加收藏的标签按钮
        for tag in self.favorite_tags:
            btn = QPushButton(tag)
            btn.setCheckable(True)
            btn.setChecked(self.current_tag == tag)
            btn.clicked.connect(lambda checked, t=tag: self.filter_by_tag(t))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e8e8e8;
                    border: 1px solid #d0d0d0;
                    border-radius: 3px;
                    padding: 4px 8px;
                }
                QPushButton:checked {
                    background-color: #2980b9;
                    color: white;
                    border: 1px solid #2573a7;
                }
                QPushButton:hover:!checked {
                    background-color: #d0d0d0;
                }
            """)
            
            # 在占位符前插入
            self.tags_layout.insertWidget(self.tags_layout.count() - 2, btn)
    
    def update_all_tags(self, tags):
        """更新所有标签"""
        self.all_tags = set(tags)
        self._update_tag_list()
        self._update_quick_filter_buttons()
    
    def _update_tag_list(self):
        """更新标签列表"""
        self.all_tags_list.clear()
        
        # 添加"显示全部"选项
        all_item = QListWidgetItem("显示全部")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        all_item.setBackground(QColor(240, 240, 240))
        self.all_tags_list.addItem(all_item)
        
        # 添加分隔线
        separator = QListWidgetItem()
        separator.setFlags(Qt.ItemFlag.NoItemFlags)
        separator.setBackground(QColor(220, 220, 220))
        self.all_tags_list.addItem(separator)
        
        # 添加所有标签
        for tag in sorted(self.all_tags):
            item = QListWidgetItem(tag)
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.all_tags_list.addItem(item)
    
    def filter_by_tag(self, tag):
        """根据标签筛选"""
        # 更新当前标签
        self.current_tag = tag
        
        # 更新按钮状态
        self.all_button.setChecked(tag is None)
        
        for i in range(1, self.tags_layout.count() - 2):  # 跳过第一个和最后两个
            btn = self.tags_layout.itemAt(i).widget()
            if isinstance(btn, QPushButton):
                btn.setChecked(btn.text() == tag)
        
        # 更新列表选中项
        for i in range(self.all_tags_list.count()):
            item = self.all_tags_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == tag:
                self.all_tags_list.setCurrentItem(item)
                break
        
        # 发出信号
        self.tagFilterChanged.emit(tag) 