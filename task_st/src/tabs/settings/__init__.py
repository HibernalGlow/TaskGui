"""设置模块包，负责整合所有设置界面"""
import streamlit as st

# 导入各个子模块的设置渲染函数
from src.tabs.settings.basic.basic_settings import render_basic_settings, load_basic_settings, save_basic_settings
from src.tabs.settings.background.background_settings import render_background_settings
from src.tabs.settings.card.card_settings import render_card_settings
from src.tabs.settings.table.table_settings import render_table_settings
from src.tabs.settings.sidebar.sidebar_settings import render_sidebar_settings

# 重新导出函数，保持向后兼容性
__all__ = [
    'render_settings_tab', 
    'load_basic_settings', 
    'save_basic_settings',
    'render_basic_settings',
    'render_background_settings',
    'render_card_settings',
    'render_table_settings',
    'render_sidebar_settings'
]

def render_settings_tab():
    """渲染设置标签页"""
    st.markdown("## ⚙️ 系统设置")
    
    # 创建设置子标签页
    settings_tabs = st.tabs(["基本设置", "🎨 背景设置", "卡片设置", "📊 表格设置", "侧边栏设置"])
    
    # 基本设置标签页
    with settings_tabs[0]:
        render_basic_settings()
    
    # 背景设置标签页
    with settings_tabs[1]:
        render_background_settings()
        
    # 卡片设置标签页
    with settings_tabs[2]:
        render_card_settings()
        
    # 表格设置标签页
    with settings_tabs[3]:
        render_table_settings()
        
    # 侧边栏设置标签页
    with settings_tabs[4]:
        render_sidebar_settings() 