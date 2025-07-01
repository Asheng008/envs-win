"""
注册表操作模块

提供Windows注册表的安全访问接口。
"""

import winreg
import ctypes
import subprocess
from typing import Dict, Optional, Tuple
from .exceptions import RegistryAccessError, PermissionError as PermError
from ..utils.constants import REGISTRY_PATHS
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RegistryOps:
    """注册表操作类"""
    
    def __init__(self):
        """初始化注册表操作"""
        self._system_key_path = REGISTRY_PATHS['SYSTEM_ENV']
        self._user_key_path = REGISTRY_PATHS['USER_ENV']
    
    def get_system_env_vars(self) -> Dict[str, str]:
        """获取系统环境变量"""
        try:
            return self._read_registry_key(winreg.HKEY_LOCAL_MACHINE, self._system_key_path)
        except Exception as e:
            logger.error(f"获取系统环境变量失败: {e}")
            raise RegistryAccessError(f"无法读取系统环境变量: {e}")
    
    def get_user_env_vars(self) -> Dict[str, str]:
        """获取用户环境变量"""
        try:
            return self._read_registry_key(winreg.HKEY_CURRENT_USER, self._user_key_path)
        except Exception as e:
            logger.error(f"获取用户环境变量失败: {e}")
            raise RegistryAccessError(f"无法读取用户环境变量: {e}")
    
    def set_env_var(self, name: str, value: str, system: bool = False) -> bool:
        """设置环境变量"""
        try:
            if system:
                # 检查管理员权限
                if not self._is_admin():
                    raise PermError("修改系统环境变量需要管理员权限")
                
                root_key = winreg.HKEY_LOCAL_MACHINE
                key_path = self._system_key_path
            else:
                root_key = winreg.HKEY_CURRENT_USER
                key_path = self._user_key_path
            
            # 打开注册表键
            with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_SET_VALUE) as key:
                # 设置值
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            
            # 广播环境变量更改消息
            self._broadcast_env_change()
            
            logger.info(f"成功设置{'系统' if system else '用户'}环境变量: {name}")
            return True
            
        except PermissionError:
            raise PermError(f"权限不足，无法设置{'系统' if system else '用户'}环境变量")
        except Exception as e:
            logger.error(f"设置环境变量失败: {e}")
            raise RegistryAccessError(f"设置环境变量失败: {e}")
    
    def delete_env_var(self, name: str, system: bool = False) -> bool:
        """删除环境变量"""
        try:
            if system:
                # 检查管理员权限
                if not self._is_admin():
                    raise PermError("删除系统环境变量需要管理员权限")
                
                root_key = winreg.HKEY_LOCAL_MACHINE
                key_path = self._system_key_path
            else:
                root_key = winreg.HKEY_CURRENT_USER
                key_path = self._user_key_path
            
            # 打开注册表键
            with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_SET_VALUE) as key:
                # 删除值
                winreg.DeleteValue(key, name)
            
            # 广播环境变量更改消息
            self._broadcast_env_change()
            
            logger.info(f"成功删除{'系统' if system else '用户'}环境变量: {name}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"环境变量不存在: {name}")
            return True  # 变量不存在视为删除成功
        except PermissionError:
            raise PermError(f"权限不足，无法删除{'系统' if system else '用户'}环境变量")
        except Exception as e:
            logger.error(f"删除环境变量失败: {e}")
            raise RegistryAccessError(f"删除环境变量失败: {e}")
    
    def env_var_exists(self, name: str, system: bool = False) -> bool:
        """检查环境变量是否存在"""
        try:
            env_vars = self.get_system_env_vars() if system else self.get_user_env_vars()
            return name in env_vars
        except Exception:
            return False
    
    def get_env_var_value(self, name: str, system: bool = False) -> Optional[str]:
        """获取单个环境变量的值"""
        try:
            env_vars = self.get_system_env_vars() if system else self.get_user_env_vars()
            return env_vars.get(name)
        except Exception:
            return None
    
    def _read_registry_key(self, root_key: int, key_path: str) -> Dict[str, str]:
        """读取注册表键的所有值"""
        env_vars = {}
        
        try:
            with winreg.OpenKey(root_key, key_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        env_vars[name] = value
                        i += 1
                    except WindowsError:
                        # 没有更多值了
                        break
        except Exception as e:
            raise RegistryAccessError(f"无法读取注册表键 {key_path}: {e}")
        
        return env_vars
    
    def _is_admin(self) -> bool:
        """检查是否具有管理员权限"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _broadcast_env_change(self) -> None:
        """广播环境变量更改消息，通知系统更新"""
        try:
            # 使用SendMessageTimeout广播WM_SETTINGCHANGE消息
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            
            result = ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,  # 5秒超时
                ctypes.byref(ctypes.c_ulong())
            )
            
            if result:
                logger.debug("成功广播环境变量更改消息")
            else:
                logger.warning("广播环境变量更改消息可能失败")
                
        except Exception as e:
            logger.warning(f"广播环境变量更改消息失败: {e}")
    
    def backup_registry_key(self, key_path: str, backup_file: str, system: bool = False) -> bool:
        """备份注册表键到文件"""
        try:
            root = "HKLM" if system else "HKCU"
            full_path = f"{root}\\{key_path}"
            
            # 使用reg export命令导出注册表
            cmd = f'reg export "{full_path}" "{backup_file}" /y'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"成功备份注册表键到: {backup_file}")
                return True
            else:
                logger.error(f"备份注册表键失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"备份注册表键失败: {e}")
            return False
    
    def restore_registry_key(self, backup_file: str) -> bool:
        """从备份文件恢复注册表键"""
        try:
            # 使用reg import命令导入注册表
            cmd = f'reg import "{backup_file}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"成功从备份文件恢复注册表键: {backup_file}")
                self._broadcast_env_change()
                return True
            else:
                logger.error(f"恢复注册表键失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"恢复注册表键失败: {e}")
            return False 
