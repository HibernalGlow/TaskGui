import os
import glob
import subprocess
import platform
import pyperclip

# 常量
DEFAULT_TASKFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Taskfile.yml')

# 复制命令到剪贴板
def copy_to_clipboard(text):
    """
    将文本复制到剪贴板
    
    参数:
        text: 要复制的文本
        
    返回:
        布尔值，表示是否成功复制
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"复制到剪贴板时出错: {str(e)}")
        return False

# 生成task命令文本
def get_task_command(task_name, taskfile_path=None):
    """
    获取任务的命令
    
    参数:
        task_name: 任务名称
        taskfile_path: 可选的Taskfile路径
        
    返回:
        命令字符串
    """
    if taskfile_path and os.path.exists(taskfile_path):
        return f'task --taskfile "{taskfile_path}" {task_name}'
    else:
        return f'task {task_name}'

# 查找Taskfile文件
def find_taskfiles(start_dir=None):
    """
    在指定目录及其父目录中寻找Taskfile
    
    参数:
        start_dir: 起始目录
        
    返回:
        Taskfile路径列表
    """
    if not start_dir:
        start_dir = os.getcwd()
    
    # 支持的Taskfile名称
    taskfile_patterns = [
        'Taskfile.y*ml',
        'taskfile.y*ml',
        '.taskfile.y*ml',
        'task.y*ml',
        '.task.y*ml'
    ]
    
    taskfiles = []
    
    # 在当前目录及子目录中查找
    for pattern in taskfile_patterns:
        search_pattern = os.path.join(start_dir, '**', pattern)
        taskfiles.extend(glob.glob(search_pattern, recursive=True))
    
    # 添加当前目录的匹配
    for pattern in taskfile_patterns:
        search_pattern = os.path.join(start_dir, pattern)
        taskfiles.extend(glob.glob(search_pattern))
    
    return sorted(list(set(taskfiles)))

# 获取最近的Taskfile
def get_nearest_taskfile(start_dir=None):
    """
    获取最近的Taskfile
    
    参数:
        start_dir: 起始目录
        
    返回:
        Taskfile的完整路径，如果没有找到则返回None
    """
    if not start_dir:
        start_dir = os.getcwd()
    
    # 支持的Taskfile名称模式
    taskfile_names = [
        'Taskfile.yml',
        'Taskfile.yaml',
        'taskfile.yml',
        'taskfile.yaml',
        '.taskfile.yml',
        '.taskfile.yaml',
        'task.yml',
        'task.yaml',
        '.task.yml',
        '.task.yaml'
    ]
    
    # 首先检查当前目录
    for name in taskfile_names:
        file_path = os.path.join(start_dir, name)
        if os.path.exists(file_path):
            return file_path
    
    # 如果当前目录没有，查找父目录
    current_dir = start_dir
    max_levels = 5  # 最多向上查找的层数
    
    for _ in range(max_levels):
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # 已到达根目录
            break
        
        for name in taskfile_names:
            file_path = os.path.join(parent_dir, name)
            if os.path.exists(file_path):
                return file_path
        
        current_dir = parent_dir
    
    # 如果还没找到，则返回已找到的第一个Taskfile
    taskfiles = find_taskfiles(start_dir)
    return taskfiles[0] if taskfiles else None

# 打开文件或目录
def open_file(file_path):
    """
    使用系统默认程序打开文件或目录
    
    参数:
        file_path: 文件或目录路径
        
    返回:
        布尔值，表示是否成功打开
    """
    if not file_path:
        print("文件路径为空")
        return False
        
    # 处理路径中的Taskfile变量
    file_path = resolve_taskfile_variables(file_path)
    
    if not os.path.exists(file_path):
        print(f"路径不存在: {file_path}")
        return False
    
    try:
        if platform.system() == 'Windows':
            subprocess.run(['explorer', file_path], shell=True)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f"打开文件时出错: {str(e)}")
        return False

# 获取目录下的文件
def get_directory_files(directory):
    """
    获取目录中的所有文件
    
    参数:
        directory: 目录路径
        
    返回:
        文件名列表
    """
    if not directory:
        print("目录路径为空")
        return []
        
    # 处理路径中的Taskfile变量
    directory = resolve_taskfile_variables(directory)
    
    if not os.path.exists(directory):
        print(f"目录不存在: {directory}")
        return []
        
    if not os.path.isdir(directory):
        print(f"路径不是目录: {directory}")
        return []
    
    try:
        # 只返回文件，不包括目录
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        print(f"获取目录文件时出错: {str(e)}")
        return []

# 解析Taskfile变量
def resolve_taskfile_variables(path):
    """
    解析路径中的Taskfile变量，如{{.ROOT_DIR}}
    
    参数:
        path: 包含变量的路径
        
    返回:
        解析后的路径
    """
    if not path:
        return path
        
    # 处理常见的Taskfile变量
    if "{{.ROOT_DIR}}" in path:
        # 获取Taskfile所在目录作为根目录
        taskfile_path = get_nearest_taskfile()
        if taskfile_path:
            root_dir = os.path.dirname(taskfile_path)
            return path.replace("{{.ROOT_DIR}}", root_dir)
        else:
            # 如果找不到Taskfile，使用当前工作目录
            root_dir = os.getcwd()
            return path.replace("{{.ROOT_DIR}}", root_dir)
    
    # 可以在这里添加更多变量的处理
    
    return path 