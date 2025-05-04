import streamlit as st
import os
from taskgui.config.taskfile_manager import get_taskfile_manager
from taskgui.utils.file_utils import find_taskfiles, get_nearest_taskfile
from taskgui.services.taskfile import load_taskfile
from taskgui.utils.selection_utils import register_task_file, register_tasks_from_df

def render_taskfile_manager_expander(current_taskfile):
    """渲染任务文件管理折叠面板"""
    # 获取任务文件管理器
    manager = get_taskfile_manager()
    
    with st.expander("📂 任务文件管理", expanded=False):
        # 显示当前任务文件
        if current_taskfile:
            st.markdown(f"**当前任务文件:** `{os.path.basename(current_taskfile)}`")
            st.caption(f"路径: `{current_taskfile}`")
        else:
            st.info("未加载任何任务文件")
        
        # 添加新的任务文件
        st.subheader("添加任务文件", divider="blue")
        
        # 方法1: 从可用的任务文件中选择
        available_taskfiles = find_taskfiles()
        if available_taskfiles:
            # 过滤掉已添加的任务文件
            existing_taskfiles = manager.get_taskfiles()
            new_taskfiles = [tf for tf in available_taskfiles if tf not in existing_taskfiles]
            
            if new_taskfiles:
                selected_file = st.selectbox(
                    "可用的任务文件:", 
                    options=new_taskfiles,
                    format_func=lambda x: f"{os.path.basename(x)} ({os.path.dirname(x)})"
                )
                
                if st.button("添加选定的任务文件"):
                    if manager.add_taskfile(selected_file):
                        st.success(f"已添加任务文件: {os.path.basename(selected_file)}")
                        # 刷新页面
                        st.rerun()
                    else:
                        st.error("添加任务文件失败")
            else:
                st.info("所有可用的任务文件已添加")
        
        # 方法2: 手动输入路径 - 不使用嵌套expander，改用checkbox控制显示
        show_manual_add = st.checkbox("手动添加任务文件", value=False, key="show_manual_add")
        
        if show_manual_add:
            st.markdown("---")
            st.markdown("#### 手动添加任务文件")
            taskfile_path = st.text_input("任务文件路径:", placeholder="例如: /path/to/Taskfile.yml")
            
            if st.button("添加", key="add_taskfile_manual"):
                if taskfile_path and os.path.exists(taskfile_path):
                    if manager.add_taskfile(taskfile_path):
                        st.success(f"已添加任务文件: {os.path.basename(taskfile_path)}")
                        # 刷新页面
                        st.rerun()
                    else:
                        st.error("添加任务文件失败")
                else:
                    st.error(f"文件不存在: {taskfile_path}")
            st.markdown("---")
        
        # 管理已添加的任务文件
        st.subheader("管理任务文件", divider="blue")
        
        # 获取所有已添加的任务文件
        taskfiles = manager.get_taskfiles()
        active_taskfile = manager.get_active_taskfile()
        
        if not taskfiles:
            st.info("未配置任何任务文件")
        else:
            # 列出所有任务文件，并提供切换和删除选项
            for tf in taskfiles:
                if not os.path.exists(tf):
                    continue  # 跳过不存在的文件
                    
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    is_active = (tf == active_taskfile)
                    prefix = "🟢 " if is_active else "⚪ "
                    
                    if st.button(
                        f"{prefix}{os.path.basename(tf)}", 
                        key=f"select_{tf}",
                        help=f"切换到此任务文件\n{tf}"
                    ):
                        if manager.set_active_taskfile(tf):
                            st.success(f"已切换到任务文件: {os.path.basename(tf)}")
                            # 加载新选择的任务文件
                            tasks_df = load_taskfile(tf)
                            if tasks_df is not None and not tasks_df.empty:
                                # 注册任务文件和任务
                                register_task_file(tf)
                                register_tasks_from_df(tasks_df, tf)
                                # 更新会话状态
                                st.session_state.last_taskfile_path = tf
                                # 刷新页面
                                st.rerun()
                        else:
                            st.error("切换任务文件失败")
                
                with col2:
                    # 不允许删除当前活动的任务文件
                    if tf != active_taskfile:
                        if st.button("❌", key=f"remove_{tf}", help=f"移除此任务文件\n{tf}"):
                            if manager.remove_taskfile(tf):
                                st.success(f"已移除任务文件: {os.path.basename(tf)}")
                                # 刷新页面
                                st.rerun()
                            else:
                                st.error("移除任务文件失败")
                
                # 显示路径
                st.caption(tf)
        
        # 合并模式设置
        st.subheader("显示模式", divider="blue")
        merge_mode = manager.get_merge_mode()
        
        if st.checkbox("合并显示所有任务文件中的任务", value=merge_mode, key="merge_mode_checkbox"):
            if not merge_mode:
                # 启用合并模式
                manager.set_merge_mode(True)
                st.success("已启用合并模式")
                # 刷新页面
                st.rerun()
        else:
            if merge_mode:
                # 禁用合并模式
                manager.set_merge_mode(False)
                st.success("已禁用合并模式")
                # 刷新页面
                st.rerun()
        
        st.info(
            "合并模式下，将显示所有任务文件中的任务。\n\n"
            "单一模式下，只显示当前选中的任务文件中的任务。"
        )