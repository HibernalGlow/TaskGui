import streamlit as st

def update_aggrid_setting(setting_key, value):
    """更新AgGrid设置并保存到session_state"""
    if 'aggrid_settings' not in st.session_state:
        st.session_state.aggrid_settings = {}
    st.session_state.aggrid_settings[setting_key] = value

def get_default_settings():
    """获取默认AgGrid设置"""
    return {
        'enable_filter': True,
        'enable_sorting': True,
        'enable_trigger': True,
        'enable_row_group': True,
        'enable_multiselect': True,  # 使用自定义勾选列进行多选，原生勾选框被隐藏
        'enable_editing': False,
        'enable_enterprise': True,
        'theme': 'streamlit',
        'enable_excel_export': True,
        'enable_row_pinning': True,
        'group_by_columns': [],  # 默认不使用目录分组
        'auto_group_column': True,
        'group_hide_open_parents': True,
        'enable_pagination': True,
        'page_size': 100,
        'enable_column_resize': True,
        'enable_side_bar': True,
        'enable_quick_filter': True,
        'quick_filter_text': '',
        'enable_full_height': True,  # 默认显示全部内容，不使用滚动条
        'fixed_height': 500,  # 默认固定高度值（当不使用全高度时）
    }

def init_aggrid_settings():
    """初始化AgGrid设置"""
    # 初始化配置持久化状态
    if 'aggrid_settings' not in st.session_state:
        st.session_state.aggrid_settings = {}
    
    # 初始化或更新默认设置
    default_settings = get_default_settings()
    for key, value in default_settings.items():
        if key not in st.session_state.aggrid_settings:
            st.session_state.aggrid_settings[key] = value

def reset_to_default_settings():
    """重置为默认设置"""
    default_settings = get_default_settings()
    for key, value in default_settings.items():
        st.session_state.aggrid_settings[key] = value 