# Windows环境变量管理工具 (EnvManager)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)](https://pypi.org/project/PySide6/)
[![Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个基于PySide6的Windows环境变量管理工具，提供友好的图形界面来管理系统和用户环境变量，支持独立运行和插件集成两种模式。

## ✨ 项目特点

- 🎯 **简洁易用** - 直观的图形界面，告别Windows原生的繁琐操作
- 🔧 **功能强大** - 支持环境变量的增删改查、批量操作、备份恢复
- 🔌 **插件化架构** - 可作为独立应用运行，也可集成到其他PySide6项目中
- 🛡️ **安全可靠** - 操作前自动备份，支持撤销重做，确保系统安全
- 🚀 **高性能** - 快速启动，流畅操作，支持1000+环境变量管理

## 🎯 功能特性

### 核心功能
- **环境变量管理**
  - 分别查看和编辑系统/用户环境变量
  - 支持变量的添加、修改、删除操作
  - 特别优化的PATH变量编辑器
  - 实时搜索和过滤功能

- **批量操作**
  - 支持JSON、CSV、REG格式的批量导入导出
  - 批量删除选中的环境变量
  - 从剪贴板快速添加变量

- **备份恢复**
  - 操作前自动创建快照
  - 手动备份和恢复功能
  - 备份历史管理和清理

- **高级功能**
  - 操作撤销/重做
  - 变量值有效性验证
  - 重复变量检测和清理
  - 使用统计和分析

### 插件化支持
- **独立运行模式** - 完整的桌面应用程序
- **插件集成模式** - 可嵌入的QWidget组件
- **标准插件接口** - 方便第三方集成

## 🔧 系统要求

- **操作系统**: Windows 10/11
- **Python版本**: 3.8 或更高
- **运行权限**: 管理员权限（用于修改系统环境变量）

### 依赖库
```
PySide6 >= 6.0.0
```

## 📦 安装指南

### 从源码安装

1. **克隆仓库**
   ```cmd
   git clone https://github.com/your-username/envs-win.git
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

### 使用预编译版本

1. 从 [Releases](https://github.com/your-username/envs-win/releases) 页面下载最新版本
2. 解压到任意目录
3. 以管理员权限运行 `EnvManager.exe`

## 🚀 快速开始

### 独立运行模式

```cmd
# 直接运行主程序
python main.py
```

### 插件集成模式

```python
from env_manager.plugin import EnvManagerPlugin

# 在您的PySide6应用中
plugin = EnvManagerPlugin()
plugin.initialize(host_context)
widget = plugin.get_widget()

# 将widget添加到您的界面中
layout.addWidget(widget)
```

## 📁 项目结构

```
env_manager/
├── core/                    # 核心业务逻辑
│   ├── env_manager.py       # 环境变量管理器
│   ├── registry_ops.py      # 注册表操作封装
│   ├── backup_manager.py    # 备份恢复管理
│   ├── validator.py         # 数据验证器
│   └── exceptions.py        # 自定义异常
├── ui/                      # 用户界面
│   ├── main_window.py       # 主窗口
│   ├── plugin_widget.py     # 插件组件
│   ├── dialogs/             # 对话框
│   └── components/          # UI组件
├── plugin/                  # 插件系统
│   ├── interface.py         # 插件接口定义
│   ├── manager.py           # 插件管理器
│   └── registry.py          # 插件注册表
├── utils/                   # 工具模块
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志工具
│   └── helpers.py           # 辅助函数
├── resources/               # 资源文件
├── tests/                   # 测试代码
├── main.py                  # 独立运行入口
├── plugin_entry.py          # 插件入口
└── requirements.txt         # 依赖列表
```

## 📖 使用指南

### 基本操作

1. **查看环境变量**
   - 启动程序后，可在"系统变量"和"用户变量"标签间切换
   - 使用搜索框快速查找特定变量

2. **添加环境变量**
   - 点击"新建"按钮
   - 输入变量名和变量值
   - 选择添加到系统变量或用户变量

3. **编辑环境变量**
   - 双击变量行或点击"编辑"按钮
   - 修改变量值后保存

4. **删除环境变量**
   - 选择要删除的变量
   - 点击"删除"按钮并确认

### 高级功能

1. **PATH变量编辑**
   - 选择PATH变量后点击"编辑"
   - 在专用的PATH编辑器中逐行编辑路径

2. **批量导入导出**
   - 使用"文件"菜单中的导入/导出功能
   - 支持JSON、CSV、REG格式

3. **备份恢复**
   - 程序会在重要操作前自动创建备份
   - 可通过"工具"菜单手动备份或恢复

## 🔌 插件开发

如果您想将EnvManager集成到自己的PySide6项目中，请参考以下接口：

```python
from env_manager.plugin.interface import IEnvPlugin

class YourEnvPlugin(IEnvPlugin):
    def initialize(self, host_context):
        # 初始化插件
        return True
    
    def get_widget(self):
        # 返回插件的主要Widget
        return self.main_widget
    
    def cleanup(self):
        # 清理资源
        pass
```

更多详细信息请参考 [插件开发指南](docs/plugin_development.md)。

## 🧪 开发和测试

### 开发环境设置

```cmd
# 克隆项目
git clone https://github.com/your-username/envs-win.git
cd envs-win

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 运行测试

```cmd
# 运行单元测试
python -m pytest tests/

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=env_manager
```

### 代码格式化

```cmd
# 使用black格式化代码
black env_manager/

# 使用flake8检查代码质量
flake8 env_manager/
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

- [x] 基础环境变量管理功能
- [x] 图形用户界面
- [ ] 批量操作功能
- [ ] 备份恢复系统
- [ ] 插件化架构
- [ ] 主题支持
- [ ] 多语言支持
- [ ] 自动更新功能

## ❓ 常见问题

### Q: 为什么需要管理员权限？
A: 修改系统环境变量需要管理员权限。如果只操作用户环境变量，可以普通权限运行。

### Q: 支持哪些Windows版本？
A: 支持Windows 10和Windows 11。理论上也兼容Windows 8.1，但未充分测试。

### Q: 如何备份现有的环境变量？
A: 程序会在重要操作前自动备份，您也可以通过"工具"菜单手动创建备份。

### Q: 可以撤销操作吗？
A: 是的，程序支持撤销/重做功能，也可以从自动备份中恢复。

## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。

## 🙏 致谢

- [PySide6](https://pypi.org/project/PySide6/) - 优秀的Python GUI框架
- [Qt](https://www.qt.io/) - 强大的跨平台应用程序框架
- 所有贡献者和使用者

## 📞 联系方式

- 项目主页: https://github.com/your-username/envs-win
- 问题报告: https://github.com/your-username/envs-win/issues
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！ 
