import os
import subprocess
import platform
import threading

def run_task_via_cmd(task_name, taskfile_path=None):
    """
    通过命令行运行任务
    
    参数:
        task_name: 任务名称
        taskfile_path: Taskfile路径
        
    返回:
        subprocess.Popen对象或None（如果启动失败）
    """
    try:
        # 构建命令
        if taskfile_path and os.path.exists(taskfile_path):
            command = f'task --taskfile "{taskfile_path}" {task_name}'
        else:
            command = f'task {task_name}'
        
        # 根据操作系统确定如何运行命令
        if platform.system() == 'Windows':
            # 在Windows上使用cmd运行
            process = subprocess.Popen(
                f'start cmd.exe /k "{command}"',
                shell=True
            )
        else:
            # 在类Unix系统上使用终端运行
            if platform.system() == 'Darwin':  # macOS
                process = subprocess.Popen([
                    'osascript', '-e', 
                    f'tell application "Terminal" to do script "{command}"'
                ])
            else:  # Linux
                # 检测可用的终端
                if os.path.exists('/usr/bin/gnome-terminal'):
                    process = subprocess.Popen([
                        'gnome-terminal', '--', 'bash', '-c', f'{command}; exec bash'
                    ])
                elif os.path.exists('/usr/bin/xterm'):
                    process = subprocess.Popen([
                        'xterm', '-e', f'{command}; exec bash'
                    ])
                else:
                    process = subprocess.Popen([
                        'x-terminal-emulator', '-e', f'{command}; exec bash'
                    ])
        
        return process
    except Exception as e:
        print(f"运行任务时出错: {str(e)}")
        return None

def run_multiple_tasks(task_names, taskfile_path, parallel=False):
    """
    运行多个任务
    
    参数:
        task_names: 任务名称列表
        taskfile_path: Taskfile路径
        parallel: 是否并行运行
        
    返回:
        消息列表，每个消息对应一个任务的运行结果
    """
    if not task_names:
        return ["没有指定任务"]
    
    messages = []
    
    if parallel:
        # 并行运行
        threads = []
        for task_name in task_names:
            thread = threading.Thread(
                target=lambda: run_task_via_cmd(task_name, taskfile_path)
            )
            threads.append(thread)
            thread.start()
            messages.append(f"任务 {task_name} 已在新窗口启动")
        
        # 等待所有线程完成（通常是立即返回的，因为只是启动进程）
        for thread in threads:
            thread.join(0.1)  # 设置超时，避免长时间等待
    else:
        # 顺序运行
        for task_name in task_names:
            process = run_task_via_cmd(task_name, taskfile_path)
            if process:
                messages.append(f"任务 {task_name} 已在新窗口启动")
            else:
                messages.append(f"任务 {task_name} 启动失败")
    
    return messages 