import streamlit as st
import os

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
    """设置自定义CSS样式"""
    # 注入自定义CSS样式
    st.markdown("""
    <style>
    /* 自定义标题样式 */
    .st-emotion-cache-1gulkj5 > h1,
    .st-emotion-cache-1gulkj5 > h2,
    .st-emotion-cache-1gulkj5 > h3 {
        margin-top: 0;
        padding-top: 0.5rem;
    }
    
    /* 自定义按钮样式 */
    .stButton button {
        border-radius: 4px;
        padding: 2px 10px;
    }
    
    /* 调整卡片视图样式 */
    .card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    }
    
    .card:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    }
    
    /* 调整选项卡容器样式 */
    .stTabs [role="tablist"] {
        border-bottom: 1px solid #e0e0e0;
    }
    
    .stTabs [role="tab"] {
        padding: 8px 16px;
        background-color: transparent;
        border: none;
        border-radius: 4px 4px 0 0;
        margin-right: 4px;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        border: 1px solid #e0e0e0;
        border-bottom: none;
        font-weight: bold;
    }
    
    .stTabs [role="tabpanel"] {
        padding: 16px;
        border: 1px solid #e0e0e0;
        border-radius: 0 0 4px 4px;
        border-top: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 加载背景设置
    try:
        from src.utils.selection_utils import load_background_settings
        from src.components.sidebar import set_background_image, set_sidebar_background
        
        # 获取背景设置
        bg_settings = load_background_settings()
        
        # 应用主界面背景
        if bg_settings.get('enabled', False) and bg_settings.get('image_path', '') and os.path.exists(bg_settings['image_path']):
            set_background_image(
                bg_settings['image_path'],
                bg_settings.get('opacity', 0.5),
                bg_settings.get('blur', 0)
            )
        
        # 应用侧边栏背景
        if bg_settings.get('sidebar_enabled', False) and bg_settings.get('sidebar_image_path', '') and os.path.exists(bg_settings['sidebar_image_path']):
            set_sidebar_background(bg_settings['sidebar_image_path'])
    except Exception as e:
        # 忽略错误，确保应用仍能正常启动
        pass 