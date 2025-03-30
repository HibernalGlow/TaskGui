"""
快速启动任务管理器
无需手动输入streamlit run命令
"""
import os
import subprocess
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")
    
    print("正在启动任务管理器...")
    
    # 构建命令
    cmd = [sys.executable, "-m", "streamlit", "run", main_script, "--server.headless=false"]
    
    # 添加任何传递给此脚本的附加参数
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # 执行命令
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n用户中断了任务管理器")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按任意键退出...")

if __name__ == "__main__":
    main()