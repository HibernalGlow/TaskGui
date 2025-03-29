# Taskfile GUI 工具

这是一个简单的GUI工具，用于解析、选择和执行[Taskfile](https://taskfile.dev/)中定义的任务。

## 功能

- 解析Taskfile.yml文件
- 可视化显示可用任务列表
- 选择要执行的一个或多个任务
- 实时预览生成的task命令
- 复制命令到剪贴板
- 支持串行和并行执行模式
- 直接执行选定的任务

## 依赖

- Python 3.6+
- PyQt6
- PyYAML
- task命令行工具（需要在系统PATH中可用）

## 安装

1. 克隆或下载该仓库
2. 安装依赖：
```
pip install -r requirements.txt
```
3. 确保已安装[Task](https://taskfile.dev/installation/)命令行工具

## 使用方法

### GUI版本

```
python task_gui_min.py
```

1. 点击"浏览..."按钮选择一个Taskfile.yml文件
2. 从任务列表中选择一个或多个任务
3. 选择执行模式：
   - 串行模式（默认）：按顺序执行所有任务
   - 并行模式：同时执行多个任务（选中"并行模式"复选框）
4. 在右侧命令预览窗口中查看将要执行的task命令
5. 点击"复制命令"按钮将命令复制到剪贴板
6. 点击"执行任务"按钮运行所选任务

### 命令行版本

```
python task_parser_min.py <taskfile_path> [task1 task2 ...] [--parallel]
```

例如：
```
# 串行执行
python task_parser_min.py Taskfile.yml build test

# 并行执行
python task_parser_min.py Taskfile.yml build test --parallel
```

## 执行模式

### 串行模式
在串行模式下，所有选定的任务会组合成一个命令，使用task命令的多任务功能按顺序执行：
```
task --taskfile path/to/Taskfile.yml task1 task2 task3
```

### 并行模式
在并行模式下，每个任务将单独启动一个线程执行，多个任务会同时运行：
```
# 实际执行时会在多个线程中同时运行这些命令
task --taskfile path/to/Taskfile.yml task1
task --taskfile path/to/Taskfile.yml task2
task --taskfile path/to/Taskfile.yml task3
```

## 注意事项

- 请确保系统中已安装[Task](https://taskfile.dev/installation/)命令行工具，并且可以在命令行中直接运行`task`命令
- 执行任务时会在当前工作目录中运行task命令，请确保当前目录和Taskfile所在目录一致，或者已经设置了`--taskfile`参数
- 串行模式下，多个任务会按照在GUI中选择的顺序执行
- 并行模式适合执行相互独立的任务，如果任务之间有依赖关系，请使用串行模式

## 许可证

MIT 