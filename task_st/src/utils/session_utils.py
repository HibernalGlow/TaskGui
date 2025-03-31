import streamlit as st
from .selection_utils import load_local_config

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
    
    # 从本地配置加载常用标签
    if 'favorite_tags' not in st.session_state:
        local_config = load_local_config()
        if "favorite_tags" in local_config:
            st.session_state.favorite_tags = local_config["favorite_tags"]
        else:
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
        margin-bottom: 10px !important;
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
    
    /* 添加下拉框样式 */
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 20px !important;
    }
    
    .stSelectbox div[data-baseweb="select"] div {
        background-color: #f7f7f7 !important;
        border-radius: 20px !important;
    }
    
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: #4361ee !important;
    }
    
    /* 标签选择部分的标题样式 */
    .stMarkdown h3 {
        font-size: 1.2rem !important;
        margin-top: 20px !important;
        margin-bottom: 10px !important;
        padding-bottom: 5px;
        border-bottom: 1px solid #eee;
    }
    
    .stMarkdown h4 {
        font-size: 1rem !important;
        margin-top: 15px !important;
        margin-bottom: 8px !important;
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