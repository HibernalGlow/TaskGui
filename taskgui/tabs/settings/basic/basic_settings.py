import streamlit as st
import os
import json
import yaml
from taskgui.config.config_manager import get_config, get_setting, update_setting, save_config

def load_basic_settings():
    """从统一的config.yaml加载基本设置"""
    # 默认设置
    default_settings = {
        "dark_mode": False,
        "auto_load_recent": True,
        "run_mode": "sequential",
        "auto_backup": True,
        "backup_interval": 30,
        "show_welcome": True,
        "max_log_files": 10,
        "notify_on_completion": True,
        # 添加标签页显示默认设置
        "show_card_tab": True,
        "show_table_tab": True,
        "show_preview_tab": True,
        "show_dashboard_tab": True,
        "show_settings_tab": True,
        "show_state_tab": True
    }
    
    # 从配置管理器获取设置
    settings = get_setting("basic_settings")
    
    # 如果没有找到设置，初始化默认值
    if not settings:
        settings = default_settings
        update_setting("basic_settings", value=default_settings)
    else:
        # 合并缺失的默认值
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
        # 保存更新后的设置（如果有默认值被添加）
        update_setting("basic_settings", value=settings)
    
    return settings

def save_basic_settings(settings):
    """保存基本设置到统一的config.yaml"""
    try:
        # 更新基本设置
        update_setting("basic_settings", value=settings)
        return True
    except Exception as e:
        st.error(f"保存设置时出错: {str(e)}")
        return False

def render_basic_settings():
    """渲染基本设置"""
    # 初始化或获取设置
    if 'basic_settings' not in st.session_state:
        st.session_state.basic_settings = load_basic_settings()
    
    with st.form("basic_settings_form"):
        st.subheader("界面设置")
        dark_mode = st.checkbox("启用深色模式", 
                               value=st.session_state.basic_settings.get("dark_mode", False),
                               help="切换深色模式显示")
        
        auto_load = st.checkbox("自动加载最近的任务文件", 
                              value=st.session_state.basic_settings.get("auto_load_recent", True),
                              help="程序启动时自动加载最近打开的任务文件")
        
        show_welcome = st.checkbox("显示欢迎界面", 
                                 value=st.session_state.basic_settings.get("show_welcome", True),
                                 help="程序启动时显示欢迎页面")
        
        # 添加标签页显示设置
        st.subheader("标签页显示设置")
        st.write("选择要在应用中显示的标签页:")
        st.info("更改标签页显示设置后，请刷新页面以应用更改。")
        
        # 显示当前启用的标签页
        enabled_tabs = []
        if st.session_state.basic_settings.get("show_card_tab", True):
            enabled_tabs.append("卡片视图")
        if st.session_state.basic_settings.get("show_table_tab", True):
            enabled_tabs.append("表格视图") 
        if st.session_state.basic_settings.get("show_preview_tab", True):
            enabled_tabs.append("预览")
        if st.session_state.basic_settings.get("show_dashboard_tab", True):
            enabled_tabs.append("仪表盘")
        if st.session_state.basic_settings.get("show_settings_tab", True):
            enabled_tabs.append("设置")
        if st.session_state.basic_settings.get("show_state_tab", True):
            enabled_tabs.append("状态")
            
        st.write(f"当前已启用: {', '.join(enabled_tabs)}")
        
        show_card_tab = st.checkbox("显示卡片视图", 
                                  value=st.session_state.basic_settings.get("show_card_tab", True),
                                  help="启用或禁用卡片视图标签页")
        
        show_table_tab = st.checkbox("显示表格视图", 
                                   value=st.session_state.basic_settings.get("show_table_tab", True),
                                   help="启用或禁用表格视图标签页")
        
        show_preview_tab = st.checkbox("显示预览标签页", 
                                     value=st.session_state.basic_settings.get("show_preview_tab", True),
                                     help="启用或禁用预览标签页")
        
        show_dashboard_tab = st.checkbox("显示仪表盘", 
                                       value=st.session_state.basic_settings.get("show_dashboard_tab", True),
                                       help="启用或禁用仪表盘标签页")
        
        show_settings_tab = st.checkbox("显示设置标签页", 
                                       value=st.session_state.basic_settings.get("show_settings_tab", True),
                                       help="启用或禁用设置标签页", 
                                       disabled=True)  # 设置页面不能禁用，因为用户需要通过它来恢复其他标签页
        
        show_state_tab = st.checkbox("显示状态标签页", 
                                    value=st.session_state.basic_settings.get("show_state_tab", True),
                                    help="启用或禁用状态管理标签页")
        
        st.subheader("任务执行")
        run_mode = st.radio("默认运行模式", 
                          options=["顺序执行", "并行执行"], 
                          index=0 if st.session_state.basic_settings.get("run_mode", "sequential") == "sequential" else 1,
                          help="选择默认任务执行模式")
        
        notify_completion = st.checkbox("任务完成通知", 
                                      value=st.session_state.basic_settings.get("notify_on_completion", True),
                                      help="任务完成时发送系统通知")
        
        st.subheader("数据管理")
        auto_backup = st.checkbox("自动备份数据", 
                                value=st.session_state.basic_settings.get("auto_backup", True),
                                help="自动备份任务数据和设置")
        
        backup_interval = st.slider("备份间隔（分钟）", 
                                  min_value=5, 
                                  max_value=120, 
                                  value=st.session_state.basic_settings.get("backup_interval", 30),
                                  step=5,
                                  help="设置自动备份的时间间隔")
        
        max_logs = st.slider("最大日志文件数", 
                           min_value=5, 
                           max_value=50, 
                           value=st.session_state.basic_settings.get("max_log_files", 10),
                           step=5,
                           help="保留的最大日志文件数量，超过将自动清理")
        
        # 提交按钮
        submitted = st.form_submit_button("保存设置")
        
        if submitted:
            # 检查标签页设置是否发生变化
            tabs_changed = False
            for tab_setting in ["show_card_tab", "show_table_tab", "show_preview_tab", 
                               "show_dashboard_tab", "show_settings_tab", "show_state_tab"]:
                if st.session_state.basic_settings.get(tab_setting, True) != locals()[tab_setting]:
                    tabs_changed = True
                    break
            
            # 更新设置
            new_settings = {
                "dark_mode": dark_mode,
                "auto_load_recent": auto_load,
                "run_mode": "sequential" if run_mode == "顺序执行" else "parallel",
                "auto_backup": auto_backup,
                "backup_interval": backup_interval,
                "show_welcome": show_welcome,
                "max_log_files": max_logs,
                "notify_on_completion": notify_completion,
                # 添加标签页显示设置
                "show_card_tab": show_card_tab,
                "show_table_tab": show_table_tab,
                "show_preview_tab": show_preview_tab,
                "show_dashboard_tab": show_dashboard_tab,
                "show_settings_tab": True,  # 设置页始终启用
                "show_state_tab": show_state_tab
            }
            
            # 保存到session_state
            st.session_state.basic_settings = new_settings
            
            # 保存到文件
            if save_basic_settings(new_settings):
                st.success("基本设置已保存")
                
                # 如果标签页设置发生变化，提示刷新页面
                if tabs_changed:
                    st.warning("标签页设置已更改，请刷新页面以应用新设置")
    
    # 表单外部添加刷新按钮
    if 'basic_settings' in st.session_state and st.button("刷新页面"):
        st.rerun()