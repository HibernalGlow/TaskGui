import sys
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from .core import exit, run

def create_image():
    """创建托盘图标的图像"""
    width = 64
    height = 64
    color1 = "#000000"
    color2 = "#ffffff"

    image = Image.new("RGB", (width, height), color1)
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
        fill=color2,
    )
    return image

def on_exit(icon, item):
    """退出应用"""
    icon.stop()
    try:
        exit.stop_streamlit()
    except Exception as e:
        print(f"退出应用时出错: {str(e)}")
        # 确保应用能够退出，即使 stop_streamlit 失败
        import os
        os._exit(0)

def on_restart(icon, item):
    """重启应用"""
    icon.stop()
    try:
        run.main()
    except Exception as e:
        print(f"重启应用时出错: {str(e)}")
        # 尝试重新启动
        main()

def on_open(icon, item):
    """打开应用"""
    try:
        run.main()
    except Exception as e:
        print(f"打开应用时出错: {str(e)}")

def start_tray():
    """启动托盘图标"""
    try:
        menu = Menu(
            MenuItem("打开", on_open),
            MenuItem("重启", on_restart),
            MenuItem("退出", on_exit),
        )
        icon = Icon("TaskGui", create_image(), "TaskGui", menu)
        icon.run()
    except Exception as e:
        print(f"托盘初始化出错: {str(e)}")

def main():
    """处理命令行参数并调用相应函数"""
    # 启动托盘图标线程
    tray_thread = threading.Thread(target=start_tray, daemon=True)
    tray_thread.start()

    # 检查是否提供了子命令
    if len(sys.argv) > 1 and sys.argv[1] == 'exit':
        # 删除子命令，这样exit.stop_streamlit()就不会将其视为参数
        sys.argv.pop(1)
        try:
            exit.stop_streamlit()
        except Exception as e:
            print(f"退出应用时出错: {str(e)}")
    else:
        # 默认行为是启动应用
        try:
            run.main()
        except Exception as e:
            print(f"启动应用时出错: {str(e)}")

if __name__ == "__main__":
    main()