import os
import subprocess

def stop_streamlit():
    try:
        # 查找占用2042端口的进程
        result = subprocess.check_output(
            'netstat -ano | findstr :2042 | findstr LISTENING', 
            shell=True, 
            text=True
        )
        
        # 解析PID
        for line in result.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5:
                pid = parts[4]
                print(f"找到进程ID: {pid}，正在终止...")
                
                # 终止进程
                subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                print(f"已成功终止进程 {pid}")
                
        return True
    except subprocess.CalledProcessError:
        print("没有找到正在运行的任务管理器进程")
        return False
    except Exception as e:
        print(f"终止失败: {e}")
        return False

if __name__ == "__main__":
    stop_streamlit()