"""
PATH编辑器对话框测试脚本

用于测试PATH编辑器对话框的功能。
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QMessageBox
from env_manager.ui.dialogs.path_editor_dialog import PathEditorDialog
from env_manager.models.env_model import EnvType


def test_path_editor_dialog():
    """测试PATH编辑器对话框"""
    print("启动PATH编辑器对话框测试...")
    
    app = QApplication(sys.argv)
    
    # 创建对话框（用户变量）
    dialog = PathEditorDialog(env_type=EnvType.USER)
    
    # 连接信号
    def on_path_updated(path_value):
        print(f"PATH值已更新: {len(path_value)} 字符")
        QMessageBox.information(None, "PATH更新", f"PATH值已更新，包含 {len(path_value)} 个字符")
    
    dialog.path_updated.connect(on_path_updated)
    
    # 显示对话框
    print("显示PATH编辑器对话框...")
    result = dialog.exec()
    
    if result == PathEditorDialog.DialogCode.Accepted:
        path_value = dialog.get_path_value()
        print(f"用户确认了更改，PATH值: {len(path_value)} 字符")
    else:
        print("用户取消了操作")
    
    print("测试完成")


if __name__ == "__main__":
    test_path_editor_dialog() 
