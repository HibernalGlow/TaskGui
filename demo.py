import streamlit as st
import yaml
import os
import subprocess
import json
from st_aggrid  import AgGrid, GridOptionsBuilder, JsCode,GridUpdateMode  # 更正导入
import pandas as pd

# 设置页面配置
st.set_page_config(
    page_title="GlowToolBox 任务管理器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载Taskfile.yml
def load_taskfile():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'Taskfile.yml')
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    tasks = []
    for task_name, task_info in data.get('tasks', {}).items():
        # 跳过分组命令
        if isinstance(task_info, dict) and task_info.get('cmds'):
            if task_name in ['comic', 'filter', 'folder'] and 'findstr' in task_info['cmds'][0]:
                continue
            
            task = {
                'name': task_name,
                'description': task_info.get('desc', ''),
                'tags': task_info.get('tags', []) if task_info.get('tags') else [],
                'directory': task_info.get('dir', ''),
                'commands': task_info.get('cmds', []),
                'emoji': task_info.get('desc', '').split(' ')[0] if task_info.get('desc') else ''
            }
            tasks.append(task)
    
    return tasks

# 运行任务
def run_task(task_name):
    cmd = f"task {task_name}"
    process = subprocess.Popen(
        cmd, 
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    return {
        'success': process.returncode == 0,
        'output': stdout,
        'error': stderr
    }

# 创建主界面
def main():
    st.title("🧰 GlowToolBox 任务管理器")
    
    # 加载任务
    tasks = load_taskfile()
    df = pd.DataFrame(tasks)
    
    # 修正标签显示
    df['tags_str'] = df['tags'].apply(lambda x: ', '.join(x) if x else '')
    
    # 过滤选项
    st.sidebar.title("过滤选项")
    
    # 提取所有标签
    all_tags = set()
    for tags in df['tags']:
        if tags:
            all_tags.update(tags)
    
    selected_tags = st.sidebar.multiselect(
        "按标签过滤",
        options=sorted(list(all_tags))
    )
    
    search_term = st.sidebar.text_input("搜索任务")
    
    # 应用过滤器
    filtered_df = df.copy()
    if selected_tags:
        filtered_df = filtered_df[filtered_df['tags'].apply(
            lambda x: any(tag in x for tag in selected_tags) if x else False
        )]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['description'].str.contains(search_term, case=False, na=False)
        ]
    
    # 视图选择
    view_type = st.sidebar.radio(
        "视图类型",
        options=["表格视图", "卡片视图", "分组视图"]
    )
    
    # 运行结果显示区域
    output_container = st.empty()
    
    # 表格视图
    if view_type == "表格视图":
        # 设置表格选项
        gb = GridOptionsBuilder.from_dataframe(filtered_df[['emoji', 'name', 'description', 'tags_str', 'directory']])
        gb.configure_column('emoji', header_name="", width=70)
        gb.configure_column('name', header_name="任务名称", width=150)
        gb.configure_column('description', header_name="描述", width=300)
        gb.configure_column('tags_str', header_name="标签", width=150)
        gb.configure_column('directory', header_name="目录", width=200)
        
        # 添加运行按钮列
        button_renderer = JsCode("""
        function(params) {
            return '<button style="background-color: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">运行</button>';
        }
        """)
        
        gb.configure_column(
            "actions", 
            headerName="操作", 
            cellRenderer=button_renderer,
            width=100
        )
        
        grid_options = gb.build()
        
        # 修改这段代码
        grid_response = AgGrid(
            filtered_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,  # 使用正确的枚举值
            columns_auto_size_mode="FIT_CONTENTS",
            height=500,
            allow_unsafe_jscode=True
        )
        
        # 处理点击事件
        if grid_response['selected_rows']:
            selected_task = grid_response['selected_rows'][0]['name']
            st.write(f"选中任务: {selected_task}")
            
            if st.button(f"运行任务: {selected_task}"):
                with st.spinner(f"正在运行 {selected_task}..."):
                    result = run_task(selected_task)
                
                with output_container.container():
                    st.subheader("任务执行结果")
                    if result['success']:
                        st.success(f"任务 {selected_task} 执行成功")
                    else:
                        st.error(f"任务 {selected_task} 执行失败")
                    
                    st.subheader("输出")
                    st.code(result['output'])
                    
                    if result['error']:
                        st.subheader("错误")
                        st.code(result['error'], language="bash")
    
    # 卡片视图
    elif view_type == "卡片视图":
        cols = st.columns(3)
        
        for i, (_, row) in enumerate(filtered_df.iterrows()):
            with cols[i % 3]:
                with st.expander(f"{row['emoji']} {row['name']}", expanded=False):
                    st.markdown(f"**描述**: {row['description']}")
                    st.markdown(f"**标签**: {row['tags_str']}")
                    st.markdown(f"**目录**: {row['directory']}")
                    
                    if st.button(f"运行", key=f"run_{row['name']}"):
                        with st.spinner(f"正在运行 {row['name']}..."):
                            result = run_task(row['name'])
                        
                        if result['success']:
                            st.success("执行成功")
                        else:
                            st.error("执行失败")
                        
                        with st.expander("查看输出"):
                            st.code(result['output'])
                            if result['error']:
                                st.code(result['error'], language="bash")
    
    # 分组视图
    elif view_type == "分组视图":
        # 按标签分组
        if not filtered_df.empty:
            # 获取第一个标签作为主标签
            filtered_df['primary_tag'] = filtered_df['tags'].apply(
                lambda x: x[0] if x and len(x) > 0 else "未分类"
            )
            
            # 按主标签分组
            groups = filtered_df.groupby('primary_tag')
            
            for group_name, group_df in groups:
                st.subheader(f"📂 {group_name}")
                
                cols = st.columns(3)
                for i, (_, row) in enumerate(group_df.iterrows()):
                    with cols[i % 3]:
                        st.markdown(f"**{row['emoji']} {row['name']}**")
                        st.markdown(f"{row['description']}")
                        
                        if st.button(f"运行", key=f"group_run_{row['name']}"):
                            with st.spinner(f"正在运行 {row['name']}..."):
                                result = run_task(row['name'])
                            
                            if result['success']:
                                st.success("执行成功")
                            else:
                                st.error("执行失败")
                            
                            with st.expander("查看输出"):
                                st.code(result['output'])
                                if result['error']:
                                    st.code(result['error'], language="bash")
                        
                        st.markdown("---")

if __name__ == "__main__":
    main()
