import streamlit as st
from src.views.table.aggrid_config import update_aggrid_setting, reset_to_default_settings

def render_settings_ui():
    """渲染AgGrid高级设置UI"""
    # 移除expander，直接显示设置内容
    st.write("### 表格功能设置")
    
    # 其他AgGrid功能选项
    col1, col2 = st.columns(2)
    with col1:
        enable_filter = st.checkbox(
            "启用列过滤", 
            value=st.session_state.aggrid_settings['enable_filter'], 
            key="aggrid_enable_filter",
            on_change=lambda: update_aggrid_setting('enable_filter', st.session_state.aggrid_enable_filter)
        )
        enable_sorting = st.checkbox(
            "启用排序", 
            value=st.session_state.aggrid_settings['enable_sorting'], 
            key="aggrid_enable_sorting",
            on_change=lambda: update_aggrid_setting('enable_sorting', st.session_state.aggrid_enable_sorting)
        )
        enable_trigger = st.checkbox(
            "启用交互触发器", 
            value=st.session_state.aggrid_settings['enable_trigger'], 
            key="aggrid_enable_trigger",
            on_change=lambda: update_aggrid_setting('enable_trigger', st.session_state.aggrid_enable_trigger)
        )
        # 添加行分组功能
        enable_row_group = st.checkbox(
            "启用数据分组", 
            value=st.session_state.aggrid_settings['enable_row_group'], 
            key="aggrid_enable_rowgroup",
            on_change=lambda: update_aggrid_setting('enable_row_group', st.session_state.aggrid_enable_rowgroup)
        )
        # 添加多行选择功能
        enable_multi_select = st.checkbox(
            "启用多行选择", 
            value=st.session_state.aggrid_settings['enable_multiselect'], 
            key="aggrid_enable_multiselect",
            on_change=lambda: update_aggrid_setting('enable_multiselect', st.session_state.aggrid_enable_multiselect),
            help="使用自定义勾选框实现多行选择，原生勾选框已隐藏"
        )
    
    with col2:
        enable_editing = st.checkbox(
            "允许编辑单元格", 
            value=st.session_state.aggrid_settings['enable_editing'], 
            key="aggrid_enable_editing",
            on_change=lambda: update_aggrid_setting('enable_editing', st.session_state.aggrid_enable_editing)
        )
        enable_enterprise = st.checkbox(
            "启用企业功能", 
            value=st.session_state.aggrid_settings['enable_enterprise'], 
            key="aggrid_enable_enterprise",
            on_change=lambda: update_aggrid_setting('enable_enterprise', st.session_state.aggrid_enable_enterprise)
        )
        theme_options = ["streamlit", "light", "dark", "blue", "fresh", "material"]
        theme_index = theme_options.index(st.session_state.aggrid_settings['theme']) if st.session_state.aggrid_settings['theme'] in theme_options else 0
        theme_option = st.selectbox(
            "表格主题",
            options=theme_options,
            index=theme_index,
            key="aggrid_theme",
            on_change=lambda: update_aggrid_setting('theme', st.session_state.aggrid_theme)
        )
        # 添加Excel导出功能
        enable_excel_export = st.checkbox(
            "启用Excel导出", 
            value=st.session_state.aggrid_settings['enable_excel_export'], 
            key="aggrid_enable_excel_export",
            on_change=lambda: update_aggrid_setting('enable_excel_export', st.session_state.aggrid_enable_excel_export)
        )
        # 添加列/行固定功能
        enable_row_pinning = st.checkbox(
            "启用行固定", 
            value=st.session_state.aggrid_settings['enable_row_pinning'], 
            key="aggrid_enable_row_pinning",
            on_change=lambda: update_aggrid_setting('enable_row_pinning', st.session_state.aggrid_enable_row_pinning)
        )
    
    # 分组设置
    if enable_row_group:
        st.write("分组设置")
        groupable_columns = ["显示名称", "描述", "标签", "目录"]
        group_by_columns = st.multiselect(
            "选择要分组的列",
            options=groupable_columns,
            default=st.session_state.aggrid_settings['group_by_columns'],
            key="aggrid_group_columns",
            on_change=lambda: update_aggrid_setting('group_by_columns', st.session_state.aggrid_group_columns)
        )
        
        auto_group_column = st.checkbox(
            "自动创建分组列", 
            value=st.session_state.aggrid_settings['auto_group_column'], 
            key="aggrid_auto_group_column",
            on_change=lambda: update_aggrid_setting('auto_group_column', st.session_state.aggrid_auto_group_column)
        )
        group_hide_open_parents = st.checkbox(
            "隐藏已展开的父级", 
            value=st.session_state.aggrid_settings['group_hide_open_parents'], 
            key="aggrid_hide_open_parents",
            on_change=lambda: update_aggrid_setting('group_hide_open_parents', st.session_state.aggrid_hide_open_parents)
        )
    
    # 高级表格功能
    st.write("高级表格功能")
    col3, col4 = st.columns(2)
    with col3:
        enable_pagination = st.checkbox(
            "启用分页", 
            value=st.session_state.aggrid_settings['enable_pagination'], 
            key="aggrid_enable_pagination",
            on_change=lambda: update_aggrid_setting('enable_pagination', st.session_state.aggrid_enable_pagination)
        )
        if enable_pagination:
            page_size = st.number_input(
                "每页行数", 
                min_value=5, 
                max_value=100, 
                value=st.session_state.aggrid_settings['page_size'], 
                step=5, 
                key="aggrid_page_size",
                on_change=lambda: update_aggrid_setting('page_size', st.session_state.aggrid_page_size)
            )
        
        enable_column_resize = st.checkbox(
            "允许调整列宽", 
            value=st.session_state.aggrid_settings['enable_column_resize'], 
            key="aggrid_enable_column_resize",
            on_change=lambda: update_aggrid_setting('enable_column_resize', st.session_state.aggrid_enable_column_resize)
        )
        
        # 添加表格高度设置
        enable_full_height = st.checkbox(
            "显示全部内容（不滚动）", 
            value=st.session_state.aggrid_settings['enable_full_height'], 
            key="aggrid_enable_full_height",
            on_change=lambda: update_aggrid_setting('enable_full_height', st.session_state.aggrid_enable_full_height),
            help="启用后表格将显示所有行，不使用滚动条"
        )
        if not enable_full_height:
            fixed_height = st.number_input(
                "表格固定高度(px)", 
                min_value=200, 
                max_value=2000, 
                value=st.session_state.aggrid_settings['fixed_height'], 
                step=50, 
                key="aggrid_fixed_height",
                on_change=lambda: update_aggrid_setting('fixed_height', st.session_state.aggrid_fixed_height)
            )
    
    with col4:
        enable_side_bar = st.checkbox(
            "显示侧边栏", 
            value=st.session_state.aggrid_settings['enable_side_bar'], 
            key="aggrid_enable_side_bar",
            on_change=lambda: update_aggrid_setting('enable_side_bar', st.session_state.aggrid_enable_side_bar)
        )
        enable_quick_filter = st.checkbox(
            "启用快速筛选", 
            value=st.session_state.aggrid_settings['enable_quick_filter'], 
            key="aggrid_enable_quick_filter",
            on_change=lambda: update_aggrid_setting('enable_quick_filter', st.session_state.aggrid_enable_quick_filter)
        )
        if enable_quick_filter:
            quick_filter_text = st.text_input(
                "快速筛选", 
                value=st.session_state.aggrid_settings['quick_filter_text'],
                key="aggrid_quick_filter_text",
                on_change=lambda: update_aggrid_setting('quick_filter_text', st.session_state.aggrid_quick_filter_text)
            )
    
    # 添加保存/重置按钮
    col5, col6 = st.columns(2)
    with col5:
        if st.button("保存当前配置为默认", key="save_aggrid_config"):
            # 已经在on_change中保存了，这里只需提示
            st.success("当前配置已保存")
    
    with col6:
        if st.button("重置为默认配置", key="reset_aggrid_config"):
            reset_to_default_settings()
            st.rerun()
            
    # 返回UI中的关键配置值，方便其他函数使用
    ui_settings = {}
    # 所有设置已保存到session_state.aggrid_settings中
    # 这里只返回一些关键设置
    for key in ['enable_filter', 'enable_sorting', 'enable_trigger', 'enable_row_group', 
                'enable_multiselect', 'enable_editing', 'enable_enterprise', 'theme',
                'enable_excel_export', 'enable_row_pinning', 'group_by_columns', 
                'auto_group_column', 'group_hide_open_parents', 'enable_pagination',
                'page_size', 'enable_column_resize', 'enable_side_bar', 
                'enable_quick_filter', 'quick_filter_text', 'enable_full_height', 'fixed_height']:
        if key in st.session_state.aggrid_settings:
            ui_settings[key] = st.session_state.aggrid_settings[key]
    
    return ui_settings 