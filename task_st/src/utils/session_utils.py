import streamlit as st

# 初始化会话状态
def init_session_state():
    """初始化会话状态变量"""
    # 初始化会话状态变量
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
    
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    if 'search_task' not in st.session_state:
        st.session_state.search_task = ""
    
    if 'tags_filter' not in st.session_state:
        st.session_state.tags_filter = []
        
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
    
    if 'run_parallel' not in st.session_state:
        st.session_state.run_parallel = False

# 定义CSS样式
def setup_css():
    """设置应用的CSS样式"""
    st.markdown("""
    <style>
    .copy-btn {
        display: inline-block;
        padding: 2px 8px;
        background-color: #f0f2f6;
        color: #31333F;
        border: 1px solid #ddd;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        margin-left: 10px;
    }
    .copy-btn:hover {
        background-color: #ddd;
    }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 12px;
        margin-right: 5px;
        font-size: 12px;
    }
    .run-btn {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True) 