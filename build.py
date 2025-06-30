#!/usr/bin/env python3
"""
构建脚本

用于构建Windows环境变量管理工具的可执行文件。
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse


def check_requirements():
    """检查构建依赖"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ 错误: 未安装PyInstaller")
        print("请运行: pip install pyinstaller")
        return False
    
    try:
        import PySide6
        print(f"✓ PySide6版本: {PySide6.__version__}")
    except ImportError:
        print("❌ 错误: 未安装PySide6")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理.pyc文件
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
        
        # 移除__pycache__目录
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))


def build_executable(debug=False, onefile=True):
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 构建参数
    args = [
        'pyinstaller',
        '--name=EnvManager',
        '--windowed',  # Windows应用，无控制台
        '--add-data=env_manager/resources;env_manager/resources',
    ]
    
    if onefile:
        args.append('--onefile')
    else:
        args.append('--onedir')
    
    if debug:
        args.append('--debug=all')
    else:
        args.append('--optimize=2')
    
    # 添加图标（如果存在）
    icon_path = Path('env_manager/resources/icons/app.ico')
    if icon_path.exists():
        args.append(f'--icon={icon_path}')
    
    # 主文件
    args.append('main.py')
    
    print(f"执行命令: {' '.join(args)}")
    
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
        print("✓ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def create_installer():
    """创建安装程序"""
    print("创建安装程序功能待实现...")
    # TODO: 使用NSIS或其他工具创建安装程序


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='构建环境变量管理工具')
    parser.add_argument('--clean', action='store_true', help='清理构建文件')
    parser.add_argument('--debug', action='store_true', help='调试模式构建')
    parser.add_argument('--onedir', action='store_true', help='构建为目录而非单文件')
    parser.add_argument('--installer', action='store_true', help='创建安装程序')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        print("清理完成！")
        return
    
    print("Windows环境变量管理工具 - 构建脚本")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        sys.exit(1)
    
    # 清理旧的构建文件
    clean_build()
    
    # 构建可执行文件
    onefile = not args.onedir
    if build_executable(debug=args.debug, onefile=onefile):
        print("\n构建完成！")
        
        # 显示输出文件位置
        if onefile:
            exe_path = Path('dist/EnvManager.exe')
            if exe_path.exists():
                print(f"可执行文件位置: {exe_path.absolute()}")
                print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            dist_dir = Path('dist/EnvManager')
            if dist_dir.exists():
                print(f"程序目录: {dist_dir.absolute()}")
        
        # 创建安装程序
        if args.installer:
            create_installer()
    
    else:
        print("\n构建失败！")
        sys.exit(1)


if __name__ == '__main__':
    main() 
