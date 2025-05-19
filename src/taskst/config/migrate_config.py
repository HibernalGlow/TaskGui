"""
迁移配置文件的工具脚本
将根目录的config.yaml移动到taskgui/config/config.yaml
"""

import os
import yaml
import shutil
from pathlib import Path

def migrate_config_file():
    """迁移配置文件从项目根目录到taskgui/config/目录"""
    # 获取项目根目录和目标目录
    current_dir = Path(__file__).parent  # 当前脚本目录 (taskgui/config)
    project_root = current_dir.parent.parent  # 项目根目录
    
    # 源文件和目标文件路径
    source_config = project_root / "config.yaml"
    target_config = current_dir / "config.yaml"
    
    print(f"正在检查配置文件迁移...")
    print(f"源文件: {source_config}")
    print(f"目标文件: {target_config}")
    
    # 检查源文件是否存在
    if not source_config.exists():
        print("源配置文件不存在，无需迁移")
        return False
    
    # 如果目标文件已存在，检查是否需要合并
    if target_config.exists():
        print("目标配置文件已存在，正在合并内容...")
        
        # 读取源文件
        with open(source_config, 'r', encoding='utf-8') as f:
            source_data = yaml.safe_load(f) or {}
        
        # 读取目标文件
        with open(target_config, 'r', encoding='utf-8') as f:
            target_data = yaml.safe_load(f) or {}
        
        # 递归合并配置
        def merge_dict(source, target):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(value, target[key])
                else:
                    target[key] = value
        
        # 合并配置
        merge_dict(source_data, target_data)
        
        # 保存合并后的配置
        with open(target_config, 'w', encoding='utf-8') as f:
            yaml.dump(target_data, f, sort_keys=False, allow_unicode=True, indent=2)
        
        print("配置文件已成功合并")
    else:
        # 如果目标文件不存在，直接复制
        print("正在复制配置文件...")
        shutil.copy2(source_config, target_config)
        print("配置文件已成功复制")
    
    # 创建备份目录
    backup_dir = project_root / "config_backup"
    backup_dir.mkdir(exist_ok=True)
    
    # 备份老配置文件
    backup_file = backup_dir / "config.yaml.bak"
    print(f"备份原配置文件到 {backup_file}...")
    shutil.copy2(source_config, backup_file)
    
    print("配置文件迁移完成！")
    return True

if __name__ == "__main__":
    migrate_config_file()