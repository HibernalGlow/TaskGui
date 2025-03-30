import subprocess
import tempfile
import threading
import os
from datetime import datetime
from .utils import get_task_command

def run_task_via_cmd(task_name, taskfile_path=None):
    """
    通过后台打开CMD运行任务
    
    参数:
        task_name: 任务名称
        taskfile_path: Taskfile路径
        
    返回:
        result: 任务运行结果信息
    """
    # 创建一个临时的批处理文件
    with tempfile.NamedTemporaryFile(suffix='.bat', delete=False, mode='w') as f:
        f.write('@echo off\n')
        f.write('title 执行任务: %s\n' % task_name)
        f.write('color 0A\n')  # 设置绿色文字
        f.write('echo 正在执行任务: %s\n' % task_name)
        f.write('echo 时间: %s\n' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        f.write('echo ======================================\n')
        
        # 构建task命令，如果有指定taskfile
        if taskfile_path and os.path.exists(taskfile_path):
            f.write(f'task --taskfile "{taskfile_path}" {task_name}\n')
        else:
            f.write(f'task {task_name}\n')
        
        f.write('echo ======================================\n')
        f.write('echo 任务执行完成\n')
        f.write('echo 请按任意键关闭窗口...\n')
        f.write('pause > nul\n')
        batch_file = f.name
    
    # 使用subprocess启动CMD窗口但不等待它完成
    subprocess.Popen(['start', 'cmd', '/c', batch_file], shell=True)
    
    return {
        'success': True,
        'output': "任务已在新窗口中启动，请查看CMD窗口获取输出",
        'error': ""
    }

def run_multiple_tasks(task_names, taskfile_path=None, parallel=False):
    """
    运行多个任务 - 支持并行
    
    参数:
        task_names: 任务名称列表
        taskfile_path: Taskfile路径
        parallel: 是否并行运行
        
    返回:
        result_msg: 任务运行结果信息
    """
    if not task_names or len(task_names) == 0:
        return "没有选择任务"
        
    if parallel:
        # 并行运行
        threads = []
        for task_name in task_names:
            thread = threading.Thread(
                target=run_task_via_cmd,
                args=(task_name, taskfile_path)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # 不等待线程完成
        return f"已并行启动 {len(task_names)} 个任务"
    else:
        # 顺序运行
        for task_name in task_names:
            run_task_via_cmd(task_name, taskfile_path)
        return f"已顺序启动 {len(task_names)} 个任务" 