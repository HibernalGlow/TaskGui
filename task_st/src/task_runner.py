import subprocess
import os
import threading
from .utils import get_task_command

def run_task_via_cmd(task_name, taskfile_path):
    """
    通过命令行运行指定的任务
    
    参数:
        task_name: 任务名称
        taskfile_path: Taskfile的路径
    
    返回:
        布尔值，表示是否成功启动任务
    """
    try:
        cmd = get_task_command(task_name, taskfile_path)
        if not cmd:
            return False
        
        # 确定任务的工作目录
        from .taskfile import read_taskfile
        tasks_df = read_taskfile(taskfile_path)
        task_row = tasks_df[tasks_df['name'] == task_name]
        
        if task_row.empty:
            return False
            
        # 使用任务的目录作为工作目录
        work_dir = task_row['directory'].values[0]
        if not work_dir or not os.path.exists(work_dir):
            work_dir = os.path.dirname(taskfile_path)
        
        # 创建一个新的cmd/控制台窗口来运行任务
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                f'start cmd /c "cd /d "{work_dir}" && {cmd} && pause"',
                shell=True
            )
        else:  # Linux/Mac
            subprocess.Popen(
                f'gnome-terminal -- bash -c "cd "{work_dir}" && {cmd}; read -p \'按回车键继续...\'"',
                shell=True
            )
        
        return True
    except Exception as e:
        print(f"运行任务时出错: {str(e)}")
        return False

def run_multiple_tasks(task_names, taskfile_path, parallel=False):
    """
    运行多个任务
    
    参数:
        task_names: 任务名称列表
        taskfile_path: Taskfile的路径
        parallel: 是否并行执行，默认为False
    
    返回:
        字符串列表，包含每个任务的运行结果信息
    """
    results = []
    
    if parallel:
        # 使用线程并行运行任务
        threads = []
        for task_name in task_names:
            thread = threading.Thread(
                target=lambda tn=task_name: run_task_via_cmd(tn, taskfile_path)
            )
            thread.start()
            threads.append(thread)
            results.append(f"已启动任务: {task_name}")
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(0.1)  # 非阻塞等待
        
        return results
    else:
        # 顺序运行任务
        for task_name in task_names:
            success = run_task_via_cmd(task_name, taskfile_path)
            if success:
                results.append(f"已启动任务: {task_name}")
            else:
                results.append(f"启动任务失败: {task_name}")
        
        return results 