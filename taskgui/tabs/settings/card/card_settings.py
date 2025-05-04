import streamlit as st
from taskgui.utils.selection_utils import get_card_view_settings, update_card_view_settings, load_local_config, save_local_config
from taskgui.tabs.settings.basic.basic_settings import load_basic_settings, save_basic_settings
from taskgui.components.tag_filters import get_all_tags
from taskgui.utils.file_utils import get_nearest_taskfile

def render_card_settings():
    """渲染卡片设置"""
    st.subheader("卡片元素显示设置")
    
    # 获取当前卡片设置
    card_settings = get_card_view_settings()
    
    # 确保use_sidebar_editor存在于session_state中
    if 'use_sidebar_editor' not in st.session_state:
        st.session_state.use_sidebar_editor = card_settings.get("use_sidebar_editor", True)
    
    # 创建设置表单
    with st.form("card_view_settings_form"):
        st.write("选择要在任务卡片中显示的元素：")
        
        # 描述显示选项
        show_description = st.checkbox(
            "显示任务描述", 
            value=card_settings.get("show_description", True),
            help="显示任务的详细描述"
        )
        
        # 标签显示选项
        show_tags = st.checkbox(
            "显示任务标签", 
            value=card_settings.get("show_tags", True),
            help="显示任务的相关标签"
        )
        
        # 目录显示选项
        show_directory = st.checkbox(
            "显示任务目录", 
            value=card_settings.get("show_directory", True),
            help="显示任务相关的目录路径"
        )
        
        # 命令显示选项
        show_command = st.checkbox(
            "显示任务命令", 
            value=card_settings.get("show_command", True),
            help="显示执行任务的命令"
        )
        
        # 添加侧边栏编辑选项
        use_sidebar_editor = st.checkbox(
            "在侧边栏中编辑任务", 
            value=st.session_state.use_sidebar_editor,
            help="在侧边栏中编辑任务，而不是直接在卡片内编辑"
        )
        
        # 提交按钮
        submitted = st.form_submit_button("保存设置")
        
        if submitted:
            # 更新设置
            new_settings = {
                "show_description": show_description,
                "show_tags": show_tags,
                "show_directory": show_directory,
                "show_command": show_command,
                "use_sidebar_editor": use_sidebar_editor
            }
            
            # 更新session_state
            st.session_state.use_sidebar_editor = use_sidebar_editor
            
            # 保存设置
            update_card_view_settings(new_settings)
            st.success("卡片显示设置已更新！")

    # 加载当前配置
    config = load_local_config()
    
    # 卡片分组设置
    card_group_by_tag = st.checkbox(
        "按第一个标签分组显示卡片",
        value=config.get('card_group_by_tag', False),
        help="启用后，卡片将按照第一个标签进行分组显示"
    )
    
    # 获取当前任务文件路径
    default_taskfile = get_nearest_taskfile()
    
    # 获取所有可用标签
    all_tags = get_all_tags(default_taskfile) if default_taskfile else []
    
    # 置顶标签设置
    pinned_tags = st.multiselect(
        "置顶标签（优先显示）",
        options=all_tags,
        default=config.get('pinned_tags', []),
        help="选择要优先显示的标签，这些标签会显示在分组的最前面"
    )
    
    # 保存设置
    if card_group_by_tag != config.get('card_group_by_tag', False) or pinned_tags != config.get('pinned_tags', []):
        config['card_group_by_tag'] = card_group_by_tag
        config['pinned_tags'] = pinned_tags
        save_local_config(config)
        st.success("设置已保存") 