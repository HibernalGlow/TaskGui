import streamlit as st
import pandas as pd

# 尝试导入AgGrid
try:
    from st_aggrid import AgGrid, GridUpdateMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    st.error("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")

# 导入选择状态更新函数
from taskgui.utils.selection_utils import get_selected_tasks, init_global_state

# 导入自定义模块
from taskgui.views.table.aggrid_config import init_aggrid_settings
# 移除下面的导入，不再在表格视图中显示设置
# from taskgui.views.table.aggrid_ui import render_settings_ui
from taskgui.views.table.aggrid_data import prepare_display_data, process_grid_selection_changes
from taskgui.views.table.aggrid_renderers import build_grid_options

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格 - 使用内存状态管理"""
    if not HAS_AGGRID:
        st.warning("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")
        return
    
    # 确保全局状态已初始化
    init_global_state()
    
    # 初始化AgGrid设置
    init_aggrid_settings()
    
    # 不再调用render_settings_ui函数来显示设置UI
    # 直接从session_state获取设置
    settings = st.session_state.aggrid_settings
    
    # 准备表格数据
    display_df, filtered_df_copy = prepare_display_data(filtered_df)
    
    # 构建表格选项
    grid_options = build_grid_options(display_df, settings)
    
    # 获取主题
    theme_option = settings.get('theme', 'streamlit')
    
    # 渲染 AgGrid
    grid_return = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # 始终使用MODEL_CHANGED模式避免刷新问题
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=settings.get('enable_enterprise', True),
        height=None if settings.get('enable_full_height', True) else settings.get('fixed_height', 500),
        width='100%',
        key='aggrid_table',
        reload_data=False,
        allow_unsafe_jscode=True,
        theme=theme_option,
        # 添加新的高级功能支持
        enable_sidebar=settings.get('enable_side_bar', True),
        columns_auto_size_mode='FIT_CONTENTS' if settings.get('enable_column_resize', True) else 'FIT_ALL_COLUMNS_TO_VIEW',
        # 全高度显示所需的额外配置
        domLayout='normal' if settings.get('enable_full_height', True) else 'autoHeight'
    )
    
    # 处理表格勾选状态变化
    has_changes = process_grid_selection_changes(grid_return)
    
    # 如果有状态变化，强制刷新页面
    if has_changes:
        st.rerun()
    
    # 表格下方添加状态信息
    # selected_tasks = get_selected_tasks()
    # st.write(f"当前选中: {len(selected_tasks)} 个任务")
    
    return grid_return
