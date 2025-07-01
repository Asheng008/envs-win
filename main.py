
"""
Windows环境变量管理工具 - 主入口文件

这是应用程序的启动点，负责初始化应用程序并启动主界面。
"""

import sys
import os
import argparse
from pathlib import Path

# 确保能够导入项目模块
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt, QSettings
    from PySide6.QtGui import QIcon
except ImportError as e:
    print(f"错误: 无法导入PySide6库: {e}")
    print("请运行以下命令安装依赖:")
    print("pip install -r requirements.txt")
    sys.exit(1)

from env_manager.utils.logger import setup_logger, get_logger
from env_manager.utils.config import ConfigManager
from env_manager.utils.constants import APP_NAME, APP_VERSION, CONFIG_DIR
from env_manager.utils.helpers import ensure_directory


class SingletonApplication:
    """单例应用程序类，确保只有一个实例运行"""
    
    def __init__(self):
        self.settings = QSettings("EnvManager", "SingleInstance")
        self.is_running = False
    
    def check_running(self) -> bool:
        """检查应用程序是否已经在运行"""
        # 简单的单例检查机制
        lock_file = os.path.join(CONFIG_DIR, "app.lock")
        
        try:
            if os.path.exists(lock_file):
                # 检查进程是否真的在运行
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # 在Windows上检查进程是否存在
                import psutil
                if psutil.pid_exists(pid):
                    return True
                else:
                    # 进程不存在，删除锁文件
                    os.remove(lock_file)
            
            # 创建新的锁文件
            ensure_directory(CONFIG_DIR)
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            self.is_running = False
            return False
            
        except (IOError, ValueError, ImportError):
            # 如果检查失败，假设没有运行
            self.is_running = False
            return False
    
    def cleanup(self):
        """清理资源"""
        if not self.is_running:
            lock_file = os.path.join(CONFIG_DIR, "app.lock")
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except OSError:
                pass


def check_admin_privileges() -> bool:
    """检查是否具有管理员权限"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def show_privilege_warning():
    """显示权限警告"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle("权限提醒")
    msg_box.setText("检测到您没有管理员权限")
    msg_box.setInformativeText(
        "没有管理员权限将无法修改系统环境变量，只能修改用户环境变量。\n\n"
        "建议以管理员身份运行本程序以获得完整功能。"
    )
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
    
    result = msg_box.exec()
    return result == QMessageBox.StandardButton.Ok


def setup_application() -> QApplication:
    """设置应用程序"""
    # 设置应用程序属性
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(APP_VERSION)
    QApplication.setOrganizationName("Asheng008")
    QApplication.setOrganizationDomain("github.com/Asheng008")
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    try:
        icon_path = Path(__file__).parent / "env_manager" / "resources" / "icons" / "app.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
    except Exception:
        pass  # 如果图标不存在，忽略错误
    
    # 设置样式
    app.setStyle("Fusion")  # 使用Fusion样式获得更好的跨平台外观
    
    return app


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - Windows环境变量管理工具",
        epilog="更多信息请访问: https://github.com/Asheng008/envs-win"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}"
    )
    
    parser.add_argument(
        "--no-admin-check",
        action="store_true",
        help="跳过管理员权限检查"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--config-dir",
        type=str,
        help="指定配置目录路径"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果指定了配置目录，更新常量
    if args.config_dir:
        import env_manager.utils.constants as constants
        constants.CONFIG_DIR = args.config_dir
        constants.BACKUP_DIR = os.path.join(args.config_dir, "backups")
        constants.LOG_DIR = os.path.join(args.config_dir, "logs")
        constants.CONFIG_FILE = os.path.join(args.config_dir, "config.ini")
    
    # 确保必要目录存在
    ensure_directory(CONFIG_DIR)
    
    # 设置日志
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logger(level=log_level)
    logger.info(f"启动 {APP_NAME} v{APP_VERSION}")
    
    try:
        # 检查单例
        singleton = SingletonApplication()
        if singleton.check_running():
            logger.warning("应用程序已经在运行")
            QMessageBox.information(
                None, 
                "提示", 
                f"{APP_NAME} 已经在运行中！\n请检查系统托盘或任务栏。"
            )
            return 1
        
        # 检查管理员权限（如果需要）
        if not args.no_admin_check:
            has_admin = check_admin_privileges()
            if not has_admin:
                logger.warning("没有管理员权限")
                if not show_privilege_warning():
                    logger.info("用户取消启动")
                    return 0
        
        # 设置应用程序
        app = setup_application()
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        logger.info("配置管理器初始化完成")
        
        # 导入并创建主窗口
        try:
            from env_manager.ui.main_window import MainWindow
            
            # 创建主窗口
            main_window = MainWindow()
            logger.info("主窗口创建完成")
            
            # 应用窗口配置
            window_config = config_manager.get_window_config()
            
            # 确保转换为整数类型
            width = int(window_config['width'])
            height = int(window_config['height'])
            main_window.resize(width, height)
            
            if window_config['maximized']:
                main_window.showMaximized()
            else:
                main_window.show()
                
                # 设置窗口位置
                if window_config['position']:
                    pos = window_config['position']
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        x, y = int(pos[0]), int(pos[1])
                        main_window.move(x, y)
            
            logger.info("应用程序界面初始化完成")
            
            # 设置应用程序退出时的清理函数
            def cleanup():
                singleton.cleanup()
                logger.info("应用程序退出")
            
            app.aboutToQuit.connect(cleanup)
            
            # 启动事件循环
            logger.info("启动应用程序事件循环")
            exit_code = app.exec()
            
            return exit_code
            
        except ImportError as e:
            logger.error(f"无法导入主窗口模块: {e}")
            QMessageBox.critical(
                None,
                "导入错误",
                f"无法导入主窗口模块:\n{e}\n\n请检查项目结构是否完整。"
            )
            return 1
    
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}", exc_info=True)
        
        # 显示错误对话框
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "启动失败",
                f"应用程序启动失败:\n{e}\n\n请查看日志文件了解详细信息。"
            )
        except Exception:
            print(f"应用程序启动失败: {e}")
        
        return 1


if __name__ == "__main__":
    # 设置异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = get_logger()
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
    
    # 运行主程序
    exit_code = main()
    sys.exit(exit_code) 
