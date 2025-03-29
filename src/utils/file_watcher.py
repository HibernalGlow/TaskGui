#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from threading import Thread
from PyQt6.QtCore import QObject, pyqtSignal

class FileWatcher(QObject):
    """文件变更监控器"""
    
    # 信号定义
    file_changed = pyqtSignal()
    
    def __init__(self, filepath, check_interval=1):
        super().__init__()
        self.filepath = filepath
        self.check_interval = check_interval  # 秒
        self.last_modified = self._get_modified_time()
        self.running = False
        self.thread = None
    
    def _get_modified_time(self):
        """获取文件修改时间"""
        if os.path.exists(self.filepath):
            return os.path.getmtime(self.filepath)
        return 0
    
    def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._watch_thread, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
    
    def _watch_thread(self):
        """监控线程"""
        while self.running:
            current_modified = self._get_modified_time()
            
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                self.file_changed.emit()
            
            time.sleep(self.check_interval)