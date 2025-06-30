"""
自定义异常模块

定义了环境变量管理工具中使用的各种异常类。
"""


class EnvManagerException(Exception):
    """环境变量管理工具基础异常类"""
    pass


class RegistryAccessError(EnvManagerException):
    """注册表访问异常"""
    def __init__(self, message="注册表访问失败"):
        self.message = message
        super().__init__(self.message)


class PermissionError(EnvManagerException):
    """权限不足异常"""
    def __init__(self, message="权限不足，请以管理员身份运行"):
        self.message = message
        super().__init__(self.message)


class ValidationError(EnvManagerException):
    """数据验证异常"""
    def __init__(self, message="数据验证失败"):
        self.message = message
        super().__init__(self.message)


class BackupError(EnvManagerException):
    """备份操作异常"""
    def __init__(self, message="备份操作失败"):
        self.message = message
        super().__init__(self.message)


class PathLengthError(EnvManagerException):
    """PATH长度超限异常"""
    def __init__(self, message="PATH变量长度超过系统限制"):
        self.message = message
        super().__init__(self.message)


class InvalidPathError(EnvManagerException):
    """无效路径异常"""
    def __init__(self, path, message=None):
        self.path = path
        self.message = message or f"无效的路径: {path}"
        super().__init__(self.message) 
