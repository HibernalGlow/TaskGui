#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Taskfile GUI主程序
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# 添加项目根目录到路径

from src.gui.notion_main_window import NotionMainWindow

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")  # 使用Fusion风格，在所有平台上较为一致
    
    # 设置应用信息
    app.setApplicationName("TaskfileQt")
    app.setApplicationDisplayName("Taskfile管理器")
    app.setApplicationVersion("2.0.0")
    
    # 创建主窗口
    window = NotionMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 