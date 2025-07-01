"""
测试环境变量编辑对话框

用于测试EditDialog的功能。
"""

import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from PySide6.QtCore import Qt

from env_manager.models.env_model import EnvironmentVariable, EnvType
from env_manager.ui.dialogs.edit_dialog import EditDialog


class TestWindow(QWidget):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试环境变量编辑对话框")
        self.setMinimumSize(400, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加标题
        layout.addWidget(QPushButton("环境变量编辑对话框测试"))
        
        # 创建测试按钮
        button_layout = QHBoxLayout()
        
        # 新建变量按钮
        self.new_btn = QPushButton("新建变量")
        self.new_btn.clicked.connect(self.test_new_variable)
        button_layout.addWidget(self.new_btn)
        
        # 编辑用户变量按钮
        self.edit_user_btn = QPushButton("编辑用户变量")
        self.edit_user_btn.clicked.connect(self.test_edit_user_variable)
        button_layout.addWidget(self.edit_user_btn)
        
        # 编辑PATH变量按钮
        self.edit_path_btn = QPushButton("编辑PATH变量")
        self.edit_path_btn.clicked.connect(self.test_edit_path_variable)
        button_layout.addWidget(self.edit_path_btn)
        
        layout.addLayout(button_layout)
        
        # 结果显示
        self.result_btn = QPushButton("最后编辑结果会显示在这里")
        self.result_btn.setEnabled(False)
        layout.addWidget(self.result_btn)
    
    def test_new_variable(self):
        """测试新建变量"""
        dialog = EditDialog(self)
        dialog.variable_saved.connect(self.on_variable_saved)
        dialog.exec()
    
    def test_edit_user_variable(self):
        """测试编辑用户变量"""
        # 创建一个示例用户变量
        sample_var = EnvironmentVariable(
            name="TEST_USER_VAR",
            value="这是一个测试用户变量",
            env_type=EnvType.USER
        )
        
        dialog = EditDialog(self, sample_var)
        dialog.variable_saved.connect(self.on_variable_saved)
        dialog.exec()
    
    def test_edit_path_variable(self):
        """测试编辑PATH变量"""
        # 创建一个示例PATH变量
        sample_paths = [
            "C:\\Windows\\System32",
            "C:\\Windows",
            "C:\\Program Files\\Git\\bin",
            "C:\\Python39",
            "C:\\Python39\\Scripts"
        ]
        path_value = ";".join(sample_paths)
        
        sample_var = EnvironmentVariable(
            name="PATH",
            value=path_value,
            env_type=EnvType.SYSTEM
        )
        
        dialog = EditDialog(self, sample_var)
        dialog.variable_saved.connect(self.on_variable_saved)
        dialog.exec()
    
    def on_variable_saved(self, variable: EnvironmentVariable):
        """处理变量保存"""
        result_text = f"保存成功: {variable.name} = {variable.value[:50]}..."
        if len(variable.value) > 50:
            result_text += f" (共{len(variable.value)}字符)"
        
        self.result_btn.setText(result_text)
        print(f"变量保存成功:")
        print(f"  名称: {variable.name}")
        print(f"  类型: {'系统变量' if variable.env_type == EnvType.SYSTEM else '用户变量'}")
        print(f"  值: {variable.value}")
        print(f"  是否新建: {variable.is_new}")
        print(f"  是否修改: {variable.is_modified}")
        print("-" * 50)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = TestWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
