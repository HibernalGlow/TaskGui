import streamlit as st
from ..services.taskfile import read_taskfile
from streamlit_tags import st_tags
from ..utils.selection_utils import save_favorite_tags

def render_sidebar(current_taskfile):
    """渲染侧边栏控件"""
    with st.sidebar:
        st.title("任务管理器")
        
        # 添加任务过滤
        st.markdown("## 过滤任务")
        
        # 按名称搜索
        search_term = st.text_input("搜索任务名称:", key="search_task")
        
        # 获取所有标签
        all_tags = get_all_tags(current_taskfile)
        
        # 初始化常用标签和筛选状态
        if 'favorite_tags' not in st.session_state:
            st.session_state.favorite_tags = []
            
        # 确保tags_filter存在于session_state中
        if 'tags_filter' not in st.session_state:
            st.session_state.tags_filter = []
        
        # 确保tags_widget_key存在，用于控制st_tags组件的刷新
        if 'tags_widget_key' not in st.session_state:
            st.session_state.tags_widget_key = 0
            
        # 显示快速标签过滤按钮
        st.markdown("### ⚡ 快速选择")
        
        # 添加操作按钮
        quick_cols = st.columns(2)
        with quick_cols[0]:
            if st.button("🔍 全部", key="show_all_tags"):
                # 清空筛选标签
                st.session_state.tags_filter = []
                # 增加key值以强制刷新st_tags组件
                st.session_state.tags_widget_key += 1
                st.rerun()
                
        with quick_cols[1]:
            if st.button("❌ 清除", key="clear_tag_filters"):
                # 清空筛选标签
                st.session_state.tags_filter = []
                # 增加key值以强制刷新st_tags组件
                st.session_state.tags_widget_key += 1
                st.rerun()
        
        # 显示收藏标签作为快速过滤器按钮
        if st.session_state.favorite_tags:
            st.markdown("#### 常用标签")
            # 使用更紧凑的布局显示常用标签
            cols_per_row = 2
            for i in range(0, len(st.session_state.favorite_tags), cols_per_row):
                fav_tag_cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(st.session_state.favorite_tags):
                        tag = sorted(st.session_state.favorite_tags)[i + j]
                        with fav_tag_cols[j]:
                            # 创建按钮，点击时添加或移除该标签的过滤
                            is_active = tag in st.session_state.tags_filter
                            btn_label = f"✓ #{tag}" if is_active else f"#{tag}"
                            btn_type = "primary" if is_active else "secondary"
                            
                            if st.button(btn_label, key=f"quick_{tag}", type=btn_type):
                                # 切换标签的状态
                                if tag in st.session_state.tags_filter:
                                    # 移除标签
                                    st.session_state.tags_filter.remove(tag)
                                else:
                                    # 添加标签
                                    st.session_state.tags_filter.append(tag)
                                # 增加key值以强制刷新st_tags组件
                                st.session_state.tags_widget_key += 1
                                st.rerun()
            
        # 快速标签过滤器
        st.markdown("### 🏷️ 标签筛选")
        
        # 添加一个下拉框，用于快速选择标签
        if all_tags:
            tag_dropdown = st.selectbox(
                "从列表选择标签:",
                options=[""] + sorted(all_tags),  # 添加空选项作为默认值
                index=0,  # 默认选择第一个（空选项）
                key="tag_dropdown"
            )
            
            # 如果用户从下拉框选择了一个非空标签，添加到标签过滤器中
            if tag_dropdown and tag_dropdown not in st.session_state.tags_filter:
                st.session_state.tags_filter.append(tag_dropdown)
                # 增加key值以强制刷新st_tags组件
                st.session_state.tags_widget_key += 1
                st.rerun()
        
        # 使用streamlit-tags组件进行标签选择
        # 通过动态key值确保组件刷新
        widget_key = f"tags_selector_{st.session_state.tags_widget_key}"
        
        # 这个组件允许用户通过文本输入和下拉菜单选择标签
        selected_tags = st_tags(
            label="",  # 移除标签文本，避免重复
            text="输入或选择标签...",
            value=st.session_state.tags_filter,  # 使用当前选中的标签作为默认值
            suggestions=sorted(all_tags),  # 所有可用标签作为建议
            maxtags=10,  # 最多可以选择的标签数
            key=widget_key
        )
        
        # 将selected_tags的结果同步到session_state
        st.session_state.tags_filter = selected_tags
        
        # 常用标签管理
        with st.expander("管理常用标签", expanded=False):
            st.markdown("选择要保存为常用标签的标签:")
            
            # 初始化标记，用于检测常用标签是否有变化
            tags_changed = False
            
            # 创建一个多列布局，用于显示所有标签的checkbox
            if all_tags:
                all_tag_cols = st.columns(3)
                for i, tag in enumerate(sorted(all_tags)):
                    with all_tag_cols[i % 3]:
                        # 创建checkbox来添加/移除收藏标签
                        was_selected = tag in st.session_state.favorite_tags
                        is_selected = st.checkbox(tag, value=was_selected, key=f"fav_{tag}")
                        
                        # 检测是否发生变化
                        if was_selected != is_selected:
                            tags_changed = True
                            
                            if is_selected and tag not in st.session_state.favorite_tags:
                                st.session_state.favorite_tags.append(tag)
                            elif not is_selected and tag in st.session_state.favorite_tags:
                                st.session_state.favorite_tags.remove(tag)
            else:
                st.info("没有找到标签")
            
            # 如果常用标签有变化，保存到本地
            if tags_changed:
                save_favorite_tags(st.session_state.favorite_tags)
                st.success("常用标签已保存")
        
        # 添加并行执行模式选项
        st.markdown("## 执行设置")
        
        if 'run_parallel' not in st.session_state:
            st.session_state.run_parallel = False
            
        parallel_mode = st.checkbox(
            "并行执行任务", 
            value=st.session_state.run_parallel,
            help="选中时，多个任务将同时启动"
        )
        
        st.session_state.run_parallel = parallel_mode
        
        # 显示已选任务数量
        if 'selected_tasks' in st.session_state and st.session_state.selected_tasks:
            st.markdown(f"## 已选择 {len(st.session_state.selected_tasks)} 个任务")
        
        # 添加关于部分
        with st.expander("关于"):
            st.markdown("""
            ### 任务管理器
            
            这个工具可以帮助您管理和运行各种任务。
            
            **功能**:
            - 支持多种视图模式
            - 可以同时运行多个任务
            - 支持文件浏览和打开
            - 可以复制命令到剪贴板
            
            **使用方法**:
            1. 选择您喜欢的视图模式
            2. 筛选您想要的任务
            3. 选择任务并执行操作
            """)

def get_all_tags(taskfile_path):
    """获取所有可用的标签"""
    try:
        tasks_df = read_taskfile(taskfile_path)
        all_tags = []
        for tags in tasks_df["tags"]:
            if isinstance(tags, list):
                all_tags.extend(tags)
        return sorted(list(set(all_tags)))
    except Exception as e:
        return []