"""
辅助函数模块

提供各种实用的辅助函数。
"""

import os
import re
import hashlib
from typing import List, Dict, Optional, Union
from pathlib import Path

from .constants import PATH_SEPARATOR, MAX_SINGLE_PATH_LENGTH


def ensure_directory(directory: str) -> None:
    """确保目录存在，不存在则创建"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除或替换Windows文件名中的非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, '_', filename)


def format_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """截断文本，如果超过最大长度则添加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_path(path: str) -> str:
    """标准化路径格式"""
    if not path:
        return ""
    
    # 移除首尾空白字符
    path = path.strip()
    
    # 移除双引号
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    
    # 标准化路径分隔符
    path = path.replace('/', '\\')
    
    # 移除末尾的反斜杠（除了根目录）
    if len(path) > 3 and path.endswith('\\'):
        path = path.rstrip('\\')
    
    return path


def validate_path(path: str) -> bool:
    """验证路径是否有效"""
    if not path:
        return False
    
    try:
        normalized = normalize_path(path)
        
        # 检查路径长度
        if len(normalized) > MAX_SINGLE_PATH_LENGTH:
            return False
        
        # 检查是否包含非法字符
        illegal_chars = '<>"|*?'
        if any(char in normalized for char in illegal_chars):
            return False
        
        # 检查路径是否存在
        return os.path.exists(normalized)
    
    except (OSError, ValueError):
        return False


def split_path_value(path_value: str) -> List[str]:
    """分割PATH值为路径列表"""
    if not path_value:
        return []
    
    paths = []
    for path in path_value.split(PATH_SEPARATOR):
        path = path.strip()
        if path:  # 排除空字符串
            paths.append(normalize_path(path))
    
    return paths


def join_path_value(paths: List[str]) -> str:
    """将路径列表合并为PATH值"""
    if not paths:
        return ""
    
    # 过滤空路径并标准化
    valid_paths = []
    for path in paths:
        normalized = normalize_path(path)
        if normalized:
            valid_paths.append(normalized)
    
    return PATH_SEPARATOR.join(valid_paths)


def remove_duplicate_paths(paths: List[str]) -> List[str]:
    """移除重复的路径（保持顺序）"""
    seen = set()
    result = []
    
    for path in paths:
        normalized = normalize_path(path).lower()
        if normalized not in seen:
            seen.add(normalized)
            result.append(path)
    
    return result


def calculate_md5(text: str) -> str:
    """计算文本的MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def is_valid_var_name(name: str) -> bool:
    """验证环境变量名是否有效"""
    if not name:
        return False
    
    # 环境变量名不能包含等号
    if '=' in name:
        return False
    
    # 环境变量名不能以数字开头
    if name[0].isdigit():
        return False
    
    # 只能包含字母、数字、下划线
    return re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) is not None


def format_env_value_display(value: str, max_length: int = 100) -> str:
    """格式化环境变量值的显示"""
    if not value:
        return ""
    
    # 如果是PATH变量，显示路径数量
    if PATH_SEPARATOR in value:
        paths = split_path_value(value)
        if len(paths) > 1:
            return f"[{len(paths)}个路径]"
    
    # 其他变量直接截断显示
    return truncate_text(value, max_length)


def get_system_info() -> Dict[str, str]:
    """获取系统信息"""
    import platform
    
    return {
        'system': platform.system(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }


def safe_dict_get(dictionary: Dict, key: str, default=None):
    """安全地从字典获取值"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, KeyError):
        return default 
