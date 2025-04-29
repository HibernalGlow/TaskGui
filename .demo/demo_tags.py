import streamlit as st
import pandas as pd
import json
import random
from datetime import datetime

# 尝试导入必要的库，如果不存在则提供安装说明
libraries_installed = True
installation_instructions = ""

try:
    from streamlit_tags import st_tags
except ImportError:
    libraries_installed = False
    installation_instructions += "- 安装 streamlit-tags: `pip install streamlit-tags`\n"

try:
    from streamlit_extras.tags import tagger_component
except ImportError:
    libraries_installed = False
    installation_instructions += "- 安装 streamlit-extras: `pip install streamlit-extras`\n"

# 页面配置
st.set_page_config(
    page_title="Streamlit 标签组件比较",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    /* 标签样式 */
    .tag {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 2px 8px;
        margin: 2px;
        display: inline-block;
        font-size: 0.8em;
    }
    
    .tag-selected {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 2px 8px;
        margin: 2px;
        display: inline-block;
        font-size: 0.8em;
    }
    
    .tag-clickable {
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .tag-clickable:hover {
        background-color: #e1e1e1;
    }
    
    /* 标签通用容器 */
    .tags-container {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-bottom: 10px;
    }
    
    /* 库演示区域样式 */
    .library-section {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .streamlit-tags {
        background-color: #f0f7ff;
    }
    
    .streamlit-extras {
        background-color: #f0fff7;
    }
    
    .custom-tags {
        background-color: #fff7f0;
    }
    
    .advanced-tags {
        background-color: #f7f0ff;
    }
    
    /* 统计卡片样式 */
    .stat-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        color: #333;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9em;
    }
    
    /* 标签管理器样式 */
    .tag-editor {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    
    .tag-list-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px;
        border-bottom: 1px solid #eee;
    }
    
    .tag-list-item:last-child {
        border-bottom: none;
    }
    
    /* 搜索框样式 */
    .search-container {
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 示例任务数据
tasks = [
    {
        "id": 1,
        "name": "构建项目",
        "description": "执行项目构建脚本，生成前端和后端资源",
        "tags": ["build", "frontend", "backend"],
        "priority": "高",
        "status": "待处理"
    },
    {
        "id": 2,
        "name": "部署到测试环境",
        "description": "将应用部署到测试服务器进行验证",
        "tags": ["deploy", "test"],
        "priority": "中",
        "status": "进行中"
    },
    {
        "id": 3,
        "name": "运行单元测试",
        "description": "执行所有单元测试并生成测试报告",
        "tags": ["test", "report"],
        "priority": "中",
        "status": "完成"
    },
    {
        "id": 4,
        "name": "代码静态分析",
        "description": "运行ESLint和Flake8进行代码质量检查",
        "tags": ["lint", "quality"],
        "priority": "低",
        "status": "待处理"
    },
    {
        "id": 5,
        "name": "数据库迁移",
        "description": "应用最新的数据库迁移脚本",
        "tags": ["database", "migration"],
        "priority": "高",
        "status": "进行中"
    },
    {
        "id": 6,
        "name": "生成文档",
        "description": "从代码注释生成API文档",
        "tags": ["docs", "api"],
        "priority": "低",
        "status": "待处理"
    },
    {
        "id": 7,
        "name": "更新依赖",
        "description": "更新项目依赖到最新版本",
        "tags": ["dependencies", "update"],
        "priority": "中",
        "status": "待处理"
    },
    {
        "id": 8,
        "name": "性能优化",
        "description": "优化应用性能，减少加载时间",
        "tags": ["performance", "optimization"],
        "priority": "高",
        "status": "进行中"
    }
]

# 创建Pandas DataFrame
tasks_df = pd.DataFrame(tasks)

# 提取所有唯一标签
all_tags = []
for task in tasks:
    all_tags.extend(task["tags"])
all_tags = sorted(list(set(all_tags)))

# 主界面
st.title("Streamlit 标签组件比较")
st.markdown("本示例展示了不同的Streamlit标签组件实现方式，包括增删改查功能")

# 检查库是否已安装
if not libraries_installed:
    st.warning("需要安装以下库来运行此示例:")
    st.code(installation_instructions)
    st.stop()

# 初始化会话状态
if "selected_tags" not in st.session_state:
    st.session_state.selected_tags = []
if "tag_stats" not in st.session_state:
    st.session_state.tag_stats = {tag: random.randint(1, 15) for tag in all_tags}
if "new_tag" not in st.session_state:
    st.session_state.new_tag = ""
if "edit_tag" not in st.session_state:
    st.session_state.edit_tag = ""
if "edit_tag_old" not in st.session_state:
    st.session_state.edit_tag_old = ""
if "filtered_tasks" not in st.session_state:
    st.session_state.filtered_tasks = tasks

# 使用标签页来组织不同的标签库
tab1, tab2, tab3, tab4 = st.tabs([
    "streamlit-tags", 
    "streamlit-extras", 
    "自定义标签组件", 
    "高级标签管理"
])

# 过滤任务函数
def filter_tasks_by_tags(tasks, selected_tags):
    if not selected_tags:
        return tasks
    
    filtered = []
    for task in tasks:
        if any(tag in selected_tags for tag in task["tags"]):
            filtered.append(task)
    return filtered

# 更新任务标签函数
def update_task_tag(tasks, old_tag, new_tag):
    for task in tasks:
        if old_tag in task["tags"]:
            task["tags"].remove(old_tag)
            if new_tag not in task["tags"]:
                task["tags"].append(new_tag)
    return tasks

# 删除标签函数
def remove_tag_from_tasks(tasks, tag_to_remove):
    for task in tasks:
        if tag_to_remove in task["tags"]:
            task["tags"].remove(tag_to_remove)
    return tasks

# ================ streamlit-tags 示例 ================
with tab1:
    st.markdown('<div class="library-section streamlit-tags">', unsafe_allow_html=True)
    st.subheader("streamlit-tags 组件")
    st.markdown("""
    **特点:**
    - 专为标签输入设计
    - 支持自动完成和建议
    - 允许自定义最大标签数
    - 适合标签输入和展示
    """)
    
    # 创建标签输入和展示布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # streamlit-tags标签输入组件
        if 'st_tags' in globals():
            selected_tags = st_tags(
                label='筛选任务标签:',
                text='选择或输入标签，按Enter添加',
                value=st.session_state.selected_tags,
                suggestions=all_tags,
                maxtags=10,
                key='streamlit_tags_input')
            
            st.session_state.selected_tags = selected_tags
            
            # 过滤任务
            filtered_tasks = filter_tasks_by_tags(tasks, selected_tags)
            st.session_state.filtered_tasks = filtered_tasks
            
            # 显示过滤后的任务
            st.subheader(f"过滤结果 ({len(filtered_tasks)}/{len(tasks)})")
            for task in filtered_tasks:
                with st.container():
                    st.markdown(f"**{task['name']}** - {task['description']}")
                    st.markdown(
                        " ".join([f"<span class='tag'>{tag}</span>" for tag in task["tags"]]),
                        unsafe_allow_html=True
                    )
                    st.caption(f"优先级: {task['priority']} | 状态: {task['status']}")
                    st.divider()
        else:
            st.warning("streamlit-tags 未安装或导入有误，无法显示此组件")
    
    with col2:
        # 标签统计信息
        st.subheader("标签统计")
        for tag, count in st.session_state.tag_stats.items():
            tag_color = "#4CAF50" if tag in st.session_state.selected_tags else "#f0f2f6"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;padding:5px;'>"
                f"<span style='background-color:{tag_color};color:{'white' if tag in st.session_state.selected_tags else 'black'};border-radius:10px;padding:2px 8px;'>{tag}</span>"
                f"<span>{count}个任务</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ streamlit-extras 示例 ================
with tab2:
    st.markdown('<div class="library-section streamlit-extras">', unsafe_allow_html=True)
    st.subheader("streamlit-extras 标签组件")
    st.markdown("""
    **特点:**
    - 集成在streamlit-extras包中
    - 支持默认选中值
    - 简洁的标签选择界面
    - 结果以列表形式返回
    """)
    
    # 创建布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 使用streamlit-extras的标签选择器
        if 'tagger_component' in globals():
            st.subheader("标签选择器")
            # 修改这里 - 去掉不支持的default参数
            # 检查当前选中的标签
            current_selection = st.session_state.selected_tags.copy() if st.session_state.selected_tags else []
            
            # 使用正确的参数调用tagger_component
            selected_tags = tagger_component(
                "选择标签筛选任务:",
                all_tags
            )
            
            # 如果有已选择的标签，手动设置为选中状态
            if current_selection and selected_tags != current_selection:
                # 注意：这里没有直接方式预设选中的标签，所以我们只能显示已选择的标签
                st.write("当前选中的标签:")
                for tag in current_selection:
                    st.markdown(f"<span class='tag-selected'>{tag}</span>", unsafe_allow_html=True)
            
            # 更新会话状态
            st.session_state.selected_tags = selected_tags
            
            # 过滤任务
            filtered_tasks = filter_tasks_by_tags(tasks, selected_tags)
            st.session_state.filtered_tasks = filtered_tasks
            
            # 显示过滤后的任务
            st.subheader(f"过滤结果 ({len(filtered_tasks)}/{len(tasks)})")
            for task in filtered_tasks:
                with st.container():
                    st.markdown(f"**{task['name']}** - {task['description']}")
                    st.markdown(
                        " ".join([f"<span class='tag'>{tag}</span>" for tag in task["tags"]]),
                        unsafe_allow_html=True
                    )
                    st.caption(f"优先级: {task['priority']} | 状态: {task['status']}")
                    st.divider()
        else:
            st.warning("streamlit-extras 未安装或导入有误，无法显示此组件")
    
    with col2:
        # 标签搜索
        st.subheader("标签搜索")
        search_term = st.text_input("搜索标签:", key="extras_search")
        
        # 过滤标签
        filtered_tags = [tag for tag in all_tags if search_term.lower() in tag.lower()] if search_term else all_tags
        
        # 显示过滤后的标签
        for tag in filtered_tags:
            is_selected = tag in st.session_state.selected_tags
            tag_class = "tag-selected" if is_selected else "tag"
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;margin:5px 0;'>"
                f"<span class='{tag_class}'>{tag}</span>"
                f"<span>{st.session_state.tag_stats[tag]}个任务</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ 自定义标签组件 ================
with tab3:
    st.markdown('<div class="library-section custom-tags">', unsafe_allow_html=True)
    st.subheader("自定义标签组件")
    st.markdown("""
    **特点:**
    - 纯Streamlit实现，无依赖
    - 完全可定制的UI
    - 点击标签切换选择状态
    - 更灵活的布局和交互
    """)
    
    # 标签点击回调函数
    def toggle_tag(tag):
        if tag in st.session_state.selected_tags:
            st.session_state.selected_tags.remove(tag)
        else:
            st.session_state.selected_tags.append(tag)
    
    # 自定义标签过滤器
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("点击标签进行筛选")
        
        # 显示所有标签，可点击切换状态
        st.markdown("<div class='tags-container'>", unsafe_allow_html=True)
        tag_html = ""
        for tag in all_tags:
            is_selected = tag in st.session_state.selected_tags
            tag_class = "tag-selected" if is_selected else "tag tag-clickable"
            tag_html += f"<span class='{tag_class}' onclick='handleTagClick(\"{tag}\")'>{tag} ({st.session_state.tag_stats[tag]})</span>"
        
        st.markdown(tag_html + "</div>", unsafe_allow_html=True)
        
        # JavaScript处理点击事件
        st.markdown("""
        <script>
        function handleTagClick(tag) {
            // 使用sessionStorage传递点击的标签
            sessionStorage.setItem('clicked_tag', tag);
            // 触发重新加载
            window.dispatchEvent(new Event('storage'));
        }
        </script>
        """, unsafe_allow_html=True)
        
        # 检查是否有标签被点击，这在实际中不会工作，仅为演示
        # 注意：真实的点击处理需要使用Streamlit的回调机制
        if st.button("模拟标签点击", key="simulate_tag_click"):
            # 这里我们随机选择一个标签来模拟点击
            random_tag = random.choice(all_tags)
            toggle_tag(random_tag)
            st.rerun()
        
        # 清除选择按钮
        if st.button("清除所有选择", key="clear_tags"):
            st.session_state.selected_tags = []
            st.rerun()
        
        # 过滤任务
        filtered_tasks = filter_tasks_by_tags(tasks, st.session_state.selected_tags)
        st.session_state.filtered_tasks = filtered_tasks
        
        # 显示过滤后的任务
        st.subheader(f"过滤结果 ({len(filtered_tasks)}/{len(tasks)})")
        
        # 使用列表展示过滤后的任务
        for i, task in enumerate(filtered_tasks):
            with st.container():
                col_task, col_status = st.columns([3, 1])
                with col_task:
                    st.markdown(f"**{task['name']}**")
                    st.caption(task['description'])
                with col_status:
                    st.markdown(f"优先级: {task['priority']}")
                    st.markdown(f"状态: {task['status']}")
                
                # 显示任务标签
                st.markdown(
                    "<div class='tags-container'>" + 
                    "".join([f"<span class='tag'>{tag}</span>" for tag in task["tags"]]) +
                    "</div>",
                    unsafe_allow_html=True
                )
                st.divider()
    
    with col2:
        # 标签统计卡片
        st.subheader("标签分布")
        
        # 创建饼图数据
        tag_counts = {}
        for task in tasks:
            for tag in task["tags"]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 使用自定义卡片展示统计
        for tag, count in sorted(st.session_state.tag_stats.items(), key=lambda x: x[1], reverse=True):
            # 计算任务占比
            percentage = (count / len(tasks)) * 100
            is_selected = tag in st.session_state.selected_tags
            
            # 不同的背景色以显示选中状态
            bg_color = "#e7f3eb" if is_selected else "#f9f9f9"
            border = "2px solid #4CAF50" if is_selected else "1px solid #e6e6e6"
            
            st.markdown(
                f"""
                <div style="background-color:{bg_color};border-radius:10px;padding:10px;margin-bottom:10px;border:{border};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:bold;">{tag}</span>
                        <span>{count}个任务</span>
                    </div>
                    <div style="background-color:#eee;border-radius:5px;height:10px;margin-top:5px;">
                        <div style="background-color:#4CAF50;width:{percentage}%;height:10px;border-radius:5px;"></div>
                    </div>
                    <div style="text-align:right;font-size:0.8em;color:#666;">{percentage:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ 高级标签管理 ================
with tab4:
    st.markdown('<div class="library-section advanced-tags">', unsafe_allow_html=True)
    st.subheader("高级标签管理系统")
    st.markdown("""
    **特点:**
    - 完整的标签增删改查功能
    - 任务标签更新与同步
    - 标签使用统计和可视化
    - 批量操作和筛选功能
    """)
    
    # 布局：左侧为标签管理，右侧为统计和验证
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # 创建标签管理界面
        st.subheader("标签管理")
        
        # 添加新标签
        with st.container():
            new_tag_col, add_btn_col = st.columns([3, 1])
            with new_tag_col:
                new_tag = st.text_input("添加新标签:", value=st.session_state.new_tag, key="new_tag_input_adv")
                st.session_state.new_tag = new_tag
            
            with add_btn_col:
                if st.button("添加标签", key="add_tag_btn_adv"):
                    if new_tag and new_tag not in all_tags:
                        all_tags.append(new_tag)
                        # 初始化新标签的统计数据
                        st.session_state.tag_stats[new_tag] = 0
                        st.success(f"已添加新标签: {new_tag}")
                        st.session_state.new_tag = ""
                        st.rerun()
                    elif new_tag in all_tags:
                        st.warning(f"标签 '{new_tag}' 已存在")
                    else:
                        st.warning("请输入有效的标签名称")
        
        # 标签编辑界面
        with st.expander("编辑现有标签", expanded=True):
            # 搜索框
            search_term = st.text_input("搜索标签:", key="tag_search")
            
            # 过滤标签
            filtered_tags = [tag for tag in all_tags if search_term.lower() in tag.lower()] if search_term else all_tags
            
            # 标签编辑界面
            if filtered_tags:
                for tag in filtered_tags:
                    with st.container():
                        st.markdown(f"<div class='tag-list-item'>", unsafe_allow_html=True)
                        
                        # 列分布：标签名称，使用次数，编辑和删除按钮
                        cols = st.columns([3, 1, 1, 1])
                        
                        # 显示标签名称
                        with cols[0]:
                            # 判断是否在编辑中
                            if st.session_state.edit_tag_old == tag:
                                edited_tag = st.text_input(
                                    "编辑标签:", 
                                    value=st.session_state.edit_tag or tag,
                                    key=f"edit_input_{tag}"
                                )
                                st.session_state.edit_tag = edited_tag
                            else:
                                st.markdown(f"<span class='tag'>{tag}</span>", unsafe_allow_html=True)
                        
                        # 显示使用统计
                        with cols[1]:
                            st.markdown(f"{st.session_state.tag_stats.get(tag, 0)}个任务")
                        
                        # 编辑按钮
                        with cols[2]:
                            if st.session_state.edit_tag_old == tag:
                                # 正在编辑，显示保存按钮
                                if st.button("保存", key=f"save_btn_{tag}"):
                                    if st.session_state.edit_tag and st.session_state.edit_tag != tag:
                                        if st.session_state.edit_tag not in all_tags:
                                            # 更新任务中的标签引用
                                            tasks = update_task_tag(tasks, tag, st.session_state.edit_tag)
                                            tasks_df = pd.DataFrame(tasks)
                                            
                                            # 更新标签统计
                                            tag_count = st.session_state.tag_stats.get(tag, 0)
                                            st.session_state.tag_stats[st.session_state.edit_tag] = tag_count
                                            if tag in st.session_state.tag_stats:
                                                del st.session_state.tag_stats[tag]
                                            
                                            # 更新标签列表
                                            all_tags.remove(tag)
                                            all_tags.append(st.session_state.edit_tag)
                                            all_tags.sort()
                                            
                                            # 更新选中标签
                                            if tag in st.session_state.selected_tags:
                                                st.session_state.selected_tags.remove(tag)
                                                st.session_state.selected_tags.append(st.session_state.edit_tag)
                                            
                                            st.success(f"已更新标签: {tag} → {st.session_state.edit_tag}")
                                        else:
                                            st.warning(f"标签 '{st.session_state.edit_tag}' 已存在")
                                    
                                    # 重置编辑状态
                                    st.session_state.edit_tag_old = ""
                                    st.session_state.edit_tag = ""
                                    st.rerun()
                            else:
                                # 未编辑，显示编辑按钮
                                if st.button("编辑", key=f"edit_btn_{tag}"):
                                    st.session_state.edit_tag_old = tag
                                    st.session_state.edit_tag = tag
                                    st.rerun()
                        
                        # 删除按钮
                        with cols[3]:
                            if st.button("删除", key=f"delete_btn_{tag}"):
                                # 确认是否要删除
                                if st.session_state.tag_stats.get(tag, 0) > 0:
                                    st.warning(f"标签 '{tag}' 正在被 {st.session_state.tag_stats.get(tag, 0)} 个任务使用。")
                                    if st.button(f"确认删除 '{tag}'", key=f"confirm_delete_{tag}"):
                                        # 从任务中移除标签
                                        tasks = remove_tag_from_tasks(tasks, tag)
                                        tasks_df = pd.DataFrame(tasks)
                                        
                                        # 更新标签列表和统计
                                        all_tags.remove(tag)
                                        if tag in st.session_state.tag_stats:
                                            del st.session_state.tag_stats[tag]
                                        
                                        # 更新选中标签
                                        if tag in st.session_state.selected_tags:
                                            st.session_state.selected_tags.remove(tag)
                                        
                                        st.success(f"已删除标签: {tag}")
                                        st.rerun()
                                else:
                                    # 直接删除未使用的标签
                                    all_tags.remove(tag)
                                    if tag in st.session_state.tag_stats:
                                        del st.session_state.tag_stats[tag]
                                    if tag in st.session_state.selected_tags:
                                        st.session_state.selected_tags.remove(tag)
                                    
                                    st.success(f"已删除标签: {tag}")
                                    st.rerun()
                        
                        st.markdown(f"</div>", unsafe_allow_html=True)
            else:
                st.info("没有找到匹配的标签")
        
        # 高级筛选和操作
        with st.expander("批量操作", expanded=False):
            st.subheader("批量标签操作")
            
            # 批量选择
            batch_options = st.multiselect(
                "选择要批量操作的标签:",
                options=all_tags
            )
            
            # 批量操作按钮
            if batch_options:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("批量删除所选标签"):
                        for tag in batch_options:
                            # 从任务中移除标签
                            tasks = remove_tag_from_tasks(tasks, tag)
                            # 更新标签列表和统计
                            if tag in all_tags:
                                all_tags.remove(tag)
                            if tag in st.session_state.tag_stats:
                                del st.session_state.tag_stats[tag]
                            if tag in st.session_state.selected_tags:
                                st.session_state.selected_tags.remove(tag)
                        
                        st.success(f"已删除 {len(batch_options)} 个标签")
                        st.rerun()
                
                with col2:
                    prefix = st.text_input("添加前缀:", placeholder="例如: new-")
                    if st.button("为所选标签添加前缀"):
                        if prefix:
                            for tag in batch_options:
                                new_tag = f"{prefix}{tag}"
                                if new_tag not in all_tags:
                                    # 更新任务标签
                                    tasks = update_task_tag(tasks, tag, new_tag)
                                    # 更新标签列表
                                    all_tags.remove(tag)
                                    all_tags.append(new_tag)
                                    # 更新统计
                                    st.session_state.tag_stats[new_tag] = st.session_state.tag_stats.get(tag, 0)
                                    if tag in st.session_state.tag_stats:
                                        del st.session_state.tag_stats[tag]
                                    # 更新选中标签
                                    if tag in st.session_state.selected_tags:
                                        st.session_state.selected_tags.remove(tag)
                                        st.session_state.selected_tags.append(new_tag)
                            
                            all_tags.sort()
                            st.success(f"已为 {len(batch_options)} 个标签添加前缀")
                            st.rerun()
                        else:
                            st.warning("请输入有效的前缀")
            else:
                st.info("请选择要操作的标签")
    
    with col2:
        # 标签统计和可视化
        st.subheader("标签使用统计")
        
        # 计算标签使用情况
        tag_counts = {}
        for task in tasks:
            for tag in task["tags"]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 更新会话状态中的标签统计
        st.session_state.tag_stats = tag_counts
        
        # 标签统计图表
        if tag_counts:
            # 准备数据
            chart_data = pd.DataFrame({
                "标签": list(tag_counts.keys()),
                "任务数量": list(tag_counts.values())
            })
            
            # 按任务数量排序
            chart_data = chart_data.sort_values("任务数量", ascending=False)
            
            # 显示条形图
            st.bar_chart(chart_data.set_index("标签"))
            
            # 显示饼图占比
            st.subheader("标签使用占比")
            
            # 计算任务中标签的总出现次数（一个任务可能有多个标签）
            total_tag_usages = sum(tag_counts.values())
            
            # 使用自定义HTML/CSS显示占比
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_tag_usages) * 100
                
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;margin-bottom:5px;">
                        <div style="width:30%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                            <span class="tag">{tag}</span>
                        </div>
                        <div style="width:50%;margin:0 10px;">
                            <div style="background-color:#eee;border-radius:5px;height:15px;">
                                <div style="background-color:#4CAF50;width:{percentage}%;height:15px;border-radius:5px;"></div>
                            </div>
                        </div>
                        <div style="width:20%;text-align:right;">
                            {percentage:.1f}% ({count})
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("无标签统计数据")
        
        # 标签筛选结果
        st.subheader("当前筛选")
        if st.session_state.selected_tags:
            st.markdown("已选择标签:")
            st.markdown(
                "<div class='tags-container'>" + 
                "".join([f"<span class='tag-selected'>{tag}</span>" for tag in st.session_state.selected_tags]) +
                "</div>",
                unsafe_allow_html=True
            )
            
            # 显示当前筛选结果
            filtered_count = len(st.session_state.filtered_tasks)
            st.metric("筛选到的任务数", filtered_count, f"{filtered_count - len(tasks)}")
        else:
            st.info("未选择任何标签进行筛选")
        
        # 导出标签数据
        st.subheader("导出/导入标签数据")
        
        # 准备标签数据
        tag_data = {
            "tags": all_tags,
            "statistics": st.session_state.tag_stats,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 转换为JSON
        tag_json = json.dumps(tag_data, indent=2)
        
        # 导出按钮
        if st.download_button(
            label="导出标签数据 (JSON)",
            data=tag_json,
            file_name="task_tags.json",
            mime="application/json"
        ):
            st.success("标签数据已导出")
        
        # 导入功能
        uploaded_file = st.file_uploader("导入标签数据", type=["json"])
        if uploaded_file is not None:
            try:
                imported_data = json.load(uploaded_file)
                if "tags" in imported_data:
                    # 合并标签
                    for tag in imported_data["tags"]:
                        if tag not in all_tags:
                            all_tags.append(tag)
                    all_tags.sort()
                    
                    # 更新统计
                    if "statistics" in imported_data:
                        for tag, count in imported_data["statistics"].items():
                            if tag not in st.session_state.tag_stats:
                                st.session_state.tag_stats[tag] = count
                    
                    st.success(f"成功导入 {len(imported_data['tags'])} 个标签")
            except json.JSONDecodeError:
                st.error("导入的文件不是有效的JSON格式")