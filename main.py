#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir
from src.gui.main_window import MainWindow

def main():
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用样式
    style_path = os.path.join(QDir.currentPath(), "resources", "styles", "dark_theme.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()