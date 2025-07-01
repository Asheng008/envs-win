"""
PATH编辑器组件

专门用于编辑PATH类型环境变量的高级组件。
"""

import os
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLabel, QLineEdit, QDialog, QDialogButtonBox,
    QMessageBox, QSplitter, QGroupBox, QTextEdit, QCheckBox,
    QToolButton, QMenu, QFileDialog, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer
from PySide6.QtGui import QDrag, QPixmap, QPainter, QIcon, QAction, QFont

from ...models.env_model import PathInfo, EnvironmentVariable, PathStatus
from ...core.path_controller import PathController
from ...utils.helpers import normalize_path, validate_path
from ...utils.constants import MAX_SINGLE_PATH_LENGTH, MAX_PATH_LENGTH
from ...utils.logger import get_logger


class PathListWidget(QListWidget):
    """支持拖拽的路径列表控件"""
    
    paths_reordered = Signal(list)  # 路径重新排序信号
    path_double_clicked = Signal(PathInfo)  # 路径双击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(True)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def dropEvent(self, event):
        """处理拖放事件"""
        super().dropEvent(event)
        # 发射重新排序信号
        path_infos = []
        for i in range(self.count()):
            item = self.item(i)
            if item:
                path_info = item.data(Qt.ItemDataRole.UserRole)
                if path_info:
                    path_infos.append(path_info)
        self.paths_reordered.emit(path_infos)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """处理双击事件"""
        path_info = item.data(Qt.ItemDataRole.UserRole)
        if path_info:
            self.path_double_clicked.emit(path_info)


class PathEditDialog(QDialog):
    """路径编辑对话框"""
    
    def __init__(self, path_info: Optional[PathInfo] = None, parent=None):
        super().__init__(parent)
        self.path_info = path_info
        self.is_editing = path_info is not None
        self._setup_ui()
        self._setup_signals()
        
        if self.is_editing:
            self.setWindowTitle("编辑路径")
            self.path_edit.setText(path_info.path)
        else:
            self.setWindowTitle("添加路径")
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 路径输入区域
        path_group = QGroupBox("路径设置")
        path_layout = QVBoxLayout(path_group)
        
        # 路径输入框
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入文件夹路径...")
        path_layout.addWidget(QLabel("路径:"))
        path_layout.addWidget(self.path_edit)
        
        # 浏览按钮
        browse_layout = QHBoxLayout()
        self.browse_btn = QPushButton("浏览...")
        browse_layout.addWidget(self.browse_btn)
        browse_layout.addStretch()
        path_layout.addLayout(browse_layout)
        
        # 路径验证信息
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        path_layout.addWidget(self.validation_label)
        
        layout.addWidget(path_group)
        
        # 按钮区域
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("确定")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        
        layout.addWidget(button_box)
        
        # 连接信号
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
    
    def _setup_signals(self):
        """设置信号连接"""
        self.path_edit.textChanged.connect(self._validate_path)
        self.browse_btn.clicked.connect(self._browse_path)
    
    def _validate_path(self):
        """验证路径"""
        path = self.path_edit.text().strip()
        
        if not path:
            self.validation_label.setText("")
            self.ok_button.setEnabled(False)
            return
        
        normalized = normalize_path(path)
        
        # 检查长度
        if len(normalized) > MAX_SINGLE_PATH_LENGTH:
            self.validation_label.setText(
                f"❌ 路径长度超限 ({len(normalized)}/{MAX_SINGLE_PATH_LENGTH})"
            )
            self.validation_label.setStyleSheet("color: red;")
            self.ok_button.setEnabled(False)
            return
        
        # 检查存在性
        exists = os.path.exists(normalized)
        if exists:
            if os.path.isdir(normalized):
                self.validation_label.setText("✅ 有效的目录路径")
                self.validation_label.setStyleSheet("color: green;")
            else:
                self.validation_label.setText("⚠️ 路径存在但不是目录")
                self.validation_label.setStyleSheet("color: orange;")
        else:
            self.validation_label.setText("⚠️ 路径不存在")
            self.validation_label.setStyleSheet("color: orange;")
        
        self.ok_button.setEnabled(True)
    
    def _browse_path(self):
        """浏览路径"""
        current_path = self.path_edit.text().strip()
        if current_path and os.path.exists(current_path):
            start_dir = current_path
        else:
            start_dir = os.getcwd()
        
        path = QFileDialog.getExistingDirectory(
            self, "选择目录", start_dir
        )
        
        if path:
            self.path_edit.setText(path)
    
    def get_path(self) -> str:
        """获取输入的路径"""
        return normalize_path(self.path_edit.text().strip())


class PathEditor(QWidget):
    """PATH编辑器主组件"""
    
    # 信号定义
    paths_changed = Signal(list)  # 路径列表变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.path_controller = PathController()
        self.path_infos: List[PathInfo] = []
        self._setup_ui()
        self._setup_signals()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧 - 路径列表
        left_widget = self._create_path_list_widget()
        splitter.addWidget(left_widget)
        
        # 右侧 - 统计和操作
        right_widget = self._create_control_widget()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 2)  # 左侧占2/3
        splitter.setStretchFactor(1, 1)  # 右侧占1/3
        
        layout.addWidget(splitter)
    
    def _create_path_list_widget(self) -> QWidget:
        """创建路径列表部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题和工具栏
        header_layout = QHBoxLayout()
        title = QLabel("PATH路径列表")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # 工具栏按钮
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加")
        self.edit_btn = QPushButton("编辑")
        self.remove_btn = QPushButton("删除")
        
        toolbar_layout.addWidget(self.add_btn)
        toolbar_layout.addWidget(self.edit_btn)
        toolbar_layout.addWidget(self.remove_btn)
        toolbar_layout.addStretch()
        
        # 批量操作菜单
        self.batch_btn = QToolButton()
        self.batch_btn.setText("批量操作")
        self.batch_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        batch_menu = QMenu(self.batch_btn)
        batch_menu.addAction("去除重复", self._remove_duplicates)
        batch_menu.addAction("清理无效", self._clean_invalid)
        batch_menu.addAction("优化排序", self._optimize_paths)
        batch_menu.addSeparator()
        batch_menu.addAction("全选", self._select_all)
        batch_menu.addAction("反选", self._invert_selection)
        self.batch_btn.setMenu(batch_menu)
        
        toolbar_layout.addWidget(self.batch_btn)
        
        header_layout.addLayout(toolbar_layout)
        layout.addLayout(header_layout)
        
        # 路径列表
        self.path_list = PathListWidget()
        layout.addWidget(self.path_list)
        
        return widget
    
    def _create_control_widget(self) -> QWidget:
        """创建控制面板部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        # 长度进度条
        self.length_progress = QProgressBar()
        self.length_progress.setMaximum(MAX_PATH_LENGTH)
        self.length_label = QLabel()
        stats_layout.addWidget(QLabel("PATH总长度:"))
        stats_layout.addWidget(self.length_progress)
        stats_layout.addWidget(self.length_label)
        
        layout.addWidget(stats_group)
        
        # 快速操作
        actions_group = QGroupBox("快速操作")
        actions_layout = QVBoxLayout(actions_group)
        
        self.remove_dup_btn = QPushButton("去除重复路径")
        self.clean_invalid_btn = QPushButton("清理无效路径")
        self.optimize_btn = QPushButton("优化路径顺序")
        
        actions_layout.addWidget(self.remove_dup_btn)
        actions_layout.addWidget(self.clean_invalid_btn)
        actions_layout.addWidget(self.optimize_btn)
        
        layout.addWidget(actions_group)
        
        # 导入导出
        io_group = QGroupBox("导入导出")
        io_layout = QVBoxLayout(io_group)
        
        self.import_btn = QPushButton("从文件导入")
        self.export_btn = QPushButton("导出到文件")
        
        io_layout.addWidget(self.import_btn)
        io_layout.addWidget(self.export_btn)
        
        layout.addWidget(io_group)
        
        # 验证结果
        validation_group = QGroupBox("验证结果")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(100)
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)
        
        layout.addWidget(validation_group)
        
        layout.addStretch()
        return widget
    
    def _setup_signals(self):
        """设置信号连接"""
        # 路径列表信号
        self.path_list.paths_reordered.connect(self._on_paths_reordered)
        self.path_list.path_double_clicked.connect(self._edit_path)
        self.path_list.itemSelectionChanged.connect(self._update_buttons_state)
        
        # 按钮信号
        self.add_btn.clicked.connect(self._add_path)
        self.edit_btn.clicked.connect(self._edit_selected_path)
        self.remove_btn.clicked.connect(self._remove_selected_paths)
        
        # 快速操作信号
        self.remove_dup_btn.clicked.connect(self._remove_duplicates)
        self.clean_invalid_btn.clicked.connect(self._clean_invalid)
        self.optimize_btn.clicked.connect(self._optimize_paths)
        
        # 导入导出信号
        self.import_btn.clicked.connect(self._import_paths)
        self.export_btn.clicked.connect(self._export_paths)
    
    def set_paths(self, path_infos: List[PathInfo]):
        """设置路径列表"""
        self.path_infos = path_infos.copy()
        self._refresh_list()
        self._update_statistics()
        self._validate_paths()
    
    def get_paths(self) -> List[PathInfo]:
        """获取当前路径列表"""
        return self.path_infos.copy()
    
    def _refresh_list(self):
        """刷新路径列表显示"""
        self.path_list.clear()
        
        for path_info in self.path_infos:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, path_info)
            
            # 设置显示文本
            display_text = path_info.display_name
            if path_info.status != PathStatus.VALID:
                status_icon = {
                    PathStatus.INVALID: "❌",
                    PathStatus.DUPLICATE: "🔄",
                    PathStatus.TOO_LONG: "📏"
                }.get(path_info.status, "")
                display_text = f"{status_icon} {display_text}"
            elif path_info.exists:
                display_text = f"✅ {display_text}"
            else:
                display_text = f"⚠️ {display_text}"
            
            item.setText(display_text)
            item.setToolTip(path_info.tooltip)
            
            # 设置颜色
            if path_info.status == PathStatus.INVALID:
                item.setForeground(Qt.GlobalColor.red)
            elif path_info.status == PathStatus.DUPLICATE:
                item.setForeground(Qt.GlobalColor.blue)
            elif path_info.status == PathStatus.TOO_LONG:
                item.setForeground(Qt.GlobalColor.magenta)
            elif not path_info.exists:
                item.setForeground(Qt.GlobalColor.darkYellow)
            
            self.path_list.addItem(item)
    
    def _update_statistics(self):
        """更新统计信息"""
        stats = self.path_controller.get_path_statistics(self.path_infos)
        
        stats_text = f"""总路径数: {stats['total']}
有效路径: {stats['valid']}
无效路径: {stats['invalid']}
重复路径: {stats['duplicate']}
超长路径: {stats['too_long']}
存在路径: {stats['existing']}
缺失路径: {stats['missing']}"""
        
        self.stats_label.setText(stats_text)
        
        # 更新长度进度条
        total_length = stats['total_length']
        self.length_progress.setValue(total_length)
        
        percentage = (total_length / MAX_PATH_LENGTH) * 100
        self.length_label.setText(f"{total_length}/{MAX_PATH_LENGTH} ({percentage:.1f}%)")
        
        # 设置进度条颜色
        if percentage > 90:
            self.length_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif percentage > 70:
            self.length_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.length_progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
    
    def _validate_paths(self):
        """验证路径"""
        errors = self.path_controller.validate_paths(self.path_infos)
        
        if errors:
            self.validation_text.setText("发现以下问题:\n" + "\n".join(f"• {error}" for error in errors))
            self.validation_text.setStyleSheet("color: red;")
        else:
            self.validation_text.setText("✅ 所有路径验证通过")
            self.validation_text.setStyleSheet("color: green;")
    
    def _update_buttons_state(self):
        """更新按钮状态"""
        has_selection = bool(self.path_list.selectedItems())
        self.edit_btn.setEnabled(has_selection and len(self.path_list.selectedItems()) == 1)
        self.remove_btn.setEnabled(has_selection)
    
    def _on_paths_reordered(self, path_infos: List[PathInfo]):
        """处理路径重新排序"""
        self.path_infos = path_infos
        self._update_statistics()
        self._validate_paths()
        self.paths_changed.emit(self.path_infos)
    
    def _add_path(self):
        """添加路径"""
        dialog = PathEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = dialog.get_path()
            if new_path:
                # 创建新的PathInfo
                path_info = PathInfo(path=new_path, status=PathStatus.VALID)
                self.path_infos.append(path_info)
                
                # 重新解析以更新状态
                self.path_infos = self.path_controller.parse_path_value(
                    self.path_controller.build_path_value(self.path_infos)
                )
                
                self._refresh_list()
                self._update_statistics()
                self._validate_paths()
                self.paths_changed.emit(self.path_infos)
    
    def _edit_selected_path(self):
        """编辑选中的路径"""
        selected_items = self.path_list.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            path_info = item.data(Qt.ItemDataRole.UserRole)
            self._edit_path(path_info)
    
    def _edit_path(self, path_info: PathInfo):
        """编辑路径"""
        dialog = PathEditDialog(path_info, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = dialog.get_path()
            if new_path != path_info.path:
                # 更新路径
                index = self.path_infos.index(path_info)
                self.path_infos[index] = PathInfo(path=new_path, status=PathStatus.VALID)
                
                # 重新解析以更新状态
                self.path_infos = self.path_controller.parse_path_value(
                    self.path_controller.build_path_value(self.path_infos)
                )
                
                self._refresh_list()
                self._update_statistics()
                self._validate_paths()
                self.paths_changed.emit(self.path_infos)
    
    def _remove_selected_paths(self):
        """删除选中的路径"""
        selected_items = self.path_list.selectedItems()
        if not selected_items:
            return
        
        if len(selected_items) == 1:
            message = "确定要删除选中的路径吗？"
        else:
            message = f"确定要删除选中的 {len(selected_items)} 个路径吗？"
        
        reply = QMessageBox.question(
            self, "确认删除", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 获取要删除的路径信息
            to_remove = []
            for item in selected_items:
                path_info = item.data(Qt.ItemDataRole.UserRole)
                if path_info:
                    to_remove.append(path_info)
            
            # 从列表中移除
            for path_info in to_remove:
                if path_info in self.path_infos:
                    self.path_infos.remove(path_info)
            
            self._refresh_list()
            self._update_statistics()
            self._validate_paths()
            self.paths_changed.emit(self.path_infos)
    
    def _remove_duplicates(self):
        """去除重复路径"""
        original_count = len(self.path_infos)
        self.path_infos = self.path_controller.remove_duplicates(self.path_infos)
        removed_count = original_count - len(self.path_infos)
        
        if removed_count > 0:
            QMessageBox.information(
                self, "操作完成", f"已移除 {removed_count} 个重复路径"
            )
            self._refresh_list()
            self._update_statistics()
            self._validate_paths()
            self.paths_changed.emit(self.path_infos)
        else:
            QMessageBox.information(self, "操作完成", "没有发现重复路径")
    
    def _clean_invalid(self):
        """清理无效路径"""
        original_count = len(self.path_infos)
        self.path_infos = self.path_controller.clean_invalid_paths(self.path_infos)
        removed_count = original_count - len(self.path_infos)
        
        if removed_count > 0:
            QMessageBox.information(
                self, "操作完成", f"已清理 {removed_count} 个无效路径"
            )
            self._refresh_list()
            self._update_statistics()
            self._validate_paths()
            self.paths_changed.emit(self.path_infos)
        else:
            QMessageBox.information(self, "操作完成", "没有发现无效路径")
    
    def _optimize_paths(self):
        """优化路径顺序"""
        self.path_infos = self.path_controller.optimize_paths(self.path_infos)
        self._refresh_list()
        self._update_statistics()
        self._validate_paths()
        self.paths_changed.emit(self.path_infos)
        QMessageBox.information(self, "操作完成", "路径已优化完成")
    
    def _select_all(self):
        """全选"""
        self.path_list.selectAll()
    
    def _invert_selection(self):
        """反选"""
        for i in range(self.path_list.count()):
            item = self.path_list.item(i)
            item.setSelected(not item.isSelected())
    
    def _import_paths(self):
        """从文件导入路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入路径", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # 解析导入的路径
                imported_paths = self.path_controller.parse_path_value(content)
                
                if imported_paths:
                    # 合并到现有路径
                    all_paths = self.path_infos + imported_paths
                    self.path_infos = self.path_controller.remove_duplicates(all_paths)
                    
                    self._refresh_list()
                    self._update_statistics()
                    self._validate_paths()
                    self.paths_changed.emit(self.path_infos)
                    
                    QMessageBox.information(
                        self, "导入完成", f"成功导入 {len(imported_paths)} 个路径"
                    )
                else:
                    QMessageBox.warning(self, "导入失败", "文件中没有找到有效的路径")
                    
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入文件时出错: {str(e)}")
    
    def _export_paths(self):
        """导出路径到文件"""
        if not self.path_infos:
            QMessageBox.warning(self, "导出失败", "没有路径可以导出")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出路径", "paths.txt", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                path_value = self.path_controller.build_path_value(self.path_infos)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(path_value)
                
                QMessageBox.information(
                    self, "导出完成", f"成功导出 {len(self.path_infos)} 个路径到文件"
                )
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时出错: {str(e)}") 
