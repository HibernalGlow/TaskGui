import pandas as pd
from st_aggrid import GridOptionsBuilder, JsCode

def get_row_style_js():
    """获取行样式的JavaScript代码"""
    return JsCode("""
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

def get_custom_events_js():
    """获取自定义事件的JavaScript代码"""
    return JsCode("""
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

def configure_grid_columns(gb, display_df, settings):
    """配置表格列"""
    # 提取设置
    enable_editing = settings.get('enable_editing', False)
    
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
        filterable=settings.get('enable_filter', True),
        sorteable=settings.get('enable_sorting', True),
        editable=enable_editing,
    )
    
    return gb

def configure_grid_options(gb, settings):
    """配置表格选项"""
    # 提取设置
    enable_row_group = settings.get('enable_row_group', True)
    group_by_columns = settings.get('group_by_columns', [])
    enable_multi_select = settings.get('enable_multiselect', True)
    enable_row_pinning = settings.get('enable_row_pinning', True)
    enable_pagination = settings.get('enable_pagination', True)
    page_size = settings.get('page_size', 100)
    enable_column_resize = settings.get('enable_column_resize', True)
    enable_side_bar = settings.get('enable_side_bar', True)
    enable_quick_filter = settings.get('enable_quick_filter', True)
    quick_filter_text = settings.get('quick_filter_text', '')
    enable_excel_export = settings.get('enable_excel_export', True)
    enable_trigger = settings.get('enable_trigger', True)
    group_hide_open_parents = settings.get('group_hide_open_parents', True)
    
    # 配置分组功能
    if enable_row_group:
        # 如果有预设的分组列，则设置
        if group_by_columns:
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
        if group_hide_open_parents:
            group_options['groupHideOpenParents'] = True
            
        # 应用分组配置
        gb.configure_grid_options(**group_options)
    
    # 配置多行选择
    if enable_multi_select:
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
    if enable_row_pinning:
        gb.configure_grid_options(
            enableRowDrag=True,
            suppressRowDrag=False,
            suppressMovableColumns=False,
            rowDragManaged=True,
            suppressMoveWhenRowDragging=False
        )
    
    # 配置分页
    if enable_pagination:
        gb.configure_pagination(
            enabled=True,
            paginationAutoPageSize=False,
            paginationPageSize=page_size
        )
    
    # 配置列宽调整
    if enable_column_resize:
        gb.configure_grid_options(
            enableColumnResizing=True,
            suppressColumnVirtualisation=True
        )
    
    # 配置侧边栏
    if enable_side_bar:
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
    if enable_quick_filter:
        gb.configure_grid_options(
            enableQuickFilter=True,
            quickFilterText=quick_filter_text
        )
    
    # 配置Excel导出功能
    if enable_excel_export:
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
    
    # 获取自定义 JavaScript 代码处理选择事件
    js_code = get_row_style_js()
    
    # 获取自定义触发器 JavaScript 代码
    custom_js = get_custom_events_js()
    
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
    
    return gb

def build_grid_options(display_df, settings):
    """构建表格选项"""
    # 创建GridOptionsBuilder实例
    gb = GridOptionsBuilder.from_dataframe(display_df)
    
    # 配置列
    gb = configure_grid_columns(gb, display_df, settings)
    
    # 配置表格选项
    gb = configure_grid_options(gb, settings)
    
    # 构建最终选项
    grid_options = gb.build()
    
    return grid_options