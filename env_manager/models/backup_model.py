"""
备份数据模型

定义备份信息的数据结构。
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os


@dataclass
class BackupInfo:
    """备份信息数据模型"""
    backup_id: str
    name: str
    file_path: str
    created_time: datetime
    description: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    env_count: int = 0
    system_env_count: int = 0
    user_env_count: int = 0
    is_automatic: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        # 更新文件信息
        self.update_file_info()
    
    def update_file_info(self) -> None:
        """更新文件信息"""
        try:
            if os.path.exists(self.file_path):
                stat = os.stat(self.file_path)
                self.file_size = stat.st_size
                
                # 计算文件校验和
                from ..utils.helpers import calculate_md5
                with open(self.file_path, 'rb') as f:
                    content = f.read()
                    self.checksum = calculate_md5(content.decode('utf-8', errors='ignore'))
        except (OSError, IOError):
            self.file_size = None
            self.checksum = None
    
    @property
    def file_exists(self) -> bool:
        """检查备份文件是否存在"""
        return os.path.exists(self.file_path)
    
    @property
    def file_size_display(self) -> str:
        """获取文件大小的显示字符串"""
        if self.file_size is None:
            return "未知"
        from ..utils.helpers import format_size
        return format_size(self.file_size)
    
    @property
    def created_time_display(self) -> str:
        """获取创建时间的显示字符串"""
        return self.created_time.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def backup_type_display(self) -> str:
        """获取备份类型的显示字符串"""
        return "自动备份" if self.is_automatic else "手动备份"
    
    @property
    def summary(self) -> str:
        """获取备份摘要信息"""
        parts = []
        
        if self.env_count > 0:
            parts.append(f"共{self.env_count}个变量")
        
        if self.system_env_count > 0:
            parts.append(f"系统{self.system_env_count}个")
        
        if self.user_env_count > 0:
            parts.append(f"用户{self.user_env_count}个")
        
        return " | ".join(parts) if parts else "无环境变量"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'backup_id': self.backup_id,
            'name': self.name,
            'file_path': self.file_path,
            'created_time': self.created_time.isoformat(),
            'description': self.description,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'env_count': self.env_count,
            'system_env_count': self.system_env_count,
            'user_env_count': self.user_env_count,
            'is_automatic': self.is_automatic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        """从字典创建实例"""
        backup = cls(
            backup_id=data['backup_id'],
            name=data['name'],
            file_path=data['file_path'],
            created_time=datetime.fromisoformat(data['created_time']),
            description=data.get('description'),
            file_size=data.get('file_size'),
            checksum=data.get('checksum'),
            env_count=data.get('env_count', 0),
            system_env_count=data.get('system_env_count', 0),
            user_env_count=data.get('user_env_count', 0),
            is_automatic=data.get('is_automatic', False)
        )
        return backup 
