"""
PATH变量专用编辑器对话框

专门用于管理PATH环境变量的高级编辑工具。
"""

import os
import winreg
from typing import List, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem, 
    QPushButton, QToolBar, QGroupBox, QLabel, QLineEdit, QTextEdit, 
    QProgressBar, QMessageBox, QFileDialog, QMenu, QCheckBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QAction, QFont, QColor

from ...models.env_model import EnvType
from ...core.path_controller import PathController  
from ...utils.helpers import split_path_value, join_path_value, validate_path


class PathValidationWorker(QThread):
    """路径验证工作线程"""
    validation_progress = Signal(int, int)
    path_validated = Signal(int, bool, str)
    validation_complete = Signal()
    
    def __init__(self, paths: List[str]):
        super().__init__()
        self.paths = paths
        self.should_stop = False
    
    def run(self):
        total = len(self.paths)
        for i, path in enumerate(self.paths):
            if self.should_stop:
                break
            try:
                is_valid = validate_path(path)
                error_msg = "" if is_valid else "路径无效或不存在"
                self.path_validated.emit(i, is_valid, error_msg)
            except Exception as e:
                self.path_validated.emit(i, False, str(e))
            self.validation_progress.emit(i + 1, total)
        self.validation_complete.emit()
    
    def stop(self):
        self.should_stop = True


class PathListWidget(QListWidget):
    """支持拖拽的路径列表组件"""
    paths_reordered = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def dropEvent(self, event):
        super().dropEvent(event)
        paths = [self.item(i).text() for i in range(self.count())]
        self.paths_reordered.emit(paths)
    
    def _show_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)
        
        copy_action = QAction("复制路径", self)
        copy_action.triggered.connect(self._copy_path)
        menu.addAction(copy_action)
        
        if os.path.exists(item.text()):
            open_action = QAction("在文件管理器中打开", self)
            open_action.triggered.connect(self._open_in_explorer)
            menu.addAction(open_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def _delete_selected(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        paths = [self.item(i).text() for i in range(self.count())]
        self.paths_reordered.emit(paths)
    
    def _copy_path(self):
        item = self.currentItem()
        if item:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(item.text())
    
    def _open_in_explorer(self):
        item = self.currentItem()
        if item and os.path.exists(item.text()):
            os.startfile(item.text())


class PathEditorDialog(QDialog):
    """PATH变量专用编辑器对话框"""
    path_updated = Signal(str)
    
    def __init__(self, parent=None, env_type: EnvType = EnvType.USER):
        super().__init__(parent)
        
        self.env_type = env_type
        self.path_controller = PathController()
        self.validation_worker = None
        self.original_paths: List[str] = []
        self.current_paths: List[str] = []
        
        type_name = "系统" if env_type == EnvType.SYSTEM else "用户"
        self.setWindowTitle(f"PATH编辑器 - {type_name}变量")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        self.setModal(True)
        
        self._init_ui()
        self._setup_connections()
        self._load_current_path()
        self._validate_all_paths()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 主要内容
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("重置")
        self.cancel_btn = QPushButton("取消")
        self.apply_btn = QPushButton("应用")
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_toolbar(self) -> QToolBar:
        toolbar = QToolBar("PATH工具")
        
        self.add_action = QAction("添加", self)
        self.add_action.triggered.connect(self._add_path)
        toolbar.addAction(self.add_action)
        
        self.delete_action = QAction("删除", self)
        self.delete_action.triggered.connect(self._delete_selected_paths)
        toolbar.addAction(self.delete_action)
        
        toolbar.addSeparator()
        
        self.move_up_action = QAction("上移", self)
        self.move_up_action.triggered.connect(self._move_path_up)
        toolbar.addAction(self.move_up_action)
        
        self.move_down_action = QAction("下移", self)
        self.move_down_action.triggered.connect(self._move_path_down)
        toolbar.addAction(self.move_down_action)
        
        toolbar.addSeparator()
        
        self.validate_action = QAction("验证", self)
        self.validate_action.triggered.connect(self._validate_all_paths)
        toolbar.addAction(self.validate_action)
        
        self.cleanup_action = QAction("清理", self)
        self.cleanup_action.triggered.connect(self._cleanup_invalid_paths)
        toolbar.addAction(self.cleanup_action)
        
        self.dedup_action = QAction("去重", self)
        self.dedup_action.triggered.connect(self._remove_duplicates)
        toolbar.addAction(self.dedup_action)
        
        toolbar.addSeparator()
        
        self.import_action = QAction("导入", self)
        self.import_action.triggered.connect(self._import_paths)
        toolbar.addAction(self.import_action)
        
        self.export_action = QAction("导出", self)
        self.export_action.triggered.connect(self._export_paths)
        toolbar.addAction(self.export_action)
        
        return toolbar
    
    def _create_content_area(self) -> QSplitter:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：路径列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索路径...")
        search_layout.addWidget(self.search_edit)
        left_layout.addLayout(search_layout)
        
        # 路径列表
        self.path_list = PathListWidget()
        self.path_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.path_list)
        
        # 快速添加
        add_layout = QHBoxLayout()
        self.quick_add_edit = QLineEdit()
        self.quick_add_edit.setPlaceholderText("输入路径...")
        self.browse_btn = QPushButton("浏览")
        self.quick_add_btn = QPushButton("添加")
        
        add_layout.addWidget(self.quick_add_edit)
        add_layout.addWidget(self.browse_btn)
        add_layout.addWidget(self.quick_add_btn)
        left_layout.addLayout(add_layout)
        
        # 右侧：详细信息
        right_widget = self._create_details_area()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        
        return splitter
    
    def _create_details_area(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.details_tabs = QTabWidget()
        
        # 统计标签页
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_group = QGroupBox("PATH统计")
        stats_group_layout = QVBoxLayout(stats_group)
        
        self.total_paths_label = QLabel("总路径数: 0")
        self.valid_paths_label = QLabel("有效路径: 0")
        self.invalid_paths_label = QLabel("无效路径: 0")
        self.duplicate_paths_label = QLabel("重复路径: 0")
        
        stats_group_layout.addWidget(self.total_paths_label)
        stats_group_layout.addWidget(self.valid_paths_label)
        stats_group_layout.addWidget(self.invalid_paths_label)
        stats_group_layout.addWidget(self.duplicate_paths_label)
        
        stats_layout.addWidget(stats_group)
        
        # 验证进度
        validation_group = QGroupBox("验证进度")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_progress = QProgressBar()
        self.validation_status = QLabel("等待验证...")
        
        validation_layout.addWidget(self.validation_progress)
        validation_layout.addWidget(self.validation_status)
        
        stats_layout.addWidget(validation_group)
        stats_layout.addStretch()
        
        # 预览标签页
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        preview_group = QGroupBox("PATH变量预览")
        preview_group_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        
        preview_group_layout.addWidget(self.preview_text)
        preview_layout.addWidget(preview_group)
        
        # 变更摘要
        changes_group = QGroupBox("变更摘要")
        changes_layout = QVBoxLayout(changes_group)
        
        self.changes_text = QTextEdit()
        self.changes_text.setReadOnly(True)
        self.changes_text.setMaximumHeight(150)
        
        changes_layout.addWidget(self.changes_text)
        preview_layout.addWidget(changes_group)
        
        self.details_tabs.addTab(stats_tab, "统计")
        self.details_tabs.addTab(preview_tab, "预览")
        
        layout.addWidget(self.details_tabs)
        return widget
    
    def _setup_connections(self):
        """设置信号连接"""
        # 路径列表事件
        self.path_list.paths_reordered.connect(self._on_paths_reordered)
        self.path_list.itemSelectionChanged.connect(self._update_selection_info)
        
        # 搜索
        self.search_edit.textChanged.connect(self._filter_paths)
        
        # 快速添加
        self.browse_btn.clicked.connect(self._browse_folder)
        self.quick_add_btn.clicked.connect(self._quick_add_path)
        self.quick_add_edit.returnPressed.connect(self._quick_add_path)
        
        # 按钮事件
        self.reset_btn.clicked.connect(self._reset_paths)
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn.clicked.connect(self._apply_changes)
        self.ok_btn.clicked.connect(self._save_and_close)
    
    def _load_current_path(self):
        """加载当前PATH变量"""
        try:
            # 获取当前PATH值
            current_value = ""
            if self.env_type == EnvType.SYSTEM:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                    current_value, _ = winreg.QueryValueEx(key, "PATH")
            else:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                    current_value, _ = winreg.QueryValueEx(key, "PATH")
            
            # 解析路径
            self.original_paths = split_path_value(current_value)
            self.current_paths = self.original_paths.copy()
            self._refresh_path_list()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法加载PATH变量: {e}")
            self.original_paths = []
            self.current_paths = []
    
    def _validate_all_paths(self):
        """验证所有路径"""
        if self.validation_worker and self.validation_worker.isRunning():
            self.validation_worker.stop()
            self.validation_worker.wait()
        
        if not self.current_paths:
            self._update_statistics()
            return
        
        self.validation_worker = PathValidationWorker(self.current_paths)
        self.validation_worker.validation_progress.connect(self._on_validation_progress)
        self.validation_worker.path_validated.connect(self._on_path_validated)
        self.validation_worker.validation_complete.connect(self._on_validation_complete)
        
        self.validation_progress.setMaximum(len(self.current_paths))
        self.validation_progress.setValue(0)
        self.validation_status.setText("验证中...")
        
        self.validation_worker.start()
    
    def _add_path(self):
        """添加新路径"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self._add_path_to_list(folder)
    
    def _delete_selected_paths(self):
        """删除选中的路径"""
        selected_items = self.path_list.selectedItems()
        if not selected_items:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_items)} 个路径吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                row = self.path_list.row(item)
                self.current_paths.pop(row)
                self.path_list.takeItem(row)
            
            self._refresh_path_list()
            self._update_preview()
    
    def _move_path_up(self):
        """向上移动路径"""
        current_row = self.path_list.currentRow()
        if current_row > 0:
            # 交换路径位置
            self.current_paths[current_row], self.current_paths[current_row - 1] = \
                self.current_paths[current_row - 1], self.current_paths[current_row]
            
            self._refresh_path_list()
            self.path_list.setCurrentRow(current_row - 1)
            self._update_preview()
    
    def _move_path_down(self):
        """向下移动路径"""
        current_row = self.path_list.currentRow()
        if current_row < len(self.current_paths) - 1:
            # 交换路径位置
            self.current_paths[current_row], self.current_paths[current_row + 1] = \
                self.current_paths[current_row + 1], self.current_paths[current_row]
            
            self._refresh_path_list()
            self.path_list.setCurrentRow(current_row + 1)
            self._update_preview()
    
    def _cleanup_invalid_paths(self):
        """清理无效路径"""
        valid_paths = [path for path in self.current_paths if validate_path(path)]
        removed_count = len(self.current_paths) - len(valid_paths)
        
        if removed_count > 0:
            reply = QMessageBox.question(
                self, "确认清理",
                f"将移除 {removed_count} 个无效路径，是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_paths = valid_paths
                self._refresh_path_list()
                self._update_preview()
                QMessageBox.information(self, "清理完成", f"已移除 {removed_count} 个无效路径")
        else:
            QMessageBox.information(self, "清理完成", "没有发现无效路径")
    
    def _remove_duplicates(self):
        """移除重复路径"""
        seen = set()
        unique_paths = []
        
        for path in self.current_paths:
            path_lower = path.lower()
            if path_lower not in seen:
                seen.add(path_lower)
                unique_paths.append(path)
        
        removed_count = len(self.current_paths) - len(unique_paths)
        
        if removed_count > 0:
            self.current_paths = unique_paths
            self._refresh_path_list()
            self._update_preview()
            QMessageBox.information(self, "去重完成", f"已移除 {removed_count} 个重复路径")
        else:
            QMessageBox.information(self, "去重完成", "没有发现重复路径")
    
    def _import_paths(self):
        """导入路径配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入PATH配置", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                imported_paths = split_path_value(content)
                self.current_paths.extend(imported_paths)
                self._refresh_path_list()
                self._update_preview()
                
                QMessageBox.information(self, "导入成功", f"已导入 {len(imported_paths)} 个路径")
                
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"无法读取文件: {e}")
    
    def _export_paths(self):
        """导出路径配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出PATH配置", "path_config.txt", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                content = join_path_value(self.current_paths)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(self, "导出成功", f"PATH配置已保存到: {file_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"无法保存文件: {e}")
    
    def _browse_folder(self):
        """浏览选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.quick_add_edit.setText(folder)
    
    def _quick_add_path(self):
        """快速添加路径"""
        path = self.quick_add_edit.text().strip()
        if path:
            self._add_path_to_list(path)
            self.quick_add_edit.clear()
    
    def _add_path_to_list(self, path: str):
        """添加路径到列表"""
        if path not in self.current_paths:
            self.current_paths.append(path)
            self._refresh_path_list()
            self._update_preview()
    
    def _refresh_path_list(self):
        """刷新路径列表显示"""
        self.path_list.clear()
        for path in self.current_paths:
            item = QListWidgetItem(path)
            # 设置路径状态颜色
            if validate_path(path):
                item.setBackground(QColor(144, 238, 144))  # 浅绿色
            else:
                item.setBackground(QColor(211, 211, 211))  # 浅灰色
            
            self.path_list.addItem(item)
        
        self._update_statistics()
        self._update_preview()
    
    def _update_statistics(self):
        """更新统计信息"""
        total = len(self.current_paths)
        valid = sum(1 for path in self.current_paths if validate_path(path))
        invalid = total - valid
        
        # 计算重复路径
        seen = set()
        duplicates = 0
        for path in self.current_paths:
            path_lower = path.lower()
            if path_lower in seen:
                duplicates += 1
            else:
                seen.add(path_lower)
        
        self.total_paths_label.setText(f"总路径数: {total}")
        self.valid_paths_label.setText(f"有效路径: {valid}")
        self.invalid_paths_label.setText(f"无效路径: {invalid}")
        self.duplicate_paths_label.setText(f"重复路径: {duplicates}")
    
    def _update_preview(self):
        """更新预览"""
        path_value = join_path_value(self.current_paths)
        self.preview_text.setPlainText(path_value)
        
        # 更新变更摘要
        changes = []
        if len(self.current_paths) != len(self.original_paths):
            changes.append(f"路径数量: {len(self.original_paths)} → {len(self.current_paths)}")
        
        if self.current_paths != self.original_paths:
            changes.append("路径内容已修改")
        
        if changes:
            self.changes_text.setPlainText("检测到以下变更:\n" + "\n".join(changes))
        else:
            self.changes_text.setPlainText("无变更")
    
    def _on_paths_reordered(self, paths: List[str]):
        """处理路径重新排序"""
        self.current_paths = paths
        self._update_preview()
    
    def _on_validation_progress(self, current: int, total: int):
        """处理验证进度"""
        self.validation_progress.setValue(current)
        self.validation_status.setText(f"验证中... {current}/{total}")
    
    def _on_path_validated(self, index: int, is_valid: bool, error_msg: str):
        """处理单个路径验证结果"""
        if index < self.path_list.count():
            item = self.path_list.item(index)
            if is_valid:
                item.setBackground(QColor(144, 238, 144))  # 浅绿色
                item.setToolTip("")
            else:
                item.setBackground(QColor(211, 211, 211))  # 浅灰色
                item.setToolTip(error_msg)
    
    def _on_validation_complete(self):
        """处理验证完成"""
        self.validation_status.setText("验证完成")
        self._update_statistics()
    
    def _update_selection_info(self):
        """更新选中路径信息"""
        pass  # 可以在这里添加选中路径的详细信息显示
    
    def _filter_paths(self, text: str):
        """过滤路径显示"""
        for i in range(self.path_list.count()):
            item = self.path_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _reset_paths(self):
        """重置到原始路径"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置为原始PATH值吗？所有修改将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_paths = self.original_paths.copy()
            self._refresh_path_list()
    
    def _apply_changes(self):
        """应用更改"""
        try:
            path_value = join_path_value(self.current_paths)
            # 这里会发送信号，由主程序处理实际的注册表写入
            self.path_updated.emit(path_value)
            self.status_label.setText("更改已应用")
            
        except Exception as e:
            QMessageBox.warning(self, "应用失败", f"无法应用更改: {e}")
    
    def _save_and_close(self):
        """保存并关闭"""
        self._apply_changes()
        self.accept()
    
    def get_path_value(self) -> str:
        """获取当前PATH值"""
        return join_path_value(self.current_paths)
