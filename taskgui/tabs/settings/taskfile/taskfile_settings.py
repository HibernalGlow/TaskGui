"""任务文件管理设置页面"""
import streamlit as st
import os
import subprocess
import platform
from src.utils.taskfile_manager import get_taskfile_manager
from src.utils.file_utils import find_taskfiles, get_nearest_taskfile, open_file
from src.services.taskfile import read_taskfile, load_taskfile
from src.utils.selection_utils import register_task_file, register_tasks_from_df

def render_taskfile_settings():
    """渲染任务文件管理设置页面"""
    st.markdown("## 📂 任务文件管理")
    
    # 获取任务文件管理器
    manager = get_taskfile_manager()
    
    # 获取当前活动Taskfile
    active_taskfile = manager.get_active_taskfile()
    
    # 显示当前任务文件信息
    st.subheader("当前任务文件", divider="blue")
    if active_taskfile:
        st.markdown(f"**文件名:** `{os.path.basename(active_taskfile)}`")
        st.markdown(f"**完整路径:** `{active_taskfile}`")
        
        # 提供打开当前任务文件的按钮
        if st.button("📝 用系统默认应用打开当前任务文件", key="open_active_file"):
            if open_file(active_taskfile):
                st.success(f"已打开文件: {os.path.basename(active_taskfile)}")
            else:
                st.error("无法打开文件，请检查文件是否存在或系统关联")
    else:
        st.warning("未加载任何任务文件")
    
    # 添加新的任务文件
    st.subheader("添加任务文件", divider="blue")
    
    # 从可用的任务文件中选择
    available_taskfiles = find_taskfiles()
    if available_taskfiles:
        # 过滤掉已添加的任务文件
        existing_taskfiles = manager.get_taskfiles()
        new_taskfiles = [tf for tf in available_taskfiles if tf not in existing_taskfiles]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if new_taskfiles:
                selected_file = st.selectbox(
                    "可用的任务文件:", 
                    options=new_taskfiles,
                    format_func=lambda x: f"{os.path.basename(x)} ({os.path.dirname(x)})",
                    key="taskfile_settings_select"
                )
            else:
                st.info("所有可用的任务文件已添加")
                selected_file = None
        
        with col2:
            if selected_file and st.button("添加", key="add_taskfile_btn"):
                if manager.add_taskfile(selected_file):
                    st.success(f"已添加任务文件: {os.path.basename(selected_file)}")
                    # 刷新页面
                    st.rerun()
                else:
                    st.error("添加任务文件失败")
    
    # 手动添加任务文件
    st.subheader("手动添加", divider="blue")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        manual_taskfile_path = st.text_input(
            "输入任务文件路径:", 
            placeholder="例如: D:/Projects/MyProject/Taskfile.yml",
            key="manual_taskfile_path"
        )
    
    with col2:
        if manual_taskfile_path and st.button("添加", key="add_manual_taskfile_btn"):
            if os.path.exists(manual_taskfile_path):
                if manager.add_taskfile(manual_taskfile_path):
                    st.success(f"已添加任务文件: {os.path.basename(manual_taskfile_path)}")
                    # 刷新页面
                    st.rerun()
                else:
                    st.error("添加任务文件失败")
            else:
                st.error(f"文件不存在: {manual_taskfile_path}")
    
    # 管理已添加的任务文件
    st.subheader("管理任务文件", divider="blue")
    
    # 获取所有已添加的任务文件
    taskfiles = manager.get_taskfiles()
    
    if not taskfiles:
        st.info("未配置任何任务文件")
    else:
        # 使用表格布局展示任务文件
        task_files_data = []
        for i, tf in enumerate(taskfiles):
            is_active = (tf == active_taskfile)
            status = "🟢 活动" if is_active else "⚪ 未选"
            task_files_data.append({
                "序号": i + 1,
                "状态": status,
                "文件名": os.path.basename(tf),
                "路径": tf,
                "操作": tf  # 临时存储路径用于操作按钮
            })
        
        # 创建表格标题行
        col1, col2, col3, col4 = st.columns([0.5, 2, 3.5, 1.5])
        with col1:
            st.markdown("**#**")
        with col2:
            st.markdown("**状态/文件名**")
        with col3:
            st.markdown("**路径**")
        with col4:
            st.markdown("**操作**")
        
        st.markdown("---")
        
        # 创建自定义表格
        for i, tf_data in enumerate(task_files_data):
            col1, col2, col3, col4 = st.columns([0.5, 2, 3.5, 1.5])
            
            with col1:
                st.markdown(f"**{tf_data['序号']}**")
            
            with col2:
                st.markdown(f"{tf_data['状态']} **{tf_data['文件名']}**")
            
            with col3:
                st.caption(tf_data['路径'])
            
            with col4:
                taskfile_path = tf_data['操作']
                is_active = (taskfile_path == active_taskfile)
                
                # 创建三列布局用于操作按钮
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                # 第一列：打开文件按钮
                with btn_col1:
                    if st.button("📝", key=f"open_btn_{i}", help=f"用系统默认应用打开 {os.path.basename(taskfile_path)}"):
                        if os.path.exists(taskfile_path):
                            if open_file(taskfile_path):
                                st.success(f"已打开: {os.path.basename(taskfile_path)}")
                            else:
                                st.error("无法打开文件")
                        else:
                            st.error("文件不存在")
                
                # 第二列：选择/激活按钮或当前状态
                with btn_col2:
                    # 如果不是活动状态，显示设为活动的按钮
                    if not is_active:
                        if st.button("选择", key=f"select_btn_{i}", help="设为活动任务文件"):
                            if manager.set_active_taskfile(taskfile_path):
                                st.success(f"已切换到任务文件: {os.path.basename(taskfile_path)}")
                                # 加载新选择的任务文件
                                tasks_df = load_taskfile(taskfile_path)
                                if tasks_df is not None and not tasks_df.empty:
                                    # 注册任务文件和任务
                                    register_task_file(taskfile_path)
                                    register_tasks_from_df(tasks_df, taskfile_path)
                                    # 更新会话状态
                                    st.session_state.last_taskfile_path = taskfile_path
                                    # 刷新页面
                                    st.rerun()
                            else:
                                st.error("切换任务文件失败")
                    else:
                        # 显示当前活动状态
                        st.info("当前")
                
                # 第三列：删除按钮
                with btn_col3:
                    if not is_active:
                        if st.button("🗑️", key=f"remove_btn_{i}", help="从列表中移除"):
                            if manager.remove_taskfile(taskfile_path):
                                st.success(f"已移除任务文件: {os.path.basename(taskfile_path)}")
                                # 刷新页面
                                st.rerun()
                            else:
                                st.error("移除任务文件失败")
            
            st.markdown("---")
    
    # 合并模式设置
    st.subheader("显示模式设置", divider="blue")
    merge_mode = manager.get_merge_mode()
    
    merge_mode_new = st.checkbox(
        "合并显示所有任务文件中的任务", 
        value=merge_mode,
        key="merge_mode_settings",
        help="启用后，将同时显示所有任务文件中的任务"
    )
    
    if merge_mode_new != merge_mode:
        # 更新合并模式设置
        manager.set_merge_mode(merge_mode_new)
        st.success(f"已{'启用' if merge_mode_new else '禁用'}合并模式")
        # 刷新页面
        st.rerun()
    
    # 显示模式说明
    st.info(
        "**合并模式：** 显示所有任务文件中的所有任务，适合需要全局视图时使用。\n\n"
        "**单一模式：** 只显示当前选中的任务文件中的任务，适合专注于特定项目时使用。"
    )