"""
配置管理模块

使用QSettings进行配置的读写操作。
"""

from PySide6.QtCore import QSettings
from typing import Any, Optional, Dict
import os

from .constants import CONFIG_DIR, CONFIG_FILE, APP_NAME, APP_AUTHOR
from .helpers import ensure_directory


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 确保配置目录存在
        ensure_directory(CONFIG_DIR)
        
        # 使用QSettings进行配置管理
        self.settings = QSettings(QSettings.Format.IniFormat, 
                                QSettings.Scope.UserScope,
                                APP_AUTHOR, APP_NAME)
        
        # 设置默认配置
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """设置默认配置值"""
        defaults = {
            # 窗口设置
            'window/width': 1000,
            'window/height': 700,
            'window/maximized': False,
            'window/position': None,
            
            # 界面设置
            'ui/theme': 'light',
            'ui/language': 'zh_CN',
            'ui/font_size': 9,
            'ui/show_system_tray': True,
            
            # 功能设置
            'general/auto_backup': True,
            'general/backup_count': 10,
            'general/confirm_delete': True,
            'general/show_path_count': True,
            
            # 搜索设置
            'search/case_sensitive': False,
            'search/regex_enabled': False,
            'search/remember_history': True,
            
            # 高级设置
            'advanced/check_path_validity': True,
            'advanced/auto_remove_duplicates': False,
            'advanced/path_validation_timeout': 5,
            
            # 日志设置
            'logging/level': 'INFO',
            'logging/max_file_size': 10 * 1024 * 1024,  # 10MB
            'logging/backup_count': 5,
        }
        
        # 只有当配置不存在时才设置默认值
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.settings.value(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.settings.setValue(key, value)
        self.settings.sync()
    
    def remove(self, key: str) -> None:
        """移除配置项"""
        self.settings.remove(key)
        self.settings.sync()
    
    def contains(self, key: str) -> bool:
        """检查配置项是否存在"""
        return self.settings.contains(key)
    
    def get_all_keys(self) -> list:
        """获取所有配置键"""
        return self.settings.allKeys()
    
    def clear(self) -> None:
        """清空所有配置"""
        self.settings.clear()
        self.settings.sync()
        self._set_defaults()
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            # 创建临时设置对象用于导出
            export_settings = QSettings(file_path, QSettings.Format.IniFormat)
            
            # 复制所有设置
            for key in self.settings.allKeys():
                value = self.settings.value(key)
                export_settings.setValue(key, value)
            
            export_settings.sync()
            return True
        except Exception:
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从文件导入配置"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # 创建临时设置对象用于导入
            import_settings = QSettings(file_path, QSettings.Format.IniFormat)
            
            # 复制所有设置
            for key in import_settings.allKeys():
                value = import_settings.value(key)
                self.settings.setValue(key, value)
            
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def backup_config(self, backup_path: str = None) -> Optional[str]:
        """备份当前配置"""
        try:
            if backup_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"config_backup_{timestamp}.ini"
                backup_path = os.path.join(CONFIG_DIR, backup_filename)
            
            if self.export_config(backup_path):
                return backup_path
            return None
        except Exception:
            return None
    
    def get_window_config(self) -> Dict[str, Any]:
        """获取窗口相关配置"""
        return {
            'width': self.get('window/width', 1000),
            'height': self.get('window/height', 700),
            'maximized': self.get('window/maximized', False),
            'position': self.get('window/position')
        }
    
    def set_window_config(self, width: int = None, height: int = None, 
                         maximized: bool = None, position: tuple = None) -> None:
        """设置窗口相关配置"""
        if width is not None:
            self.set('window/width', width)
        if height is not None:
            self.set('window/height', height)
        if maximized is not None:
            self.set('window/maximized', maximized)
        if position is not None:
            self.set('window/position', position)
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI相关配置"""
        return {
            'theme': self.get('ui/theme', 'light'),
            'language': self.get('ui/language', 'zh_CN'),
            'font_size': self.get('ui/font_size', 9),
            'show_system_tray': self.get('ui/show_system_tray', True)
        }
    
    def get_general_config(self) -> Dict[str, Any]:
        """获取通用功能配置"""
        return {
            'auto_backup': self.get('general/auto_backup', True),
            'backup_count': self.get('general/backup_count', 10),
            'confirm_delete': self.get('general/confirm_delete', True),
            'show_path_count': self.get('general/show_path_count', True)
        } 
