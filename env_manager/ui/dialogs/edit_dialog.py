"""
环境变量编辑对话框

提供新建和编辑环境变量的界面。
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QGroupBox,
    QCheckBox, QSplitter, QScrollArea, QFrame, QMessageBox,
    QApplication, QWidget, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter, QTextDocument

from ...models.env_model import EnvironmentVariable, EnvType
from ...core.validator import Validator
from ...utils.helpers import is_valid_var_name, split_path_value, join_path_value, validate_path
from ...utils.constants import MAX_PATH_LENGTH, MAX_SINGLE_PATH_LENGTH, PATH_SEPARATOR


class PathHighlighter(QSyntaxHighlighter):
    """PATH变量语法高亮器"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        
        # 定义颜色格式
        self.valid_format = QTextCharFormat()
        self.valid_format.setForeground(Qt.GlobalColor.darkGreen)
        
        self.invalid_format = QTextCharFormat()
        self.invalid_format.setForeground(Qt.GlobalColor.red)
        
        self.separator_format = QTextCharFormat()
        self.separator_format.setForeground(Qt.GlobalColor.blue)
        self.separator_format.setBackground(Qt.GlobalColor.lightGray)
    
    def highlightBlock(self, text: str):
        """高亮PATH变量"""
        if not text:
            return
        
        paths = text.split(PATH_SEPARATOR)
        position = 0
        
        for i, path in enumerate(paths):
            if i > 0:  # 不是第一个路径，需要处理前面的分隔符
                separator_start = position - 1
                self.setFormat(separator_start, 1, self.separator_format)
            
            if path.strip():
                # 验证路径有效性
                if validate_path(path.strip()):
                    self.setFormat(position, len(path), self.valid_format)
                else:
                    self.setFormat(position, len(path), self.invalid_format)
            
            position += len(path) + 1  # +1 for separator


class EditDialog(QDialog):
    """环境变量编辑对话框"""
    
    # 信号定义
    variable_saved = Signal(EnvironmentVariable)  # 变量保存成功信号
    
    def __init__(self, parent=None, variable: Optional[EnvironmentVariable] = None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            variable: 要编辑的环境变量，None表示新建模式
        """
        super().__init__(parent)
        
        # 初始化属性
        self.original_variable = variable
        self.is_edit_mode = variable is not None
        self.validator = Validator()
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_input)
        
        # 设置对话框属性
        self.setWindowTitle("编辑环境变量" if self.is_edit_mode else "新建环境变量")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        self.setModal(True)
        
        # 初始化UI
        self._init_ui()
        self._setup_connections()
        self._load_data()
        
        # 在所有UI创建完成后设置初始状态
        self._setup_initial_state()
        
        # 初始验证
        self._validate_input()
    
    def _init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 基本信息标签页
        basic_tab = self._create_basic_tab()
        self.tab_widget.addTab(basic_tab, "基本信息")
        
        # 高级设置标签页
        advanced_tab = self._create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, "高级设置")
        
        # 预览标签页
        preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(preview_tab, "预览")
        
        # 验证状态显示
        self.validation_frame = self._create_validation_frame()
        main_layout.addWidget(self.validation_frame)
        
        # 按钮区域
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
    
    def _create_basic_tab(self) -> QWidget:
        """创建基本信息标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)
        
        # 变量名输入
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入环境变量名称...")
        if self.is_edit_mode and self.original_variable:
            self.name_edit.setText(self.original_variable.name)
            self.name_edit.setEnabled(False)  # 编辑模式下不允许修改变量名
        
        basic_layout.addRow("变量名*:", self.name_edit)
        
        # 变量类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItem("用户变量", EnvType.USER)
        self.type_combo.addItem("系统变量", EnvType.SYSTEM)
        
        if self.is_edit_mode and self.original_variable:
            index = 0 if self.original_variable.env_type == EnvType.USER else 1
            self.type_combo.setCurrentIndex(index)
            self.type_combo.setEnabled(False)  # 编辑模式下不允许修改类型
        
        basic_layout.addRow("变量类型*:", self.type_combo)
        
        layout.addWidget(basic_group)
        
        # 变量值组
        value_group = QGroupBox("变量值")
        value_layout = QVBoxLayout(value_group)
        
        # 检测PATH类型变量的复选框
        self.is_path_check = QCheckBox("这是一个PATH类型的变量")
        self.is_path_check.setToolTip("PATH类型变量会自动进行路径验证和格式化")
        value_layout.addWidget(self.is_path_check)
        
        # 简单值输入（单行）
        self.simple_value_edit = QLineEdit()
        self.simple_value_edit.setPlaceholderText("输入环境变量值...")
        
        # 多行值输入（文本区域）
        self.multi_value_edit = QTextEdit()
        self.multi_value_edit.setPlaceholderText("输入环境变量值...\n可以输入多行文本")
        self.multi_value_edit.setMaximumHeight(150)
        
        # PATH值编辑器
        self.path_value_edit = QTextEdit()
        self.path_value_edit.setPlaceholderText(f"输入PATH变量值，用 {PATH_SEPARATOR} 分隔多个路径...")
        self.path_value_edit.setMaximumHeight(150)
        
        # 为PATH编辑器添加语法高亮
        self.path_highlighter = PathHighlighter(self.path_value_edit.document())
        
        value_layout.addWidget(QLabel("简单值:"))
        value_layout.addWidget(self.simple_value_edit)
        value_layout.addWidget(QLabel("多行值:"))
        value_layout.addWidget(self.multi_value_edit)
        value_layout.addWidget(QLabel("PATH值:"))
        value_layout.addWidget(self.path_value_edit)
        
        layout.addWidget(value_group)
        
        # 注意：不在这里调用_switch_value_editor，因为path_tools_group还没创建
        # 默认显示简单值输入
        self.simple_value_edit.show()
        self.multi_value_edit.hide()
        self.path_value_edit.hide()
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # PATH工具组（仅在PATH变量时显示）
        self.path_tools_group = QGroupBox("PATH工具")
        path_tools_layout = QVBoxLayout(self.path_tools_group)
        
        # PATH路径列表显示
        self.path_list_edit = QTextEdit()
        self.path_list_edit.setReadOnly(True)
        self.path_list_edit.setMaximumHeight(200)
        path_tools_layout.addWidget(QLabel("路径列表:"))
        path_tools_layout.addWidget(self.path_list_edit)
        
        # PATH工具按钮
        path_button_layout = QHBoxLayout()
        
        self.format_path_btn = QPushButton("格式化")
        self.format_path_btn.setToolTip("格式化PATH变量，每行一个路径")
        
        self.remove_duplicates_btn = QPushButton("去重")
        self.remove_duplicates_btn.setToolTip("移除重复的路径")
        
        self.validate_paths_btn = QPushButton("验证路径")
        self.validate_paths_btn.setToolTip("验证所有路径的有效性")
        
        path_button_layout.addWidget(self.format_path_btn)
        path_button_layout.addWidget(self.remove_duplicates_btn)
        path_button_layout.addWidget(self.validate_paths_btn)
        path_button_layout.addStretch()
        
        path_tools_layout.addLayout(path_button_layout)
        
        layout.addWidget(self.path_tools_group)
        
        # 验证设置组
        validation_group = QGroupBox("验证设置")
        validation_layout = QFormLayout(validation_group)
        
        self.strict_validation_check = QCheckBox("严格验证")
        self.strict_validation_check.setToolTip("启用更严格的变量值验证")
        self.strict_validation_check.setChecked(True)
        
        self.auto_format_check = QCheckBox("自动格式化")
        self.auto_format_check.setToolTip("自动格式化变量值")
        self.auto_format_check.setChecked(True)
        
        validation_layout.addRow("验证选项:", self.strict_validation_check)
        validation_layout.addRow("", self.auto_format_check)
        
        layout.addWidget(validation_group)
        layout.addStretch()
        
        return widget
    
    def _create_preview_tab(self) -> QWidget:
        """创建预览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 预览组
        preview_group = QGroupBox("变量预览")
        preview_layout = QVBoxLayout(preview_group)
        
        # 预览文本
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        
        preview_layout.addWidget(self.preview_text)
        layout.addWidget(preview_group)
        
        # 统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QFormLayout(stats_group)
        
        self.name_length_label = QLabel("0")
        self.value_length_label = QLabel("0")
        self.path_count_label = QLabel("0")
        
        stats_layout.addRow("变量名长度:", self.name_length_label)
        stats_layout.addRow("变量值长度:", self.value_length_label)
        stats_layout.addRow("PATH路径数量:", self.path_count_label)
        
        layout.addWidget(stats_group)
        
        return widget
    
    def _create_validation_frame(self) -> QFrame:
        """创建验证状态显示框架"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(5)
        
        # 验证状态标签
        self.validation_status_label = QLabel("✓ 输入有效")
        self.validation_status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.validation_status_label)
        
        # 警告信息
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: orange;")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        # 错误信息
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        return frame
    
    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮布局"""
        layout = QHBoxLayout()
        
        # 左侧按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setToolTip("重置所有输入到初始状态")
        layout.addWidget(self.reset_btn)
        
        layout.addStretch()
        
        # 右侧按钮
        self.cancel_btn = QPushButton("取消")
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        
        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.ok_btn)
        
        return layout
    
    def _setup_connections(self):
        """设置信号连接"""
        # 输入变化监听
        self.name_edit.textChanged.connect(self._on_input_changed)
        self.simple_value_edit.textChanged.connect(self._on_input_changed)
        self.multi_value_edit.textChanged.connect(self._on_input_changed)
        self.path_value_edit.textChanged.connect(self._on_input_changed)
        self.type_combo.currentTextChanged.connect(self._on_input_changed)
        
        # PATH类型变量切换
        self.is_path_check.toggled.connect(self._on_path_type_changed)
        
        # PATH工具按钮
        self.format_path_btn.clicked.connect(self._format_path_value)
        self.remove_duplicates_btn.clicked.connect(self._remove_duplicate_paths)
        self.validate_paths_btn.clicked.connect(self._validate_all_paths)
        
        # 标签页切换
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # 按钮连接
        self.reset_btn.clicked.connect(self._reset_inputs)
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn.clicked.connect(self._save_variable)
    
    def _load_data(self):
        """加载数据到界面"""
        if not self.is_edit_mode or not self.original_variable:
            return
        
        var = self.original_variable
        
        # 加载基本信息
        self.name_edit.setText(var.name)
        
        # 检测是否为PATH类型变量
        is_path = var.is_path_variable
        self.is_path_check.setChecked(is_path)
        
        # 加载变量值
        if is_path:
            self.path_value_edit.setPlainText(var.value)
        elif '\n' in var.value or len(var.value) > 100:
            self.multi_value_edit.setPlainText(var.value)
        else:
            self.simple_value_edit.setText(var.value)
    
    def _setup_initial_state(self):
        """设置初始状态"""
        # 在所有UI组件创建完成后设置初始状态
        if self.is_edit_mode and self.original_variable:
            is_path = self.original_variable.is_path_variable
            self._switch_value_editor(is_path)
        else:
            self._switch_value_editor(False)
    
    def _switch_value_editor(self, is_path: bool):
        """切换值编辑器"""
        # 隐藏所有编辑器
        self.simple_value_edit.hide()
        self.multi_value_edit.hide()
        self.path_value_edit.hide()
        
        # 显示相应的编辑器
        if is_path:
            self.path_value_edit.show()
            self.path_tools_group.show()
        else:
            # 根据值的复杂性选择编辑器
            current_value = self._get_current_value()
            if '\n' in current_value or len(current_value) > 100:
                self.multi_value_edit.show()
            else:
                self.simple_value_edit.show()
            self.path_tools_group.hide()
    
    def _get_current_value(self) -> str:
        """获取当前输入的值"""
        if self.is_path_check.isChecked():
            return self.path_value_edit.toPlainText()
        elif self.multi_value_edit.isVisible():
            return self.multi_value_edit.toPlainText()
        else:
            return self.simple_value_edit.text()
    
    def _set_current_value(self, value: str):
        """设置当前值"""
        if self.is_path_check.isChecked():
            self.path_value_edit.setPlainText(value)
        elif self.multi_value_edit.isVisible():
            self.multi_value_edit.setPlainText(value)
        else:
            self.simple_value_edit.setText(value)
    
    def _on_input_changed(self):
        """处理输入变化"""
        # 延迟验证，避免频繁验证
        self.validation_timer.start(300)
        
        # 更新预览
        self._update_preview()
    
    def _on_path_type_changed(self, is_path: bool):
        """处理PATH类型变化"""
        self._switch_value_editor(is_path)
        self._validate_input()
        self._update_path_list()
    
    def _on_tab_changed(self, index: int):
        """处理标签页切换"""
        if index == 2:  # 预览标签页
            self._update_preview()
        elif index == 1:  # 高级设置标签页
            self._update_path_list()
    
    def _validate_input(self):
        """验证输入"""
        # 清除之前的状态
        self.validation_status_label.hide()
        self.warning_label.hide()
        self.error_label.hide()
        
        # 获取输入值
        name = self.name_edit.text().strip()
        value = self._get_current_value()
        env_type = self.type_combo.currentData()
        
        # 验证变量名
        if not name:
            self._show_validation_error("变量名不能为空")
            self.ok_btn.setEnabled(False)
            return
        
        name_valid, name_error = self.validator.validate_variable_name(name)
        if not name_valid:
            self._show_validation_error(f"变量名错误: {name_error}")
            self.ok_btn.setEnabled(False)
            return
        
        # 验证变量值
        value_valid, value_error = self.validator.validate_variable_value(value, name)
        if not value_valid:
            self._show_validation_error(f"变量值错误: {value_error}")
            self.ok_btn.setEnabled(False)
            return
        
        # 创建临时变量进行完整验证
        temp_var = EnvironmentVariable(name=name, value=value, env_type=env_type)
        
        # 完整验证
        var_valid, var_error = self.validator.validate_variable(temp_var)
        if not var_valid:
            self._show_validation_error(f"验证失败: {var_error}")
            self.ok_btn.setEnabled(False)
            return
        
        # 检查警告
        warnings = []
        if temp_var.is_path_variable:
            _, _, path_warnings = self.validator.validate_path_variable_change(temp_var)
            warnings.extend(path_warnings)
        
        # 系统变量警告
        if env_type == EnvType.SYSTEM:
            _, _, sys_warnings = self.validator.validate_system_variable_change(temp_var, True)
            warnings.extend(sys_warnings)
        
        # 显示状态
        if warnings:
            self._show_validation_warning("; ".join(warnings))
        else:
            self._show_validation_success("输入有效")
        
        self.ok_btn.setEnabled(True)
    
    def _show_validation_success(self, message: str):
        """显示验证成功"""
        self.validation_status_label.setText(f"✓ {message}")
        self.validation_status_label.setStyleSheet("color: green; font-weight: bold;")
        self.validation_status_label.show()
    
    def _show_validation_warning(self, message: str):
        """显示验证警告"""
        self.validation_status_label.setText("⚠ 输入有效但存在警告")
        self.validation_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.validation_status_label.show()
        
        self.warning_label.setText(f"警告: {message}")
        self.warning_label.show()
    
    def _show_validation_error(self, message: str):
        """显示验证错误"""
        self.validation_status_label.setText("✗ 输入无效")
        self.validation_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.validation_status_label.show()
        
        self.error_label.setText(f"错误: {message}")
        self.error_label.show()
    
    def _update_preview(self):
        """更新预览"""
        name = self.name_edit.text().strip()
        value = self._get_current_value()
        env_type = self.type_combo.currentData()
        
        # 构建预览文本
        preview_lines = []
        preview_lines.append(f"变量名: {name}")
        preview_lines.append(f"变量类型: {'系统变量' if env_type == EnvType.SYSTEM else '用户变量'}")
        preview_lines.append(f"变量值长度: {len(value)} 字符")
        
        if self.is_path_check.isChecked() and value:
            paths = split_path_value(value)
            preview_lines.append(f"PATH路径数量: {len(paths)}")
            preview_lines.append("")
            preview_lines.append("PATH路径列表:")
            for i, path in enumerate(paths, 1):
                status = "✓" if validate_path(path) else "✗"
                preview_lines.append(f"  {i:2d}. {status} {path}")
        else:
            preview_lines.append("")
            preview_lines.append("变量值:")
            preview_lines.append(value)
        
        self.preview_text.setPlainText("\n".join(preview_lines))
        
        # 更新统计信息
        self.name_length_label.setText(str(len(name)))
        self.value_length_label.setText(str(len(value)))
        
        if self.is_path_check.isChecked() and value:
            self.path_count_label.setText(str(len(split_path_value(value))))
        else:
            self.path_count_label.setText("0")
    
    def _update_path_list(self):
        """更新PATH路径列表"""
        if not self.is_path_check.isChecked():
            self.path_list_edit.clear()
            return
        
        value = self._get_current_value()
        if not value:
            self.path_list_edit.clear()
            return
        
        paths = split_path_value(value)
        path_info_lines = []
        
        for i, path in enumerate(paths, 1):
            # 验证路径
            is_valid = validate_path(path)
            status = "✓" if is_valid else "✗"
            
            # 检查是否存在
            import os
            exists = os.path.exists(path) if path else False
            exists_str = "(存在)" if exists else "(不存在)" if path else ""
            
            path_info_lines.append(f"{i:2d}. {status} {path} {exists_str}")
        
        self.path_list_edit.setPlainText("\n".join(path_info_lines))
    
    def _format_path_value(self):
        """格式化PATH值"""
        if not self.is_path_check.isChecked():
            return
        
        value = self._get_current_value()
        if not value:
            return
        
        paths = split_path_value(value)
        # 移除空路径
        paths = [path for path in paths if path.strip()]
        
        # 重新组合
        formatted_value = join_path_value(paths)
        self._set_current_value(formatted_value)
        
        self._update_path_list()
        self._validate_input()
    
    def _remove_duplicate_paths(self):
        """移除重复路径"""
        if not self.is_path_check.isChecked():
            return
        
        value = self._get_current_value()
        if not value:
            return
        
        paths = split_path_value(value)
        # 去重，保持顺序
        seen = set()
        unique_paths = []
        for path in paths:
            path_lower = path.lower()
            if path_lower not in seen and path.strip():
                seen.add(path_lower)
                unique_paths.append(path)
        
        # 重新组合
        cleaned_value = join_path_value(unique_paths)
        self._set_current_value(cleaned_value)
        
        self._update_path_list()
        self._validate_input()
        
        QMessageBox.information(self, "去重完成", 
                               f"已移除 {len(paths) - len(unique_paths)} 个重复路径")
    
    def _validate_all_paths(self):
        """验证所有路径"""
        if not self.is_path_check.isChecked():
            return
        
        value = self._get_current_value()
        if not value:
            QMessageBox.information(self, "验证结果", "没有路径需要验证")
            return
        
        paths = split_path_value(value)
        valid_count = 0
        invalid_paths = []
        
        for path in paths:
            if validate_path(path):
                valid_count += 1
            else:
                invalid_paths.append(path)
        
        # 显示验证结果
        result_lines = [f"总路径数量: {len(paths)}"]
        result_lines.append(f"有效路径: {valid_count}")
        result_lines.append(f"无效路径: {len(invalid_paths)}")
        
        if invalid_paths:
            result_lines.append("")
            result_lines.append("无效路径列表:")
            for path in invalid_paths[:10]:  # 最多显示10个
                result_lines.append(f"  • {path}")
            if len(invalid_paths) > 10:
                result_lines.append(f"  ... 还有 {len(invalid_paths) - 10} 个")
        
        QMessageBox.information(self, "路径验证结果", "\n".join(result_lines))
        self._update_path_list()
    
    def _reset_inputs(self):
        """重置输入"""
        if self.is_edit_mode:
            # 重置为原始值
            self._load_data()
        else:
            # 清空所有输入
            self.name_edit.clear()
            self.simple_value_edit.clear()
            self.multi_value_edit.clear()
            self.path_value_edit.clear()
            self.type_combo.setCurrentIndex(0)
            self.is_path_check.setChecked(False)
        
        self._validate_input()
    
    def _save_variable(self):
        """保存变量"""
        # 最终验证
        name = self.name_edit.text().strip()
        value = self._get_current_value()
        env_type = self.type_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "错误", "变量名不能为空")
            return
        
        # 创建环境变量对象
        new_var = EnvironmentVariable(
            name=name,
            value=value,
            env_type=env_type,
            is_new=not self.is_edit_mode
        )
        
        if self.is_edit_mode and self.original_variable:
            new_var.original_value = self.original_variable.original_value
            new_var.created_time = self.original_variable.created_time
            new_var.mark_modified()
        
        # 最终验证
        valid, error = self.validator.validate_variable(new_var)
        if not valid:
            QMessageBox.warning(self, "验证失败", f"变量验证失败:\n{error}")
            return
        
        # 检查重要变量修改
        if env_type == EnvType.SYSTEM:
            _, _, warnings = self.validator.validate_system_variable_change(new_var, True)
            if warnings:
                reply = QMessageBox.question(
                    self, "确认修改",
                    f"检测到以下警告:\n\n{chr(10).join(warnings)}\n\n是否继续修改？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        
        # 发送信号并关闭对话框
        self.variable_saved.emit(new_var)
        self.accept()
    
    def get_variable(self) -> Optional[EnvironmentVariable]:
        """获取编辑后的变量（用于非信号方式）"""
        if self.result() == QDialog.DialogCode.Accepted:
            name = self.name_edit.text().strip()
            value = self._get_current_value()
            env_type = self.type_combo.currentData()
            
            new_var = EnvironmentVariable(
                name=name,
                value=value,
                env_type=env_type,
                is_new=not self.is_edit_mode
            )
            
            if self.is_edit_mode and self.original_variable:
                new_var.original_value = self.original_variable.original_value
                new_var.created_time = self.original_variable.created_time
                new_var.mark_modified()
            
            return new_var
        
        return None 
