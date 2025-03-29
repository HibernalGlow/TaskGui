#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QCheckBox, QPushButton, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QMouseEvent, QColor, QPalette, QPainter, QPen

from src.models.task_model import Task

class DragHandle(QWidget):
    """Notion风格的左侧拖动把手"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(20)
        self.setStyleSheet("""
            background-color: transparent;
        """)
        self._hovered = False
    
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制垂直线条（在hover时才显示）
        if self._hovered:
            painter.setPen(QPen(QColor(150, 150, 150), 2))
            center_x = self.width() // 2
            # 绘制三条短线
            for i in range(3):
                y_pos = self.height() // 2 - 10 + i * 10
                painter.drawLine(center_x, y_pos, center_x, y_pos + 6)

class TaskBlockWidget(QWidget):
    """可拖拽的任务块组件"""
    
    # 信号定义
    selectionChanged = pyqtSignal(bool)
    
    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.drag_start_position = None
        self.is_dragging = False
        
        # 设置样式
        self.setAutoFillBackground(True)
        self._update_background()
        
        # 允许接收拖放
        self.setAcceptDrops(True)
        
        # 初始化UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 10, 5)
        
        # 添加左侧拖动把手
        self.drag_handle = DragHandle()
        main_layout.addWidget(self.drag_handle)
        
        # 添加选择框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task.is_selected)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        main_layout.addWidget(self.checkbox)
        
        # 添加内容布局
        content_layout = QVBoxLayout()
        main_layout.addLayout(content_layout)
        
        # 添加任务名称
        name_label = QLabel(f"<b>{self.task.name}</b>")
        content_layout.addWidget(name_label)
        
        # 添加任务描述（如果有）
        if self.task.description:
            desc_label = QLabel(self.task.description)
            desc_label.setWordWrap(True)
            content_layout.addWidget(desc_label)
        
        # 添加命令预览
        if self.task.command:
            cmd_text = " ".join(self.task.command) if isinstance(self.task.command, list) else self.task.command
            cmd_preview = QLabel(f"<i>$ {cmd_text}</i>")
            cmd_preview.setStyleSheet("color: #888888;")
            content_layout.addWidget(cmd_preview)
        
        # 添加依赖信息（如果有）
        if self.task.depends:
            deps_text = "依赖: " + ", ".join(self.task.depends)
            deps_label = QLabel(deps_text)
            deps_label.setStyleSheet("color: #888888;")
            content_layout.addWidget(deps_label)
        
        # 为了让内容占据更多空间
        main_layout.addStretch(1)
    
    def _on_checkbox_changed(self, state):
        """复选框状态变化处理"""
        self.task.is_selected = (state == Qt.CheckState.Checked)
        self._update_background()
        self.selectionChanged.emit(self.task.is_selected)
    
    def _update_background(self):
        """根据选择状态更新背景色"""
        palette = self.palette()
        if self.task.is_selected:
            palette.setColor(QPalette.ColorRole.Window, QColor(220, 240, 220))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        self.setPalette(palette)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件处理"""
        # 检查是否在拖动把手上按下
        if event.button() == Qt.MouseButton.LeftButton and self.drag_handle.geometry().contains(event.position().toPoint()):
            self.drag_start_position = event.position()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件处理，实现拖拽"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if not self.drag_start_position:
            return
            
        # 计算移动距离
        distance = (event.position() - self.drag_start_position).manhattanLength()
        
        # 如果移动距离足够，开始拖拽
        if distance >= 10 and not self.is_dragging:
            self.is_dragging = True
            self._start_drag()
            self.is_dragging = False
        
        super().mouseMoveEvent(event)
    
    def _start_drag(self):
        """开始拖拽操作"""
        # 创建拖拽对象
        drag = QDrag(self)
        
        # 创建MIME数据
        mime_data = QMimeData()
        mime_data.setText(self.task.name)
        drag.setMimeData(mime_data)
        
        # 设置拖拽时的视觉反馈
        drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))
        
        # 执行拖拽
        drag.exec(Qt.DropAction.MoveAction)