"""
常量定义模块

定义了应用程序中使用的各种常量。
"""

import os

# 应用程序信息
APP_NAME = "EnvManager"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Asheng008"
APP_DESCRIPTION = "Windows环境变量管理工具"

# 注册表路径常量
REGISTRY_PATHS = {
    'SYSTEM_ENV': r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'USER_ENV': r'Environment'
}

# 注册表根键
REGISTRY_ROOTS = {
    'HKEY_LOCAL_MACHINE': 'HKLM',
    'HKEY_CURRENT_USER': 'HKCU'
}

# 文件和目录常量
CONFIG_DIR = os.path.expanduser("~/.envmanager")
BACKUP_DIR = os.path.join(CONFIG_DIR, "backups")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")

# 支持的文件格式
SUPPORTED_FORMATS = {
    'YAML': ['.yml', '.yaml'],
    'JSON': ['.json'],
    'CSV': ['.csv'],
    'REG': ['.reg']
}

# 默认备份保留数量
DEFAULT_BACKUP_COUNT = 10

# PATH变量相关常量
PATH_SEPARATOR = ';'
MAX_PATH_LENGTH = 32767  # Windows PATH变量最大长度
MAX_SINGLE_PATH_LENGTH = 260  # 单个路径最大长度

# UI相关常量
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 700

# 表格列索引
TABLE_COLUMNS = {
    'NAME': 0,
    'VALUE': 1,
    'ACTIONS': 2
}

# 搜索类型
SEARCH_TYPES = {
    'NAME': '变量名',
    'VALUE': '变量值',
    'BOTH': '全部'
}

# 消息类型
MESSAGE_TYPES = {
    'INFO': 'information',
    'WARNING': 'warning',
    'ERROR': 'critical',
    'QUESTION': 'question'
}

# 操作类型
OPERATION_TYPES = {
    'CREATE': 'create',
    'UPDATE': 'update',
    'DELETE': 'delete',
    'IMPORT': 'import',
    'EXPORT': 'export'
}

# 环境变量类型
ENV_TYPES = {
    'SYSTEM': 'system',
    'USER': 'user'
}

# 主题常量
THEMES = {
    'LIGHT': 'light',
    'DARK': 'dark'
}

# 语言常量
LANGUAGES = {
    'ZH_CN': 'zh_CN',
    'EN_US': 'en_US'
}

# 快捷键常量
SHORTCUTS = {
    'NEW': 'Ctrl+N',
    'EDIT': 'Ctrl+E',
    'DELETE': 'Delete',
    'SAVE': 'Ctrl+S',
    'IMPORT': 'Ctrl+I',
    'EXPORT': 'Ctrl+Shift+E',
    'FIND': 'Ctrl+F',
    'REFRESH': 'F5',
    'QUIT': 'Ctrl+Q'
} 
