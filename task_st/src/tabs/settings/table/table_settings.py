import streamlit as st
from src.views.table.aggrid_config import init_aggrid_settings
from src.views.table.aggrid_ui import render_settings_ui

def render_table_settings():
    """渲染表格设置标签页"""
    st.subheader("📊 表格显示设置")
    
    # 初始化AgGrid设置
    init_aggrid_settings()
    
    # 调用AgGrid高级设置UI渲染函数
    render_settings_ui() 