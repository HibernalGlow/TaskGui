#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QMessageBox,
                            QStatusBar, QSplitter, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.core.parser import TaskfileParser
from src.core.config import ConfigManager
from src.gui.components.tag_manager import TagManager
from src.gui.components.task_view import TaskView
from src.gui.components.command_panel import CommandPanel

class NotionMainWindow(QMainWindow):
    """Notion风格的任务管理器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化解析器
        self.parser = TaskfileParser()
        self.task_collection = None
        self.current_taskfile_path = None
        
        # 设置窗口属性
        self.setWindowTitle("Taskfile管理器")
        self.setMinimumSize(900, 700)
        
        # 初始化界面
        self._init_ui()
        
        # 加载上次打开的文件
        self.load_last_session()
    
    def _init_ui(self):
        """初始化界面"""
        # 创建中央小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        file_label = QLabel("任务文件:")
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("color: #666;")
        
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_file)
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_button)
        
        main_layout.addLayout(file_layout)
        
        # 内容区域 (使用分割器)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧区域：标签管理器
        self.tag_manager = TagManager()
        self.tag_manager.tagFilterChanged.connect(self._on_tag_filter_changed)
        
        # 中间区域：任务视图
        self.task_view = TaskView()
        self.task_view.selectionChanged.connect(self._on_selection_changed)
        self.task_view.tagEdited.connect(self._on_tag_edited)
        
        # 右侧区域：命令面板
        self.command_panel = CommandPanel()
        self.command_panel.commandExecuted.connect(self._on_command_executed)
        
        # 添加到分割器
        splitter.addWidget(self.tag_manager)
        splitter.addWidget(self.task_view)
        splitter.addWidget(self.command_panel)
        
        # 设置默认大小比例
        splitter.setSizes([200, 450, 250])  # 左侧占20%，中间占45%，右侧占25%
        
        main_layout.addWidget(splitter, 1)  # 分割器占用剩余空间
        
        # 创建状态栏
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("就绪")
    
    def load_last_session(self):
        """加载上次会话"""
        # 加载并行模式设置
        parallel_mode = self.config_manager.get("parallel_mode", False)
        self.command_panel.parallel_checkbox.setChecked(parallel_mode)
        
        # 加载上次打开的文件
        last_file = self.config_manager.get("last_file")
        if last_file and os.path.exists(last_file):
            self.load_taskfile(last_file)
    
    def save_session(self):
        """保存当前会话设置"""
        # 保存并行模式设置
        self.config_manager.set("parallel_mode", self.command_panel.parallel_mode)
        
        # 保存当前文件路径
        if self.current_taskfile_path:
            self.config_manager.set("last_file", self.current_taskfile_path)
        
        # 保存标签管理器的收藏标签
        if hasattr(self.tag_manager, 'favorite_tags'):
            self.config_manager.set("favorite_tags", self.tag_manager.favorite_tags)
    
    def browse_file(self):
        """浏览并选择任务文件"""
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
    
    def load_taskfile(self, file_path):
        """加载任务文件"""
        try:
            # 解析任务文件
            self.task_collection = self.parser.parse_file(file_path)
            self.current_taskfile_path = file_path
            
            # 更新界面
            self.file_path_label.setText(os.path.basename(file_path))
            
            # 更新标签管理器
            self.tag_manager.update_all_tags(self.task_collection.get_all_tags())
            
            # 设置任务视图
            self.task_view.set_task_collection(self.task_collection)
            
            # 设置命令面板
            self.command_panel.set_task_data(self.task_collection, file_path)
            
            # 从配置加载收藏标签
            favorite_tags = self.config_manager.get("favorite_tags", [])
            if favorite_tags:
                self.tag_manager.favorite_tags = favorite_tags
                self.tag_manager._update_quick_filter_buttons()
            
            # 更新状态栏
            self.statusBar().showMessage(f"已加载任务文件: {os.path.basename(file_path)}", 3000)
            
            # 保存到配置
            self.config_manager.set("last_file", file_path)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法解析任务文件: {str(e)}")
            return False
    
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
    
    def _on_tag_filter_changed(self, tag):
        """当标签筛选更改时"""
        self.task_view.filter_by_tag(tag)
        
        if tag:
            self.statusBar().showMessage(f"筛选标签: {tag}", 3000)
        else:
            self.statusBar().showMessage("显示所有任务", 3000)
    
    def _on_selection_changed(self):
        """当任务选择变化时"""
        self.command_panel.update_command()
    
    def _on_tag_edited(self):
        """当标签被编辑时"""
        # 更新标签管理器
        self.tag_manager.update_all_tags(self.task_collection.get_all_tags())
        
        # 保存到文件
        self.save_taskfile()
    
    def _on_command_executed(self, success, output):
        """当命令执行时"""
        if success:
            self.statusBar().showMessage(f"任务执行成功: {output}", 5000)
        else:
            self.statusBar().showMessage("任务执行失败", 3000)
            QMessageBox.critical(self, "错误", f"任务执行失败:\n{output}")
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        # 保存会话设置
        self.save_session()
        event.accept()

# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = NotionMainWindow()
    window.show()
    
    sys.exit(app.exec()) 