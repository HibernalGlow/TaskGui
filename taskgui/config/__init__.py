"""
配置管理模块，提供全局统一的配置文件访问
"""

from .config_manager import (
    get_config, 
    get_setting, 
    update_setting, 
    save_config, 
    config_manager
)

__all__ = ['get_config', 'get_setting', 'update_setting', 'save_config', 'config_manager']