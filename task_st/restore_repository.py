import subprocess
import sys
import os

# 设置环境变量，确保git使用UTF-8输出
os.environ['PYTHONIOENCODING'] = 'utf-8'

# ANSI颜色代码
class Colors:
    CYAN = '\033[96m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# 目标提交哈希
TARGET_COMMIT = "0d0d7218d073c360746b11f6e3a6e952a179e14e"

def run_command(command, error_msg=None):
    """运行Git命令并处理错误"""
    try:
        # 明确指定编码为utf-8，避免系统默认编码问题
        process = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            encoding='utf-8',  # 显式指定UTF-8编码
            errors='replace'   # 对无法解码的字符进行替换而非抛出异常
        )
        return process.stdout.strip() if process.stdout else ""
    except subprocess.CalledProcessError as e:
        if error_msg:
            print(f"{Colors.RED}{error_msg}{Colors.RESET}")
        print(f"{Colors.RED}命令执行失败: {command}{Colors.RESET}")
        print(f"{Colors.RED}错误信息: {e.stderr if e.stderr else '未知错误'}{Colors.RESET}")
        sys.exit(1)

# 获取当前分支名称
CURRENT_BRANCH = run_command("git symbolic-ref --short HEAD")

print(f"{Colors.CYAN}正在恢复仓库到提交 {TARGET_COMMIT} 并保留后续提交...{Colors.RESET}")

# 1. 创建一个临时分支，指向目标提交
run_command(f"git checkout -b temp_restore_branch {TARGET_COMMIT}", "创建临时分支失败！")

# 2. 创建一个新分支，用于存储恢复后的状态
run_command("git checkout -b restored_branch", "创建恢复分支失败！")

# 3. 获取从目标提交到当前最新提交的所有提交哈希（从旧到新）
commits_output = run_command(f"git log --reverse --format=\"%H\" {TARGET_COMMIT}..{CURRENT_BRANCH}")
COMMITS_TO_REAPPLY = [commit for commit in commits_output.split('\n') if commit.strip()]

# 4. 对每个提交执行cherry-pick操作
total_commits = len(COMMITS_TO_REAPPLY)
current_commit = 0

for commit in COMMITS_TO_REAPPLY:
    if commit:
        current_commit += 1
        try:
            commit_msg = run_command(f'git log -1 --pretty=format:"%s" {commit}')
            print(f"{Colors.YELLOW}[{current_commit}/{total_commits}] 正在应用提交: {commit_msg}{Colors.RESET}")
            run_command(f"git cherry-pick {commit}")
        except Exception as e:
            print(f"{Colors.RED}处理提交 {commit} 时出错: {str(e)}{Colors.RESET}")
            print(f"{Colors.RED}请解决冲突后运行 'git cherry-pick --continue'{Colors.RESET}")
            print(f"{Colors.RED}或者中止操作运行 'git cherry-pick --abort'{Colors.RESET}")
            sys.exit(1)

# 5. 输出恢复结果
print(f"\n{Colors.GREEN}✅ 仓库已成功恢复到提交 {TARGET_COMMIT} 并保留了所有后续更改！{Colors.RESET}")
print(f"\n{Colors.CYAN}后续操作:{Colors.RESET}")
print(f"{Colors.WHITE}  1. 检查恢复分支: git checkout restored_branch{Colors.RESET}")
print(f"{Colors.WHITE}  2. 删除临时分支: git branch -D temp_restore_branch{Colors.RESET}")
print(f"{Colors.WHITE}  3. 替换当前分支(可选): {Colors.RESET}")
print(f"{Colors.WHITE}     git branch -m {CURRENT_BRANCH} old_{CURRENT_BRANCH}{Colors.RESET}")
print(f"{Colors.WHITE}     git branch -m restored_branch {CURRENT_BRANCH}{Colors.RESET}")
