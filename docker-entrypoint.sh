#!/bin/bash
# 数据库初始化入口脚本

set -e

echo "等待MySQL服务就绪..."
# 使用可配置的 DB_HOST 并在客户端禁用 SSL 校验（容器间使用自签证书时会触发 TLS 验证失败）
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD:-rootpassword}
DB_HOST=${DB_HOST:-mysql}
until mysqladmin ping -h "$DB_HOST" -u root -p"${DB_ROOT_PASSWORD}" --silent --skip-ssl 2>/dev/null \
  || mysqladmin ping -h "$DB_HOST" -u root --silent --skip-ssl 2>/dev/null; do
  echo "MySQL未就绪，等待5秒..."
  sleep 5
done

echo "MySQL已就绪，初始化数据库..."

# 执行数据库初始化
python -c "
from server import app, db
with app.app_context():
    try:
        db.create_all()
        print('数据库表创建完成')
    except Exception as e:
        print(f'数据库初始化警告: {e}')
        print('继续启动服务...')
"

echo "启动后端服务..."
exec python server.py

