import streamlit as st
from taskgui.utils.selection_utils import get_card_view_settings, update_card_view_settings

def render_sidebar_settings():
    """渲染侧边栏设置标签页"""
    st.subheader("侧边栏设置")
    
    # 获取当前侧边栏设置
    sidebar_settings = get_card_view_settings()
    
    # 确保侧边栏设置存在于session_state中
    if 'sidebar_settings' not in st.session_state:
        st.session_state.sidebar_settings = sidebar_settings.get("sidebar_settings", {})
    
    # 默认的expander列表及其图标
    default_expanders = [
        {"id": "outline", "name": "📑 分组大纲", "enabled": True},
        {"id": "filter_tasks", "name": "🔍 过滤任务", "enabled": True},
        {"id": "edit_task", "name": "✏️ 编辑任务", "enabled": True},
        {"id": "tag_filters", "name": "🏷️ 标签筛选", "enabled": True},
        {"id": "system", "name": "系统", "enabled": True},
        {"id": "appearance", "name": "🎨 外观设置", "enabled": True}
    ]
    
    # 确保expander_order存在于session_state中
    if 'expander_order' not in st.session_state.sidebar_settings:
        st.session_state.sidebar_settings['expander_order'] = [exp["id"] for exp in default_expanders]
    
    with st.form("sidebar_settings_form"):
        st.write("自定义侧边栏组件：")
        
        # 显示所有可用的expander及其启用状态
        st.write("组件显示设置：")
        
        # 获取当前的expander顺序
        current_order = st.session_state.sidebar_settings.get('expander_order', [exp["id"] for exp in default_expanders])
        
        # 显示每个expander的开关和排序数字
        cols = st.columns([3, 1, 1])
        with cols[0]:
            st.write("**组件名称**")
        with cols[1]:
            st.write("**启用**")
        with cols[2]:
            st.write("**排序**")
        
        # 为每个expander创建设置行
        expander_status = {}
        expander_positions = {}
        
        for exp in default_expanders:
            exp_id = exp["id"]
            exp_name = exp["name"]
            
            # 获取当前状态
            is_enabled = st.session_state.sidebar_settings.get(f"{exp_id}_enabled", True)
            
            # 计算当前位置
            try:
                current_position = current_order.index(exp_id) + 1
            except ValueError:
                current_position = len(default_expanders)  # 如果不在列表中，放在最后
            
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"{exp_name}")
            with cols[1]:
                expander_status[exp_id] = st.checkbox(
                    f"启用{exp_name}",
                    value=is_enabled,
                    key=f"enable_{exp_id}",
                    label_visibility="collapsed"
                )
            with cols[2]:
                expander_positions[exp_id] = st.number_input(
                    f"{exp_name}排序",
                    min_value=1,
                    max_value=len(default_expanders),
                    value=current_position,
                    step=1,
                    key=f"position_{exp_id}",
                    label_visibility="collapsed"
                )
        
        # 添加"在侧边栏中编辑任务"的设置
        st.write("---")
        use_sidebar_editor = st.checkbox(
            "在侧边栏中编辑任务", 
            value=st.session_state.sidebar_settings.get("use_sidebar_editor", True),
            help="在侧边栏中编辑任务，而不是直接在卡片内编辑"
        )
        
        # 提交按钮
        submitted = st.form_submit_button("保存设置")
        
        if submitted:
            # 根据位置排序expander
            sorted_expanders = sorted([(exp["id"], expander_positions[exp["id"]]) for exp in default_expanders], key=lambda x: x[1])
            new_order = [exp_id for exp_id, _ in sorted_expanders]
            
            # 更新设置
            new_settings = {
                "sidebar_settings": {
                    "expander_order": new_order,
                    "use_sidebar_editor": use_sidebar_editor
                }
            }
            
            # 添加每个expander的启用状态
            for exp_id in expander_status:
                new_settings["sidebar_settings"][f"{exp_id}_enabled"] = expander_status[exp_id]
            
            # 更新session_state
            st.session_state.sidebar_settings = new_settings["sidebar_settings"]
            
            # 保存设置
            update_card_view_settings(new_settings)
            st.success("侧边栏设置已更新！") 