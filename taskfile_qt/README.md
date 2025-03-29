# Taskfile GUI 工具

这是一个简单的GUI工具，用于解析、选择和执行[Taskfile](https://taskfile.dev/)中定义的任务。

## 功能

- 解析Taskfile.yml文件
- 卡片式展示可用任务列表，直观美观
- 支持按名称、描述或默认顺序排序任务
- 选择要执行的一个或多个任务
- 实时预览生成的task命令
- 复制命令到剪贴板
- 支持串行和并行执行模式
- 记忆上次打开的文件和设置
- 在Windows Terminal中使用PowerShell执行命令
- 支持清空选择和全选功能
- 执行任务后自动清空选择
- 直接执行选定的任务，无需成功弹窗打断工作流
- 支持暗色主题

## 项目结构

```
taskfile_gui/
├── src/
│   ├── __init__.py
│   ├── core/                # 核心功能
│   │   ├── __init__.py
│   │   ├── parser.py        # Taskfile解析器
│   │   └── config.py        # 配置管理
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── task.py          # 任务模型
│   ├── gui/                 # 图形界面
│   │   ├── __init__.py
│   │   ├── main_window.py   # 主窗口
│   │   └── components/      # UI组件
│   │       ├── __init__.py
│   │       └── task_card.py # 任务卡片
│   └── utils/               # 工具类
│       ├── __init__.py
│       └── command.py       # 命令生成与执行
├── resources/               # 资源文件
│   ├── styles/
│   │   └── dark.qss        # 暗色主题样式
│   └── icons/
├── main.py                  # 程序入口
└── requirements.txt         # 依赖清单
```

## 依赖

- Python 3.6+
- PyQt6
- PyYAML
- task命令行工具（需要在系统PATH中可用）
- Windows Terminal (wt.exe)（Windows平台）

## 安装

1. 克隆或下载该仓库
2. 安装依赖：
```bash
pip install -r requirements.txt
```
3. 确保已安装[Task](https://taskfile.dev/installation/)命令行工具
4. Windows用户需要安装[Windows Terminal](https://aka.ms/terminal)

## 使用方法

```bash
python main.py
```

1. 启动时会自动加载上次打开的Taskfile（如有）
2. 点击"浏览..."按钮可以选择一个新的Taskfile.yml文件
3. 从卡片视图中选择一个或多个任务
4. 使用"按名称排序"、"按描述排序"、"默认顺序"来调整任务展示顺序
5. 使用"全选"和"清空选择"按钮快速管理选择
6. 选择执行模式：
   - 串行模式（默认）：按顺序执行所有任务
   - 并行模式：同时执行多个任务（选中"并行模式"复选框）
7. 在右侧命令预览窗口中查看将要执行的task命令
8. 点击"复制命令"按钮将命令复制到剪贴板
9. 点击"执行任务"按钮在Windows Terminal中运行所选任务

## 配置和记忆功能

程序会自动记住以下设置：

- 上次打开的Taskfile文件路径（下次启动时自动加载）
- 并行/串行执行模式的选择
- 任务排序方式（按名称、按描述或默认顺序）

配置信息保存在用户主目录下的`.taskgui_config.json`文件中。

## 注意事项

- 请确保系统中已安装[Task](https://taskfile.dev/installation/)命令行工具，并且可以在命令行中直接运行`task`命令
- Windows用户需要安装Windows Terminal并确保`wt.exe`在系统路径中可用
- 执行任务时会在当前工作目录中运行task命令，请确保当前目录和Taskfile所在目录一致，或者已经设置了`--taskfile`参数
- 串行模式下，多个任务会按照排序方式确定的顺序执行
- 并行模式适合执行相互独立的任务，如果任务之间有依赖关系，请使用串行模式

## 许可证

MIT 