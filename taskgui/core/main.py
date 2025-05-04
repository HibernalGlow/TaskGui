import os
import sys
import gc
import time
import psutil
import atexit

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块化组件
from taskgui.ui.config import setup_page_config
from taskgui.ui.styles import apply_custom_css, add_clipboard_js
from taskgui.app import main
from taskgui.utils.selection_utils import get_memory_usage, run_gc, clear_memory_cache

# 内存管理配置
MEMORY_CHECK_INTERVAL = 60  # 内存检查间隔（秒）
MEMORY_WARNING_THRESHOLD = 80  # 内存警告阈值（百分比）
MEMORY_CRITICAL_THRESHOLD = 90  # 内存危险阈值（百分比）

# 上次内存检查时间
last_memory_check = 0

def check_memory_usage():
    """检查内存使用情况并在必要时执行清理"""
    global last_memory_check
    
    current_time = time.time()
    if current_time - last_memory_check < MEMORY_CHECK_INTERVAL:
        return
    
    last_memory_check = current_time
    
    try:
        # 获取内存使用情况
        memory_usage = get_memory_usage()
        
        # 如果内存使用率超过警告阈值，执行垃圾回收
        if memory_usage["percent"] > MEMORY_WARNING_THRESHOLD:
            print(f"内存使用率较高 ({memory_usage['percent']:.2f}%)，执行垃圾回收")
            run_gc()
        
        # 如果内存使用率超过危险阈值，执行更激进的清理
        if memory_usage["percent"] > MEMORY_CRITICAL_THRESHOLD:
            print(f"内存使用率危险 ({memory_usage['percent']:.2f}%)，执行内存清理")
            clear_memory_cache()
            gc.collect(2)  # 使用更激进的垃圾回收
            
            # 再次检查内存使用情况
            memory_usage = get_memory_usage()
            print(f"清理后内存使用: {memory_usage['rss']:.2f} MB ({memory_usage['percent']:.2f}%)")
    except Exception as e:
        print(f"检查内存使用情况时出错: {str(e)}")

def cleanup_resources():
    """程序退出时清理资源"""
    try:
        print("正在清理资源...")
        clear_memory_cache()
        gc.collect(2)
        
        # 获取最终内存使用情况
        memory_usage = get_memory_usage()
        print(f"最终内存使用: {memory_usage['rss']:.2f} MB ({memory_usage['percent']:.2f}%)")
    except Exception as e:
        print(f"清理资源时出错: {str(e)}")

# 注册退出处理函数
atexit.register(cleanup_resources)

if __name__ == "__main__":
    # 设置页面配置
    setup_page_config()

    # 应用自定义CSS
    apply_custom_css()

    # 添加剪贴板JS功能
    add_clipboard_js()
    
    # 初始化内存管理
    gc.enable()  # 确保垃圾回收已启用
    
    # 运行主程序
    try:
        # 定期检查内存使用情况
        check_memory_usage()
        
        # 运行主程序
        main()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 程序结束时清理资源
        cleanup_resources()