import os
import glob
import subprocess
import platform
import pyperclip
import webbrowser
from pathlib import Path
import urllib.parse

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
        # 将路径转换为绝对路径
        abs_path = os.path.abspath(file_path)
        # 将路径转换为URL格式
        file_url = Path(abs_path).as_uri()
        
        # 使用webbrowser模块打开文件或目录
        webbrowser.open(file_url)
        return True
    except Exception as e:
        print(f"使用webbrowser打开失败: {str(e)}")
        
        # 备选方法1: 使用平台特定的命令
        try:
            if platform.system() == 'Windows':
                os.system(f'start "" "{os.path.normpath(file_path)}"')
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{file_path}"')
            return True
        except Exception as e2:
            print(f"备选方法1失败: {str(e2)}")
            
            # 备选方法2: 使用subprocess
            try:
                if platform.system() == 'Windows':
                    subprocess.Popen(['explorer', os.path.normpath(file_path)])
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', file_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', file_path])
                return True
            except Exception as e3:
                print(f"备选方法2失败: {str(e3)}")
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
    从Taskfile.yml文件中读取变量定义
    
    参数:
        path: 包含变量的路径
        
    返回:
        解析后的路径
    """
    if not path:
        return path
    
    if "{{." not in path:
        return path
        
    # 获取Taskfile路径
    taskfile_path = get_nearest_taskfile()
    if not taskfile_path:
        print("无法找到Taskfile.yml文件")
        return path
    
    try:
        # 导入yaml模块
        import yaml
        
        # 读取Taskfile内容
        with open(taskfile_path, 'r', encoding='utf-8') as f:
            taskfile_content = yaml.safe_load(f)
        
        # 提取变量定义
        variables = {}
        if 'vars' in taskfile_content and isinstance(taskfile_content['vars'], dict):
            variables = taskfile_content['vars']
            
        # 获取根目录作为默认值
        root_dir = os.path.dirname(taskfile_path)
        
        # 处理特殊变量
        if 'ROOT_DIR' not in variables:
            variables['ROOT_DIR'] = root_dir
            
        # 替换路径中的变量引用
        result_path = path
        for var_name, var_value in variables.items():
            var_pattern = f"{{{{.{var_name}}}}}"
            if var_pattern in result_path:
                print(f"替换变量: {var_pattern} -> {var_value}")
                result_path = result_path.replace(var_pattern, str(var_value))
        
        # 检查是否还有未解析的变量
        if "{{." in result_path and "}}" in result_path:
            import re
            unresolved_vars = re.findall(r'{{\.([^}]+)}}', result_path)
            if unresolved_vars:
                print(f"警告: 未解析的变量: {unresolved_vars}")
                
        return result_path
        
    except Exception as e:
        print(f"解析Taskfile变量时出错: {str(e)}")
        return path 