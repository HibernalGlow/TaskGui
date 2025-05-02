import os
import yaml
import streamlit as st
from typing import List, Dict, Any, Optional

class TaskfileManager:
    """多Taskfile管理器"""
    
    def __init__(self):
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "config.yaml"
        )
        self.init_manager()
    
    def init_manager(self) -> None:
        """初始化管理器"""
        # 确保会话状态中有taskfile配置
        if 'taskfiles_config' not in st.session_state:
            st.session_state.taskfiles_config = self.load_taskfiles_config()
    
    def load_taskfiles_config(self) -> Dict[str, Any]:
        """从配置文件加载Taskfile配置"""
        if not os.path.exists(self.config_file):
            return {"taskfiles": [], "active_taskfile": None, "merge_mode": False}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # 确保必要的键存在
            if 'taskfiles' not in config:
                config['taskfiles'] = []
            if 'active_taskfile' not in config:
                config['active_taskfile'] = None
            if 'merge_mode' not in config:
                config['merge_mode'] = False
            
            return config
        except Exception as e:
            print(f"加载Taskfile配置时出错: {str(e)}")
            return {"taskfiles": [], "active_taskfile": None, "merge_mode": False}
    
    def save_taskfiles_config(self, config: Dict[str, Any]) -> bool:
        """保存Taskfile配置到配置文件"""
        try:
            # 读取现有配置
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    full_config = yaml.safe_load(f) or {}
            else:
                full_config = {}
            
            # 更新taskfiles相关配置
            full_config['taskfiles'] = config.get('taskfiles', [])
            full_config['active_taskfile'] = config.get('active_taskfile')
            full_config['merge_mode'] = config.get('merge_mode', False)
            
            # 保存回文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(full_config, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"保存Taskfile配置时出错: {str(e)}")
            return False
    
    def get_taskfiles(self) -> List[str]:
        """获取所有已配置的Taskfile路径"""
        config = st.session_state.taskfiles_config
        return config.get('taskfiles', [])
    
    def get_active_taskfile(self) -> Optional[str]:
        """获取当前活动的Taskfile路径"""
        config = st.session_state.taskfiles_config
        active = config.get('active_taskfile')
        
        # 如果没有活动Taskfile但有配置的Taskfile，使用第一个
        if not active and config.get('taskfiles'):
            active = config['taskfiles'][0]
            config['active_taskfile'] = active
            self.save_taskfiles_config(config)
            
        return active
    
    def add_taskfile(self, taskfile_path: str) -> bool:
        """添加一个新的Taskfile到配置中"""
        if not os.path.exists(taskfile_path):
            return False
        
        config = st.session_state.taskfiles_config
        
        # 如果已存在，不重复添加
        if taskfile_path in config['taskfiles']:
            return True
        
        # 添加新Taskfile
        config['taskfiles'].append(taskfile_path)
        
        # 如果是第一个Taskfile，设为活动
        if not config['active_taskfile']:
            config['active_taskfile'] = taskfile_path
        
        # 保存配置
        self.save_taskfiles_config(config)
        return True
    
    def remove_taskfile(self, taskfile_path: str) -> bool:
        """从配置中移除一个Taskfile"""
        config = st.session_state.taskfiles_config
        
        if taskfile_path not in config['taskfiles']:
            return False
        
        # 移除Taskfile
        config['taskfiles'].remove(taskfile_path)
        
        # 如果移除的是当前活动的Taskfile，重置活动Taskfile
        if config['active_taskfile'] == taskfile_path:
            config['active_taskfile'] = config['taskfiles'][0] if config['taskfiles'] else None
        
        # 保存配置
        self.save_taskfiles_config(config)
        return True
    
    def set_active_taskfile(self, taskfile_path: str) -> bool:
        """设置活动Taskfile"""
        if not os.path.exists(taskfile_path):
            return False
        
        config = st.session_state.taskfiles_config
        
        # 如果Taskfile不在列表中，先添加
        if taskfile_path not in config['taskfiles']:
            config['taskfiles'].append(taskfile_path)
        
        # 设置为活动Taskfile
        config['active_taskfile'] = taskfile_path
        
        # 保存配置
        self.save_taskfiles_config(config)
        return True
    
    def set_merge_mode(self, enabled: bool) -> bool:
        """设置是否合并显示所有Taskfile的任务"""
        config = st.session_state.taskfiles_config
        config['merge_mode'] = enabled
        self.save_taskfiles_config(config)
        return True
    
    def get_merge_mode(self) -> bool:
        """获取是否启用合并模式"""
        config = st.session_state.taskfiles_config
        return config.get('merge_mode', False)

# 全局实例
_taskfile_manager = None

def get_taskfile_manager() -> TaskfileManager:
    """获取TaskfileManager单例"""
    global _taskfile_manager
    if _taskfile_manager is None:
        _taskfile_manager = TaskfileManager()
    return _taskfile_manager