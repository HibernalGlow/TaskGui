"""
任务管理器主包
"""
from .app import main
from .utils import (
    get_task_command, 
    copy_to_clipboard, 
    get_directory_files, 
    open_file,
    set_page_config,
    setup_css,
    initialize_session_state,
    update_running_task_status,
    get_task_status,
    load_task_data,
    apply_filters
)
from .task_runner import run_task_via_cmd, run_multiple_tasks
from .views import (
    render_table_view,
    render_card_view,
    render_group_view,
    render_settings_view,
    render_aggrid_table,
    render_batch_operations
)

__all__ = [
    'main',
    'get_task_command',
    'copy_to_clipboard',
    'get_directory_files',
    'open_file',
    'set_page_config',
    'setup_css',
    'initialize_session_state',
    'update_running_task_status',
    'get_task_status',
    'load_task_data',
    'apply_filters',
    'run_task_via_cmd',
    'run_multiple_tasks',
    'render_table_view',
    'render_card_view',
    'render_group_view',
    'render_settings_view',
    'render_aggrid_table',
    'render_batch_operations'
] 