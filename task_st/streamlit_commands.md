# Streamlit 命令行参数参考

## 基本命令

- `streamlit run [script.py]` - 运行 Streamlit 应用
- `streamlit hello` - 运行演示应用
- `streamlit docs` - 打开 Streamlit 文档
- `streamlit version` - 显示 Streamlit 版本
- `streamlit config show` - 显示所有配置选项
- `streamlit cache clear` - 清除缓存
- `streamlit help` - 显示帮助信息

## 常用命令行参数

### 服务器设置

- `--server.port=[port]` - 指定端口号（默认为 8501）
- `--server.address=[address]` - 指定服务器地址（默认为 localhost）
- `--server.headless=[true/false]` - 是否自动打开浏览器（默认为 true，即不打开）
- `--server.enableCORS=[true/false]` - 是否启用 CORS（默认为 true）
- `--server.enableXsrfProtection=[true/false]` - 是否启用 XSRF 保护（默认为 true）
- `--server.maxUploadSize=[size]` - 最大上传文件大小，单位为 MB（默认为 200）
- `--server.maxMessageSize=[size]` - WebSocket 消息的最大大小，单位为 MB（默认为 200）
- `--server.enableWebsocketCompression=[true/false]` - 是否启用 WebSocket 压缩（默认为 true）
- `--server.runOnSave=[true/false]` - 保存脚本时是否重新运行应用（默认为 true）

### 浏览器设置

- `--browser.serverAddress=[address]` - 浏览器中访问的服务器地址
- `--browser.serverPort=[port]` - 浏览器中访问的服务器端口
- `--browser.gatherUsageStats=[true/false]` - 是否收集使用统计信息（默认为 true）

### 主题设置

- `--theme.base=[light/dark]` - 设置基础主题（亮色或暗色）
- `--theme.primaryColor=[color]` - 设置主色调
- `--theme.backgroundColor=[color]` - 设置背景色
- `--theme.secondaryBackgroundColor=[color]` - 设置次要背景色
- `--theme.textColor=[color]` - 设置文本颜色
- `--theme.font=[font]` - 设置字体

### 缓存设置

- `--cache.maxEntrySize=[size]` - 缓存条目的最大大小，单位为 MB
- `--client.toolbarMode=[auto/developer/viewer/minimal]` - 设置工具栏模式
- `--client.showErrorDetails=[true/false]` - 是否在前端显示错误详情

### 日志设置

- `--logger.level=[debug/info/warning/error/critical]` - 设置日志级别
- `--logger.messageFormat=[string]` - 设置日志消息格式

## 使用示例

在 `run_task_manager.py` 中使用的命令示例：

```python
cmd = [
    sys.executable, 
    "-m", 
    "streamlit", 
    "run", 
    main_script, 
    "--server.headless=false",  # 自动打开浏览器 
    "--browser.serverAddress=localhost",  # 指定服务器地址
    "--server.runOnSave=false"  # 保存时不自动重新运行
]
```

更多详细信息请参考 [Streamlit 官方文档](https://docs.streamlit.io/library/advanced-features/configuration)
