import streamlit as st
import pandas as pd
import os
import yaml
from code_editor import code_editor
from src.utils.selection_utils import (
    get_global_state, update_global_state, 
    export_yaml_state as export_global_state_yaml, 
    import_global_state_yaml,
    validate_yaml, update_task_runtime, record_task_run,
    load_local_config, save_user_preferences
)

def render_state_manager():
    """渲染状态管理器页面"""
    st.markdown("## 🔍 全局状态管理")
    st.info("在这里您可以查看和修改系统的全局状态数据")
    
    # 获取当前状态
    global_state = get_global_state()
    
    # 基本状态信息
    st.write(f"版本: {global_state.get('version', 'N/A')}")
    st.write(f"最后更新: {global_state.get('last_updated', 'N/A')}")
    st.write(f"任务文件数: {len(global_state.get('task_files', {}))}")
    st.write(f"任务总数: {len(global_state.get('tasks', {}))}")
    st.write(f"选中任务数: {len([t for t, info in global_state.get('select', {}).items() if info])}")
    
    # 创建标签页名称和对应索引的映射
    tab_names = ["YAML编辑器", "任务文件", "选中任务", "任务运行时", "用户偏好"]
    tab_indices = {name: idx for idx, name in enumerate(tab_names)}
    
    # 创建标签页
    tabs = st.tabs(tab_names)
    
    # ===== YAML编辑器标签页 =====
    with tabs[tab_indices["YAML编辑器"]]:
        st.subheader("YAML编辑器")
        
        # 导出为YAML字符串
        yaml_str = export_global_state_yaml()
        
        # 添加操作按钮到编辑器上方
        cols = st.columns([1, 1, 1, 1])
        with cols[0]:
            # 保存修改按钮
            if st.button("应用修改", key="apply_yaml_changes"):
                try:
                    # 使用验证函数检查YAML格式
                    valid_yaml, error_msg = validate_yaml(edited_yaml if 'edited_yaml' in locals() else yaml_str)
                    
                    if valid_yaml and import_global_state_yaml(edited_yaml if 'edited_yaml' in locals() else yaml_str):
                        st.success("状态已更新")
                    else:
                        if error_msg:
                            st.error(f"YAML格式有误: {error_msg}")
                        else:
                            st.error("无法更新状态")
                except Exception as e:
                    st.error(f"更新失败: {str(e)}")
        
        with cols[1]:
            # 重置按钮
            if st.button("重置", key="reset_yaml"):
                if 'yaml_editor' in st.session_state:
                    st.session_state.yaml_editor = yaml_str
                st.rerun()
        
        with cols[2]:
            # 添加表格视图切换
            if st.button("表格视图", key="toggle_table_view"):
                if "yaml_table_view" not in st.session_state:
                    st.session_state.yaml_table_view = True
                else:
                    st.session_state.yaml_table_view = not st.session_state.yaml_table_view
                st.rerun()
        
        with cols[3]:
            # YAML验证按钮
            if st.button("验证YAML", key="validate_yaml"):
                if 'edited_yaml' in locals():
                    try:
                        valid_yaml, error_msg = validate_yaml(edited_yaml)
                        if valid_yaml:
                            st.success("YAML格式正确")
                        else:
                            st.error(f"YAML格式有误: {error_msg}")
                    except Exception as e:
                        st.error(f"验证错误: {str(e)}")
        
        # 将编辑器放在可折叠区域内
        with st.expander("展开/折叠 YAML编辑器", expanded=False):
            # 添加折叠功能提示
            st.info("💡 提示：点击行号左侧的箭头可以折叠/展开YAML结构。您也可以使用快捷键 Alt+点击 或 Ctrl+Alt+[/] 来折叠/展开代码块。")
            
            # 使用CodeMirror编辑器
            edited_yaml = code_editor(
                yaml_str,
                lang="yaml",
                height=[600, 850],
                theme="dark",
                options={
                    "lineNumbers": True,
                    "lineWrapping": True,
                    "indentWithTabs": False,
                    "tabSize": 2,
                    "scrollbarStyle": "native",
                    "autoCloseBrackets": True,
                    "matchBrackets": True,
                    "autoRefresh": True,
                    "foldGutter": True,
                    "gutters": ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
                    "foldOptions": {
                        "widget": "▾ "
                    }
                },
                key="yaml_editor"
            )["text"]
        
        # 如果启用了表格视图，显示YAML的表格表示
        if "yaml_table_view" in st.session_state and st.session_state.yaml_table_view:
            try:
                # 解析YAML到字典
                yaml_dict = yaml.safe_load(edited_yaml)
                
                # 第一级键值对展示为表格
                st.subheader("YAML顶级结构表格视图")
                
                # 创建第一级数据
                first_level_data = []
                for key, value in yaml_dict.items():
                    value_type = type(value).__name__
                    value_preview = str(value)
                    if len(value_preview) > 50:
                        value_preview = value_preview[:47] + "..."
                    
                    first_level_data.append({
                        "键": key,
                        "值类型": value_type,
                        "值预览": value_preview,
                        "子项数量": len(value) if isinstance(value, (dict, list)) else 0
                    })
                
                # 显示表格
                if first_level_data:
                    first_level_df = pd.DataFrame(first_level_data)
                    st.dataframe(first_level_df, use_container_width=True)
                else:
                    st.info("YAML中没有顶级键")
            except Exception as e:
                st.error(f"无法解析YAML为表格: {str(e)}")
                
        # 显示本地配置
        with st.expander("本地配置", expanded=False):
            local_config = load_local_config()
            
            if local_config:
                st.subheader("本地存储的配置")
                
                # 以YAML形式显示
                st.code(yaml.dump(local_config, sort_keys=False, allow_unicode=True, indent=2), language="yaml")
                
                # 显示常用标签
                if "favorite_tags" in local_config and local_config["favorite_tags"]:
                    st.subheader("常用标签")
                    
                    # 创建多列布局显示标签
                    cols_per_row = 4
                    tags = sorted(local_config["favorite_tags"])
                    rows = (len(tags) + cols_per_row - 1) // cols_per_row  # 向上取整
                    
                    for row in range(rows):
                        tag_cols = st.columns(cols_per_row)
                        for col in range(cols_per_row):
                            idx = row * cols_per_row + col
                            if idx < len(tags):
                                tag = tags[idx]
                                with tag_cols[col]:
                                    st.code(f"#{tag}", language=None)
            else:
                st.info("未找到本地配置文件或配置为空")
    
    # ===== 任务文件标签页 =====
    with tabs[tab_indices["任务文件"]]:
        st.subheader("任务文件")
        
        # 显示任务文件
        task_files = global_state.get('task_files', {})
        if task_files:
            for file_path, file_info in task_files.items():
                with st.expander(f"📄 {os.path.basename(file_path)}", expanded=False):
                    st.write(f"路径: {file_path}")
                    st.write(f"最后加载: {file_info.get('last_loaded', 'N/A')}")
                    
                    # 显示元数据
                    meta = file_info.get('meta', {})
                    if meta:
                        st.write("元数据:")
                        for key, value in meta.items():
                            st.write(f"- {key}: {value}")
        else:
            st.info("没有任务文件信息")
    
    # ===== 选中任务标签页 =====
    with tabs[tab_indices["选中任务"]]:
        st.subheader("选中任务")
        
        # 显示选中的任务
        selected_tasks = [name for name, is_selected in global_state.get('select', {}).items() 
                         if is_selected]
        
        if selected_tasks:
            for i, task_name in enumerate(selected_tasks):
                task_info = global_state.get('tasks', {}).get(task_name, {})
                with st.expander(f"{i+1}. {task_name}", expanded=False):
                    # 获取任务所属文件
                    source_file = task_info.get('source_file', 'N/A')
                    
                    # 尝试获取最后选中时间
                    last_selected = None
                    if source_file in global_state.get('task_files', {}):
                        if 'task_state' in global_state['task_files'][source_file]:
                            if task_name in global_state['task_files'][source_file]['task_state']:
                                last_selected = global_state['task_files'][source_file]['task_state'][task_name].get('last_selected', 'N/A')
                    
                    st.write(f"选中时间: {last_selected if last_selected else 'N/A'}")
                    st.write(f"来源文件: {source_file}")
                    
                    # 显示任务数据
                    task_data = task_info.get('data', {})
                    if task_data:
                        st.write("任务数据:")
                        for key, value in task_data.items():
                            st.write(f"- {key}: {value}")
                    
                    # 取消选择按钮
                    if st.button("取消选择", key=f"unselect_{task_name}"):
                        # 更新select字典
                        global_state['select'][task_name] = False
                        
                        # 如果存在task_state，也更新它
                        if source_file in global_state.get('task_files', {}):
                            if 'task_state' in global_state['task_files'][source_file]:
                                if task_name in global_state['task_files'][source_file]['task_state']:
                                    global_state['task_files'][source_file]['task_state'][task_name]['selected'] = False
                        
                        update_global_state(global_state)
                        st.rerun()
        else:
            st.info("没有选中的任务")
    
    # ===== 任务运行时标签页 =====
    with tabs[tab_indices["任务运行时"]]:
        st.subheader("任务运行时数据")
        
        # 创建任务运行时数据表格
        runtime_data = []
        for task_name, task_info in global_state.get('tasks', {}).items():
            # 获取来源文件
            source_file = task_info.get('source_file')
            runtime = {}
            
            # 从task_state获取运行时数据
            if source_file and source_file in global_state.get('task_files', {}):
                if 'task_state' in global_state['task_files'][source_file]:
                    if task_name in global_state['task_files'][source_file]['task_state']:
                        if 'runtime' in global_state['task_files'][source_file]['task_state'][task_name]:
                            runtime = global_state['task_files'][source_file]['task_state'][task_name]['runtime']
            
            runtime_data.append({
                "任务名称": task_name,
                "运行次数": runtime.get('run_count', 0),
                "最后运行": runtime.get('last_run', 'N/A'),
                "最后状态": runtime.get('last_status', 'N/A'),
                "自定义标志": len(runtime.get('custom_flags', {}))
            })
        
        if runtime_data:
            runtime_df = pd.DataFrame(runtime_data)
            st.dataframe(runtime_df, use_container_width=True)
            
            # 任务运行时详情
            st.subheader("任务运行时详情")
            task_options = [task["任务名称"] for task in runtime_data]
            selected_task = st.selectbox("选择任务查看详情", task_options)
            
            if selected_task:
                # 获取来源文件
                source_file = None
                if selected_task in global_state.get('tasks', {}):
                    source_file = global_state['tasks'][selected_task].get('source_file')
                
                task_runtime = {}
                if source_file and source_file in global_state.get('task_files', {}):
                    if 'task_state' in global_state['task_files'][source_file]:
                        if selected_task in global_state['task_files'][source_file]['task_state']:
                            if 'runtime' in global_state['task_files'][source_file]['task_state'][selected_task]:
                                task_runtime = global_state['task_files'][source_file]['task_state'][selected_task]['runtime']
                
                st.json(task_runtime)
                
                # 模拟运行按钮
                if st.button("模拟运行", key=f"simulate_run_{selected_task}"):
                    record_task_run(selected_task, status="simulated")
                    st.success(f"已记录 {selected_task} 的模拟运行")
                    st.rerun()
                
                # 添加自定义标志
                st.subheader("添加自定义标志")
                flag_cols = st.columns(2)
                with flag_cols[0]:
                    flag_key = st.text_input("标志名称", key="flag_key")
                with flag_cols[1]:
                    flag_value = st.text_input("标志值", key="flag_value")
                
                if st.button("添加标志", key="add_flag") and flag_key:
                    if "custom_flags" not in task_runtime:
                        task_runtime["custom_flags"] = {}
                    
                    task_runtime["custom_flags"][flag_key] = flag_value
                    update_task_runtime(selected_task, {"custom_flags": task_runtime["custom_flags"]})
                    st.success(f"已添加标志 {flag_key}")
                    st.rerun()
        else:
            st.info("没有任务运行时数据")
    
    # ===== 用户偏好标签页 =====
    with tabs[tab_indices["用户偏好"]]:
        st.subheader("用户偏好设置")
        
        user_prefs = global_state.get('user_preferences', {})
        if user_prefs:
            # 显示当前偏好
            st.json(user_prefs)
            
            # 简单编辑
            st.subheader("编辑常用设置")
            
            # 默认视图
            view_options = ["aggrid", "card", "group"]
            default_view_index = 0
            if user_prefs.get('default_view') in view_options:
                default_view_index = view_options.index(user_prefs.get('default_view'))
                
            default_view = st.selectbox(
                "默认视图", 
                options=view_options,
                index=default_view_index
            )
            
            # 主题
            theme_options = ["light", "dark", "blue"]
            theme_index = 0
            if user_prefs.get('ui_settings', {}).get('theme') in theme_options:
                theme_index = theme_options.index(user_prefs.get('ui_settings', {}).get('theme'))
                
            theme = st.selectbox(
                "主题", 
                options=theme_options,
                index=theme_index
            )
            
            # 应用按钮
            if st.button("应用设置", key="apply_user_prefs"):
                # 更新用户偏好
                if 'ui_settings' not in user_prefs:
                    user_prefs['ui_settings'] = {}
                
                user_prefs['default_view'] = default_view
                user_prefs['ui_settings']['theme'] = theme
                
                # 保存到本地配置
                save_user_preferences(user_prefs)
                st.success("用户偏好已更新")
                st.rerun()
        else:
            st.info("没有用户偏好数据") 