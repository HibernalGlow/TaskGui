import os
import subprocess
import threading
import streamlit as st
from typing import List, Dict, Any, Optional
from .utils import get_task_command, update_running_task_status

def run_task_via_cmd(task_name: str, task_file: str) -> str:
    """
    运行单个任务并返回结果
    
    Args:
        task_name: 任务名称
        task_file: 任务文件路径
        
    Returns:
        运行结果消息
    """
    # 获取任务命令
    cmd = get_task_command(task_name, task_file)
    
    # 更新任务状态为运行中
    update_running_task_status(task_name, 'running')
    
    try:
        # 使用线程在后台运行任务
        def run_task_thread():
            try:
                # 在新的进程窗口中运行命令
                if os.name == 'nt':  # Windows
                    process = subprocess.Popen(
                        f'start cmd /k "{cmd}"', 
                        shell=True
                    )
                else:  # Linux/Mac
                    process = subprocess.Popen(
                        f'gnome-terminal -- bash -c "{cmd}; exec bash"', 
                        shell=True
                    )
                
                # 更新任务状态为完成
                update_running_task_status(task_name, 'completed', output=["任务已在新窗口启动"])
            except Exception as e:
                # 更新任务状态为失败
                update_running_task_status(task_name, 'failed', output=[str(e)])
        
        # 启动线程
        thread = threading.Thread(target=run_task_thread)
        thread.daemon = True
        thread.start()
        
        # 更新会话状态，记录正在运行的任务
        if 'task_to_run' not in st.session_state:
            st.session_state.task_to_run = ''
        
        st.session_state.task_to_run = task_name
        
        return "任务已在新窗口启动"
    
    except Exception as e:
        # 更新任务状态为失败
        update_running_task_status(task_name, 'failed', output=[str(e)])
        return f"任务启动失败: {str(e)}"

def run_multiple_tasks(task_names: List[str], task_file: str, parallel: bool = False) -> str:
    """
    运行多个任务
    
    Args:
        task_names: 任务名称列表
        task_file: 任务文件路径
        parallel: 是否并行运行
        
    Returns:
        运行结果消息
    """
    if not task_names:
        return "没有选择任务"
    
    # 获取所有任务命令
    cmds = [get_task_command(task, task_file) for task in task_names]
    
    try:
        if parallel:
            # 并行运行所有任务
            for i, (task, cmd) in enumerate(zip(task_names, cmds)):
                # 更新任务状态为运行中
                update_running_task_status(task, 'running')
                
                # 启动任务
                if os.name == 'nt':  # Windows
                    process = subprocess.Popen(
                        f'start cmd /k "{cmd}"', 
                        shell=True
                    )
                else:  # Linux/Mac
                    process = subprocess.Popen(
                        f'gnome-terminal -- bash -c "{cmd}; exec bash"', 
                        shell=True
                    )
                
                # 更新任务状态为完成
                update_running_task_status(task, 'completed', output=["任务已在新窗口启动"])
        else:
            # 顺序运行所有任务 - 创建批处理文件并运行
            if os.name == 'nt':  # Windows
                batch_file = "run_tasks.bat"
                with open(batch_file, "w") as f:
                    f.write("@echo off\n")
                    f.write("echo 正在顺序运行选定的任务...\n")
                    
                    for i, (task, cmd) in enumerate(zip(task_names, cmds)):
                        f.write(f"echo 运行任务 {i+1}/{len(cmds)}: {task}\n")
                        f.write(f"{cmd}\n")
                        f.write("echo 任务 {0} 完成\n".format(task))
                        f.write("echo.\n")
                    
                    f.write("echo 所有任务已完成\n")
                    f.write("pause\n")
                
                # 运行批处理文件
                process = subprocess.Popen(
                    f'start cmd /k "{batch_file}"', 
                    shell=True
                )
            else:  # Linux/Mac
                shell_file = "run_tasks.sh"
                with open(shell_file, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo '正在顺序运行选定的任务...'\n")
                    
                    for i, (task, cmd) in enumerate(zip(task_names, cmds)):
                        f.write(f"echo '运行任务 {i+1}/{len(cmds)}: {task}'\n")
                        f.write(f"{cmd}\n")
                        f.write("echo '任务 {0} 完成'\n".format(task))
                        f.write("echo\n")
                    
                    f.write("echo '所有任务已完成'\n")
                    f.write("read -p '按Enter键继续...'\n")
                
                # 赋予执行权限
                os.chmod(shell_file, 0o755)
                
                # 运行shell脚本
                process = subprocess.Popen(
                    f'gnome-terminal -- bash -c "./{shell_file}; exec bash"', 
                    shell=True
                )
        
        mode = "并行" if parallel else "顺序"
        return f"已在新窗口{mode}启动 {len(task_names)} 个任务"
    
    except Exception as e:
        for task in task_names:
            update_running_task_status(task, 'failed', output=[str(e)])
        return f"任务启动失败: {str(e)}" 