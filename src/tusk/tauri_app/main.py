"""
TaskST Tauri应用启动器

这个脚本使用PyTauri创建一个桌面应用，它会启动一个Streamlit服务器作为后端，
然后在WebView窗口中加载这个服务。这样可以将Python的Streamlit应用打包成桌面应用。
"""

import json
import os
import subprocess
import sys
import time
from os import environ
from pathlib import Path
import socket
import signal
import atexit

from anyio.from_thread import start_blocking_portal
from pytauri import BuilderArgs, Commands
from pytauri_wheel.lib import builder_factory, context_factory
from pydantic import BaseModel


# 配置目录
SRC_TAURI_DIR = Path(__file__).parent.absolute()
STREAMLIT_PROCESS = None
STREAMLIT_PORT = None


# 创建命令处理器
commands = Commands()


class PortResponse(BaseModel):
    port: int


@commands.command()
async def start_streamlit_server() -> PortResponse:
    """启动Streamlit服务器，返回服务器端口"""
    global STREAMLIT_PROCESS, STREAMLIT_PORT
    
    # 寻找可用端口
    port = find_available_port(start_port=8501)
    
    if not port:
        raise Exception("无法找到可用端口")
    
    # 获取taskst包的安装路径
    try:
        import taskst
        package_path = Path(taskst.__file__).parent
        print(f"Found taskst package at: {package_path}")
          # 启动Streamlit服务器
        env = os.environ.copy()
        
        # 直接运行taskst包的命令行入口点
        if sys.platform == "win32":
            cmd = [
                "taskst",  # 使用安装的taskst命令
            ]
        else:
            cmd = [
                "taskst",  # 使用安装的taskst命令
            ]

        print(f"Starting Streamlit with command: {' '.join(cmd)}")

        # 启动子进程
        if sys.platform == "win32":
            # Windows平台使用CREATE_NO_WINDOW标志
            STREAMLIT_PROCESS = subprocess.Popen(
                cmd, 
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            STREAMLIT_PROCESS = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
        STREAMLIT_PORT = port
        
        # 注册程序退出时的清理函数
        atexit.register(stop_streamlit_server_impl)
        
        # 返回端口号
        return PortResponse(port=port)
    
    except ImportError:
        raise Exception("找不到taskst包，请确认已正确安装")


@commands.command()
async def stop_streamlit_server() -> PortResponse:
    """停止Streamlit服务器"""
    stop_streamlit_server_impl()
    return PortResponse(port=0)


def stop_streamlit_server_impl():
    """停止Streamlit服务器的实现"""
    global STREAMLIT_PROCESS
    if STREAMLIT_PROCESS:
        print("Stopping Streamlit server...")
        if sys.platform == "win32":
            # Windows下使用taskkill强制终止进程树
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(STREAMLIT_PROCESS.pid)], 
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            # Unix系统发送SIGTERM信号
            try:
                os.killpg(os.getpgid(STREAMLIT_PROCESS.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        STREAMLIT_PROCESS = None


def find_available_port(start_port=8000, max_attempts=100):
    """查找可用端口"""
    port = start_port
    for _ in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            port += 1
    return None


def main() -> int:
    """主函数"""
    # 创建Tauri应用并运行
    with start_blocking_portal("asyncio") as portal:
        app = builder_factory().build(
            BuilderArgs(
                context=context_factory(SRC_TAURI_DIR),
                invoke_handler=commands.generate_handler(portal),
            )
        )
        exit_code = app.run_return()
        
        # 确保Streamlit服务器被正确关闭
        stop_streamlit_server_impl()
        
        return exit_code


if __name__ == "__main__":
    sys.exit(main())
