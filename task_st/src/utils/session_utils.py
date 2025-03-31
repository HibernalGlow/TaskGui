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
    /* 复制按钮样式 */
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
    
    /* 标签样式 */
    .tag {
        display: inline-block;
        padding: 2px 8px;
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 12px;
        margin-right: 5px;
        font-size: 12px;
    }
    
    /* 运行按钮样式 */
    .run-btn {
        background-color: #4CAF50;
        color: white;
    }
    
    /* streamlit-tags自定义样式 */
    .stTags {
        margin-bottom: 20px;
    }
    
    .stTags > div {
        gap: 8px !important;
    }
    
    .stTags > div div[data-baseweb="tag"] {
        background-color: #4361ee !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 2px 10px !important;
        font-size: 14px !important;
    }
    
    .stTags > div div[data-baseweb="tag"] span {
        max-width: 120px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .stTags > div div[data-baseweb="tag"]:hover {
        background-color: #3a56d4 !important;
    }
    
    .stTags input {
        border-radius: 20px !important;
        padding: 8px 12px !important;
    }
    
    /* 快速标签按钮样式 */
    .stButton button[type="secondary"] {
        background-color: #f0f2f6;
        color: #31333F;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 13px;
    }
    
    .stButton button[type="primary"] {
        background-color: #4361ee;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True) 