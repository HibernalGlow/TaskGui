# GlowToolBox 任务管理器

一个基于Streamlit的任务管理界面，用于管理和执行Taskfile.yml中定义的任务。

## 功能特性

- 表格视图、卡片视图和分组视图三种展示方式
- 支持按名称、描述和标签排序
- 支持按标签和关键词过滤任务
- 支持打开任务相关文件（使用默认程序）
- 支持复制和运行任务命令
- 支持批量选择和执行任务
- 支持并行执行任务

## 安装

1. 安装依赖包：

```bash
pip install -r requirements.txt
```

2. 安装AgGrid（强烈推荐，获得更好的表格体验）：

```bash
pip install streamlit-aggrid
```

如果已经安装了依赖包，但AgGrid不能正常工作，可以尝试重新安装：

```bash
pip uninstall -y streamlit-aggrid
pip install streamlit-aggrid
```

## 运行

双击`run_task_manager.bat`或执行：

```bash
python run_task_manager.py
```

## 使用说明

1. 启动后，程序会自动加载同级目录下的Taskfile.yml
2. 可以在侧边栏选择其他Taskfile文件
3. 使用表格视图可以排序和筛选任务：
   - 如果安装了AgGrid，点击表格行选择任务，详细信息会显示在下方
   - 如果没有安装AgGrid，将使用标准表格，功能略有限制
4. 点击"打开"按钮可以用默认程序打开任务目录下的文件
5. 点击"复制"按钮可以复制task命令到剪贴板
6. 点击"运行"按钮可以在新的CMD窗口中执行任务

## 关于表格排序

- 使用AgGrid时，可以直接点击表格表头进行排序
- 不使用AgGrid时，可以通过顶部的排序选项进行排序

## 注意事项

- 任务运行在独立的CMD窗口中，不会阻塞主界面
- 并行模式下，多个任务会同时启动，适合互不干扰的任务 