"""
数据验证器

提供各种数据验证功能。
"""

import re
import os
from typing import Tuple, Optional, List
from ..models.env_model import EnvironmentVariable, EnvType
from ..utils.constants import MAX_PATH_LENGTH, MAX_SINGLE_PATH_LENGTH, PATH_SEPARATOR
from ..utils.helpers import is_valid_var_name, split_path_value, validate_path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Validator:
    """数据验证器"""
    
    def __init__(self):
        """初始化验证器"""
        # 系统保留的环境变量名（不应该修改或删除）
        self.reserved_system_vars = {
            'COMPUTERNAME', 'COMSPEC', 'NUMBER_OF_PROCESSORS', 'OS', 
            'PROCESSOR_ARCHITECTURE', 'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL',
            'PROCESSOR_REVISION', 'SYSTEMDRIVE', 'SYSTEMROOT', 'WINDIR'
        }
        
        # 重要的环境变量（修改时需要警告）
        self.important_vars = {
            'PATH', 'PATHEXT', 'PYTHONPATH', 'CLASSPATH', 'JAVA_HOME',
            'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA'
        }
    
    def validate_variable_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """验证环境变量名"""
        if not name:
            return False, "变量名不能为空"
        
        # 去除首尾空格
        name = name.strip()
        
        # 检查长度
        if len(name) > 255:
            return False, "变量名长度不能超过255个字符"
        
        # 使用辅助函数验证基本格式
        if not is_valid_var_name(name):
            return False, "变量名只能包含字母、数字和下划线，且不能以数字开头"
        
        # 检查是否包含等号
        if '=' in name:
            return False, "变量名不能包含等号"
        
        # 检查是否包含其他非法字符
        illegal_chars = ['<', '>', '|', '&', '^', '"', '%']
        for char in illegal_chars:
            if char in name:
                return False, f"变量名不能包含字符: {char}"
        
        # 检查是否为保留的系统变量
        if name.upper() in self.reserved_system_vars:
            return False, f"'{name}' 是系统保留变量，不建议修改"
        
        return True, None
    
    def validate_variable_value(self, value: str, var_name: str = "") -> Tuple[bool, Optional[str]]:
        """验证环境变量值"""
        if value is None:
            return False, "变量值不能为None"
        
        # 空值是允许的
        if value == "":
            return True, None
        
        # 检查长度
        if len(value) > MAX_PATH_LENGTH:
            return False, f"变量值长度不能超过{MAX_PATH_LENGTH}个字符"
        
        # 如果是PATH类型变量，进行特殊验证
        if var_name.upper() in ['PATH', 'PYTHONPATH', 'CLASSPATH']:
            return self._validate_path_value(value)
        
        # 检查是否包含非法字符（对于非PATH变量）
        if '\x00' in value:
            return False, "变量值不能包含空字符"
        
        return True, None
    
    def validate_variable(self, var: EnvironmentVariable) -> Tuple[bool, Optional[str]]:
        """验证完整的环境变量"""
        # 验证变量名
        name_valid, name_error = self.validate_variable_name(var.name)
        if not name_valid:
            return False, name_error
        
        # 验证变量值
        value_valid, value_error = self.validate_variable_value(var.value, var.name)
        if not value_valid:
            return False, value_error
        
        # 使用模型自带的验证方法
        model_valid, model_error = var.validate()
        if not model_valid:
            return False, model_error
        
        return True, None
    
    def validate_path_variable_change(self, var: EnvironmentVariable) -> Tuple[bool, Optional[str], List[str]]:
        """验证PATH变量更改，返回验证结果、错误信息和警告列表"""
        warnings = []
        
        # 基本验证
        valid, error = self.validate_variable(var)
        if not valid:
            return False, error, warnings
        
        # PATH变量特殊检查
        if var.is_path_variable:
            paths = split_path_value(var.value)
            
            # 检查路径数量
            if len(paths) > 100:
                warnings.append(f"PATH变量包含{len(paths)}个路径，过多的路径可能影响系统性能")
            
            # 检查重复路径
            path_set = set()
            duplicates = []
            for path in paths:
                path_normalized = path.lower()
                if path_normalized in path_set:
                    duplicates.append(path)
                else:
                    path_set.add(path_normalized)
            
            if duplicates:
                warnings.append(f"发现重复路径: {', '.join(duplicates[:3])}" + 
                              (f" 等{len(duplicates)}个" if len(duplicates) > 3 else ""))
            
            # 检查无效路径
            invalid_paths = []
            for path in paths[:10]:  # 只检查前10个，避免太慢
                if not validate_path(path):
                    invalid_paths.append(path)
            
            if invalid_paths:
                warnings.append(f"发现无效路径: {', '.join([os.path.basename(p) for p in invalid_paths[:3]])}" +
                              (f" 等{len(invalid_paths)}个" if len(invalid_paths) > 3 else ""))
        
        return True, None, warnings
    
    def validate_system_variable_change(self, var: EnvironmentVariable, is_system: bool) -> Tuple[bool, Optional[str], List[str]]:
        """验证系统变量更改"""
        warnings = []
        
        # 基本验证
        valid, error = self.validate_variable(var)
        if not valid:
            return False, error, warnings
        
        # 系统变量特殊检查
        if is_system and var.name.upper() in self.reserved_system_vars:
            return False, f"不能修改系统保留变量 '{var.name}'", warnings
        
        # 重要变量警告
        if var.name.upper() in self.important_vars:
            warnings.append(f"'{var.name}' 是重要的系统变量，修改可能影响系统功能")
        
        return True, None, warnings
    
    def validate_batch_operation(self, variables: List[EnvironmentVariable]) -> Tuple[bool, List[str], List[str]]:
        """验证批量操作"""
        errors = []
        warnings = []
        
        if not variables:
            return False, ["没有要处理的变量"], warnings
        
        # 检查变量名重复
        names = {}
        for var in variables:
            key = (var.name.upper(), var.env_type)
            if key in names:
                errors.append(f"变量名重复: {var.name} ({var.env_type.value})")
            else:
                names[key] = var
        
        # 验证每个变量
        for var in variables:
            valid, error = self.validate_variable(var)
            if not valid:
                errors.append(f"变量 '{var.name}': {error}")
        
        # 检查批量操作的合理性
        if len(variables) > 50:
            warnings.append(f"批量操作包含{len(variables)}个变量，操作可能需要较长时间")
        
        return len(errors) == 0, errors, warnings
    
    def _validate_path_value(self, path_value: str) -> Tuple[bool, Optional[str]]:
        """验证PATH类型变量的值"""
        if not path_value:
            return True, None
        
        # 检查PATH分隔符
        if PATH_SEPARATOR not in path_value and len(path_value) > MAX_SINGLE_PATH_LENGTH:
            return False, f"单个路径长度不能超过{MAX_SINGLE_PATH_LENGTH}个字符"
        
        # 分割PATH值
        paths = split_path_value(path_value)
        
        # 检查每个路径
        for i, path in enumerate(paths):
            if len(path) > MAX_SINGLE_PATH_LENGTH:
                return False, f"第{i+1}个路径长度超过{MAX_SINGLE_PATH_LENGTH}个字符"
            
            # 检查路径格式
            if not path.strip():
                continue  # 跳过空路径
            
            # 检查非法字符
            illegal_chars = ['<', '>', '|', '*', '?', '"']
            for char in illegal_chars:
                if char in path:
                    return False, f"路径包含非法字符 '{char}': {path}"
        
        return True, None
    
    def suggest_variable_name_fix(self, name: str) -> str:
        """建议变量名修复"""
        if not name:
            return "NEW_VAR"
        
        # 移除非法字符
        fixed_name = re.sub(r'[^A-Za-z0-9_]', '_', name)
        
        # 确保不以数字开头
        if fixed_name and fixed_name[0].isdigit():
            fixed_name = 'VAR_' + fixed_name
        
        # 确保不为空
        if not fixed_name:
            fixed_name = 'NEW_VAR'
        
        return fixed_name.upper()
    
    def check_variable_conflicts(self, var: EnvironmentVariable, existing_vars: List[EnvironmentVariable]) -> List[str]:
        """检查变量冲突"""
        conflicts = []
        
        for existing in existing_vars:
            if (existing.name.upper() == var.name.upper() and 
                existing.env_type == var.env_type and 
                existing != var):
                conflicts.append(f"与现有变量冲突: {existing.name}")
        
        return conflicts 
