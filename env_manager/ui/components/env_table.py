"""
环境变量表格组件

实现环境变量的表格显示和操作功能。
"""

from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QApplication,
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QCheckBox, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QDrag, QPixmap, QPainter, QIcon

from ...models.env_model import EnvironmentVariable, EnvType
from ...utils.constants import TABLE_COLUMNS, SHORTCUTS, ENV_TYPES
from ...utils.logger import get_logger


class EnvTableWidget(QTableWidget):
    """自定义表格控件，支持拖拽和排序"""
    
    # 信号定义
    item_double_clicked = Signal(EnvironmentVariable)
    selection_changed = Signal(list)  # 选中项变化
    context_menu_requested = Signal(EnvironmentVariable, object)  # 右键菜单请求
    drag_drop_performed = Signal(int, int)  # 拖拽操作完成
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._env_vars: List[EnvironmentVariable] = []
        self._setup_ui()
        self._setup_signals()
        
    def _setup_ui(self):
        """设置UI"""
        # 设置列数和列标题
        self.setColumnCount(4)
        headers = ["变量名", "变量值", "类型", "状态"]
        self.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # 设置拖拽
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        
        # 设置列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 变量名
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 变量值
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 类型
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        
        # 设置垂直表头
        self.verticalHeader().setVisible(False)
        
    def _setup_signals(self):
        """设置信号连接"""
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.customContextMenuRequested.connect(self._on_context_menu_requested)
        
    def set_env_vars(self, env_vars: List[EnvironmentVariable]):
        """设置环境变量列表"""
        self._env_vars = env_vars
        self._refresh_table()
        
    def get_env_vars(self) -> List[EnvironmentVariable]:
        """获取环境变量列表"""
        return self._env_vars
        
    def get_selected_env_vars(self) -> List[EnvironmentVariable]:
        """获取选中的环境变量"""
        selected_vars = []
        for row in self._get_selected_rows():
            if row < len(self._env_vars):
                selected_vars.append(self._env_vars[row])
        return selected_vars
        
    def _get_selected_rows(self) -> List[int]:
        """获取选中的行号列表"""
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())
        return sorted(list(selected_rows))
        
    def _refresh_table(self):
        """刷新表格显示"""
        self.setRowCount(len(self._env_vars))
        
        for row, env_var in enumerate(self._env_vars):
            self._set_row_data(row, env_var)
            
    def _set_row_data(self, row: int, env_var: EnvironmentVariable):
        """设置行数据"""
        # 变量名
        name_item = QTableWidgetItem(env_var.name)
        name_item.setData(Qt.ItemDataRole.UserRole, env_var)
        self.setItem(row, 0, name_item)
        
        # 变量值
        value_item = QTableWidgetItem(env_var.display_value)
        value_item.setToolTip(env_var.value)
        self.setItem(row, 1, value_item)
        
        # 类型
        type_text = "系统" if env_var.env_type == EnvType.SYSTEM else "用户"
        type_item = QTableWidgetItem(type_text)
        if env_var.env_type == EnvType.SYSTEM:
            type_item.setBackground(Qt.GlobalColor.lightGray)
        self.setItem(row, 2, type_item)
        
        # 状态
        status_text = self._get_status_text(env_var)
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(self._get_status_color(env_var))
        self.setItem(row, 3, status_item)
        
    def _get_status_text(self, env_var: EnvironmentVariable) -> str:
        """获取状态文本"""
        if env_var.is_deleted:
            return "已删除"
        elif env_var.is_new:
            return "新建"
        elif env_var.is_modified:
            return "已修改"
        else:
            return "正常"
            
    def _get_status_color(self, env_var: EnvironmentVariable):
        """获取状态颜色"""
        if env_var.is_deleted:
            return Qt.GlobalColor.red
        elif env_var.is_new:
            return Qt.GlobalColor.green
        elif env_var.is_modified:
            return Qt.GlobalColor.blue
        else:
            return Qt.GlobalColor.black
            
    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """处理双击事件"""
        env_var = item.data(Qt.ItemDataRole.UserRole)
        if env_var:
            self.item_double_clicked.emit(env_var)
            
    def _on_selection_changed(self):
        """处理选择变化事件"""
        selected_vars = self.get_selected_env_vars()
        self.selection_changed.emit(selected_vars)
        
    def _on_context_menu_requested(self, position):
        """处理右键菜单请求"""
        item = self.itemAt(position)
        if not item:
            return
            
        env_var = item.data(Qt.ItemDataRole.UserRole)
        if env_var:
            self.context_menu_requested.emit(env_var, self.mapToGlobal(position))
    
    def add_env_var(self, env_var: EnvironmentVariable):
        """添加环境变量"""
        self._env_vars.append(env_var)
        self._refresh_table()
        
    def update_env_var(self, env_var: EnvironmentVariable):
        """更新环境变量"""
        for i, var in enumerate(self._env_vars):
            if var.name == env_var.name and var.env_type == env_var.env_type:
                self._env_vars[i] = env_var
                self._set_row_data(i, env_var)
                break
                
    def remove_env_var(self, env_var: EnvironmentVariable):
        """移除环境变量"""
        self._env_vars = [var for var in self._env_vars 
                         if not (var.name == env_var.name and var.env_type == env_var.env_type)]
        self._refresh_table()


class EnvTable(QWidget):
    """环境变量表格组件"""
    
    # 信号定义
    edit_requested = Signal(EnvironmentVariable)
    delete_requested = Signal(list)  # 删除请求，传递选中的变量列表
    duplicate_requested = Signal(EnvironmentVariable)
    export_requested = Signal(list)
    path_edit_requested = Signal(EnvironmentVariable)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._setup_ui()
        self._setup_signals()
        self._setup_context_menu()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 类型过滤
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全部", "系统变量", "用户变量"])
        toolbar_layout.addWidget(QLabel("类型:"))
        toolbar_layout.addWidget(self.type_filter)
        
        # 状态过滤
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "正常", "已修改", "新建", "已删除"])
        toolbar_layout.addWidget(QLabel("状态:"))
        toolbar_layout.addWidget(self.status_filter)
        
        toolbar_layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel("总计: 0 个变量")
        toolbar_layout.addWidget(self.stats_label)
        
        layout.addLayout(toolbar_layout)
        
        # 表格
        self.table = EnvTableWidget()
        layout.addWidget(self.table)
        
    def _setup_signals(self):
        """设置信号连接"""
        self.table.item_double_clicked.connect(self.edit_requested.emit)
        self.table.selection_changed.connect(self._on_selection_changed)
        self.table.context_menu_requested.connect(self._show_context_menu)
        
        self.type_filter.currentTextChanged.connect(self._apply_filters)
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        
    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = QMenu(self)
        
        # 编辑
        edit_action = QAction("编辑", self)
        edit_action.setShortcut(SHORTCUTS['EDIT'])
        edit_action.triggered.connect(self._edit_selected)
        self.context_menu.addAction(edit_action)
        
        # PATH编辑器
        path_edit_action = QAction("PATH编辑器", self)
        path_edit_action.triggered.connect(self._edit_path)
        self.context_menu.addAction(path_edit_action)
        
        self.context_menu.addSeparator()
        
        # 复制
        duplicate_action = QAction("复制", self)
        duplicate_action.triggered.connect(self._duplicate_selected)
        self.context_menu.addAction(duplicate_action)
        
        self.context_menu.addSeparator()
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.setShortcut(SHORTCUTS['DELETE'])
        delete_action.triggered.connect(self._delete_selected)
        self.context_menu.addAction(delete_action)
        
        self.context_menu.addSeparator()
        
        # 导出
        export_action = QAction("导出", self)
        export_action.triggered.connect(self._export_selected)
        self.context_menu.addAction(export_action)
        
    def _show_context_menu(self, env_var: EnvironmentVariable, position):
        """显示右键菜单"""
        selected_vars = self.table.get_selected_env_vars()
        
        # 根据选择情况启用/禁用菜单项
        has_selection = len(selected_vars) > 0
        single_selection = len(selected_vars) == 1
        has_path_var = any(var.is_path_variable for var in selected_vars)
        
        for action in self.context_menu.actions():
            if action.text() == "编辑":
                action.setEnabled(single_selection)
            elif action.text() == "PATH编辑器":
                action.setEnabled(single_selection and has_path_var)
            elif action.text() == "复制":
                action.setEnabled(single_selection)
            else:
                action.setEnabled(has_selection)
                
        self.context_menu.exec(position)
        
    def _edit_selected(self):
        """编辑选中项"""
        selected_vars = self.table.get_selected_env_vars()
        if selected_vars:
            self.edit_requested.emit(selected_vars[0])
            
    def _edit_path(self):
        """编辑PATH"""
        selected_vars = self.table.get_selected_env_vars()
        if selected_vars and selected_vars[0].is_path_variable:
            self.path_edit_requested.emit(selected_vars[0])
            
    def _duplicate_selected(self):
        """复制选中项"""
        selected_vars = self.table.get_selected_env_vars()
        if selected_vars:
            self.duplicate_requested.emit(selected_vars[0])
            
    def _delete_selected(self):
        """删除选中项"""
        selected_vars = self.table.get_selected_env_vars()
        if selected_vars:
            self.delete_requested.emit(selected_vars)
            
    def _export_selected(self):
        """导出选中项"""
        selected_vars = self.table.get_selected_env_vars()
        if selected_vars:
            self.export_requested.emit(selected_vars)
            
    def _on_selection_changed(self, selected_vars: List[EnvironmentVariable]):
        """处理选择变化"""
        count = len(selected_vars)
        if count == 0:
            self.stats_label.setText(f"总计: {len(self.table.get_env_vars())} 个变量")
        else:
            self.stats_label.setText(f"已选择: {count} 个变量")
            
    def _apply_filters(self):
        """应用过滤器"""
        # 类型过滤
        type_text = self.type_filter.currentText()
        if type_text == "系统变量":
            env_type_filter = EnvType.SYSTEM
        elif type_text == "用户变量":
            env_type_filter = EnvType.USER
        else:
            env_type_filter = None
            
        # 状态过滤
        status_text = self.status_filter.currentText()
        
        # 应用过滤
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                env_var = item.data(Qt.ItemDataRole.UserRole)
                
                # 检查类型过滤
                type_match = env_type_filter is None or env_var.env_type == env_type_filter
                
                # 检查状态过滤
                status_match = True
                if status_text != "全部":
                    if status_text == "正常":
                        status_match = not (env_var.is_modified or env_var.is_new or env_var.is_deleted)
                    elif status_text == "已修改":
                        status_match = env_var.is_modified
                    elif status_text == "新建":
                        status_match = env_var.is_new
                    elif status_text == "已删除":
                        status_match = env_var.is_deleted
                
                self.table.setRowHidden(row, not (type_match and status_match))
                
    def set_env_vars(self, env_vars: List[EnvironmentVariable]):
        """设置环境变量列表"""
        self.table.set_env_vars(env_vars)
        self._update_stats()
        
    def get_env_vars(self) -> List[EnvironmentVariable]:
        """获取环境变量列表"""
        return self.table.get_env_vars()
        
    def get_selected_env_vars(self) -> List[EnvironmentVariable]:
        """获取选中的环境变量"""
        return self.table.get_selected_env_vars()
        
    def add_env_var(self, env_var: EnvironmentVariable):
        """添加环境变量"""
        self.table.add_env_var(env_var)
        self._update_stats()
        
    def update_env_var(self, env_var: EnvironmentVariable):
        """更新环境变量"""
        self.table.update_env_var(env_var)
        
    def remove_env_var(self, env_var: EnvironmentVariable):
        """移除环境变量"""
        self.table.remove_env_var(env_var)
        self._update_stats()
        
    def refresh(self):
        """刷新表格"""
        self.table._refresh_table()
        self._update_stats()
        
    def _update_stats(self):
        """更新统计信息"""
        total = len(self.table.get_env_vars())
        selected = len(self.table.get_selected_env_vars())
        
        if selected == 0:
            self.stats_label.setText(f"总计: {total} 个变量")
        else:
            self.stats_label.setText(f"已选择: {selected} 个变量 (总计: {total})") 
