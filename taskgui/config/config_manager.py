import os
import yaml
import streamlit as st
from pathlib import Path

class ConfigManager:
    """配置管理器，提供统一的方式访问配置文件"""
    _instance = None
    _config = None
    
    # 配置文件的绝对路径
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """从配置文件加载配置"""
        try:
            # 确保配置文件所在目录存在
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self._config = {}
                # 初次加载如果没有配置文件，尝试从旧位置复制
                old_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.yaml")
                if os.path.exists(old_config_path):
                    with open(old_config_path, "r", encoding="utf-8") as f:
                        self._config = yaml.safe_load(f) or {}
                    # 保存到新位置
                    self.save_config()
        except Exception as e:
            print(f"加载配置时出错: {str(e)}")
            self._config = {}
    
    def get_config(self):
        """获取整个配置"""
        if self._config is None:
            self._load_config()
        return self._config
    
    def get_setting(self, section, key=None, default=None):
        """获取特定部分或键的设置
        
        Args:
            section: 设置部分，如 'basic_settings'
            key: 特定设置键，如果为None则返回整个部分
            default: 如果设置不存在，返回的默认值
        """
        if self._config is None:
            self._load_config()
            
        if section not in self._config:
            return default
            
        if key is None:
            return self._config[section]
        
        if key in self._config[section]:
            return self._config[section][key]
        return default
    
    def update_setting(self, section, key=None, value=None):
        """更新特定部分或键的设置
        
        Args:
            section: 设置部分，如 'basic_settings'
            key: 特定设置键，如果为None则整个部分被value替换
            value: 新的设置值
        """
        if self._config is None:
            self._load_config()
            
        if key is None:
            self._config[section] = value
        else:
            if section not in self._config:
                self._config[section] = {}
            self._config[section][key] = value
        
        self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, sort_keys=False, allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"保存配置时出错: {str(e)}")
            return False
    
# 创建全局单例，方便直接导入
config_manager = ConfigManager()

# 方便的访问函数
def get_config():
    """获取完整配置"""
    return config_manager.get_config()

def get_setting(section, key=None, default=None):
    """获取特定设置"""
    return config_manager.get_setting(section, key, default)

def update_setting(section, key=None, value=None):
    """更新特定设置"""
    return config_manager.update_setting(section, key, value)

def save_config():
    """保存配置到文件"""
    return config_manager.save_config()