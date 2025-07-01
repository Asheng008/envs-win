"""
环境变量控制器

核心业务逻辑控制器，负责环境变量的管理。
"""

from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum

from ..models.env_model import EnvironmentVariable, EnvType
from .registry_ops import RegistryOps
from .validator import Validator
from .exceptions import (
    RegistryAccessError, PermissionError, ValidationError,
    EnvManagerException
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OperationType(Enum):
    """操作类型枚举"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"
    BATCH_DELETE = "batch_delete"


class OperationRecord:
    """操作记录"""
    def __init__(self, op_type: OperationType, variable: EnvironmentVariable, 
                 old_value: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.op_type = op_type
        self.variable = variable
        self.old_value = old_value
        self.timestamp = timestamp or datetime.now()
        self.success = False
        self.error_message: Optional[str] = None


class EnvController:
    """环境变量控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.registry_ops = RegistryOps()
        self.validator = Validator()
        
        # 操作历史记录
        self.operation_history: List[OperationRecord] = []
        self.max_history_size = 100
        
        # 变更通知回调函数列表
        self._change_callbacks: List[Callable[[str, EnvironmentVariable, Optional[str]], None]] = []
        
        # 缓存的环境变量
        self._system_vars_cache: Optional[List[EnvironmentVariable]] = None
        self._user_vars_cache: Optional[List[EnvironmentVariable]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_timeout = 60  # 缓存超时时间（秒）
    
    def get_all_variables(self) -> List[EnvironmentVariable]:
        """获取所有环境变量"""
        try:
            system_vars = self.get_system_variables()
            user_vars = self.get_user_variables()
            all_vars = system_vars + user_vars
            
            logger.debug(f"获取所有环境变量: 系统变量{len(system_vars)}个, 用户变量{len(user_vars)}个")
            return all_vars
            
        except Exception as e:
            logger.error(f"获取所有环境变量失败: {e}")
            raise EnvManagerException(f"获取环境变量失败: {e}")
    
    def get_system_variables(self) -> List[EnvironmentVariable]:
        """获取系统环境变量"""
        try:
            # 检查缓存
            if self._is_cache_valid() and self._system_vars_cache is not None:
                logger.debug("使用缓存的系统环境变量")
                return self._system_vars_cache.copy()
            
            # 从注册表获取
            system_vars_dict = self.registry_ops.get_system_env_vars()
            system_vars = []
            
            for name, value in system_vars_dict.items():
                var = EnvironmentVariable(
                    name=name,
                    value=value,
                    env_type=EnvType.SYSTEM
                )
                system_vars.append(var)
            
            # 更新缓存
            self._system_vars_cache = system_vars.copy()
            self._update_cache_timestamp()
            
            logger.info(f"获取系统环境变量成功: {len(system_vars)}个")
            return system_vars
            
        except Exception as e:
            logger.error(f"获取系统环境变量失败: {e}")
            raise
    
    def get_user_variables(self) -> List[EnvironmentVariable]:
        """获取用户环境变量"""
        try:
            # 检查缓存
            if self._is_cache_valid() and self._user_vars_cache is not None:
                logger.debug("使用缓存的用户环境变量")
                return self._user_vars_cache.copy()
            
            # 从注册表获取
            user_vars_dict = self.registry_ops.get_user_env_vars()
            user_vars = []
            
            for name, value in user_vars_dict.items():
                var = EnvironmentVariable(
                    name=name,
                    value=value,
                    env_type=EnvType.USER
                )
                user_vars.append(var)
            
            # 更新缓存
            self._user_vars_cache = user_vars.copy()
            self._update_cache_timestamp()
            
            logger.info(f"获取用户环境变量成功: {len(user_vars)}个")
            return user_vars
            
        except Exception as e:
            logger.error(f"获取用户环境变量失败: {e}")
            raise
    
    def create_variable(self, name: str, value: str, env_type: EnvType) -> bool:
        """创建环境变量"""
        try:
            # 创建环境变量对象
            var = EnvironmentVariable(
                name=name.strip(),
                value=value,
                env_type=env_type,
                is_new=True
            )
            
            # 验证变量
            valid, error = self.validate_variable(var)
            if not valid:
                raise ValidationError(error)
            
            # 检查是否已存在
            if self.variable_exists(name, env_type):
                raise ValidationError(f"环境变量 '{name}' 已存在")
            
            # 记录操作
            record = OperationRecord(OperationType.CREATE, var)
            
            try:
                # 执行创建操作
                is_system = (env_type == EnvType.SYSTEM)
                success = self.registry_ops.set_env_var(name, value, is_system)
                
                if success:
                    record.success = True
                    var.apply_changes()
                    
                    # 清除缓存
                    self._clear_cache()
                    
                    # 触发变更通知
                    self._notify_change("created", var, None)
                    
                    logger.info(f"成功创建{'系统' if is_system else '用户'}环境变量: {name}")
                    return True
                else:
                    record.error_message = "注册表操作失败"
                    return False
                    
            except Exception as e:
                record.error_message = str(e)
                raise
            finally:
                self._add_operation_record(record)
                
        except Exception as e:
            logger.error(f"创建环境变量失败: {e}")
            raise
    
    def update_variable(self, var: EnvironmentVariable) -> bool:
        """更新环境变量"""
        try:
            # 验证变量
            valid, error = self.validate_variable(var)
            if not valid:
                raise ValidationError(error)
            
            # 获取原始值
            old_value = self.get_variable_value(var.name, var.env_type)
            if old_value is None:
                raise ValidationError(f"环境变量 '{var.name}' 不存在")
            
            # 记录操作
            record = OperationRecord(OperationType.UPDATE, var, old_value)
            
            try:
                # 执行更新操作
                is_system = (var.env_type == EnvType.SYSTEM)
                success = self.registry_ops.set_env_var(var.name, var.value, is_system)
                
                if success:
                    record.success = True
                    var.apply_changes()
                    
                    # 清除缓存
                    self._clear_cache()
                    
                    # 触发变更通知
                    self._notify_change("updated", var, old_value)
                    
                    logger.info(f"成功更新{'系统' if is_system else '用户'}环境变量: {var.name}")
                    return True
                else:
                    record.error_message = "注册表操作失败"
                    return False
                    
            except Exception as e:
                record.error_message = str(e)
                raise
            finally:
                self._add_operation_record(record)
                
        except Exception as e:
            logger.error(f"更新环境变量失败: {e}")
            raise
    
    def delete_variable(self, var: EnvironmentVariable) -> bool:
        """删除环境变量"""
        try:
            # 验证是否可以删除
            if var.name.upper() in self.validator.reserved_system_vars:
                raise ValidationError(f"不能删除系统保留变量 '{var.name}'")
            
            # 获取当前值（用于历史记录）
            current_value = self.get_variable_value(var.name, var.env_type)
            
            # 记录操作
            record = OperationRecord(OperationType.DELETE, var, current_value)
            
            try:
                # 执行删除操作
                is_system = (var.env_type == EnvType.SYSTEM)
                success = self.registry_ops.delete_env_var(var.name, is_system)
                
                if success:
                    record.success = True
                    var.is_deleted = True
                    
                    # 清除缓存
                    self._clear_cache()
                    
                    # 触发变更通知
                    self._notify_change("deleted", var, current_value)
                    
                    logger.info(f"成功删除{'系统' if is_system else '用户'}环境变量: {var.name}")
                    return True
                else:
                    record.error_message = "注册表操作失败"
                    return False
                    
            except Exception as e:
                record.error_message = str(e)
                raise
            finally:
                self._add_operation_record(record)
                
        except Exception as e:
            logger.error(f"删除环境变量失败: {e}")
            raise
    
    def validate_variable(self, var: EnvironmentVariable) -> Tuple[bool, Optional[str]]:
        """验证环境变量"""
        try:
            return self.validator.validate_variable(var)
        except Exception as e:
            logger.error(f"验证环境变量失败: {e}")
            return False, f"验证失败: {e}"
    
    def validate_variable_change(self, var: EnvironmentVariable, is_system: bool = None) -> Tuple[bool, Optional[str], List[str]]:
        """验证环境变量更改（包含警告信息）"""
        try:
            if is_system is None:
                is_system = (var.env_type == EnvType.SYSTEM)
            
            # PATH变量特殊验证
            if var.is_path_variable:
                return self.validator.validate_path_variable_change(var)
            
            # 系统变量验证
            return self.validator.validate_system_variable_change(var, is_system)
            
        except Exception as e:
            logger.error(f"验证环境变量更改失败: {e}")
            return False, f"验证失败: {e}", []
    
    def variable_exists(self, name: str, env_type: EnvType) -> bool:
        """检查环境变量是否存在"""
        try:
            is_system = (env_type == EnvType.SYSTEM)
            return self.registry_ops.env_var_exists(name, is_system)
        except Exception as e:
            logger.error(f"检查环境变量存在性失败: {e}")
            return False
    
    def get_variable_value(self, name: str, env_type: EnvType) -> Optional[str]:
        """获取环境变量的值"""
        try:
            is_system = (env_type == EnvType.SYSTEM)
            return self.registry_ops.get_env_var_value(name, is_system)
        except Exception as e:
            logger.error(f"获取环境变量值失败: {e}")
            return None
    
    def search_variables(self, query: str, search_in_name: bool = True, 
                        search_in_value: bool = True, case_sensitive: bool = False) -> List[EnvironmentVariable]:
        """搜索环境变量"""
        try:
            all_vars = self.get_all_variables()
            results = []
            
            if not query:
                return all_vars
            
            search_query = query if case_sensitive else query.lower()
            
            for var in all_vars:
                match = False
                
                if search_in_name:
                    name_to_search = var.name if case_sensitive else var.name.lower()
                    if search_query in name_to_search:
                        match = True
                
                if not match and search_in_value:
                    value_to_search = var.value if case_sensitive else var.value.lower()
                    if search_query in value_to_search:
                        match = True
                
                if match:
                    results.append(var)
            
            logger.debug(f"搜索环境变量 '{query}': 找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"搜索环境变量失败: {e}")
            return []
    
    def refresh_cache(self) -> None:
        """刷新缓存"""
        self._clear_cache()
        logger.debug("环境变量缓存已刷新")
    
    def add_change_callback(self, callback: Callable[[str, EnvironmentVariable, Optional[str]], None]) -> None:
        """添加变更通知回调函数"""
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, EnvironmentVariable, Optional[str]], None]) -> None:
        """移除变更通知回调函数"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def get_operation_history(self, limit: int = 50) -> List[OperationRecord]:
        """获取操作历史记录"""
        return self.operation_history[-limit:] if limit > 0 else self.operation_history.copy()
    
    def clear_operation_history(self) -> None:
        """清除操作历史记录"""
        self.operation_history.clear()
        logger.debug("操作历史记录已清除")
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_timestamp is None:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_timeout
    
    def _update_cache_timestamp(self) -> None:
        """更新缓存时间戳"""
        self._cache_timestamp = datetime.now()
    
    def _clear_cache(self) -> None:
        """清除缓存"""
        self._system_vars_cache = None
        self._user_vars_cache = None
        self._cache_timestamp = None
    
    def _notify_change(self, action: str, variable: EnvironmentVariable, old_value: Optional[str]) -> None:
        """通知变更"""
        for callback in self._change_callbacks:
            try:
                callback(action, variable, old_value)
            except Exception as e:
                logger.error(f"变更通知回调执行失败: {e}")
    
    def _add_operation_record(self, record: OperationRecord) -> None:
        """添加操作记录"""
        self.operation_history.append(record)
        
        # 限制历史记录大小
        if len(self.operation_history) > self.max_history_size:
            self.operation_history.pop(0)
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        try:
            all_vars = self.get_all_variables()
            system_vars = [v for v in all_vars if v.env_type == EnvType.SYSTEM]
            user_vars = [v for v in all_vars if v.env_type == EnvType.USER]
            path_vars = [v for v in all_vars if v.is_path_variable]
            
            return {
                'total_variables': len(all_vars),
                'system_variables': len(system_vars),
                'user_variables': len(user_vars),
                'path_variables': len(path_vars),
                'operation_records': len(self.operation_history)
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {} 
