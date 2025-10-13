#!/usr/bin/env python3
"""
后端服务器启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import sqlalchemy
        import PIL
        import exifread
        import cv2
        import numpy
        print("✅ 所有Python依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_database():
    """检查数据库连接"""
    try:
        from server import app, db
        print("SQLAlchemy URI =", app.config['SQLALCHEMY_DATABASE_URI'])
        with app.app_context():
            db.create_all()
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请检查MySQL服务是否启动，并确保数据库配置正确")
        return False

def create_directories():
    """创建必要的目录"""
    directories = ['uploads', 'thumbnails']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def start_server():
    """启动服务器"""
    print("🚀 启动图片管理后端服务器...")
    print("📍 服务器地址: http://localhost:5000")
    print("📚 API文档: http://localhost:5000/api")
    print("按 Ctrl+C 停止服务器")
    
    try:
        from server import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

def main():
    """主函数"""
    load_dotenv()
    print("=" * 50)
    print("🖼️  图片管理网站 - 后端服务器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 检查数据库
    if not check_database():
        print("\n💡 提示:")
        print("1. 确保MySQL服务正在运行")
        print("2. 创建数据库: CREATE DATABASE photo_management;")
        print("3. 导入数据库结构: mysql -u root -p photo_management < database_schema.sql")
        sys.exit(1)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
