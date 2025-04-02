import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块化组件
from src.ui.config import setup_page_config
from src.ui.styles import apply_custom_css, add_clipboard_js
from src.app import main

if __name__ == "__main__":
# 设置页面配置
    setup_page_config()

    # 应用自定义CSS
    apply_custom_css()

    # 添加剪贴板JS功能
    add_clipboard_js()
    
    # 运行主程序
    main()