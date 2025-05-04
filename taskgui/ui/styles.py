import streamlit as st

def apply_custom_css():
    """应用自定义CSS样式"""
    # 添加自定义CSS
    st.markdown("""
    <style>
        /* 确保所有组件使用全局背景色设置 */
        
        /* 标签样式，但不设置背景色 */
        .tag {
            border-radius: 10px;
            padding: 2px 8px;
            margin: 2px;
            display: inline-block;
            font-size: 0.8em;
        }
        
        .stButton>button {
            width: 100%;
        }
        
        /* 添加页签样式 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 5px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0 0;
        }
        
        /* 主要页签样式 */
        .main-tabs [data-baseweb="tab"] {
            font-weight: bold;
        }
        
        /* 预览区域样式 */
        .preview-card {
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
            border: 1px solid #e6e6e6;
        }
        
        /* YAML编辑器样式 */
        .yaml-editor {
            font-family: monospace;
            border-radius: 4px;
            color: #e6e6e6;
            padding: 16px;
            border: 1px solid #444;
            font-size: 14px;
            line-height: 1.5;
        }
        
        /* 自定义文本区域样式，使其看起来像代码编辑器 */
        .stTextArea textarea {
            font-family: 'Courier New', Courier, monospace !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            padding: 12px !important;
            background-color: white !important;
            color: black !important;
            border: 1px solid #cccccc !important;
            border-radius: 4px !important;
        }
        
        /* 统一表单控件样式，但不设置背景色 */
        .stTextInput input,
        .stSelectbox [data-baseweb="select"] div,
        .stMultiSelect [data-baseweb="select"] div {
            color: black !important;
        }
        
        /* 多选框选中的项保持可读性，但不设置背景色 */
        .stMultiSelect [data-baseweb="tag"] {
            color: black !important;
        }
        
        /* 下拉选项保持可读性，但不设置背景色 */
        .stMultiSelect [role="listbox"] li {
            color: black !important;
        }
        
        /* 字段标签隐藏 */
        .hide-label .stTextArea label {
            display: none;
        }
        
        /* 语法高亮区域 */
        .yaml-preview {
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            border: 1px solid #444;
            overflow-x: auto;
        }
        
        /* 复制按钮样式 */
        .copy-button {
            position: absolute;
            top: 5px;
            right: 5px;
            padding: 5px 10px;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        
        /* markdown代码块样式增强 */
        pre {
            position: relative;
            padding: 15px !important;
            border-radius: 5px !important;
            margin-bottom: 15px !important;
        }
        
        code {
            font-family: 'Courier New', Courier, monospace !important;
            color: #d4d4d4 !important;
        }
        
        /* 强烈减少所有容器的顶部空白 */
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0rem !important;
        }
        
        [data-testid="stHeader"] {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
            height: auto !important;
        }
        
        section[data-testid="stSidebar"] > div {
            padding-top: 2rem !important;
        }
        
        # [data-testid="stToolbar"] {
        #     display: none !important;
        # }
        
        /* 主要内容区减少空白 */
        [data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 95% !important;
        }
        
        /* 减少标题和元素间距 */
        .main h1, .main h2, .main h3, .main div[data-testid="stVerticalBlock"] > div {
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            line-height: 1.2 !important;
        }
        
        /* 标签页减少边距 */
        div[data-testid="stTabs"] {
            margin-top: 0 !important;
        }
        
        /* 预览卡片紧凑显示 */
        .preview-card {
            margin-top: 5px !important;
            padding: 10px !important;
        }
        
        /* 恢复侧边栏的响应式行为 */
        @media (max-width: 992px) {
            section[data-testid="stSidebar"] {
                position: fixed !important;
                left: -21rem !important;
                width: 21rem !important;
                transition: left 0.3s ease-in-out !important;
                z-index: 1000 !important;
                height: 100% !important;
                top: 0 !important;
                background-color: white !important;
                box-shadow: 0 0 10px rgba(0,0,0,0.2) !important;
            }
            
            section[data-testid="stSidebar"]:hover,
            section[data-testid="stSidebar"]:focus,
            section[data-testid="stSidebar"]:active {
                left: 0 !important;
            }
            
        }
    </style>
    """, unsafe_allow_html=True)

def add_clipboard_js():
    """添加复制到剪贴板的JavaScript函数"""
    st.markdown("""
    <script>
    function copyToClipboard(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('已复制到剪贴板!');
    }
    </script>
    """, unsafe_allow_html=True)

def reset_background_css():
    """重置背景CSS"""
    st.markdown("""
    <style>
    .stApp {
        background-image: none;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-image: none;
    }
    </style>
    """, unsafe_allow_html=True) 