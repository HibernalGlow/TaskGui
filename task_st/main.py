import streamlit as st
import pandas as pd
import os
import sys
import traceback
from src import (
    init_session_state, 
    setup_css,
    load_taskfile, 
    prepare_dataframe, 
    get_all_tags, 
    filter_tasks,
    render_table_view,
    render_card_view,
    render_sidebar,
    render_tag_filters,
    find_taskfiles,
    get_nearest_taskfile
)
from src.services.taskfile import read_taskfile
from src.utils.file_utils import open_file, get_directory_files
from src.views.styles import apply_custom_styles
from src.components.preview_card import render_shared_preview
from src.utils.selection_utils import (
    get_global_state, update_global_state, 
    export_yaml_state as export_global_state_yaml, 
    import_global_state_yaml,
    save_global_state, register_task_file, register_tasks_from_df,
    update_task_runtime, record_task_run, init_global_state
)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置页面配置
st.set_page_config(
    page_title="任务管理器",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加自定义CSS
st.markdown("""
<style>
    .tag {
        background-color: #f0f2f6;
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
        background-color: #f0f2f6;
        font-weight: bold;
    }
    
    /* 预览区域样式 */
    .preview-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-top: 20px;
        border: 1px solid #e6e6e6;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    try:
        # 初始化会话状态
        init_session_state()
        
        # 设置CSS样式
        setup_css()
        
        # 初始化全局状态
        init_global_state()
        
        # 获取任务文件列表
        taskfiles = find_taskfiles()
        if not taskfiles:
            st.error("未找到任务文件。请确保当前目录下有Taskfile.yml文件。")
            return
        
        # 获取默认任务文件
        default_taskfile = get_nearest_taskfile()
        if not default_taskfile:
            default_taskfile = taskfiles[0]
        
        # 注册任务文件
        register_task_file(default_taskfile)
        
        # 加载任务文件
        tasks_df = load_taskfile(default_taskfile)
        if tasks_df is None or tasks_df.empty:
            st.error("无法加载任务文件或任务文件为空。")
            return
        
        # 注册所有任务
        register_tasks_from_df(tasks_df, default_taskfile)
        
        # 准备数据框
        tasks_df = prepare_dataframe(tasks_df)
        
        # 获取所有标签
        all_tags = get_all_tags(tasks_df)
        
        # 渲染侧边栏
        render_sidebar(default_taskfile)
        
        # 渲染标签过滤器
        render_tag_filters(all_tags)
        
        # 过滤任务
        filtered_df = filter_tasks(tasks_df)
        
        # 共享预览区域 - 放在页签上方
        preview_expander = st.expander("📌 选中任务预览", expanded=True)
        with preview_expander:
            render_shared_preview(filtered_df, default_taskfile)
        
        # 使用字典存储页签标题和索引的映射，便于动态管理
        tab_names = ["📊 表格视图", "🗂️ 卡片视图", "📈 仪表盘", "⚙️ 设置", "🔍 状态管理"]
        tab_indices = {name: idx for idx, name in enumerate(tab_names)}
        
        # 创建页签
        tabs = st.tabs(tab_names)
        
        # 表格视图
        with tabs[tab_indices["📊 表格视图"]]:
            render_table_view(filtered_df, default_taskfile, show_sidebar=False)  # 关闭右侧预览
        
        # 卡片视图
        with tabs[tab_indices["🗂️ 卡片视图"]]:
            render_card_view(filtered_df, default_taskfile)
        
        # 仪表盘页签
        with tabs[tab_indices["📈 仪表盘"]]:
            st.markdown("## 📊 任务仪表盘")
            st.info("仪表盘功能正在开发中...")
            
            # 占位内容
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总任务数", len(tasks_df))
            with col2:
                st.metric("选中任务", len(st.session_state.selected_tasks))
            
            # 示例图表
            st.subheader("标签分布")
            st.write("此处将显示任务标签的分布统计")
        
        # 设置页签
        with tabs[tab_indices["⚙️ 设置"]]:
            st.markdown("## ⚙️ 系统设置")
            st.info("设置功能正在开发中...")
            
            # 示例设置选项
            st.subheader("界面设置")
            st.checkbox("启用深色模式", value=False, disabled=True)
            st.checkbox("自动加载最近的任务文件", value=True, disabled=True)
            
            st.subheader("任务执行")
            st.radio("默认运行模式", options=["顺序执行", "并行执行"], index=0, disabled=True)
        
        # 状态管理页签
        with tabs[tab_indices["🔍 状态管理"]]:
            render_state_manager()
            
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc())

def filter_tasks(tasks_df):
    """根据过滤条件过滤任务"""
    filtered_df = tasks_df.copy()
    
    # 应用搜索过滤
    if 'search_task' in st.session_state and st.session_state.search_task:
        search_term = st.session_state.search_task.lower()
        # 过滤名称或描述包含搜索词的任务
        mask = filtered_df['name'].str.lower().str.contains(search_term, na=False) | \
               filtered_df['description'].str.lower().str.contains(search_term, na=False)
        filtered_df = filtered_df[mask]
    
    # 应用标签过滤
    if 'tags_filter' in st.session_state and st.session_state.tags_filter:
        tags_to_filter = st.session_state.tags_filter
        # 过滤包含所选标签的任务
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: any(tag in x for tag in tags_to_filter) if isinstance(x, list) else False
        )]
    
    return filtered_df

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
    st.write(f"选中任务数: {len([t for t, info in global_state.get('tasks', {}).items() if info.get('selected', False)])}")
    
    # 创建标签页
    tabs = st.tabs(["YAML编辑器", "任务文件", "选中任务", "任务运行时", "用户偏好"])
    
    # YAML编辑器标签页
    with tabs[0]:
        st.subheader("YAML编辑器")
        
        # 导出为YAML字符串
        yaml_str = export_global_state_yaml()
        
        # 使用markdown代码块显示YAML（只读视图）
        st.markdown("### 当前状态 (只读视图)")
        st.markdown(f"```yaml\n{yaml_str}\n```")
        
        # 添加编辑区域
        edited_yaml = st.text_area("编辑状态YAML", yaml_str, height=400)
        
        # 保存修改按钮
        if st.button("应用修改", key="apply_yaml_changes"):
            if import_global_state_yaml(edited_yaml):
                st.success("状态已更新")
            else:
                st.error("无法更新状态，YAML格式可能有误")
    
    # 任务文件标签页
    with tabs[1]:
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
    
    # 选中任务标签页
    with tabs[2]:
        st.subheader("选中任务")
        
        # 显示选中的任务
        selected_tasks = [name for name, info in global_state.get('tasks', {}).items() 
                         if info.get('selected', False)]
        
        if selected_tasks:
            for i, task_name in enumerate(selected_tasks):
                task_info = global_state.get('tasks', {}).get(task_name, {})
                with st.expander(f"{i+1}. {task_name}", expanded=False):
                    st.write(f"选中时间: {task_info.get('last_selected', 'N/A')}")
                    st.write(f"来源文件: {task_info.get('source_file', 'N/A')}")
                    
                    # 显示任务数据
                    task_data = task_info.get('data', {})
                    if task_data:
                        st.write("任务数据:")
                        for key, value in task_data.items():
                            st.write(f"- {key}: {value}")
                    
                    # 取消选择按钮
                    if st.button("取消选择", key=f"unselect_{task_name}"):
                        task_info['selected'] = False
                        update_global_state(global_state)
                        st.rerun()
        else:
            st.info("没有选中的任务")
    
    # 任务运行时标签页
    with tabs[3]:
        st.subheader("任务运行时数据")
        
        # 创建任务运行时数据表格
        runtime_data = []
        for task_name, task_info in global_state.get('tasks', {}).items():
            runtime = task_info.get('runtime', {})
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
                task_runtime = global_state.get('tasks', {}).get(selected_task, {}).get('runtime', {})
                st.json(task_runtime)
                
                # 模拟运行按钮
                if st.button("模拟运行", key=f"simulate_run_{selected_task}"):
                    record_task_run(selected_task, status="simulated")
                    st.success(f"已记录 {selected_task} 的模拟运行")
                    st.rerun()
                
                # 添加自定义标志
                st.subheader("添加自定义标志")
                col1, col2 = st.columns(2)
                with col1:
                    flag_key = st.text_input("标志名称", key="flag_key")
                with col2:
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
    
    # 用户偏好标签页
    with tabs[4]:
        st.subheader("用户偏好设置")
        
        user_prefs = global_state.get('user_preferences', {})
        if user_prefs:
            # 显示当前偏好
            st.json(user_prefs)
            
            # 简单编辑
            st.subheader("编辑常用设置")
            
            # 默认视图
            view_options = ["aggrid", "card", "group"]
            default_view = st.selectbox(
                "默认视图", 
                options=view_options,
                index=view_options.index(user_prefs.get('default_view', 'aggrid')) if user_prefs.get('default_view') in view_options else 0
            )
            
            # 主题
            theme_options = ["light", "dark", "blue"]
            theme = st.selectbox(
                "主题", 
                options=theme_options,
                index=theme_options.index(user_prefs.get('ui_settings', {}).get('theme', 'light')) if user_prefs.get('ui_settings', {}).get('theme') in theme_options else 0
            )
            
            # 应用按钮
            if st.button("应用设置", key="apply_user_prefs"):
                # 更新用户偏好
                if 'ui_settings' not in user_prefs:
                    user_prefs['ui_settings'] = {}
                
                user_prefs['default_view'] = default_view
                user_prefs['ui_settings']['theme'] = theme
                
                # 更新全局状态
                global_state['user_preferences'] = user_prefs
                update_global_state(global_state)
                st.success("用户偏好已更新")
                st.rerun()
        else:
            st.info("没有用户偏好数据")

if __name__ == "__main__":
    main()