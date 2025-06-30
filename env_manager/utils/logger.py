"""
日志工具模块

提供应用程序的日志记录功能。
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

from .constants import LOG_DIR, APP_NAME
from .helpers import ensure_directory


def setup_logger(name: str = APP_NAME, 
                level: str = 'INFO',
                log_file: str = None,
                max_file_size: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志器名称
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: 日志文件路径，如果为None则使用默认路径
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的备份文件数量
    
    Returns:
        配置好的日志器
    """
    # 确保日志目录存在
    ensure_directory(LOG_DIR)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除现有的处理器，避免重复
    logger.handlers.clear()
    
    # 创建日志文件路径
    if log_file is None:
        log_file = os.path.join(LOG_DIR, f"{APP_NAME}.log")
    
    # 创建文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # 设置格式化器
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器到日志器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则使用应用程序名称
    
    Returns:
        日志器实例
    """
    if name is None:
        name = APP_NAME
    
    logger = logging.getLogger(name)
    
    # 如果日志器没有处理器，说明还未初始化，使用默认设置初始化
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


class OperationLogger:
    """操作日志记录器"""
    
    def __init__(self):
        self.logger = get_logger(f"{APP_NAME}.operation")
        self.audit_file = os.path.join(LOG_DIR, "audit.log")
        
        # 创建审计日志处理器
        audit_handler = logging.handlers.RotatingFileHandler(
            self.audit_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)
        
        # 创建专门的审计日志器
        self.audit_logger = logging.getLogger(f"{APP_NAME}.audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)
        
        # 防止传播到根日志器
        self.audit_logger.propagate = False
    
    def log_operation(self, operation: str, target: str, details: str = None, 
                     success: bool = True) -> None:
        """
        记录操作日志
        
        Args:
            operation: 操作类型 (CREATE, UPDATE, DELETE, IMPORT, EXPORT等)
            target: 操作目标 (环境变量名等)
            details: 操作详情
            success: 操作是否成功
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} - {target} - {status}"
        
        if details:
            message += f" - {details}"
        
        # 记录到主日志
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
        
        # 记录到审计日志
        self.audit_logger.info(message)
    
    def log_env_create(self, name: str, env_type: str, success: bool = True) -> None:
        """记录环境变量创建"""
        self.log_operation("CREATE_ENV", f"{env_type}:{name}", success=success)
    
    def log_env_update(self, name: str, env_type: str, success: bool = True) -> None:
        """记录环境变量更新"""
        self.log_operation("UPDATE_ENV", f"{env_type}:{name}", success=success)
    
    def log_env_delete(self, name: str, env_type: str, success: bool = True) -> None:
        """记录环境变量删除"""
        self.log_operation("DELETE_ENV", f"{env_type}:{name}", success=success)
    
    def log_backup_create(self, backup_path: str, success: bool = True) -> None:
        """记录备份创建"""
        self.log_operation("CREATE_BACKUP", backup_path, success=success)
    
    def log_backup_restore(self, backup_path: str, success: bool = True) -> None:
        """记录备份恢复"""
        self.log_operation("RESTORE_BACKUP", backup_path, success=success)
    
    def log_import(self, file_path: str, count: int, success: bool = True) -> None:
        """记录批量导入"""
        details = f"imported {count} variables" if success else None
        self.log_operation("IMPORT", file_path, details, success)
    
    def log_export(self, file_path: str, count: int, success: bool = True) -> None:
        """记录批量导出"""
        details = f"exported {count} variables" if success else None
        self.log_operation("EXPORT", file_path, details, success)


# 全局操作日志器实例
operation_logger = OperationLogger()


def log_exception(logger: logging.Logger, exception: Exception, 
                 context: str = None) -> None:
    """
    记录异常信息
    
    Args:
        logger: 日志器实例
        exception: 异常对象
        context: 异常上下文信息
    """
    import traceback
    
    error_msg = f"Exception occurred: {type(exception).__name__}: {str(exception)}"
    
    if context:
        error_msg = f"{context} - {error_msg}"
    
    # 记录异常信息和堆栈跟踪
    logger.error(error_msg)
    logger.debug(f"Stack trace:\n{traceback.format_exc()}")


def create_performance_logger() -> logging.Logger:
    """创建性能监控日志器"""
    perf_logger = logging.getLogger(f"{APP_NAME}.performance")
    perf_logger.setLevel(logging.DEBUG)
    
    # 创建性能日志文件处理器
    perf_file = os.path.join(LOG_DIR, "performance.log")
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    
    perf_formatter = logging.Formatter(
        '%(asctime)s - PERF - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False
    
    return perf_logger


def cleanup_old_logs(days: int = 30) -> None:
    """
    清理旧的日志文件
    
    Args:
        days: 保留天数，超过此天数的日志文件将被删除
    """
    try:
        import time
        
        if not os.path.exists(LOG_DIR):
            return
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        for filename in os.listdir(LOG_DIR):
            file_path = os.path.join(LOG_DIR, filename)
            
            if os.path.isfile(file_path):
                file_time = os.path.getmtime(file_path)
                if file_time < cutoff_time:
                    os.remove(file_path)
                    
    except Exception as e:
        logger = get_logger()
        logger.error(f"Failed to cleanup old logs: {e}") 
