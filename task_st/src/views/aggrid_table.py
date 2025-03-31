import streamlit as st
import pandas as pd

# 尝试导入AgGrid
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    st.error("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")

# 导入选择状态更新函数
from ..utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, force_save_state, update_memory_cache, get_selected_tasks

def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格 - 使用内存状态管理"""
    if not HAS_AGGRID:
        st.warning("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")
        return
    
    # 确保全局状态已初始化
    init_global_state()
    
    # 准备表格数据
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
    # AgGrid分组设置状态
    if 'aggrid_group_by' not in st.session_state:
        st.session_state.aggrid_group_by = []
    
    # 创建勾选列，从集中状态管理获取
    filtered_df_copy['选择'] = filtered_df_copy['name'].apply(
        lambda x: get_task_selection_state(x)
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
    
    # 为每列单独配置分组属性
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
    
    # 在表格上方添加操作按钮
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("全部选择", key="select_all_btn"):
            # 更新所有可见行的选择状态为选中
            for idx, row in filtered_df_copy.iterrows():
                task_name = row['name']
                if not get_task_selection_state(task_name):
                    update_task_selection(task_name, True, rerun=False)
            
            # 更新内存缓存
            update_memory_cache()
            st.rerun()
    
    with col2:
        if st.button("清除选择", key="clear_selection_btn"):
            # 更新所有可见行的选择状态为未选中
            for idx, row in filtered_df_copy.iterrows():
                task_name = row['name']
                if get_task_selection_state(task_name):
                    update_task_selection(task_name, False, rerun=False)
            
            # 更新内存缓存
            update_memory_cache()
            st.rerun()
    
    # 渲染 AgGrid
    grid_return = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # 始终使用MODEL_CHANGED模式避免刷新问题
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=enable_enterprise,
        height=500,
        width='100%',
        key='aggrid_table',
        reload_data=False,
        allow_unsafe_jscode=True,
        theme=theme_option,
    )
    
    # 处理表格勾选状态变化
    if 'data' in grid_return:
        updated_df = pd.DataFrame(grid_return['data'])
        
        # 记录状态是否有变化
        has_changes = False
        
        # 检查每个任务的选择状态与全局状态是否一致
        for idx, row in updated_df.iterrows():
            task_name = row['name']
            if task_name and pd.notna(task_name):  # 确保任务名有效
                current_selection = bool(row['选择'])
                previous_selection = get_task_selection_state(task_name)
                
                # 如果状态有变化，更新全局状态
                if current_selection != previous_selection:
                    has_changes = True
                    update_task_selection(task_name, current_selection, rerun=False)
        
        # 如果有状态变化，强制更新内存缓存但不刷新页面
        if has_changes:
            # 更新内存缓存
            force_save_state()
            
            # 更新会话状态中的选中任务列表，确保预览卡能正确显示
            if 'selected_tasks' not in st.session_state:
                st.session_state.selected_tasks = []
            
            # 重新构建选中任务列表
            st.session_state.selected_tasks = list(updated_df[updated_df['选择'] == True]['name'].values)
    
    # 表格下方添加状态信息
    selected_tasks = get_selected_tasks()
    st.write(f"当前选中: {len(selected_tasks)} 个任务")
    
    return grid_return
