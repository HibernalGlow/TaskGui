import streamlit as st

# 初始化会话状态
def init_session_state():
    """初始化Streamlit会话状态变量"""
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    if 'last_taskfile_path' not in st.session_state:
        st.session_state.last_taskfile_path = None
    if 'taskfile_history' not in st.session_state:
        st.session_state.taskfile_history = []
    if 'favorite_tags' not in st.session_state:
        st.session_state.favorite_tags = []
    if 'parallel_mode' not in st.session_state:
        st.session_state.parallel_mode = False
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = '名称'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = '升序'

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

    /* 任务卡片页签样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 10px 16px;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e0f7fa;
        border-bottom: 2px solid #2196F3;
    }
    .stTabs [role="tabpanel"] {
        padding: 16px;
        border: 1px solid #e0e0e0;
        border-radius: 0 0 4px 4px;
        border-top: none;
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True) 