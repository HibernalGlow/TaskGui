def render_dataframe_view(tasks_df, selected_tasks, on_task_select, on_task_unselect, on_task_delete):
    """渲染表格视图"""
    # 创建多列布局
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 使用AgGrid显示任务列表
        gb = GridOptionsBuilder.from_dataframe(tasks_df)
        
        # 配置列
        gb.configure_column("name", headerName="任务名称", pinned='left', width=200)
        gb.configure_column("description", headerName="描述", flex=1)
        gb.configure_column("tags", headerName="标签", flex=1)
        gb.configure_column("directory", headerName="目录", flex=1)
        gb.configure_column("status", headerName="状态", width=100)
        gb.configure_column("created_at", headerName="创建时间", width=180)
        gb.configure_column("updated_at", headerName="更新时间", width=180)
        
        # 添加操作列
        gb.configure_column(
            "actions",
            headerName="操作",
            width=120,
            pinned='right',
            cellRenderer=JsCode("""
                function(params) {
                    return '<button onclick="handleTaskAction(\'' + params.data.name + '\', \'delete\')" style="color: red;">删除</button>';
                }
            """)
        )
        
        # 配置选择列
        gb.configure_selection('single')
        
        # 配置表格选项
        gb.configure_pagination(enabled=True, paginationPageSize=10)
        gb.configure_side_bar()
        gb.configure_default_column(
            sortable=True,
            filterable=True,
            resizable=True
        )
        
        # 设置表格高度
        gb.configure_grid_options(domLayout='normal')
        
        # 构建表格选项
        grid_options = gb.build()
        
        # 添加自定义JavaScript
        st.markdown("""
            <script>
                function handleTaskAction(taskName, action) {
                    const data = {
                        taskName: taskName,
                        action: action
                    };
                    window.parent.postMessage(data, '*');
                }
            </script>
        """, unsafe_allow_html=True)
        
        # 渲染表格
        grid_response = AgGrid(
            tasks_df,
            grid_options=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme='streamlit'
        )
        
        # 处理选择事件
        if grid_response['selected_rows']:
            selected_task = grid_response['selected_rows'][0]
            if selected_task['name'] not in selected_tasks:
                on_task_select(selected_task['name'])
    
    with col2:
        # 显示选中任务的详细信息
        if selected_tasks:
            st.subheader("选中任务")
            for task_name in selected_tasks:
                task_data = tasks_df[tasks_df['name'] == task_name].iloc[0]
                with st.expander(task_name, expanded=True):
                    st.write(f"描述: {task_data['description']}")
                    st.write(f"标签: {', '.join(task_data['tags'])}")
                    st.write(f"目录: {task_data['directory']}")
                    st.write(f"状态: {task_data['status']}")
                    st.write(f"创建时间: {task_data['created_at']}")
                    st.write(f"更新时间: {task_data['updated_at']}")
                    
                    # 添加取消选择和删除按钮
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("取消选择", key=f"unselect_{task_name}"):
                            on_task_unselect(task_name)
                    with col2:
                        if st.button("删除", key=f"delete_{task_name}", type="secondary"):
                            on_task_delete(task_name)
        else:
            st.info("未选择任何任务") 