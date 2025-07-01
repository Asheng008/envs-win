"""
PATH变量专用控制器

专门处理PATH环境变量的复杂操作。
"""

import os
from typing import List
from ..models.env_model import PathInfo, EnvironmentVariable, PathStatus
from ..utils.helpers import split_path_value, join_path_value, normalize_path, validate_path
from ..utils.constants import MAX_SINGLE_PATH_LENGTH, MAX_PATH_LENGTH


class PathController:
    """PATH变量控制器"""
    
    def __init__(self):
        """初始化PATH控制器"""
        pass
    
    def parse_path_value(self, path_value: str) -> List[PathInfo]:
        """解析PATH值为路径信息列表"""
        if not path_value:
            return []
        
        paths = split_path_value(path_value)
        path_infos = []
        seen_paths = set()
        
        for path in paths:
            if not path:  # 跳过空路径
                continue
                
            normalized_path = normalize_path(path)
            status = PathStatus.VALID
            
            # 检查是否重复（不区分大小写）
            path_lower = normalized_path.lower()
            if path_lower in seen_paths:
                status = PathStatus.DUPLICATE
            else:
                seen_paths.add(path_lower)
            
            # 检查长度
            if len(normalized_path) > MAX_SINGLE_PATH_LENGTH:
                status = PathStatus.TOO_LONG
            
            # 检查有效性（只有在不是重复且长度合适的情况下）
            if status == PathStatus.VALID and not validate_path(normalized_path):
                status = PathStatus.INVALID
            
            path_info = PathInfo(path=normalized_path, status=status)
            path_infos.append(path_info)
        
        return path_infos
    
    def build_path_value(self, path_infos: List[PathInfo]) -> str:
        """从路径信息列表构建PATH值"""
        if not path_infos:
            return ""
        
        paths = [info.path for info in path_infos if info.path]
        return join_path_value(paths)
    
    def validate_paths(self, path_infos: List[PathInfo]) -> List[str]:
        """验证路径有效性，返回错误信息列表"""
        errors = []
        
        if not path_infos:
            return errors
        
        # 计算总长度
        total_length = len(self.build_path_value(path_infos))
        if total_length > MAX_PATH_LENGTH:
            errors.append(f"PATH总长度 {total_length} 超过系统限制 {MAX_PATH_LENGTH}")
        
        # 检查各个路径
        invalid_paths = []
        duplicate_paths = []
        too_long_paths = []
        
        for info in path_infos:
            if info.status == PathStatus.INVALID:
                invalid_paths.append(info.path)
            elif info.status == PathStatus.DUPLICATE:
                duplicate_paths.append(info.path)
            elif info.status == PathStatus.TOO_LONG:
                too_long_paths.append(info.path)
        
        if invalid_paths:
            errors.append(f"存在 {len(invalid_paths)} 个无效路径")
        
        if duplicate_paths:
            errors.append(f"存在 {len(duplicate_paths)} 个重复路径")
        
        if too_long_paths:
            errors.append(f"存在 {len(too_long_paths)} 个路径长度超限")
        
        return errors
    
    def remove_duplicates(self, path_infos: List[PathInfo]) -> List[PathInfo]:
        """移除重复路径"""
        if not path_infos:
            return []
        
        seen_paths = set()
        unique_infos = []
        
        for info in path_infos:
            path_lower = info.path.lower()
            if path_lower not in seen_paths:
                seen_paths.add(path_lower)
                # 更新状态，移除重复标记
                if info.status == PathStatus.DUPLICATE:
                    # 重新验证状态
                    if len(info.path) > MAX_SINGLE_PATH_LENGTH:
                        info.status = PathStatus.TOO_LONG
                    elif not validate_path(info.path):
                        info.status = PathStatus.INVALID
                    else:
                        info.status = PathStatus.VALID
                unique_infos.append(info)
        
        return unique_infos
    
    def clean_invalid_paths(self, path_infos: List[PathInfo]) -> List[PathInfo]:
        """清理无效路径"""
        if not path_infos:
            return []
        
        valid_infos = []
        
        for info in path_infos:
            # 只保留有效的路径
            if info.status == PathStatus.VALID or info.status == PathStatus.DUPLICATE:
                valid_infos.append(info)
        
        return valid_infos
    
    def get_path_statistics(self, path_infos: List[PathInfo]) -> dict:
        """获取路径统计信息"""
        if not path_infos:
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'duplicate': 0,
                'too_long': 0,
                'existing': 0,
                'missing': 0,
                'total_length': 0
            }
        
        stats = {
            'total': len(path_infos),
            'valid': 0,
            'invalid': 0,
            'duplicate': 0,
            'too_long': 0,
            'existing': 0,
            'missing': 0,
            'total_length': len(self.build_path_value(path_infos))
        }
        
        for info in path_infos:
            if info.status == PathStatus.VALID:
                stats['valid'] += 1
            elif info.status == PathStatus.INVALID:
                stats['invalid'] += 1
            elif info.status == PathStatus.DUPLICATE:
                stats['duplicate'] += 1
            elif info.status == PathStatus.TOO_LONG:
                stats['too_long'] += 1
            
            if info.exists:
                stats['existing'] += 1
            else:
                stats['missing'] += 1
        
        return stats
    
    def optimize_paths(self, path_infos: List[PathInfo]) -> List[PathInfo]:
        """优化路径列表（去重、清理无效路径、排序）"""
        if not path_infos:
            return []
        
        # 1. 去重
        optimized = self.remove_duplicates(path_infos)
        
        # 2. 清理无效路径
        optimized = self.clean_invalid_paths(optimized)
        
        # 3. 按存在性和重要性排序（存在的路径在前）
        optimized.sort(key=lambda x: (not x.exists, x.path.lower()))
        
        return optimized 
