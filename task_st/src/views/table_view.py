import streamlit as st
import os
import json
import pandas as pd
from ..utils.file_utils import get_task_command, copy_to_clipboard, open_file, get_directory_files
from ..services.task_runner import run_task_via_cmd
from ..components.batch_operations import render_batch_operations
from .card_view import render_card_view

# 尝试导入AgGrid
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    st.error("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")

def render_table_view(filtered_df, current_taskfile):
    """
    渲染表格视图
    
    参数:
        filtered_df: 过滤后的任务DataFrame
        current_taskfile: 当前Taskfile路径
    """
    st.markdown("### 任务列表")
    
    # 改为优先使用标准data_editor
    # render_edit_table(filtered_df, current_taskfile)
    render_aggrid_table(filtered_df, current_taskfile)
    # 显示已选择的任务操作区域
    render_selected_tasks_section(filtered_df, current_taskfile)

def render_selected_tasks_section(filtered_df, current_taskfile):
    """渲染已选择任务的区域，包括清除选择按钮和卡片视图"""
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
    
    # 获取选中的任务列表
    selected_tasks = st.session_state.selected_tasks
    
    # 显示已选择的任务数量和操作按钮
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 已选择 {len(selected_tasks)} 个任务")
    
    # 定义清除选择的回调函数
    def clear_selection():
        st.session_state.selected_tasks = []
        if 'selected' in st.session_state:
            for task in st.session_state.selected:
                st.session_state.selected[task] = False
    
    with col2:
        if st.button("清除选择", key="clear_table_selection", on_click=clear_selection):
            pass  # 清除选择的动作由回调函数处理，避免刷新
    
    with col3:
        if st.button("运行选中的任务", key="run_selected_tasks"):
            if not selected_tasks:
                st.warning("请先选择要运行的任务")
            else:
                from ..services.task_runner import run_multiple_tasks
                with st.spinner(f"正在启动 {len(selected_tasks)} 个任务..."):
                    result_msgs = run_multiple_tasks(
                        selected_tasks, 
                        current_taskfile, 
                        parallel=st.session_state.get('run_parallel', False)
                    )
                
                for msg in result_msgs:
                    st.success(msg)
    
    # 如果有选中的任务，显示卡片视图
    if selected_tasks:
        # 过滤出选中的任务数据
        selected_df = filtered_df[filtered_df['name'].isin(selected_tasks)]
        
        # 使用卡片视图显示选中的任务
        with st.container():
            # 每行显示的卡片数量
            cards_per_row = 3
            
            # 创建行
            for i in range(0, len(selected_df), cards_per_row):
                cols = st.columns(cards_per_row)
                # 获取当前行的任务
                row_tasks = selected_df.iloc[i:min(i+cards_per_row, len(selected_df))]
                
                # 为每个列填充卡片
                for col_idx, (_, task) in enumerate(row_tasks.iterrows()):
                    with cols[col_idx]:
                        with st.container():
                            # 卡片标题
                            st.markdown(f"### {task['emoji']} {task['name']}")
                            
                            # 描述
                            st.markdown(f"**描述**: {task['description']}")
                            
                            # 标签
                            tags_str = ', '.join([f"#{tag}" for tag in task['tags']]) if isinstance(task['tags'], list) else ''
                            st.markdown(f"**标签**: {tags_str}")
                            
                            # 目录
                            st.markdown(f"**目录**: `{task['directory']}`")
                            
                            # 命令
                            cmd = get_task_command(task['name'], current_taskfile)
                            st.code(cmd, language="bash")
                            
                            # 操作按钮，不包含选择框（已经在表格中选择了）
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("运行", key=f"run_selected_{task['name']}"):
                                    with st.spinner(f"正在启动任务 {task['name']}..."):
                                        result = run_task_via_cmd(task['name'], current_taskfile)
                                    st.success(f"任务 {task['name']} 已在新窗口启动")
                            
                            with col2:
                                # 文件按钮
                                if st.button("文件", key=f"file_selected_{task['name']}"):
                                    if task['directory'] and os.path.exists(task['directory']):
                                        files = get_directory_files(task['directory'])
                                        if files:
                                            st.markdown("##### 文件列表")
                                            for j, file in enumerate(files):
                                                file_path = os.path.join(task['directory'], file)
                                                if st.button(file, key=f"file_selected_{task['name']}_{j}"):
                                                    if open_file(file_path):
                                                        st.success(f"已打开: {file}")
                                    else:
                                        st.info("没有找到文件")
                            
                            with col3:
                                # 复制命令按钮
                                if st.button("复制", key=f"copy_selected_{task['name']}"):
                                    copy_to_clipboard(cmd)
                                    st.success("命令已复制")
                            
                            st.markdown("---")

def render_edit_table(filtered_df, current_taskfile):
    """标准表格实现 - 使用Streamlit原生data_editor"""
    
    # 准备表格数据
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
        
    if 'selected' not in st.session_state:
        st.session_state.selected = {task: False for task in filtered_df_copy['name']}
    
    # 更新选择状态 - 确保所有新任务都被添加到选择状态中
    for task in filtered_df_copy['name']:
        if task not in st.session_state.selected:
            st.session_state.selected[task] = False
    
    # 设置已选择的任务状态
    for task in st.session_state.selected_tasks:
        if task in st.session_state.selected:
            st.session_state.selected[task] = True
    
    # 创建勾选框列
    filtered_df_copy['选择'] = filtered_df_copy['name'].apply(
        lambda x: st.session_state.selected.get(x, False)
    )
    
    # 准备要显示的列 - 现在包含选择列
    display_df = filtered_df_copy[['选择', 'name', '显示名称', 'description', 'tags_str', 'directory']]
    display_df = display_df.rename(columns={
        'description': '描述',
        'tags_str': '标签',
        'directory': '目录'
    })
    
    # 定义编辑器回调函数，减少页面刷新
    def on_change():
        if "edited_rows" in st.session_state.task_editor:
            has_changes = False
            for idx, changes in st.session_state.task_editor["edited_rows"].items():
                if "选择" in changes:
                    idx = int(idx)
                    if idx < len(filtered_df_copy):
                        task_name = filtered_df_copy.iloc[idx]['name']
                        if st.session_state.selected.get(task_name) != changes["选择"]:
                            st.session_state.selected[task_name] = changes["选择"]
                            has_changes = True
            
            # 只有当有变化时才更新选中的任务列表
            if has_changes:
                st.session_state.selected_tasks = [
                    task for task, is_selected in st.session_state.selected.items() 
                    if is_selected
                ]
    
    # 使用标准data_editor显示表格，使用on_change回调减少刷新
    edited_df = st.data_editor(
        display_df,
        column_config={
            "name": None,  # 隐藏name列，但保留数据
            "选择": st.column_config.CheckboxColumn(
                "选择",
                help="选择要操作的任务",
                default=False,
                width="small"
            ),
            "显示名称": st.column_config.TextColumn(
                "任务名称",
                help="任务的名称和图标",
                width="medium"
            ),
            "描述": st.column_config.TextColumn(
                "任务描述",
                width="large"
            ),
            "标签": st.column_config.TextColumn(
                "标签",
                width="medium"
            ),
            "目录": st.column_config.TextColumn(
                "任务目录",
                width="medium"
            )
        },
        hide_index=True,
        width=None,
        height=400,
        use_container_width=True,
        disabled=["显示名称", "描述", "标签", "目录"],  # 只允许编辑勾选框
        key="task_editor",
        on_change=on_change
    )
    
    # 通过on_change回调处理勾选框变化，此处不再需要手动处理
    # 因为这会导致不必要的刷新闪烁

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格 - 优化勾选状态获取并增加分组功能"""
    if not HAS_AGGRID:
        st.warning("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")
        render_edit_table(filtered_df, current_taskfile)
        return
    
    # 准备表格数据
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
    # 初始化会话状态
    if 'selected_tasks' not in st.session_state:
        st.session_state.selected_tasks = []
        
    if 'selected' not in st.session_state:
        st.session_state.selected = {task: False for task in filtered_df_copy['name']}
    
    # AgGrid分组设置状态
    if 'aggrid_group_by' not in st.session_state:
        st.session_state.aggrid_group_by = []
    
    # 确保所有任务都有选择状态
    for task in filtered_df_copy['name']:
        if task not in st.session_state.selected:
            st.session_state.selected[task] = False
    
    # 创建勾选列，从会话状态获取
    filtered_df_copy['选择'] = filtered_df_copy['name'].apply(
        lambda x: st.session_state.selected.get(x, False)
    )
    
    # 准备要显示的列
    display_df = filtered_df_copy[['选择', 'name', '显示名称', 'description', 'tags_str', 'directory']]
    display_df = display_df.rename(columns={
        'description': '描述',
        'tags_str': '标签',
        'directory': '目录'
    })
    
    # AgGrid高级设置UI
    with st.expander("AgGrid高级设置", expanded=False):
        st.write("表格分组与过滤设置")
        
        # 分组设置
        group_options = ["无分组", "标签", "目录"]
        selected_group = st.selectbox(
            "按列分组显示", 
            options=group_options,
            index=0,
            key="aggrid_group_select"
        )
        
        # 将选择转换为实际的列名
        group_mapping = {
            "标签": "标签",
            "目录": "目录"
        }
        
        # 更新分组状态
        if selected_group != "无分组" and selected_group in group_mapping:
            st.session_state.aggrid_group_by = [group_mapping[selected_group]]
        else:
            st.session_state.aggrid_group_by = []
        
        # 其他AgGrid功能选项
        col1, col2 = st.columns(2)
        with col1:
            enable_filter = st.checkbox("启用列过滤", value=True, key="aggrid_enable_filter")
            enable_sorting = st.checkbox("启用排序", value=True, key="aggrid_enable_sorting")
            enable_trigger = st.checkbox("启用交互触发器", value=True, key="aggrid_enable_trigger")
        
        with col2:
            enable_editing = st.checkbox("允许编辑单元格", value=False, key="aggrid_enable_editing")
            enable_enterprise = st.checkbox("启用企业功能", value=True, key="aggrid_enable_enterprise")
            theme_option = st.selectbox(
                "表格主题",
                options=["streamlit", "light", "dark", "blue", "fresh", "material"],
                index=0,
                key="aggrid_theme"
            )
    
    # 构建 AgGrid 选项
    gb = GridOptionsBuilder.from_dataframe(display_df)
    
    # 配置列
    gb.configure_column('name', hide=True)  # 隐藏name列，但保留数据
    gb.configure_column('选择', 
                        header_name="选择", 
                        editable=True, 
                        cellRenderer='agCheckboxCellRenderer',
                        width=70)
    
    gb.configure_column('显示名称', 
                       header_name="任务名称", 
                       editable=enable_editing,
                       enableRowGroup=True,
                       width=150)
    
    gb.configure_column('描述', 
                       header_name="任务描述", 
                       editable=enable_editing,
                       enableRowGroup=True,
                       autoHeight=True,
                       wrapText=True)
    
    # 为每列单独配置分组属性，而不是通过columnDefs整体设置
    for col in display_df.columns:
        if col in st.session_state.aggrid_group_by:
            # 对需要分组的列特殊处理
            gb.configure_column(col, 
                               rowGroup=True,  # 设置为分组列
                               hide=True,     # 隐藏原始列
                               enableRowGroup=True)
        elif col == '标签':
            gb.configure_column(col, 
                               header_name="标签", 
                               editable=enable_editing,
                               enableRowGroup=True,
                               filter=True)
        elif col == '目录':
            gb.configure_column(col, 
                               header_name="任务目录", 
                               editable=enable_editing,
                               enableRowGroup=True,
                               filter=True)
    
    # 启用分组、排序和过滤功能
    gb.configure_default_column(
        groupable=True,
        filterable=enable_filter,
        sorteable=enable_sorting,
        editable=enable_editing,
    )
    
    # 自定义 JavaScript 代码处理选择事件，确保状态同步
    js_code = JsCode("""
    function(params) {
        // 开启数据行选择颜色加亮
        if (params.data && params.data.选择 === true) {
            return {
                'background-color': 'rgba(112, 182, 255, 0.2)'
            }
        }
        return null;
    }
    """)
    
    # 添加自定义触发器 JavaScript 代码
    custom_js = JsCode("""
    function(e) {
        let api = e.api;
        let rowData = [];
        let selectedData = [];
        
        // 获取所有行数据
        api.forEachNode(node => rowData.push(node.data));
        
        // 获取选中行数据
        api.forEachNode(node => {
            if (node.data && node.data.选择 === true) {
                selectedData.push(node.data);
            }
        });
        
        // 当用户点击选择框时，发送数据到Streamlit
        if (e.type === 'cellValueChanged' && e.column && e.column.colId === '选择') {
            // 这里将选中状态数据传回Streamlit
            let targetData = {
                event_type: 'selection_changed',
                rowData: rowData,
                selectedData: selectedData
            };
            
            // 发送数据到Streamlit组件
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: targetData
            }, '*');
        }
        
        // 当用户进行筛选、排序或分组等操作时
        if (e.type === 'filterChanged' || e.type === 'sortChanged' || e.type === 'columnRowGroupChanged') {
            let targetData = {
                event_type: e.type,
                rowData: rowData
            };
            
            // 发送数据到Streamlit组件
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: targetData
            }, '*');
        }
        
        // 当用户编辑单元格内容时
        if (e.type === 'cellValueChanged' && e.column && e.column.colId !== '选择') {
            let targetData = {
                event_type: 'cell_edited',
                rowData: rowData,
                changedCell: {
                    row: e.node.rowIndex,
                    column: e.column.colId,
                    oldValue: e.oldValue,
                    newValue: e.newValue
                }
            };
            
            // 发送数据到Streamlit组件
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: targetData
            }, '*');
        }
    }
    """)
    
    gb.configure_grid_options(
        getRowStyle=js_code,
        # 启用分组功能
        groupDisplayType="groupRows",
        rowGroupPanelShow="always" if st.session_state.aggrid_group_by else "never",
        # 根据用户选择设置默认分组
        groupDefaultExpanded=-1,  # 全部展开
        # 添加拖拽功能
        rowDragManaged=True,
        animateRows=True,
        # 添加事件监听器 - 用于触发器
        onCellValueChanged=custom_js if enable_trigger else None,
        onFilterChanged=custom_js if enable_trigger else None,
        onSortChanged=custom_js if enable_trigger else None,
        onColumnRowGroupChanged=custom_js if enable_trigger else None
    )
    
    # 构建最终选项
    grid_options = gb.build()
    
    # 渲染 AgGrid
    grid_return = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED if not enable_trigger else GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=enable_enterprise,
        height=500,
        width='100%',
        key='aggrid_table',
        reload_data=False,
        allow_unsafe_jscode=True,
        theme=theme_option,
    )
    
    # 处理 AgGrid 触发器返回的数据
    if enable_trigger and grid_return.get('selected_rows') and 'data' in grid_return:
        # 这里处理通过触发器获取的数据
        if isinstance(grid_return.get('selected_rows'), list):
            # 从触发器返回的已选择行更新选择状态
            selected_names = [row.get('name') for row in grid_return['selected_rows'] if row.get('name')]
            
            # 更新选择状态
            has_changes = False
            for task, is_selected in st.session_state.selected.items():
                new_selection = task in selected_names
                if is_selected != new_selection:
                    st.session_state.selected[task] = new_selection
                    has_changes = True
            
            # 只有当有变化时才更新选中的任务列表
            if has_changes:
                st.session_state.selected_tasks = [
                    task for task, is_selected in st.session_state.selected.items() 
                    if is_selected
                ]
    # 标准数据处理 (无触发器或触发器未启用时)
    elif grid_return and 'data' in grid_return:
        updated_df = pd.DataFrame(grid_return['data'])
        
        # 检查选择状态是否有变化
        has_changes = False
        
        # 更新选择状态
        for idx, row in updated_df.iterrows():
            task_name = row['name']
            if task_name and pd.notna(task_name):  # 确保任务名有效
                # 确保布尔值类型一致
                current_selection = bool(row['选择'])
                if st.session_state.selected.get(task_name) != current_selection:
                    st.session_state.selected[task_name] = current_selection
                    has_changes = True
        
        # 只有当有变化时才更新选中的任务列表
        if has_changes:
            st.session_state.selected_tasks = [
                task for task, is_selected in st.session_state.selected.items() 
                if is_selected
            ]

def render_standard_table(filtered_df, current_taskfile):
    """保留向后兼容的标准表格实现"""
    # 由于我们现在使用标准data_editor，这里重定向到新函数
    render_edit_table(filtered_df, current_taskfile)