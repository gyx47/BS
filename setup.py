#!/usr/bin/env python3
"""
项目初始化设置脚本
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_env_file():
    """创建环境配置文件"""
    env_content = """# 图片管理网站环境配置

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=photo_management

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=24

# 文件上传配置
UPLOAD_FOLDER=uploads
THUMBNAIL_FOLDER=thumbnails
MAX_CONTENT_LENGTH=16777216

# 服务器配置
HOST=0.0.0.0
PORT=5000
DEBUG=True
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ 创建环境配置文件: .env")

def create_gitignore():
    """创建.gitignore文件"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 虚拟环境
venv/
env/
ENV/

# 环境变量
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# 数据库
*.db
*.sqlite3

# 上传文件
uploads/
thumbnails/

# 日志
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# React
build/
.env.local
.env.development.local
.env.test.local
.env.production.local

# 临时文件
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ 创建.gitignore文件")

def create_directories():
    """创建必要的目录"""
    directories = [
        'uploads',
        'thumbnails',
        'logs',
        'static',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {sys.version}")
    return True

def install_python_dependencies():
    """安装Python依赖"""
    print("📦 安装Python依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Python依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Python依赖安装失败: {e}")
        return False

def create_database_script():
    """创建数据库初始化脚本"""
    script_content = """#!/bin/bash
# 数据库初始化脚本

echo "🗄️  初始化数据库..."

# 检查MySQL是否运行
if ! pgrep -x "mysqld" > /dev/null; then
    echo "❌ MySQL服务未运行，请先启动MySQL"
    exit 1
fi

# 创建数据库
echo "📝 创建数据库..."
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS photo_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入数据库结构
echo "📋 导入数据库结构..."
mysql -u root -p photo_management < database_schema.sql

echo "✅ 数据库初始化完成"
echo "📍 数据库: photo_management"
echo "🔗 连接: mysql -u root -p photo_management"
"""
    
    with open('init_database.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod('init_database.sh', 0o755)
    print("✅ 创建数据库初始化脚本: init_database.sh")

def create_start_scripts():
    """创建启动脚本"""
    # 后端启动脚本
    backend_script = """#!/bin/bash
# 后端服务器启动脚本

echo "🚀 启动后端服务器..."
python start_backend.py
"""
    
    with open('start_backend.sh', 'w', encoding='utf-8') as f:
        f.write(backend_script)
    os.chmod('start_backend.sh', 0o755)
    print("✅ 创建后端启动脚本: start_backend.sh")
    
    # 前端启动脚本
    frontend_script = """#!/bin/bash
# 前端开发服务器启动脚本

echo "🚀 启动前端开发服务器..."
python start_frontend.py
"""
    
    with open('start_frontend.sh', 'w', encoding='utf-8') as f:
        f.write(frontend_script)
    os.chmod('start_frontend.sh', 0o755)
    print("✅ 创建前端启动脚本: start_frontend.sh")

def main():
    """主函数"""
    print("=" * 60)
    print("🖼️  图片管理网站 - 项目初始化")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 创建配置文件
    create_env_file()
    create_gitignore()
    
    # 创建数据库脚本
    create_database_script()
    
    # 创建启动脚本
    create_start_scripts()
    
    # 安装Python依赖
    if not install_python_dependencies():
        print("\n💡 请手动运行: pip install -r requirements.txt")
    
    print("\n" + "=" * 60)
    print("🎉 项目初始化完成！")
    print("=" * 60)
    print("\n📋 下一步操作:")
    print("1. 配置数据库连接 (修改 .env 文件)")
    print("2. 初始化数据库: ./init_database.sh")
    print("3. 启动后端: ./start_backend.sh")
    print("4. 启动前端: ./start_frontend.sh")
    print("\n🔗 访问地址:")
    print("   - 前端: http://localhost:3000")
    print("   - 后端: http://localhost:5000")
    print("\n📚 更多信息请查看 README.md")

if __name__ == "__main__":
    main()
