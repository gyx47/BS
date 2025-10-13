#!/bin/bash
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
