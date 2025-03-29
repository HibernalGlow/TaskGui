#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile, QTextStream
from src.gui.main_window import MainWindow

def main():
    """应用程序入口函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 加载暗色主题样式表
    style_file_path = os.path.join(os.path.dirname(__file__), "resources", "styles", "dark.qss")
    if os.path.exists(style_file_path):
        style_file = QFile(style_file_path)
        if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(style_file)
            app.setStyleSheet(stream.readAll())
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
