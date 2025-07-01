"""
搜索组件

实现环境变量的搜索和过滤功能。
"""

import re
from typing import List, Dict, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, 
    QLabel, QPushButton, QCheckBox, QCompleter, QGroupBox,
    QButtonGroup, QRadioButton, QFrame, QToolButton, QMenu,
    QWidgetAction, QSpinBox, QSlider, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer, QStringListModel, QSettings
from PySide6.QtGui import QAction, QIcon, QFont

from ...utils.constants import SEARCH_TYPES
from ...utils.logger import get_logger


class SearchHistoryManager:
    """搜索历史管理器"""
    
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.settings = QSettings()
        self._load_history()
        
    def _load_history(self):
        """加载搜索历史"""
        self.history = self.settings.value("search/history", [], list)
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
            
    def add_search(self, query: str):
        """添加搜索记录"""
        if not query.strip():
            return
            
        # 如果已存在，移动到最前面
        if query in self.history:
            self.history.remove(query)
        
        self.history.insert(0, query)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
            
        self._save_history()
        
    def get_history(self) -> List[str]:
        """获取搜索历史"""
        return self.history.copy()
        
    def clear_history(self):
        """清除搜索历史"""
        self.history.clear()
        self._save_history()
        
    def _save_history(self):
        """保存搜索历史"""
        self.settings.setValue("search/history", self.history)


class AdvancedSearchDialog(QDialog):
    """高级搜索对话框"""
    
    search_requested = Signal(dict)  # 搜索请求信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级搜索")
        self.setModal(True)  # 设置为模态对话框
        self.setFixedSize(400, 300)
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 搜索条件组
        conditions_group = QGroupBox("搜索条件")
        conditions_layout = QVBoxLayout(conditions_group)
        
        # 搜索类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("搜索范围:"))
        self.search_type = QComboBox()
        self.search_type.addItems(["变量名", "变量值", "全部"])
        type_layout.addWidget(self.search_type)
        conditions_layout.addLayout(type_layout)
        
        # 环境变量类型
        env_type_layout = QHBoxLayout()
        env_type_layout.addWidget(QLabel("变量类型:"))
        self.env_type = QComboBox()
        self.env_type.addItems(["全部", "系统变量", "用户变量"])
        env_type_layout.addWidget(self.env_type)
        conditions_layout.addLayout(env_type_layout)
        
        # 搜索选项
        self.case_sensitive = QCheckBox("区分大小写")
        self.whole_word = QCheckBox("全字匹配")
        self.regex_search = QCheckBox("正则表达式")
        
        conditions_layout.addWidget(self.case_sensitive)
        conditions_layout.addWidget(self.whole_word)
        conditions_layout.addWidget(self.regex_search)
        
        layout.addWidget(conditions_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("搜索")
        self.clear_button = QPushButton("清除")
        self.close_button = QPushButton("关闭")
        
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.search_button.clicked.connect(self._on_search)
        self.clear_button.clicked.connect(self._on_clear)
        self.close_button.clicked.connect(self.close)
        
    def _on_search(self):
        """处理搜索"""
        search_params = {
            'search_type': self.search_type.currentText(),
            'env_type': self.env_type.currentText(),
            'case_sensitive': self.case_sensitive.isChecked(),
            'whole_word': self.whole_word.isChecked(),
            'regex_search': self.regex_search.isChecked()
        }
        
        self.search_requested.emit(search_params)
        self.close()
        
    def _on_clear(self):
        """清除设置"""
        self.search_type.setCurrentIndex(0)
        self.env_type.setCurrentIndex(0)
        self.case_sensitive.setChecked(False)
        self.whole_word.setChecked(False)
        self.regex_search.setChecked(False)


class SearchWidget(QWidget):
    """搜索组件"""
    
    # 信号定义
    search_changed = Signal(str, dict)  # 搜索文本和选项变化
    filter_changed = Signal(dict)  # 过滤条件变化
    search_cleared = Signal()  # 搜索清除
    textChanged = Signal(str)  # 搜索文本实时变化（便捷信号）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.history_manager = SearchHistoryManager()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self._current_search_options = {}
        self._setup_ui()
        self._setup_signals()
        self._load_settings()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 主搜索框区域
        main_search_layout = QHBoxLayout()
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索环境变量...")
        self.search_input.setClearButtonEnabled(True)
        
        # 设置搜索历史自动完成
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_input.setCompleter(self.completer)
        self._update_completer()
        
        main_search_layout.addWidget(self.search_input)
        
        # 搜索选项按钮
        self.options_button = QToolButton()
        self.options_button.setText("选项")
        self.options_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._setup_options_menu()
        main_search_layout.addWidget(self.options_button)
        
        # 高级搜索按钮
        self.advanced_button = QPushButton("高级")
        self.advanced_button.setMaximumWidth(50)
        main_search_layout.addWidget(self.advanced_button)
        
        layout.addLayout(main_search_layout)
        
        # 搜索统计和快速过滤
        stats_layout = QHBoxLayout()
        
        # 搜索结果统计
        self.result_label = QLabel("准备搜索")
        self.result_label.setStyleSheet("color: gray; font-size: 10px;")
        stats_layout.addWidget(self.result_label)
        
        stats_layout.addStretch()
        
        # 快速过滤按钮组
        self.quick_filter_group = QButtonGroup()
        
        self.all_filter = QRadioButton("全部")
        self.all_filter.setChecked(True)
        self.system_filter = QRadioButton("系统")
        self.user_filter = QRadioButton("用户")
        self.modified_filter = QRadioButton("已修改")
        
        self.quick_filter_group.addButton(self.all_filter, 0)
        self.quick_filter_group.addButton(self.system_filter, 1)
        self.quick_filter_group.addButton(self.user_filter, 2)
        self.quick_filter_group.addButton(self.modified_filter, 3)
        
        stats_layout.addWidget(self.all_filter)
        stats_layout.addWidget(self.system_filter)
        stats_layout.addWidget(self.user_filter)
        stats_layout.addWidget(self.modified_filter)
        
        layout.addLayout(stats_layout)
        
        # 高级搜索对话框将在需要时创建（懒加载）
        self.advanced_dialog = None
        
    def _setup_options_menu(self):
        """设置选项菜单"""
        menu = QMenu(self)
        
        # 搜索范围
        range_menu = menu.addMenu("搜索范围")
        
        self.search_name_action = QAction("搜索变量名", self)
        self.search_name_action.setCheckable(True)
        self.search_name_action.setChecked(True)
        range_menu.addAction(self.search_name_action)
        
        self.search_value_action = QAction("搜索变量值", self)
        self.search_value_action.setCheckable(True)
        self.search_value_action.setChecked(True)
        range_menu.addAction(self.search_value_action)
        
        menu.addSeparator()
        
        # 搜索选项
        self.case_sensitive_action = QAction("区分大小写", self)
        self.case_sensitive_action.setCheckable(True)
        menu.addAction(self.case_sensitive_action)
        
        self.whole_word_action = QAction("全字匹配", self)
        self.whole_word_action.setCheckable(True)
        menu.addAction(self.whole_word_action)
        
        self.regex_action = QAction("正则表达式", self)
        self.regex_action.setCheckable(True)
        menu.addAction(self.regex_action)
        
        menu.addSeparator()
        
        # 历史记录
        history_menu = menu.addMenu("搜索历史")
        self.history_menu = history_menu
        self._update_history_menu()
        
        menu.addSeparator()
        
        # 清除历史
        clear_history_action = QAction("清除历史记录", self)
        clear_history_action.triggered.connect(self._clear_history)
        menu.addAction(clear_history_action)
        
        self.options_button.setMenu(menu)
        
    def _setup_signals(self):
        """设置信号连接"""
        # 搜索输入变化
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._on_search_submit)
        
        # 高级搜索按钮
        self.advanced_button.clicked.connect(self._show_advanced_search)
        
        # 快速过滤
        self.quick_filter_group.buttonClicked.connect(self._on_quick_filter_changed)
        
        # 搜索选项变化
        self.search_name_action.toggled.connect(self._on_search_options_changed)
        self.search_value_action.toggled.connect(self._on_search_options_changed)
        self.case_sensitive_action.toggled.connect(self._on_search_options_changed)
        self.whole_word_action.toggled.connect(self._on_search_options_changed)
        self.regex_action.toggled.connect(self._on_search_options_changed)
        
    def _on_search_text_changed(self, text: str):
        """处理搜索文本变化"""
        # 发射文本变化信号
        self.textChanged.emit(text)
        
        # 延迟搜索，避免过于频繁
        self.search_timer.stop()
        if text.strip():
            self.search_timer.start(300)  # 300ms延迟
        else:
            self._perform_search()
            
    def _on_search_submit(self):
        """处理搜索提交"""
        text = self.search_input.text().strip()
        if text:
            self.history_manager.add_search(text)
            self._update_completer()
            self._update_history_menu()
            
        self._perform_search()
        
    def _perform_search(self):
        """执行搜索"""
        text = self.search_input.text().strip()
        options = self._get_current_search_options()
        
        if not text:
            self.result_label.setText("准备搜索")
            self.search_cleared.emit()
        else:
            self.search_changed.emit(text, options)
            
    def _get_current_search_options(self) -> Dict[str, Any]:
        """获取当前搜索选项"""
        return {
            'search_name': self.search_name_action.isChecked(),
            'search_value': self.search_value_action.isChecked(),
            'case_sensitive': self.case_sensitive_action.isChecked(),
            'whole_word': self.whole_word_action.isChecked(),
            'regex': self.regex_action.isChecked(),
            'quick_filter': self.quick_filter_group.checkedId()
        }
        
    def _on_search_options_changed(self):
        """处理搜索选项变化"""
        if self.search_input.text().strip():
            self._perform_search()
            
    def _on_quick_filter_changed(self):
        """处理快速过滤变化"""
        filter_type = self.quick_filter_group.checkedId()
        filter_params = {'quick_filter': filter_type}
        self.filter_changed.emit(filter_params)
        
        # 如果有搜索文本，重新搜索
        if self.search_input.text().strip():
            self._perform_search()
            
    def _show_advanced_search(self):
        """显示高级搜索对话框"""
        if self.advanced_dialog is None:
            self.advanced_dialog = AdvancedSearchDialog(self)
            # 连接高级搜索对话框的信号
            self.advanced_dialog.search_requested.connect(self._on_advanced_search)
        self.advanced_dialog.exec()
        
    def _on_advanced_search(self, params: Dict[str, Any]):
        """处理高级搜索"""
        self._current_search_options.update(params)
        text = self.search_input.text().strip()
        if text:
            self.search_changed.emit(text, self._current_search_options)
        else:
            self.filter_changed.emit(params)
        
    def _update_completer(self):
        """更新自动完成"""
        model = QStringListModel(self.history_manager.get_history())
        self.completer.setModel(model)
        
    def _update_history_menu(self):
        """更新历史记录菜单"""
        self.history_menu.clear()
        
        history = self.history_manager.get_history()
        if not history:
            action = QAction("无历史记录", self)
            action.setEnabled(False)
            self.history_menu.addAction(action)
            return
            
        for query in history[:10]:  # 只显示最近10条
            action = QAction(query, self)
            action.triggered.connect(lambda checked, q=query: self._use_history_query(q))
            self.history_menu.addAction(action)
            
    def _use_history_query(self, query: str):
        """使用历史搜索查询"""
        self.search_input.setText(query)
        self._perform_search()
        
    def _clear_history(self):
        """清除搜索历史"""
        self.history_manager.clear_history()
        self._update_completer()
        self._update_history_menu()
        
    def _load_settings(self):
        """加载设置"""
        settings = QSettings()
        
        # 搜索选项
        self.search_name_action.setChecked(
            settings.value("search/search_name", True, bool))
        self.search_value_action.setChecked(
            settings.value("search/search_value", True, bool))
        self.case_sensitive_action.setChecked(
            settings.value("search/case_sensitive", False, bool))
        self.whole_word_action.setChecked(
            settings.value("search/whole_word", False, bool))
        self.regex_action.setChecked(
            settings.value("search/regex", False, bool))
            
        # 快速过滤
        filter_id = settings.value("search/quick_filter", 0, int)
        if 0 <= filter_id < self.quick_filter_group.buttons().__len__():
            self.quick_filter_group.button(filter_id).setChecked(True)
            
    def _save_settings(self):
        """保存设置"""
        settings = QSettings()
        
        settings.setValue("search/search_name", self.search_name_action.isChecked())
        settings.setValue("search/search_value", self.search_value_action.isChecked())
        settings.setValue("search/case_sensitive", self.case_sensitive_action.isChecked())
        settings.setValue("search/whole_word", self.whole_word_action.isChecked())
        settings.setValue("search/regex", self.regex_action.isChecked())
        settings.setValue("search/quick_filter", self.quick_filter_group.checkedId())
        
    def set_search_text(self, text: str):
        """设置搜索文本"""
        self.search_input.setText(text)
        
    def get_search_text(self) -> str:
        """获取搜索文本"""
        return self.search_input.text()
    
    def text(self) -> str:
        """获取搜索文本（便捷方法）"""
        return self.search_input.text()
        
    def clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.result_label.setText("准备搜索")
        self.search_cleared.emit()
    
    def clear(self):
        """清除搜索（便捷方法）"""
        self.clear_search()
        
    def set_result_count(self, total: int, filtered: int):
        """设置搜索结果数量"""
        if total == filtered:
            self.result_label.setText(f"显示 {total} 个变量")
        else:
            self.result_label.setText(f"找到 {filtered} 个变量 (共 {total} 个)")
            
    def get_search_options(self) -> Dict[str, Any]:
        """获取搜索选项"""
        return self._get_current_search_options()
        
    def is_match(self, text: str, search_query: str, options: Dict[str, Any]) -> bool:
        """检查文本是否匹配搜索条件"""
        if not search_query:
            return True
            
        # 准备搜索文本
        search_text = text
        query = search_query
        
        if not options.get('case_sensitive', False):
            search_text = search_text.lower()
            query = query.lower()
            
        # 正则表达式搜索
        if options.get('regex', False):
            try:
                flags = 0 if options.get('case_sensitive', False) else re.IGNORECASE
                return bool(re.search(query, search_text, flags))
            except re.error:
                return False
                
        # 全字匹配
        if options.get('whole_word', False):
            import re
            pattern = r'\b' + re.escape(query) + r'\b'
            flags = 0 if options.get('case_sensitive', False) else re.IGNORECASE
            return bool(re.search(pattern, search_text, flags))
            
        # 普通搜索
        return query in search_text
        
    def closeEvent(self, event):
        """关闭事件处理"""
        self._save_settings()
        super().closeEvent(event) 
