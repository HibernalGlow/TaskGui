#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

class ConfigManager:
    """配置管理器，用于保存和加载应用设置"""
    
    def __init__(self, config_file="app_settings.json"):
        # 确定配置文件的路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".taskfile_gui")
        self.config_file = os.path.join(self.config_dir, config_file)
        self.settings = {}
        
        # 创建配置目录（如果不存在）
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 加载现有配置（如果有）
        self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"加载设置时出错: {e}")
                self.settings = {}
        else:
            self.settings = {}
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存设置时出错: {e}")
            return False
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置值"""
        self.settings[key] = value
        return self.save_settings()