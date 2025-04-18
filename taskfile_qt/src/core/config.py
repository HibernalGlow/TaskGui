#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

class ConfigManager:
    """简单的配置管理器，用于保存和读取配置信息"""
    
    def __init__(self, config_file=None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为用户目录下的.taskgui_config.json
        """
        if config_file is None:
            home_dir = os.path.expanduser("~")
            self.config_file = os.path.join(home_dir, ".taskgui_config.json")
        else:
            self.config_file = config_file
        
        # 初始化配置
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # 如果配置文件损坏或无法读取，返回空配置
            return {}
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        return self._save_config()
    
    def delete(self, key):
        """删除配置值"""
        if key in self.config:
            del self.config[key]
            return self._save_config()
        return True 