"""
环境变量数据模型

定义环境变量和路径信息的数据结构。
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class EnvType(Enum):
    """环境变量类型枚举"""
    SYSTEM = "system"
    USER = "user"


class PathStatus(Enum):
    """路径状态枚举"""
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"
    TOO_LONG = "too_long"


@dataclass
class PathInfo:
    """路径信息"""
    path: str
    status: PathStatus
    exists: bool = False
    is_directory: bool = False
    size: Optional[int] = None
    last_modified: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        import os
        from ..utils.helpers import normalize_path, validate_path
        
        # 标准化路径
        self.path = normalize_path(self.path)
        
        # 检查路径存在性
        try:
            self.exists = os.path.exists(self.path)
            if self.exists:
                self.is_directory = os.path.isdir(self.path)
                stat = os.stat(self.path)
                self.size = stat.st_size if not self.is_directory else None
                self.last_modified = datetime.fromtimestamp(stat.st_mtime)
        except (OSError, ValueError) as e:
            self.exists = False
            self.error_message = str(e)
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if len(self.path) > 50:
            return f"...{self.path[-47:]}"
        return self.path
    
    @property
    def tooltip(self) -> str:
        """获取工具提示信息"""
        info = [f"路径: {self.path}"]
        info.append(f"状态: {self.status.value}")
        info.append(f"存在: {'是' if self.exists else '否'}")
        
        if self.exists:
            info.append(f"类型: {'目录' if self.is_directory else '文件'}")
            if self.last_modified:
                info.append(f"修改时间: {self.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.error_message:
            info.append(f"错误: {self.error_message}")
        
        return "\n".join(info)


@dataclass
class EnvironmentVariable:
    """环境变量数据模型"""
    name: str
    value: str
    env_type: EnvType
    original_value: Optional[str] = None
    is_modified: bool = False
    is_new: bool = False
    is_deleted: bool = False
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.original_value is None:
            self.original_value = self.value
        
        if self.created_time is None:
            self.created_time = datetime.now()
    
    @property
    def display_value(self) -> str:
        """获取显示值"""
        from ..utils.helpers import format_env_value_display
        return format_env_value_display(self.value)
    
    @property
    def is_path_variable(self) -> bool:
        """判断是否为PATH类型变量"""
        return self.name.upper() in ['PATH', 'PYTHONPATH', 'CLASSPATH']
    
    @property
    def path_count(self) -> int:
        """获取PATH变量中的路径数量"""
        if not self.is_path_variable:
            return 0
        
        from ..utils.helpers import split_path_value
        paths = split_path_value(self.value)
        return len(paths)
    
    def get_path_list(self) -> List[PathInfo]:
        """获取PATH变量的路径列表"""
        if not self.is_path_variable:
            return []
        
        from ..utils.helpers import split_path_value
        from ..utils.constants import MAX_SINGLE_PATH_LENGTH
        
        paths = split_path_value(self.value)
        path_infos = []
        seen_paths = set()
        
        for path in paths:
            # 检查路径状态
            status = PathStatus.VALID
            
            # 检查是否重复
            path_lower = path.lower()
            if path_lower in seen_paths:
                status = PathStatus.DUPLICATE
            else:
                seen_paths.add(path_lower)
            
            # 检查长度
            if len(path) > MAX_SINGLE_PATH_LENGTH:
                status = PathStatus.TOO_LONG
            
            # 检查有效性
            from ..utils.helpers import validate_path
            if status == PathStatus.VALID and not validate_path(path):
                status = PathStatus.INVALID
            
            path_info = PathInfo(path=path, status=status)
            path_infos.append(path_info)
        
        return path_infos
    
    def set_path_list(self, path_infos: List[PathInfo]) -> None:
        """设置PATH变量的路径列表"""
        if not self.is_path_variable:
            return
        
        from ..utils.helpers import join_path_value
        paths = [info.path for info in path_infos]
        self.value = join_path_value(paths)
        self.mark_modified()
    
    def mark_modified(self) -> None:
        """标记为已修改"""
        if self.value != self.original_value:
            self.is_modified = True
            self.modified_time = datetime.now()
    
    def reset_changes(self) -> None:
        """重置更改"""
        self.value = self.original_value or ""
        self.is_modified = False
        self.modified_time = None
    
    def apply_changes(self) -> None:
        """应用更改"""
        self.original_value = self.value
        self.is_modified = False
        self.is_new = False
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证环境变量"""
        from ..utils.helpers import is_valid_var_name
        from ..utils.constants import MAX_PATH_LENGTH
        
        # 验证变量名
        if not is_valid_var_name(self.name):
            return False, "无效的变量名"
        
        # 验证值长度
        if len(self.value) > MAX_PATH_LENGTH:
            return False, f"变量值过长，超过{MAX_PATH_LENGTH}字符限制"
        
        # 如果是PATH变量，验证PATH格式
        if self.is_path_variable:
            path_infos = self.get_path_list()
            invalid_paths = [info.path for info in path_infos 
                           if info.status == PathStatus.INVALID]
            if invalid_paths:
                return False, f"包含无效路径: {', '.join(invalid_paths[:3])}"
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'value': self.value,
            'env_type': self.env_type.value,
            'original_value': self.original_value,
            'is_modified': self.is_modified,
            'is_new': self.is_new,
            'is_deleted': self.is_deleted,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'modified_time': self.modified_time.isoformat() if self.modified_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentVariable':
        """从字典创建实例"""
        env_var = cls(
            name=data['name'],
            value=data['value'],
            env_type=EnvType(data['env_type']),
            original_value=data.get('original_value'),
            is_modified=data.get('is_modified', False),
            is_new=data.get('is_new', False),
            is_deleted=data.get('is_deleted', False)
        )
        
        # 解析时间
        if data.get('created_time'):
            env_var.created_time = datetime.fromisoformat(data['created_time'])
        if data.get('modified_time'):
            env_var.modified_time = datetime.fromisoformat(data['modified_time'])
        
        return env_var
    
    def __eq__(self, other) -> bool:
        """比较相等性"""
        if not isinstance(other, EnvironmentVariable):
            return False
        return (self.name == other.name and 
                self.env_type == other.env_type)
    
    def __hash__(self) -> int:
        """计算哈希值"""
        return hash((self.name, self.env_type))
    
    def __str__(self) -> str:
        """字符串表示"""
        type_str = "系统" if self.env_type == EnvType.SYSTEM else "用户"
        return f"{type_str}变量: {self.name}={self.display_value}"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"EnvironmentVariable(name='{self.name}', "
                f"value='{self.value[:50]}...', "
                f"env_type={self.env_type}, "
                f"is_modified={self.is_modified})") 
