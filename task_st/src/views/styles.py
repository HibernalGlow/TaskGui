import streamlit as st

def apply_custom_styles():
    """应用自定义CSS样式"""
    
    # 三列布局样式
    st.markdown("""
    <style>
    /* 侧边栏样式优化 */
    div[data-testid="stSidebarContent"] {
        background-color: #f8f9fa;
    }
    
    /* 任务列表样式 */
    .task-item {
        padding: 8px;
        margin-bottom: 5px;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .task-item:hover {
        background-color: rgba(112, 182, 255, 0.1);
    }
    
    .task-item.active {
        background-color: rgba(112, 182, 255, 0.2);
    }
    
    /* 按钮样式优化 */
    .stButton>button {
        width: 100%;
    }
    
    /* 任务详情样式 */
    .task-detail {
        padding: 10px;
        margin-top: 10px;
        background-color: #ffffff;
        border-radius: 5px;
        border: 1px solid #e6e6e6;
    }
    </style>
    """, unsafe_allow_html=True)
