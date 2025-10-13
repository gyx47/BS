#!/usr/bin/env python3
"""
前端开发服务器启动脚本
"""

import os
import sys, shutil
import subprocess
import json
from pathlib import Path

def check_node():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js版本: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def check_npm():
    """检查npm是否安装"""
    try:
        npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")

        if not npm_cmd:
            print("❌ npm未安装或未加入PATH")
            sys.exit(1)
        npm_version = subprocess.run([npm_cmd, "-v"], capture_output=True, text=True)
        if npm_version.returncode != 0:
            print("❌ npm未安装")
            return False
        else:
            print(f"✅ npm版本: {npm_version.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("❌ npm未安装")
        return False
def install_dependencies():
    """安装前端依赖"""
    from pathlib import Path
    
    if not Path('package.json').exists():
        print("❌ 未找到package.json文件")
        return False
    
    print("📦 安装前端依赖...")

    # ✅ 自动检测 npm 可执行文件
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("❌ 未检测到 npm，请确认 npm 已加入系统 PATH。")
        return False

    try:
        result = subprocess.run([npm_cmd, 'install'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 依赖安装完成")
            return True
        else:
            print(f"❌ 依赖安装失败:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
# def install_dependencies():
#     """安装前端依赖"""
#     if not Path('package.json').exists():
#         print("❌ 未找到package.json文件")
#         return False
    
#     print("📦 安装前端依赖...")
#     try:
#         result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
#         if result.returncode == 0:
#             print("✅ 依赖安装完成")
#             return True
#         else:
#             print(f"❌ 依赖安装失败: {result.stderr}")
#             return False
#     except Exception as e:
#         print(f"❌ 依赖安装失败: {e}")
#         return False

def start_dev_server():
    """启动开发服务器"""
    print("🚀 启动React开发服务器...")
    print("📍 前端地址: http://localhost:3000")
    print("🔗 后端代理: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    
    try:
        subprocess.run(['npm', 'start'])
    except KeyboardInterrupt:
        print("\n👋 开发服务器已停止")
    except Exception as e:
        print(f"❌ 开发服务器启动失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("🖼️  图片管理网站 - 前端开发服务器")
    print("=" * 50)
    
    # 检查Node.js
    if not check_node():
        print("\n💡 请安装Node.js: https://nodejs.org/")
        sys.exit(1)
    
    # 检查npm
    if not check_npm():
        print("\n💡 请安装npm")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 启动开发服务器
    start_dev_server()

if __name__ == "__main__":
    main()
