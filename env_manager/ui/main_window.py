"""
主窗口模块

应用程序的主界面窗口。
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QSplitter, 
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QLineEdit, QPushButton, QComboBox, QGroupBox,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon

from ..utils.config import ConfigManager
from ..utils.constants import (
    APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, SHORTCUTS
)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 自定义信号
    env_changed = Signal()  # 环境变量变更信号
    
    def __init__(self):
        super().__init__()
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化UI
        self._init_ui()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._setup_shortcuts()
        
        # 恢复窗口状态
        self._restore_window_state()
        
        # 设置窗口事件处理
        self._setup_event_handlers()
        
        # 初始化状态
        self._update_status("准备就绪")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建搜索区域
        search_group = self._create_search_area()
        main_layout.addWidget(search_group)
        
        # 创建主要内容区域
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter)
        
        # 设置焦点
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _create_search_area(self) -> QGroupBox:
        """创建搜索区域"""
        search_group = QGroupBox("搜索和筛选")
        search_layout = QHBoxLayout(search_group)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索环境变量名称或值...")
        self.search_input.setClearButtonEnabled(True)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_input)
        
        # 搜索类型选择
        self.search_type = QComboBox()
        self.search_type.addItems(["变量名", "变量值", "全部"])
        self.search_type.setCurrentText("全部")
        search_layout.addWidget(QLabel("类型:"))
        search_layout.addWidget(self.search_type)
        
        # 环境变量类型筛选
        self.env_type_filter = QComboBox()
        self.env_type_filter.addItems(["全部", "系统变量", "用户变量"])
        self.env_type_filter.setCurrentText("全部")
        search_layout.addWidget(QLabel("范围:"))
        search_layout.addWidget(self.env_type_filter)
        
        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.clear_search_button = QPushButton("清除")
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_search_button)
        
        search_layout.addStretch()
        
        return search_group
    
    def _create_content_area(self) -> QSplitter:
        """创建主要内容区域"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：环境变量列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 环境变量表格
        self.env_table = QTableWidget()
        self.env_table.setColumnCount(3)
        self.env_table.setHorizontalHeaderLabels(["变量名", "变量值", "类型"])
        self.env_table.horizontalHeader().setStretchLastSection(True)
        self.env_table.setAlternatingRowColors(True)
        self.env_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.env_table)
        
        # 右侧：详细信息和操作面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 详细信息组
        info_group = QGroupBox("详细信息")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("选择一个环境变量查看详细信息")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        info_layout.addWidget(self.info_label)
        
        right_layout.addWidget(info_group)
        
        # 操作按钮组
        actions_group = QGroupBox("操作")
        actions_layout = QVBoxLayout(actions_group)
        
        self.new_button = QPushButton("新建变量")
        self.edit_button = QPushButton("编辑变量")
        self.delete_button = QPushButton("删除变量")
        self.duplicate_button = QPushButton("复制变量")
        self.refresh_button = QPushButton("刷新列表")
        
        # 设置按钮状态
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.duplicate_button.setEnabled(False)
        
        actions_layout.addWidget(self.new_button)
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)
        actions_layout.addWidget(self.duplicate_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_button)
        
        right_layout.addWidget(actions_group)
        right_layout.addStretch()
        
        # 将左右部件添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 300])  # 设置初始大小比例
        
        return splitter
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建
        new_action = QAction("新建变量(&N)", self)
        new_action.setShortcut(QKeySequence(SHORTCUTS['NEW']))
        new_action.setStatusTip("创建新的环境变量")
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        # 导入
        import_action = QAction("导入(&I)", self)
        import_action.setShortcut(QKeySequence(SHORTCUTS['IMPORT']))
        import_action.setStatusTip("从文件导入环境变量")
        file_menu.addAction(import_action)
        
        # 导出
        export_action = QAction("导出(&E)", self)
        export_action.setShortcut(QKeySequence(SHORTCUTS['EXPORT']))
        export_action.setStatusTip("导出环境变量到文件")
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence(SHORTCUTS['QUIT']))
        quit_action.setStatusTip("退出应用程序")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 编辑
        edit_action = QAction("编辑变量(&E)", self)
        edit_action.setShortcut(QKeySequence(SHORTCUTS['EDIT']))
        edit_action.setStatusTip("编辑选中的环境变量")
        edit_menu.addAction(edit_action)
        
        # 删除
        delete_action = QAction("删除变量(&D)", self)
        delete_action.setShortcut(QKeySequence(SHORTCUTS['DELETE']))
        delete_action.setStatusTip("删除选中的环境变量")
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        # 查找
        find_action = QAction("查找(&F)", self)
        find_action.setShortcut(QKeySequence(SHORTCUTS['FIND']))
        find_action.setStatusTip("查找环境变量")
        edit_menu.addAction(find_action)
        
        # 刷新
        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut(QKeySequence(SHORTCUTS['REFRESH']))
        refresh_action.setStatusTip("刷新环境变量列表")
        edit_menu.addAction(refresh_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 显示系统变量
        show_system_action = QAction("显示系统变量", self)
        show_system_action.setCheckable(True)
        show_system_action.setChecked(True)
        view_menu.addAction(show_system_action)
        
        # 显示用户变量
        show_user_action = QAction("显示用户变量", self)
        show_user_action.setCheckable(True)
        show_user_action.setChecked(True)
        view_menu.addAction(show_user_action)
        
        view_menu.addSeparator()
        
        # 切换主题
        theme_menu = view_menu.addMenu("主题")
        light_theme_action = QAction("浅色主题", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(True)
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("深色主题", self)
        dark_theme_action.setCheckable(True)
        theme_menu.addAction(dark_theme_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # PATH编辑器
        path_editor_action = QAction("PATH编辑器(&P)", self)
        path_editor_action.setStatusTip("打开PATH变量专用编辑器")
        tools_menu.addAction(path_editor_action)
        
        # 备份管理
        backup_action = QAction("备份管理(&B)", self)
        backup_action.setStatusTip("管理环境变量备份")
        tools_menu.addAction(backup_action)
        
        tools_menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置(&S)", self)
        settings_action.setStatusTip("打开应用程序设置")
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 用户手册
        manual_action = QAction("用户手册(&M)", self)
        manual_action.setStatusTip("打开用户手册")
        help_menu.addAction(manual_action)
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于此应用程序")
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
        # 保存菜单动作引用
        self.menu_actions = {
            'new': new_action,
            'edit': edit_action,
            'delete': delete_action,
            'import': import_action,
            'export': export_action,
            'find': find_action,
            'refresh': refresh_action,
            'path_editor': path_editor_action,
            'backup': backup_action,
            'settings': settings_action
        }
    
    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 新建按钮
        new_action = QAction("新建", self)
        new_action.setStatusTip("创建新的环境变量")
        toolbar.addAction(new_action)
        
        # 编辑按钮
        edit_action = QAction("编辑", self)
        edit_action.setStatusTip("编辑选中的环境变量")
        edit_action.setEnabled(False)
        toolbar.addAction(edit_action)
        
        # 删除按钮
        delete_action = QAction("删除", self)
        delete_action.setStatusTip("删除选中的环境变量")
        delete_action.setEnabled(False)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # 导入按钮
        import_action = QAction("导入", self)
        import_action.setStatusTip("从文件导入环境变量")
        toolbar.addAction(import_action)
        
        # 导出按钮
        export_action = QAction("导出", self)
        export_action.setStatusTip("导出环境变量到文件")
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # PATH编辑器按钮
        path_editor_action = QAction("PATH编辑器", self)
        path_editor_action.setStatusTip("打开PATH变量专用编辑器")
        toolbar.addAction(path_editor_action)
        
        # 备份按钮
        backup_action = QAction("备份", self)
        backup_action.setStatusTip("管理环境变量备份")
        toolbar.addAction(backup_action)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.setStatusTip("刷新环境变量列表")
        toolbar.addAction(refresh_action)
        
        # 保存工具栏动作引用
        self.toolbar_actions = {
            'new': new_action,
            'edit': edit_action,
            'delete': delete_action,
            'import': import_action,
            'export': export_action,
            'path_editor': path_editor_action,
            'backup': backup_action,
            'refresh': refresh_action
        }
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 主要状态标签
        self.status_label = QLabel("准备就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 添加分隔符
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 环境变量计数
        self.env_count_label = QLabel("环境变量: 0")
        self.status_bar.addPermanentWidget(self.env_count_label)
        
        # 添加分隔符
        self.status_bar.addPermanentWidget(QLabel("|"))
        
        # 当前时间
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # 创建定时器更新时间
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)  # 每秒更新一次
        self._update_time()
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        # 连接快捷键到相应动作
        if hasattr(self, 'menu_actions'):
            for action_name, action in self.menu_actions.items():
                if action_name in ['new', 'edit', 'delete', 'import', 'export', 'find', 'refresh']:
                    # 这些动作将在后续实现中连接到具体的槽函数
                    pass
    
    def _setup_event_handlers(self):
        """设置事件处理器"""
        # 表格选择变化事件
        self.env_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # 搜索事件
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.clear_search_button.clicked.connect(self._on_clear_search_clicked)
        
        # 按钮点击事件
        self.new_button.clicked.connect(self._on_new_clicked)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.duplicate_button.clicked.connect(self._on_duplicate_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        window_config = self.config_manager.get_window_config()
        
        # 设置窗口大小，确保转换为整数类型
        width = int(window_config['width'])
        height = int(window_config['height'])
        self.resize(width, height)
        
        # 恢复窗口位置
        if window_config['position']:
            pos = window_config['position']
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                self.move(QPoint(int(pos[0]), int(pos[1])))
        
        # 恢复最大化状态
        if window_config['maximized']:
            self.showMaximized()
    
    def _save_window_state(self):
        """保存窗口状态"""
        is_maximized = self.isMaximized()
        
        if not is_maximized:
            size = self.size()
            pos = self.pos()
            self.config_manager.set_window_config(
                width=size.width(),
                height=size.height(),
                position=(pos.x(), pos.y())
            )
        
        self.config_manager.set_window_config(maximized=is_maximized)
    
    def _update_status(self, message: str):
        """更新状态栏消息"""
        self.status_label.setText(message)
    
    def _update_time(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
    
    def _update_env_count(self, count: int):
        """更新环境变量计数"""
        self.env_count_label.setText(f"环境变量: {count}")
    
    def _show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            f"<h3>{APP_NAME}</h3>"
            f"<p>版本: {APP_VERSION}</p>"
            f"<p>Windows环境变量管理工具</p>"
            f"<p>使用PySide6开发</p>"
        )
    
    # 事件处理方法
    def _on_selection_changed(self):
        """处理表格选择变化"""
        selected_items = self.env_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 更新按钮状态
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.duplicate_button.setEnabled(has_selection)
        
        # 更新工具栏按钮状态
        if hasattr(self, 'toolbar_actions'):
            self.toolbar_actions['edit'].setEnabled(has_selection)
            self.toolbar_actions['delete'].setEnabled(has_selection)
        
        # TODO: 更新详细信息显示
        if has_selection:
            # 获取选中行的信息
            row = self.env_table.currentRow()
            if row >= 0:
                name_item = self.env_table.item(row, 0)
                value_item = self.env_table.item(row, 1)
                type_item = self.env_table.item(row, 2)
                
                name = name_item.text() if name_item else ""
                value = value_item.text() if value_item else ""
                env_type = type_item.text() if type_item else ""
                
                info_text = f"<b>变量名:</b> {name}<br>"
                info_text += f"<b>类型:</b> {env_type}<br>"
                info_text += f"<b>变量值:</b><br>{value}"
                
                self.info_label.setText(info_text)
        else:
            self.info_label.setText("选择一个环境变量查看详细信息")
    
    def _on_search_text_changed(self):
        """处理搜索文本变化"""
        # TODO: 实现实时搜索功能
        pass
    
    def _on_search_clicked(self):
        """处理搜索按钮点击"""
        # TODO: 实现搜索功能
        search_text = self.search_input.text()
        self._update_status(f"搜索: {search_text}" if search_text else "显示所有变量")
    
    def _on_clear_search_clicked(self):
        """处理清除搜索按钮点击"""
        self.search_input.clear()
        self._update_status("显示所有变量")
    
    def _on_new_clicked(self):
        """处理新建按钮点击"""
        # TODO: 打开新建变量对话框
        self._update_status("新建环境变量...")
    
    def _on_edit_clicked(self):
        """处理编辑按钮点击"""
        # TODO: 打开编辑变量对话框
        self._update_status("编辑环境变量...")
    
    def _on_delete_clicked(self):
        """处理删除按钮点击"""
        # TODO: 确认并删除选中的环境变量
        self._update_status("删除环境变量...")
    
    def _on_duplicate_clicked(self):
        """处理复制按钮点击"""
        # TODO: 复制选中的环境变量
        self._update_status("复制环境变量...")
    
    def _on_refresh_clicked(self):
        """处理刷新按钮点击"""
        # TODO: 刷新环境变量列表
        self._update_status("刷新环境变量列表...")
    
    # 窗口事件处理
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 保存窗口状态
        self._save_window_state()
        
        # 询问是否确认退出
        if self.config_manager.get('general/confirm_exit', True):
            reply = QMessageBox.question(
                self,
                "确认退出",
                "确定要退出应用程序吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    def resizeEvent(self, event):
        """处理窗口大小变化事件"""
        super().resizeEvent(event)
        # 可以在这里添加窗口大小变化的处理逻辑
    
    def changeEvent(self, event):
        """处理窗口状态变化事件"""
        super().changeEvent(event)
        # 可以在这里处理窗口最小化、最大化等状态变化
