"""
数据模型模块

包含环境变量和备份相关的数据模型。
"""

from .env_model import EnvironmentVariable, PathInfo
from .backup_model import BackupInfo

__all__ = [
    'EnvironmentVariable',
    'PathInfo',
    'BackupInfo'
] 
