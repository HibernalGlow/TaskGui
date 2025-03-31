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
from src.utils.selection_utils import update_task_selection, get_task_selection_state, init_global_state, force_save_state, update_memory_cache, get_selected_tasks

# 添加配置更新函数
def update_aggrid_setting(setting_key, value):
    """更新AgGrid设置并保存到session_state"""
    if 'aggrid_settings' not in st.session_state:
        st.session_state.aggrid_settings = {}
    st.session_state.aggrid_settings[setting_key] = value
    
def render_aggrid_table(filtered_df, current_taskfile):
    """使用AgGrid渲染表格 - 使用内存状态管理"""
    if not HAS_AGGRID:
        st.warning("未安装st-aggrid。请使用 `pip install streamlit-aggrid` 安装")
        return
    
    # 确保全局状态已初始化
    init_global_state()
    
    # 初始化配置持久化状态
    if 'aggrid_settings' not in st.session_state:
        st.session_state.aggrid_settings = {}
    
    # 默认设置值
    default_settings = {
        'enable_filter': True,
        'enable_sorting': True,
        'enable_trigger': True,
        'enable_row_group': True,
        'enable_multiselect': True,  # 使用自定义勾选列进行多选，原生勾选框被隐藏
        'enable_editing': False,
        'enable_enterprise': True,
        'theme': 'streamlit',
        'enable_excel_export': True,
        'enable_row_pinning': True,
        'group_by_columns': [],  # 默认不使用目录分组
        'auto_group_column': True,
        'group_hide_open_parents': True,
        'enable_pagination': True,
        'page_size': 100,
        'enable_column_resize': True,
        'enable_side_bar': True,
        'enable_quick_filter': True,
        'quick_filter_text': '',
        'enable_full_height': True,  # 默认显示全部内容，不使用滚动条
        'fixed_height': 500,  # 默认固定高度值（当不使用全高度时）
    }
    
    # 初始化或更新默认设置
    for key, value in default_settings.items():
        if key not in st.session_state.aggrid_settings:
            st.session_state.aggrid_settings[key] = value
    
    # 准备表格数据
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['tags_str'] = filtered_df_copy['tags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
    filtered_df_copy['显示名称'] = filtered_df_copy.apply(lambda x: f"{x['emoji']} {x['name']}", axis=1)
    
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
        st.write("表格过滤设置")
        
        # 其他AgGrid功能选项
        col1, col2 = st.columns(2)
        with col1:
            enable_filter = st.checkbox(
                "启用列过滤", 
                value=st.session_state.aggrid_settings['enable_filter'], 
                key="aggrid_enable_filter",
                on_change=lambda: update_aggrid_setting('enable_filter', st.session_state.aggrid_enable_filter)
            )
            enable_sorting = st.checkbox(
                "启用排序", 
                value=st.session_state.aggrid_settings['enable_sorting'], 
                key="aggrid_enable_sorting",
                on_change=lambda: update_aggrid_setting('enable_sorting', st.session_state.aggrid_enable_sorting)
            )
            enable_trigger = st.checkbox(
                "启用交互触发器", 
                value=st.session_state.aggrid_settings['enable_trigger'], 
                key="aggrid_enable_trigger",
                on_change=lambda: update_aggrid_setting('enable_trigger', st.session_state.aggrid_enable_trigger)
            )
            # 添加行分组功能
            enable_row_group = st.checkbox(
                "启用数据分组", 
                value=st.session_state.aggrid_settings['enable_row_group'], 
                key="aggrid_enable_rowgroup",
                on_change=lambda: update_aggrid_setting('enable_row_group', st.session_state.aggrid_enable_rowgroup)
            )
            # 添加多行选择功能
            enable_multi_select = st.checkbox(
                "启用多行选择", 
                value=st.session_state.aggrid_settings['enable_multiselect'], 
                key="aggrid_enable_multiselect",
                on_change=lambda: update_aggrid_setting('enable_multiselect', st.session_state.aggrid_enable_multiselect),
                help="使用自定义勾选框实现多行选择，原生勾选框已隐藏"
            )
        
        with col2:
            enable_editing = st.checkbox(
                "允许编辑单元格", 
                value=st.session_state.aggrid_settings['enable_editing'], 
                key="aggrid_enable_editing",
                on_change=lambda: update_aggrid_setting('enable_editing', st.session_state.aggrid_enable_editing)
            )
            enable_enterprise = st.checkbox(
                "启用企业功能", 
                value=st.session_state.aggrid_settings['enable_enterprise'], 
                key="aggrid_enable_enterprise",
                on_change=lambda: update_aggrid_setting('enable_enterprise', st.session_state.aggrid_enable_enterprise)
            )
            theme_options = ["streamlit", "light", "dark", "blue", "fresh", "material"]
            theme_index = theme_options.index(st.session_state.aggrid_settings['theme']) if st.session_state.aggrid_settings['theme'] in theme_options else 0
            theme_option = st.selectbox(
                "表格主题",
                options=theme_options,
                index=theme_index,
                key="aggrid_theme",
                on_change=lambda: update_aggrid_setting('theme', st.session_state.aggrid_theme)
            )
            # 添加Excel导出功能
            enable_excel_export = st.checkbox(
                "启用Excel导出", 
                value=st.session_state.aggrid_settings['enable_excel_export'], 
                key="aggrid_enable_excel_export",
                on_change=lambda: update_aggrid_setting('enable_excel_export', st.session_state.aggrid_enable_excel_export)
            )
            # 添加列/行固定功能
            enable_row_pinning = st.checkbox(
                "启用行固定", 
                value=st.session_state.aggrid_settings['enable_row_pinning'], 
                key="aggrid_enable_row_pinning",
                on_change=lambda: update_aggrid_setting('enable_row_pinning', st.session_state.aggrid_enable_row_pinning)
            )
        
        # 分组设置
        if enable_row_group:
            st.write("分组设置")
            groupable_columns = ["显示名称", "描述", "标签", "目录"]
            group_by_columns = st.multiselect(
                "选择要分组的列",
                options=groupable_columns,
                default=st.session_state.aggrid_settings['group_by_columns'],
                key="aggrid_group_columns",
                on_change=lambda: update_aggrid_setting('group_by_columns', st.session_state.aggrid_group_columns)
            )
            
            auto_group_column = st.checkbox(
                "自动创建分组列", 
                value=st.session_state.aggrid_settings['auto_group_column'], 
                key="aggrid_auto_group_column",
                on_change=lambda: update_aggrid_setting('auto_group_column', st.session_state.aggrid_auto_group_column)
            )
            group_hide_open_parents = st.checkbox(
                "隐藏已展开的父级", 
                value=st.session_state.aggrid_settings['group_hide_open_parents'], 
                key="aggrid_hide_open_parents",
                on_change=lambda: update_aggrid_setting('group_hide_open_parents', st.session_state.aggrid_hide_open_parents)
            )
        
        # 高级表格功能
        st.write("高级表格功能")
        col3, col4 = st.columns(2)
        with col3:
            enable_pagination = st.checkbox(
                "启用分页", 
                value=st.session_state.aggrid_settings['enable_pagination'], 
                key="aggrid_enable_pagination",
                on_change=lambda: update_aggrid_setting('enable_pagination', st.session_state.aggrid_enable_pagination)
            )
            if enable_pagination:
                page_size = st.number_input(
                    "每页行数", 
                    min_value=5, 
                    max_value=100, 
                    value=st.session_state.aggrid_settings['page_size'], 
                    step=5, 
                    key="aggrid_page_size",
                    on_change=lambda: update_aggrid_setting('page_size', st.session_state.aggrid_page_size)
                )
            
            enable_column_resize = st.checkbox(
                "允许调整列宽", 
                value=st.session_state.aggrid_settings['enable_column_resize'], 
                key="aggrid_enable_column_resize",
                on_change=lambda: update_aggrid_setting('enable_column_resize', st.session_state.aggrid_enable_column_resize)
            )
            
            # 添加表格高度设置
            enable_full_height = st.checkbox(
                "显示全部内容（不滚动）", 
                value=st.session_state.aggrid_settings['enable_full_height'], 
                key="aggrid_enable_full_height",
                on_change=lambda: update_aggrid_setting('enable_full_height', st.session_state.aggrid_enable_full_height),
                help="启用后表格将显示所有行，不使用滚动条"
            )
            if not enable_full_height:
                fixed_height = st.number_input(
                    "表格固定高度(px)", 
                    min_value=200, 
                    max_value=2000, 
                    value=st.session_state.aggrid_settings['fixed_height'], 
                    step=50, 
                    key="aggrid_fixed_height",
                    on_change=lambda: update_aggrid_setting('fixed_height', st.session_state.aggrid_fixed_height)
                )
        
        with col4:
            enable_side_bar = st.checkbox(
                "显示侧边栏", 
                value=st.session_state.aggrid_settings['enable_side_bar'], 
                key="aggrid_enable_side_bar",
                on_change=lambda: update_aggrid_setting('enable_side_bar', st.session_state.aggrid_enable_side_bar)
            )
            enable_quick_filter = st.checkbox(
                "启用快速筛选", 
                value=st.session_state.aggrid_settings['enable_quick_filter'], 
                key="aggrid_enable_quick_filter",
                on_change=lambda: update_aggrid_setting('enable_quick_filter', st.session_state.aggrid_enable_quick_filter)
            )
            if enable_quick_filter:
                quick_filter_text = st.text_input(
                    "快速筛选", 
                    value=st.session_state.aggrid_settings['quick_filter_text'],
                    key="aggrid_quick_filter_text",
                    on_change=lambda: update_aggrid_setting('quick_filter_text', st.session_state.aggrid_quick_filter_text)
                )
        
        # 添加保存/重置按钮
        col5, col6 = st.columns(2)
        with col5:
            if st.button("保存当前配置为默认", key="save_aggrid_config"):
                # 已经在on_change中保存了，这里只需提示
                st.success("当前配置已保存")
        
        with col6:
            if st.button("重置为默认配置", key="reset_aggrid_config"):
                for key, value in default_settings.items():
                    st.session_state.aggrid_settings[key] = value
                st.rerun()
    
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
                       enableRowGroup=True,  # 启用行分组
                       width=150)
    
    gb.configure_column('描述', 
                       header_name="任务描述", 
                       editable=enable_editing,
                       enableRowGroup=True,  # 启用行分组
                       autoHeight=True,
                       wrapText=True)
    
    # 配置标签和目录列
    gb.configure_column('标签', 
                       header_name="标签", 
                       editable=enable_editing,
                       enableRowGroup=True,  # 启用行分组
                       filter=True)
    
    gb.configure_column('目录', 
                       header_name="任务目录", 
                       editable=enable_editing,
                       enableRowGroup=True,  # 启用行分组
                       filter=True)
    
    # 启用排序和过滤功能
    gb.configure_default_column(
        filterable=enable_filter,
        sorteable=enable_sorting,
        editable=enable_editing,
    )

    # 配置分组功能
    if 'enable_row_group' in locals() and enable_row_group:
        # 如果有预设的分组列，则设置
        if 'group_by_columns' in locals() and group_by_columns:
            for col in group_by_columns:
                gb.configure_column(col, rowGroup=True)
        
        # 分组专用选项
        group_options = {
            # 自动分组列定义
            'autoGroupColumnDef': {
                "headerName": "分组",
                "minWidth": 200,
                "cellRendererParams": {
                    "suppressCount": False,  # 显示每组的计数
                }
            }
        }
        
        # 隐藏已展开的父级配置（可选）
        if 'group_hide_open_parents' in locals() and group_hide_open_parents:
            group_options['groupHideOpenParents'] = True
            
        # 应用分组配置
        gb.configure_grid_options(**group_options)
    
    # 配置多行选择
    if 'enable_multi_select' in locals() and enable_multi_select:
        gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=False,  # 不使用原生勾选框
            groupSelectsChildren=True,
            groupSelectsFiltered=True
        )
        
        # 添加隐藏原生选择框的设置
        gb.configure_grid_options(
            suppressRowClickSelection=True,  # 阻止点击行时自动选择
            suppressCellSelection=False,     # 允许单元格选择
        )
    
    # 配置行固定
    if 'enable_row_pinning' in locals() and enable_row_pinning:
        gb.configure_grid_options(
            enableRowDrag=True,
            suppressRowDrag=False,
            suppressMovableColumns=False,
            rowDragManaged=True,
            suppressMoveWhenRowDragging=False
        )
    
    # 配置分页
    if 'enable_pagination' in locals() and enable_pagination:
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=page_size if 'page_size' in locals() else 20
        )
    
    # 配置列宽调整
    if 'enable_column_resize' in locals() and enable_column_resize:
        gb.configure_grid_options(
            enableColumnResizing=True,
            suppressColumnVirtualisation=True
        )
        
    # 配置全高度显示，禁用虚拟滚动
    # if 'enable_full_height' in locals() and enable_full_height:
    #     gb.configure_grid_options(
    #         domLayout='normal',  # 使用普通布局而非自动高度
    #         suppressRowVirtualisation=True,  # 禁用行虚拟化
    #         suppressColumnVirtualisation=True,  # 禁用列虚拟化
    #         suppressHorizontalScroll=False,  # 保留水平滚动
    #         suppressScrollOnNewData=True,  # 阻止新数据加载时滚动
    #         alwaysShowVerticalScroll=False  # 不总是显示垂直滚动条
    #     )
    
    # 配置侧边栏
    if 'enable_side_bar' in locals() and enable_side_bar:
        side_bar_config = {
            "toolPanels": [
                {
                    "id": "columns",
                    "labelDefault": "列",
                    "labelKey": "columns",
                    "iconKey": "columns",
                    "toolPanel": "agColumnsToolPanel",
                },
                {
                    "id": "filters",
                    "labelDefault": "筛选器",
                    "labelKey": "filters",
                    "iconKey": "filter",
                    "toolPanel": "agFiltersToolPanel",
                }
            ],
            "defaultToolPanel": ""
        }
        gb.configure_side_bar(side_bar_config)
    
    # 配置快速筛选
    if 'enable_quick_filter' in locals() and enable_quick_filter:
        gb.configure_grid_options(
            enableQuickFilter=True,
            quickFilterText=quick_filter_text if 'quick_filter_text' in locals() else ""
        )
    
    # 配置Excel导出功能
    if 'enable_excel_export' in locals() and enable_excel_export:
        gb.configure_grid_options(
            enableRangeSelection=True,
            allowContextMenuWithControlKey=True,
            getContextMenuItems=JsCode("""
            function getContextMenuItems(params) {
                return [
                    'copy',
                    'copyWithHeaders',
                    'paste',
                    'separator',
                    'export',
                    {
                        name: '导出到Excel',
                        action: function() {
                            params.api.exportDataAsExcel();
                        }
                    }
                ];
            }
            """)
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
        
        // 当用户进行筛选、排序等操作时
        if (e.type === 'filterChanged' || e.type === 'sortChanged') {
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
    
    # 基础网格选项配置（适用于所有模式）
    base_grid_options = {
        # 启用行分组面板
        'rowGroupPanelShow': 'always',  # 始终显示分组面板
        'suppressDragLeaveHidesColumns': False,  # 允许拖拽列到分组面板
        # 行分组基本配置
        'groupSelectsChildren': True,
        'groupDefaultExpanded': 1,  # 默认展开第一级
        # 拖拽配置
        'rowDragManaged': True,
        'animateRows': True,
        # 样式和事件
        'getRowStyle': js_code
    }
    
    # 添加事件监听器（仅在启用触发器时）
    if enable_trigger:
        base_grid_options.update({
            'onCellValueChanged': custom_js,
            'onFilterChanged': custom_js,
            'onSortChanged': custom_js
        })
    
    # 应用基础配置
    gb.configure_grid_options(**base_grid_options)
    
    # 构建最终选项
    grid_options = gb.build()
    

    
    # # 在表格上方添加操作按钮
    # col1, col2, col3 = st.columns([1, 1, 2])
    # with col1:
    #     if st.button("全部选择", key="select_all_btn"):
    #         # 更新所有可见行的选择状态为选中
    #         for idx, row in filtered_df_copy.iterrows():
    #             task_name = row['name']
    #             if not get_task_selection_state(task_name):
    #                 update_task_selection(task_name, True, rerun=False)
            
    #         # 更新内存缓存
    #         update_memory_cache()
    #         st.rerun()
    
    # with col2:
    #     if st.button("清除选择", key="clear_selection_btn"):
    #         # 更新所有可见行的选择状态为未选中
    #         for idx, row in filtered_df_copy.iterrows():
    #             task_name = row['name']
    #             if get_task_selection_state(task_name):
    #                 update_task_selection(task_name, False, rerun=False)
            
    #         # 更新内存缓存
    #         update_memory_cache()
    #         st.rerun()
    
    # 渲染 AgGrid
    grid_return = AgGrid(
        display_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # 始终使用MODEL_CHANGED模式避免刷新问题
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=enable_enterprise,
        height=None if 'enable_full_height' in locals() and enable_full_height else (st.session_state.aggrid_settings['fixed_height'] if 'fixed_height' in locals() else 500),
        width='100%',
        key='aggrid_table',
        reload_data=False,
        allow_unsafe_jscode=True,
        theme=theme_option,
        # 添加新的高级功能支持
        enable_sidebar=enable_side_bar if 'enable_side_bar' in locals() else st.session_state.aggrid_settings['enable_side_bar'],
        columns_auto_size_mode='FIT_CONTENTS' if 'enable_column_resize' in locals() and enable_column_resize else 'FIT_ALL_COLUMNS_TO_VIEW',
        # 全高度显示所需的额外配置
        domLayout='normal' if 'enable_full_height' in locals() and enable_full_height else 'autoHeight'
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
        
        # 如果有状态变化，强制更新内存缓存并刷新页面
        if has_changes:
            # 更新内存缓存
            force_save_state()
            
            # 更新会话状态中的选中任务列表，确保预览卡能正确显示
            if 'selected_tasks' not in st.session_state:
                st.session_state.selected_tasks = []
            
            # 重新构建选中任务列表
            st.session_state.selected_tasks = list(updated_df[updated_df['选择'] == True]['name'].values)
            
            # 立即刷新页面以更新预览
            st.rerun()
    
    # 表格下方添加状态信息
    selected_tasks = get_selected_tasks()
    st.write(f"当前选中: {len(selected_tasks)} 个任务")
    
    return grid_return
