# Windows环境变量管理工具 (EnvManager)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)](https://pypi.org/project/PySide6/)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个基于PySide6的Windows环境变量管理工具，提供友好的图形界面来管理系统和用户环境变量。采用分阶段开发策略，首先完成功能完整的独立桌面应用，后续扩展插件化架构。

## ✨ 项目特点

- 🎯 **简洁易用** - 直观的图形界面，告别Windows原生的繁琐操作
- 🔧 **功能强大** - 支持环境变量的增删改查、批量操作、备份恢复
- 🚀 **快速启动** - 轻量级设计，3秒内启动，支持1000+环境变量管理
- 🛡️ **安全可靠** - 操作前自动备份，支持撤销重做，确保系统安全
- 📈 **分阶段交付** - 优先完成独立应用，后续扩展插件功能

## 🎯 功能特性

### 第一阶段：独立桌面应用
- **环境变量管理**
  - 分别查看和编辑系统/用户环境变量
  - 支持变量的添加、修改、删除操作
  - 特别优化的PATH变量编辑器
  - 实时搜索和过滤功能

- **批量操作**
  - 支持YAML格式的批量导入导出（默认推荐），同时兼容JSON、CSV、REG格式
  - 批量删除选中的环境变量
  - 从剪贴板快速添加变量

- **备份恢复**
  - 操作前自动创建快照
  - 手动备份和恢复功能
  - 备份历史管理和清理

- **桌面应用体验**
  - 完整的菜单栏和工具栏
  - 系统托盘集成
  - 键盘快捷键支持
  - 操作撤销/重做

### 第二阶段：插件化扩展
- **插件架构** - 支持集成到其他PySide6项目
- **标准接口** - 提供插件开发SDK
- **灵活集成** - 可嵌入的QWidget组件

## 🔧 系统要求

- **操作系统**: Windows 10/11
- **Python版本**: 3.8 或更高
- **运行权限**: 管理员权限（用于修改系统环境变量）

### 依赖库
```
PySide6 >= 6.0.0
PyYAML >= 6.0.0
```

## 📦 安装指南

### 方式一：直接运行（推荐）

1. **下载预编译版本**
   - 从 [Releases](https://github.com/Asheng008/envs-win/releases) 页面下载最新版本
   - 解压到任意目录
   - 以管理员权限运行 `EnvManager.exe`

### 方式二：从源码运行

1. **克隆仓库**
   ```cmd
   git clone https://github.com/Asheng008/envs-win.git
   cd envs-win
   ```

2. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```cmd
   python main.py
   ```

## 🚀 快速开始

### 基本使用

1. 启动程序后，界面分为"系统变量"和"用户变量"两个标签页
2. 使用顶部搜索框快速查找特定变量
3. 点击"新建"按钮添加新的环境变量
4. 双击变量行或选中后点击"编辑"按钮进行修改
5. 选择变量后点击"删除"按钮可删除变量

### 高级功能

- **PATH变量编辑**: 选择PATH变量后使用专用编辑器逐行编辑路径
- **批量操作**: 通过"文件"菜单进行批量导入导出
- **备份恢复**: 程序自动备份，也可通过"工具"菜单手动操作
- **系统托盘**: 最小化到系统托盘，快速访问常用功能

## 📁 项目结构

```
env_manager/
├── core/                    # 核心业务逻辑
│   ├── env_controller.py    # 环境变量控制器
│   ├── backup_controller.py # 备份控制器
│   ├── registry_ops.py      # 注册表操作封装
│   ├── validator.py         # 数据验证器
│   └── exceptions.py        # 自定义异常
├── ui/                      # 用户界面
│   ├── main_window.py       # 主窗口
│   ├── dialogs/             # 对话框
│   └── components/          # UI组件
├── models/                  # 数据模型
│   ├── env_model.py         # 环境变量数据模型
│   └── backup_model.py      # 备份数据模型
├── utils/                   # 工具模块
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志工具
│   ├── helpers.py           # 辅助函数
│   └── constants.py         # 常量定义
├── resources/               # 资源文件
├── tests/                   # 测试代码
├── main.py                  # 应用程序入口
├── build.py                 # 构建脚本
└── requirements.txt         # 依赖列表
```

## 🏗️ 架构设计

### 当前架构（第一阶段）
采用简化的MVC架构模式：

```
┌─────────────────────────────────────────────────────────────┐
│                    EnvManager.exe                           │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (用户界面层)                                       │
│  ├── MainWindow (主窗口)                                    │
│  ├── Dialogs (对话框)                                       │
│  └── Components (UI组件)                                    │
├─────────────────────────────────────────────────────────────┤
│  Controller Layer (控制器层)                                │
│  ├── EnvController (环境变量控制器)                          │
│  ├── BackupController (备份控制器)                          │
│  └── ValidationController (验证控制器)                      │
├─────────────────────────────────────────────────────────────┤
│  Model Layer (数据模型层)                                   │
│  ├── EnvModel (环境变量模型)                                │
│  └── BackupModel (备份模型)                                 │
├─────────────────────────────────────────────────────────────┤
│  Data Access Layer (数据访问层)                             │
│  ├── RegistryOps (注册表操作)                               │
│  ├── FileOps (文件操作)                                     │
│  └── ConfigManager (配置管理)                               │
└─────────────────────────────────────────────────────────────┘
```

### 扩展架构（第二阶段）
保持现有架构不变，增加插件化支持：

- **插件接口层**: 定义标准的插件接口
- **插件管理器**: 负责插件的加载和管理
- **事件总线**: 实现插件与主程序的通信

## 🧪 开发和测试

### 开发环境设置

```cmd
# 克隆项目
git clone https://github.com/Asheng008/envs-win.git
cd envs-win

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 构建可执行文件

```cmd
# 使用构建脚本
python build.py

# 或手动使用PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "resources;resources" main.py
```

### 运行测试

```cmd
# 运行单元测试
python -m pytest tests/

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=env_manager --cov-report=html
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能
- 📝 文档改进
- 🎨 UI/UX改进
- ⚡ 性能优化
- 🧪 测试覆盖

## 📋 开发路线图

### 第一阶段：独立应用（8周）
- [x] 项目结构搭建
- [x] 基础UI框架
- [ ] 环境变量CRUD操作
- [ ] 搜索和过滤功能
- [ ] 批量操作功能
- [ ] 备份恢复系统
- [ ] PATH编辑器
- [ ] 系统托盘集成
- [ ] 打包和发布

### 第二阶段：插件化扩展（4周）
- [ ] 插件接口设计
- [ ] 核心逻辑重构
- [ ] 插件管理器
- [ ] 插件SDK开发
- [ ] 文档和示例

### 未来计划
- [ ] 主题支持（深色/浅色）
- [ ] 多语言支持
- [ ] 自动更新功能
- [ ] 云同步功能

## ❓ 常见问题

### Q: 为什么需要管理员权限？
A: 修改系统环境变量需要管理员权限。如果只操作用户环境变量，可以普通权限运行。

### Q: 支持哪些Windows版本？
A: 支持Windows 10和Windows 11。理论上也兼容Windows 8.1，但未充分测试。

### Q: 如何备份现有的环境变量？
A: 程序会在重要操作前自动备份，您也可以通过"工具"菜单手动创建备份。

### Q: 可以撤销操作吗？
A: 是的，程序支持撤销/重做功能，也可以从自动备份中恢复。

### Q: 什么时候会提供插件功能？
A: 插件功能计划在第二阶段开发，预计独立应用完成后的4周内发布。

## 📊 性能指标

- **启动时间**: < 3秒
- **内存占用**: < 100MB
- **响应时间**: < 500ms
- **支持变量数**: 1000+

## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。

## 🙏 致谢

- [PySide6](https://pypi.org/project/PySide6/) - 优秀的Python GUI框架
- [PyYAML](https://pypi.org/project/PyYAML/) - 强大的YAML解析和生成库
- [Qt](https://www.qt.io/) - 强大的跨平台应用程序框架
- 所有贡献者和使用者

## 📞 联系方式

- 项目主页: https://github.com/Asheng008/envs-win
- 问题报告: https://github.com/Asheng008/envs-win/issues
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！ 
