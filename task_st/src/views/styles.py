import streamlit as st

def apply_custom_styles():
    """应用自定义CSS样式"""
    
    # 三列布局样式
    st.markdown("""
    <style>
    /* 调整列间距 */
    .row-widget.stHorizontal {
        gap: 1rem;
    }
    
    /* 提高导航按钮样式 */
    .stButton button {
        width: 100%;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* 卡片容器样式 */
    .task-card {
        border: 1px solid #e6e6e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    
    /* 滚动条样式 */
    .task-list-container {
        max-height: 500px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }
    
    /* 调整任务列表视图 */
    .stExpander {
        border: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
