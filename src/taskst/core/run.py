"""
快速启动任务管理器
无需手动输入streamlit run命令
使用 -noterm 参数可以隐藏终端窗口
如果端口被占用，返回退出状态码1
"""
import os
import subprocess
import sys
import platform
import socket
import time

def check_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=2042, max_attempts=10):
    """查找可用端口，从起始端口开始尝试"""
    port = start_port
    for _ in range(max_attempts):
        if not check_port_in_use(port):
            return port
        port += 1
    # 如果尝试了max_attempts个端口后仍未找到可用端口，返回None
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    
    # 查找可用端口
    port = find_available_port(start_port=2042)
    if port is None:
        print(f"无法找到可用端口，请检查网络设置或关闭占用端口的应用。")
        sys.exit(1)  # 返回状态码1表示无法启动
    
    print("正在启动任务管理器...")
    
    # 检查是否有 -noterm 参数
    hide_terminal = "-noterm" in sys.argv
    if hide_terminal:
        # 如果有 -noterm 参数，从参数列表中删除，不传递给 streamlit
        sys.argv.remove("-noterm")
      # 构建命令
    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        main_script, 
        "--server.headless=true", 
        "--browser.serverAddress=localhost",
        "--server.runOnSave=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        f"--server.port={port}",
        # 添加选项以解决事件循环问题
        "--browser.gatherUsageStats=false"
    ]
    
    # 添加任何传递给此脚本的附加参数（除了已处理的 -noterm）
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
      # 执行命令
    try:
        if platform.system() == "Windows":
            # 添加环境变量以解决asyncio事件循环问题
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.dirname(os.path.dirname(script_dir))
            
            # 在Windows上尝试使用管理员权限运行
            try:
                # 首先正常尝试运行
                if hide_terminal:
                    # 使用CREATE_NO_WINDOW标志在Windows上隐藏控制台窗口
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    process = subprocess.Popen(
                        cmd, 
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        env=env
                    )
                else:
                    # 显示终端窗口
                    process = subprocess.Popen(cmd, env=env)
                
                # 短暂等待，确保服务启动
                time.sleep(2)
                
                # 再次检查端口，如果仍未启动则退出
                if not check_port_in_use(port):
                    print("服务启动失败，可能需要管理员权限")
                    # 尝试以其他端口启动
                    port = find_available_port(start_port=port+1000)
                    if port is not None:
                        print(f"尝试使用备用端口 {port}")
                        cmd[-1] = f"--server.port={port}"
                        process = subprocess.Popen(cmd, env=env)
                        time.sleep(2)
                        
                        # 再次检查端口
                        if check_port_in_use(port):
                            print(f"服务已在端口 {port} 启动")
                        else:
                            print(f"服务启动失败，请以管理员身份运行或检查网络设置")
                            sys.exit(2)  # 返回状态码2表示启动失败
                    else:
                        print("无法找到可用端口，启动失败")
                        sys.exit(2)
            except Exception as inner_e:
                print(f"启动时出现错误: {inner_e}")
                sys.exit(2)
        else:
            # 非Windows平台使用默认方式启动
            process = subprocess.Popen(cmd)
            time.sleep(2)
            
            if not check_port_in_use(port):
                print("服务启动失败")
                sys.exit(2)
                
    except Exception as e:
        print(f"启动失败: {e}")
        input("按任意键退出...")
        sys.exit(2)
    
    # 正常启动
    sys.exit(0)

if __name__ == "__main__":
    main()