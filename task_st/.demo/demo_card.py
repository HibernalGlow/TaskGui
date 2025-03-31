import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

# 尝试导入必要的库，如果不存在则提供安装说明
libraries_installed = True
installation_instructions = ""

try:
    from streamlit_card import card
except ImportError:
    libraries_installed = False
    installation_instructions += "- 安装 streamlit-card: `pip install streamlit-card`\n"

try:
    from streamlit_elements import elements, mui, html
except ImportError:
    libraries_installed = False
    installation_instructions += "- 安装 streamlit-elements: `pip install streamlit-elements`\n"

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
except ImportError:
    libraries_installed = False
    installation_instructions += "- 安装 streamlit-aggrid: `pip install streamlit-aggrid`\n"

# 页面配置
st.set_page_config(
    page_title="Streamlit 卡片组件比较",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .card-container {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .card-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .card-description {
        color: #666;
        margin-bottom: 15px;
    }
    
    .card-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin-bottom: 15px;
    }
    
    .tag {
        background-color: #e1e1e1;
        color: #333;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8em;
    }
    
    .card-footer {
        display: flex;
        justify-content: space-between;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }
    
    .library-section {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    .streamlit-card {
        background-color: #f0f7ff;
    }
    
    .elements-card {
        background-color: #f0fff7;
    }
    
    .aggrid-card {
        background-color: #fff7f0;
    }
    
    .custom-card {
        background-color: #f7f0ff;
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
        "directory": "D:/projects/myapp",
        "command": "task build",
        "emoji": "🏗️",
        "runtime": {"run_count": 15, "last_run": "2025-03-30 10:15"}
    },
    {
        "id": 2,
        "name": "部署到测试环境",
        "description": "将应用部署到测试服务器进行验证",
        "tags": ["deploy", "test"],
        "directory": "D:/projects/myapp/deploy",
        "command": "task deploy:test",
        "emoji": "🚀",
        "runtime": {"run_count": 8, "last_run": "2025-03-29 14:30"}
    },
    {
        "id": 3,
        "name": "运行单元测试",
        "description": "执行所有单元测试并生成测试报告",
        "tags": ["test", "report"],
        "directory": "D:/projects/myapp/tests",
        "command": "task test:unit",
        "emoji": "🧪",
        "runtime": {"run_count": 23, "last_run": "2025-03-31 09:45"}
    },
    {
        "id": 4,
        "name": "代码静态分析",
        "description": "运行ESLint和Flake8进行代码质量检查",
        "tags": ["lint", "quality"],
        "directory": "D:/projects/myapp",
        "command": "task lint",
        "emoji": "🔍",
        "runtime": {"run_count": 12, "last_run": "2025-03-28 16:10"}
    },
    {
        "id": 5,
        "name": "数据库迁移",
        "description": "应用最新的数据库迁移脚本",
        "tags": ["database", "migration"],
        "directory": "D:/projects/myapp/db",
        "command": "task db:migrate",
        "emoji": "💾",
        "runtime": {"run_count": 5, "last_run": "2025-03-25 11:20"}
    },
    {
        "id": 6,
        "name": "生成文档",
        "description": "从代码注释生成API文档",
        "tags": ["docs", "api"],
        "directory": "D:/projects/myapp/docs",
        "command": "task docs:generate",
        "emoji": "📚",
        "runtime": {"run_count": 7, "last_run": "2025-03-20 15:30"}
    }
]

# 创建Pandas DataFrame
tasks_df = pd.DataFrame(tasks)

# 主界面
st.title("Streamlit 卡片组件库比较")
st.markdown("本示例展示了三种不同的Streamlit卡片组件库：streamlit-card、streamlit-elements 和 streamlit-aggrid，以及一个自定义卡片实现")

# 检查库是否已安装
if not libraries_installed:
    st.warning("需要安装以下库来运行此示例:")
    st.code(installation_instructions)
    st.stop()

# 使用标签页来组织不同的卡片库
tab1, tab2, tab3, tab4 = st.tabs([
    "streamlit-card", 
    "streamlit-elements", 
    "streamlit-aggrid", 
    "自定义卡片"
])

# ================ streamlit-card 示例 ================
with tab1:
    st.markdown('<div class="library-section streamlit-card">', unsafe_allow_html=True)
    st.subheader("streamlit-card 组件")
    st.markdown("""
    **特点:**
    - 简洁易用
    - 支持图片、标题和文本
    - 支持点击和URL链接
    - 可自定义样式
    - 适合简单任务卡片
    """)
    
    # 创建3列布局
    cols = st.columns(3)
    
    for i, task in enumerate(tasks):
        with cols[i % 3]:
            card_clicked = card(
                title=f"{task['emoji']} {task['name']}",
                text=task['description'],
                image=f"https://picsum.photos/500/300?random={i+1}",
                styles={
                    "card": {
                        "width": "100%",
                        "height": "320px",
                        "border-radius": "10px",
                        "box-shadow": "0 0 10px rgba(0,0,0,0.1)",
                        "margin-bottom": "20px"
                    },
                    "filter": {
                        "background-color": "rgba(0, 0, 0, 0.2)"
                    }
                },
                key=f"sc_card_{i}"
            )
            
            # 显示标签
            st.write(" ".join([f"`#{tag}`" for tag in task["tags"]]))
            
            # 显示命令
            st.code(task["command"], language="bash")
            
            # 操作按钮
            btn_cols = st.columns(3)
            with btn_cols[0]:
                st.button("运行", key=f"sc_run_{i}")
            with btn_cols[1]:
                st.button("查看", key=f"sc_view_{i}")
            with btn_cols[2]:
                st.button("复制", key=f"sc_copy_{i}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ streamlit-elements (Material UI) 示例 ================
with tab2:
    st.markdown('<div class="library-section elements-card">', unsafe_allow_html=True)
    st.subheader("streamlit-elements (Material UI) 组件")
    st.markdown("""
    **特点:**
    - 强大的Material UI组件
    - 高度可定制化
    - 响应式布局
    - 丰富的交互选项
    - 更复杂的实现
    """)
    
    if 'streamlit_elements' in globals():
        # 使用 streamlit-elements 创建 Material UI 卡片
        with elements("mui_cards"):
            # 创建布局容器
            with mui.Grid(container=True, spacing=2):
                for i, task in enumerate(tasks):
                    with mui.Grid(item=True, xs=12, sm=6, md=4):
                        with mui.Card(
                            sx={
                                "maxWidth": "100%",
                                "height": "100%",
                                "display": "flex",
                                "flexDirection": "column",
                                "margin": "8px"
                            }
                        ):
                            # 卡片顶部图片
                            mui.CardMedia(
                                component="img",
                                height="140",
                                image=f"https://picsum.photos/500/300?random={i+10}",
                                alt=task['name']
                            )
                            
                            # 卡片内容
                            with mui.CardContent(sx={"flexGrow": 1}):
                                mui.Typography(
                                    f"{task['emoji']} {task['name']}",
                                    variant="h5",
                                    component="div",
                                    gutterBottom=True
                                )
                                mui.Typography(
                                    task['description'],
                                    variant="body2",
                                    color="text.secondary"
                                )
                                
                                # 标签组
                                with mui.Box(sx={"display": "flex", "flexWrap": "wrap", "gap": "4px", "marginTop": "8px"}):
                                    for tag in task['tags']:
                                        mui.Chip(
                                            label=f"#{tag}", 
                                            size="small", 
                                            sx={"background": "#f0f2f6"}
                                        )
                                
                                mui.Typography(
                                    f"上次运行: {task['runtime']['last_run']}",
                                    variant="body2",
                                    color="text.secondary",
                                    sx={"marginTop": "8px"}
                                )
                            
                            # 卡片操作区
                            with mui.CardActions:
                                mui.Button("运行", size="small", variant="contained")
                                mui.Button("查看", size="small")
                                mui.Button("复制", size="small")
    else:
        st.warning("streamlit-elements 未安装，无法显示 Material UI 卡片")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ streamlit-aggrid 示例 ================
with tab3:
    st.markdown('<div class="library-section aggrid-card">', unsafe_allow_html=True)
    st.subheader("streamlit-aggrid 卡片式表格")
    st.markdown("""
    **特点:**
    - 高度可定制的表格
    - 可转换为卡片布局
    - 强大的筛选和排序功能
    - 单元格自定义渲染
    - 适合大量数据
    """)
    
    if 'st_aggrid' in globals():
        # 定义卡片渲染器JavaScript代码
        card_renderer = JsCode("""
        class CardRenderer {
            init(params) {
                this.eGui = document.createElement('div');
                this.eGui.classList.add('custom-card');
                this.eGui.style.padding = '10px';
                this.eGui.style.backgroundColor = '#ffffff';
                this.eGui.style.borderRadius = '10px';
                this.eGui.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                this.eGui.style.height = '100%';
                this.eGui.style.overflow = 'hidden';
                
                const data = params.data;
                
                // 创建卡片标题
                const title = document.createElement('div');
                title.innerHTML = `<div style="font-weight: bold; font-size: 16px; margin-bottom: 10px;">${data.emoji} ${data.name}</div>`;
                
                // 创建卡片描述
                const desc = document.createElement('div');
                desc.innerHTML = `<div style="color: #666; margin-bottom: 10px;">${data.description}</div>`;
                
                // 创建标签容器
                const tags = document.createElement('div');
                tags.style.display = 'flex';
                tags.style.flexWrap = 'wrap';
                tags.style.gap = '4px';
                tags.style.marginBottom = '10px';
                
                data.tags.forEach(tag => {
                    const tagElem = document.createElement('span');
                    tagElem.innerText = '#' + tag;
                    tagElem.style.backgroundColor = '#e1e1e1';
                    tagElem.style.color = '#333';
                    tagElem.style.padding = '2px 6px';
                    tagElem.style.borderRadius = '10px';
                    tagElem.style.fontSize = '0.8em';
                    tags.appendChild(tagElem);
                });
                
                // 创建命令显示
                const cmd = document.createElement('div');
                cmd.innerHTML = `<div style="background-color: #f5f5f5; padding: 5px; border-radius: 4px; font-family: monospace; margin-bottom: 10px;">${data.command}</div>`;
                
                // 创建运行时信息
                const runtime = document.createElement('div');
                runtime.innerHTML = `<div style="color: #888; font-size: 0.9em;">运行次数: ${data.runtime.run_count} | 最后运行: ${data.runtime.last_run}</div>`;
                
                // 创建按钮区域
                const buttons = document.createElement('div');
                buttons.style.display = 'flex';
                buttons.style.justifyContent = 'space-between';
                buttons.style.marginTop = '10px';
                buttons.style.borderTop = '1px solid #eee';
                buttons.style.paddingTop = '10px';
                
                const runBtn = document.createElement('button');
                runBtn.innerText = '运行';
                runBtn.style.backgroundColor = '#4CAF50';
                runBtn.style.color = 'white';
                runBtn.style.border = 'none';
                runBtn.style.padding = '5px 10px';
                runBtn.style.borderRadius = '4px';
                runBtn.style.cursor = 'pointer';
                
                const viewBtn = document.createElement('button');
                viewBtn.innerText = '查看';
                viewBtn.style.backgroundColor = '#2196F3';
                viewBtn.style.color = 'white';
                viewBtn.style.border = 'none';
                viewBtn.style.padding = '5px 10px';
                viewBtn.style.borderRadius = '4px';
                viewBtn.style.cursor = 'pointer';
                
                const copyBtn = document.createElement('button');
                copyBtn.innerText = '复制';
                copyBtn.style.backgroundColor = '#FFC107';
                copyBtn.style.color = 'white';
                copyBtn.style.border = 'none';
                copyBtn.style.padding = '5px 10px';
                copyBtn.style.borderRadius = '4px';
                copyBtn.style.cursor = 'pointer';
                
                buttons.appendChild(runBtn);
                buttons.appendChild(viewBtn);
                buttons.appendChild(copyBtn);
                
                // 将所有元素添加到卡片
                this.eGui.appendChild(title);
                this.eGui.appendChild(desc);
                this.eGui.appendChild(tags);
                this.eGui.appendChild(cmd);
                this.eGui.appendChild(runtime);
                this.eGui.appendChild(buttons);
                
                // 添加按钮事件
                runBtn.addEventListener('click', () => {
                    alert(`运行任务: ${data.name}`);
                });
                
                viewBtn.addEventListener('click', () => {
                    alert(`查看任务: ${data.name}`);
                });
                
                copyBtn.addEventListener('click', () => {
                    navigator.clipboard.writeText(data.command);
                    alert(`已复制命令: ${data.command}`);
                });
            }
            
            getGui() {
                return this.eGui;
            }
            
            refresh(params) {
                return false;
            }
        }
        """)
        
        # 设置AgGrid选项
        gb = GridOptionsBuilder.from_dataframe(tasks_df)
        gb.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True
        )
        
        # 使用自定义卡片渲染器
        gb.configure_grid_options(
            rowHeight=250,
            domLayout='normal',
            components={
                'cardRenderer': card_renderer
            }
        )
        
        # 将所有内容列隐藏，创建一个卡片列
        for col in tasks_df.columns:
            gb.configure_column(col, hide=True)
        
        # 添加卡片列
        gb.configure_column(
            'card',
            headerName='任务卡片',
            cellRenderer='cardRenderer',
            valueGetter='data', # 传递整行数据给渲染器
            width=400,
            suppressSizeToFit=False
        )
        
        grid_options = gb.build()
        
        # 显示AgGrid表格
        AgGrid(
            tasks_df,
            gridOptions=grid_options,
            allow_unsafe_jscode=True,
            theme='material',
            update_on=['rowValueChanged', 'cellValueChanged', 'filterChanged'],
            columns_auto_size_mode='FIT_CONTENTS',
            height=800
        )
    else:
        st.warning("streamlit-aggrid 未安装，无法显示卡片式表格")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ================ 自定义纯Streamlit卡片 ================
with tab4:
    st.markdown('<div class="library-section custom-card">', unsafe_allow_html=True)
    st.subheader("纯 Streamlit 自定义卡片")
    st.markdown("""
    **特点:**
    - 无需额外依赖
    - 使用原生 Streamlit 组件
    - 完全可自定义
    - 易于集成到现有项目
    - 适合定制化需求
    """)
    
    # 自定义卡片组件函数
    def render_custom_task_card(task, col_container):
        with col_container:
            with st.container():
                # 使用HTML创建更美观的卡片外观
                st.markdown(f"""
                <div class="card-container">
                    <div class="card-title">{task['emoji']} {task['name']}</div>
                    <div class="card-description">{task['description']}</div>
                    <div class="card-tags">
                        {''.join([f'<span class="tag">#{tag}</span>' for tag in task['tags']])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 命令
                st.code(task["command"], language="bash")
                
                # 运行时信息
                st.caption(f"运行次数: {task['runtime']['run_count']} | 最后运行: {task['runtime']['last_run']}")
                
                # 显示目录
                st.caption(f"**目录**: `{task['directory']}`")
                
                # 操作按钮
                btn_cols = st.columns(3)
                with btn_cols[0]:
                    if st.button("运行", key=f"custom_run_{task['id']}"):
                        st.info(f"正在运行 {task['name']}...")
                with btn_cols[1]:
                    if st.button("查看", key=f"custom_view_{task['id']}"):
                        st.info(f"查看任务 {task['name']}...")
                with btn_cols[2]:
                    if st.button("复制", key=f"custom_copy_{task['id']}"):
                        st.success(f"已复制 {task['name']} 的命令")
                
                st.markdown("# filepath: d:\1VSCODE\GlowToolBox\src\scripts\task\task_gui\task_st\card_components_demo.py")
