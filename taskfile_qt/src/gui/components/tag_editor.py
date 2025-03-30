#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCompleter, QWidget,
                             QScrollArea, QFrame, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QFontMetrics

# 定义对话框结果常量，与PyQt5兼容
DIALOG_ACCEPTED = 1  # 对应QDialog.Accepted的值

class TagBadge(QFrame):
    """Notion风格的标签徽章"""
    
    removed = pyqtSignal(str)  # 标签移除信号
    
    # 预定义的标签颜色 (Notion风格)
    TAG_COLORS = [
        ("#e8e8e8", "#505050"),  # 灰色
        ("#ffd3ba", "#95591e"),  # 棕色
        ("#fdecc8", "#886c00"),  # 黄色
        ("#dbeddb", "#1c7c43"),  # 绿色
        ("#d3e5ef", "#0b6bcb"),  # 蓝色
        ("#e8deee", "#6940a5"),  # 紫色
        ("#f5e0e9", "#ad1a72"),  # 粉色
        ("#ffd8d8", "#c11c1c"),  # 红色
    ]
    
    def __init__(self, tag_name, parent=None):
        super().__init__(parent)
        self.tag_name = tag_name
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # 设置标签文本
        self.label = QLabel(self.tag_name)
        
        # 根据标签文本生成一个稳定的颜色
        color_index = hash(self.tag_name) % len(self.TAG_COLORS)
        bg_color, text_color = self.TAG_COLORS[color_index]
        
        # 设置标签样式
        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 3px;
            padding: 2px;
        """)
        
        # 删除按钮
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(16, 16)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {text_color};
                border: none;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: #ff6b6b;
            }}
        """)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._remove_tag)
        
        layout.addWidget(self.label)
        layout.addWidget(self.delete_btn)
    
    def _remove_tag(self):
        """删除标签"""
        self.removed.emit(self.tag_name)
    
    def sizeHint(self):
        """提供尺寸提示"""
        width = self.label.sizeHint().width() + self.delete_btn.sizeHint().width() + 20
        height = max(self.label.sizeHint().height(), self.delete_btn.sizeHint().height()) + 4
        return QSize(width, height)

class NotionStyleTagEditor(QDialog):
    """Notion风格的标签编辑器对话框"""
    
    def __init__(self, task, all_tags, parent=None):
        super().__init__(parent)
        self.task = task
        self.all_tags = all_tags
        self.selected_tags = list(task.tags)  # 复制一份，避免直接修改
        
        self.setWindowTitle(f"编辑 {task.name} 的标签")
        self.setMinimumSize(450, 350)
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        
        # 标签输入区域
        input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("添加标签... 按回车添加多个")
        self.tag_input.returnPressed.connect(self._add_tag_from_input)
        
        # 添加自动完成
        if self.all_tags:
            completer = QCompleter(list(self.all_tags))
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.tag_input.setCompleter(completer)
        
        input_layout.addWidget(self.tag_input)
        main_layout.addLayout(input_layout)
        
        # 已选标签区域
        selected_label = QLabel("已选标签:")
        main_layout.addWidget(selected_label)
        
        # 使用滚动区域放置标签容器
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("background-color: white; border: 1px solid #dcdcdc;")
        
        # 标签容器
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.tags_layout.setContentsMargins(5, 5, 5, 5)
        self.tags_layout.setSpacing(5)
        self.tags_layout.addStretch()
        
        scroll_area.setWidget(self.tags_container)
        main_layout.addWidget(scroll_area)
        
        # 所有可用标签的快速选择区域
        available_label = QLabel("所有可用标签:")
        main_layout.addWidget(available_label)
        
        # 可用标签容器
        all_tags_scroll = QScrollArea()
        all_tags_scroll.setWidgetResizable(True)
        all_tags_scroll.setStyleSheet("background-color: white; border: 1px solid #dcdcdc;")
        
        all_tags_container = QWidget()
        all_tags_layout = QHBoxLayout(all_tags_container)
        all_tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        all_tags_layout.setContentsMargins(5, 5, 5, 5)
        all_tags_layout.setSpacing(5)
        
        # 填充所有可用标签
        for tag in sorted(self.all_tags):
            if tag not in self.selected_tags:
                tag_btn = QPushButton(tag)
                tag_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f7f7f7;
                        border: 1px solid #e0e0e0;
                        border-radius: 3px;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        background-color: #e8e8e8;
                    }
                """)
                tag_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                tag_btn.clicked.connect(lambda checked, t=tag: self._add_tag(t))
                all_tags_layout.addWidget(tag_btn)
        
        all_tags_layout.addStretch()
        all_tags_scroll.setWidget(all_tags_container)
        main_layout.addWidget(all_tags_scroll)
        
        # 底部按钮区域
        buttons_layout = QHBoxLayout()
        
        apply_btn = QPushButton("应用")
        apply_btn.setStyleSheet("background-color: #2ecc71; color: white; padding: 5px 15px;")
        apply_btn.clicked.connect(self._apply_changes)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # 填充已选择的标签
        self._refresh_selected_tags()
        
        # 设置焦点到输入框
        self.tag_input.setFocus()
    
    def _refresh_selected_tags(self):
        """刷新已选择的标签显示"""
        # 清除现有标签
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item.widget() and not isinstance(item.widget(), QLabel):
                item.widget().deleteLater()
        
        # 重新添加标签
        for tag in self.selected_tags:
            tag_badge = TagBadge(tag)
            tag_badge.removed.connect(self._remove_tag)
            # 在倒数第一个位置（stretch前）添加
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, tag_badge)
    
    def _add_tag_from_input(self):
        """从输入框添加标签"""
        tag = self.tag_input.text().strip()
        if tag and tag not in self.selected_tags:
            self._add_tag(tag)
        
        self.tag_input.clear()
    
    def _add_tag(self, tag):
        """添加一个标签"""
        if tag and tag not in self.selected_tags:
            self.selected_tags.append(tag)
            self._refresh_selected_tags()
    
    def _remove_tag(self, tag):
        """移除一个标签"""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
            self._refresh_selected_tags()
    
    def _apply_changes(self):
        """应用更改"""
        # 更新任务的标签
        self.task.tags.clear()
        self.task.tags.extend(self.selected_tags)
        # 使用done()方法并传入我们定义的常量，而不是使用accept()
        self.done(DIALOG_ACCEPTED)

# 测试代码
if __name__ == "__main__":
    import sys
    from src.models.task import Task
    
    app = QApplication(sys.argv)
    
    # 创建一个测试任务
    task = Task("test_task", [], "测试任务", "")
    task.tags = ["python", "gui", "test"]
    
    # 所有可用标签
    all_tags = {"python", "gui", "test", "development", "widget", "dialog", "qt"}
    
    dialog = NotionStyleTagEditor(task, all_tags)
    result = dialog.exec()
    
    if result == DIALOG_ACCEPTED:  # 使用自定义常量
        print("更新后的标签:", task.tags)
    
    sys.exit(0) 