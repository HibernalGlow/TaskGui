import streamlit as st

def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="任务管理器",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    ) 