"""GlowToolBox 任务管理器包"""

# 导入工具函数
from .utils.file_utils import (
    copy_to_clipboard, 
    get_task_command, 
    open_file, 
    get_directory_files, 
    find_taskfiles, 
    get_nearest_taskfile
)
from .utils.session_utils import init_session_state, setup_css

# 导入服务函数
from .services.taskfile import load_taskfile, prepare_dataframe, filter_tasks, read_taskfile
from .services.task_runner import run_task_via_cmd, run_multiple_tasks

# 导入组件
from .components.sidebar import render_sidebar
from .components.tag_filters import render_tag_filters, get_all_tags
from .components.batch_operations import render_batch_operations

# 导入视图
from .views.table_view import render_table_view
from .views.card_view import render_card_view
from .views.group_view import render_group_view

# 常量
DEFAULT_TASKFILE_PATH = find_taskfiles()[0] if find_taskfiles() else None

__all__ = [
    # 工具函数
    'init_session_state',
    'copy_to_clipboard',
    'get_task_command',
    'DEFAULT_TASKFILE_PATH',
    'setup_css',
    'open_file',
    'get_directory_files',
    'find_taskfiles',
    'get_nearest_taskfile',
    
    # 服务函数
    'load_taskfile',
    'prepare_dataframe',
    'read_taskfile',
    'filter_tasks',
    'run_task_via_cmd',
    'run_multiple_tasks',
    
    # 组件
    'render_sidebar',
    'render_tag_filters',
    'get_all_tags',
    'render_batch_operations',
    
    # 视图
    'render_table_view',
    'render_card_view',
    'render_group_view'
] 