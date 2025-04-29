import sys
import run
import exit

def main():
    """处理命令行参数并调用相应函数"""
    # 检查是否提供了子命令
    if len(sys.argv) > 1 and sys.argv[1] == 'exit':
        # 删除子命令，这样exit.stop_streamlit()就不会将其视为参数
        sys.argv.pop(1)
        exit.stop_streamlit()
    else:
        # 默认行为是启动应用
        run.main()

if __name__ == "__main__":
    main()