# 部署指南

## 本地开发环境部署

### 前置要求

- Python 3.8 或更高版本
- Node.js 14 或更高版本
- npm 或 yarn

### 后端部署

1. **克隆项目并进入后端目录**

```bash
cd backend
```

2. **创建虚拟环境**

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **初始化数据库**

```bash
python init_db.py
```

这将创建 SQLite 数据库文件 `imagedb.sqlite` 和所有必要的表。

5. **运行后端服务**

```bash
python app.py
```

后端服务将在 `http://localhost:5000` 启动。

### 前端部署

1. **进入前端目录**

```bash
cd frontend
```

2. **安装依赖**

```bash
npm install
# 或使用 yarn
yarn install
```

3. **启动开发服务器**

```bash
npm start
# 或使用 yarn
yarn start
```

前端应用将在 `http://localhost:3000` 启动，并自动在浏览器中打开。

### 验证安装

1. 访问 `http://localhost:3000` 查看前端应用
2. 访问 `http://localhost:5000` 查看 API 根端点
3. 访问 `http://localhost:5000/health` 检查后端健康状态

---

## 生产环境部署

### 使用 Docker（推荐）

#### 1. 创建 Dockerfile（后端）

在 `backend/` 目录创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads thumbnails

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

#### 2. 创建 Dockerfile（前端）

在 `frontend/` 目录创建 `Dockerfile`：

```dockerfile
FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. 创建 docker-compose.yml

在项目根目录创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/imagedb
      - SECRET_KEY=your-secret-key-here
      - JWT_SECRET_KEY=your-jwt-secret-here
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/thumbnails:/app/thumbnails
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: mysql:8
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=imagedb
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

volumes:
  mysql_data:
```

#### 4. 启动服务

```bash
docker-compose up -d
```

---

### 传统服务器部署

#### 后端部署（使用 Gunicorn + Nginx）

1. **安装 Gunicorn**

```bash
pip install gunicorn
```

2. **创建 Gunicorn 配置文件** `gunicorn_config.py`

```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
```

3. **启动 Gunicorn**

```bash
gunicorn -c gunicorn_config.py app:create_app()
```

4. **配置 Nginx 反向代理**

创建 `/etc/nginx/sites-available/imagesite` 配置文件：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        try_files $uri /index.html;
    }

    # API 请求
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 文件上传大小限制
        client_max_body_size 20M;
    }

    # 图片文件
    location /api/images/file {
        proxy_pass http://localhost:5000;
        proxy_cache_valid 200 1d;
        proxy_cache_bypass $http_pragma;
    }
}
```

5. **启用站点配置**

```bash
sudo ln -s /etc/nginx/sites-available/imagesite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 使用 Systemd 管理服务

创建 `/etc/systemd/system/imagesite.service`：

```ini
[Unit]
Description=Image Management Site
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start imagesite
sudo systemctl enable imagesite
```

---

### MySQL 数据库部署

1. **安装 MySQL**

```bash
# Ubuntu/Debian
sudo apt-get install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

2. **创建数据库和用户**

```sql
CREATE DATABASE imagedb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'imageuser'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON imagedb.* TO 'imageuser'@'localhost';
FLUSH PRIVILEGES;
```

3. **导入数据库结构**

```bash
mysql -u imageuser -p imagedb < database/schema.sql
```

4. **修改后端配置**

在 `backend/` 目录创建 `.env` 文件：

```env
DATABASE_URL=mysql://imageuser:secure_password@localhost/imagedb
SECRET_KEY=your-very-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

5. **安装 MySQL 驱动**

```bash
pip install pymysql
```

在 `backend/app.py` 顶部添加：

```python
import pymysql
pymysql.install_as_MySQLdb()
```

---

## 云平台部署

### Heroku 部署

#### 后端部署

1. **创建 `Procfile`**

```
web: gunicorn app:create_app()
```

2. **创建 `runtime.txt`**

```
python-3.9.16
```

3. **部署**

```bash
heroku create your-app-name
heroku addons:create cleardb:ignite  # MySQL 数据库
git push heroku main
```

#### 前端部署（Netlify）

1. **构建命令**：`npm run build`
2. **发布目录**：`build/`
3. **环境变量**：
   ```
   REACT_APP_API_URL=https://your-backend.herokuapp.com/api
   ```

### AWS 部署

#### 使用 EC2

1. 启动 EC2 实例（Ubuntu 20.04）
2. 配置安全组（开放 80, 443 端口）
3. 按照传统服务器部署步骤操作

#### 使用 S3 + CloudFront（前端）

1. 构建前端：`npm run build`
2. 上传到 S3 bucket
3. 配置 S3 静态网站托管
4. 创建 CloudFront 分发

#### 使用 RDS（数据库）

1. 创建 MySQL RDS 实例
2. 配置安全组允许 EC2 访问
3. 更新后端的 `DATABASE_URL`

### Azure 部署

#### 使用 App Service

1. 创建 Web App（Python 3.9）
2. 配置应用设置（环境变量）
3. 通过 Git 或 ZIP 部署

```bash
az webapp up --name your-app-name --runtime "PYTHON|3.9"
```

---

## 性能优化

### 后端优化

1. **使用 Redis 缓存**

```bash
pip install redis flask-caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.cached(timeout=300)
def get_popular_tags():
    return Tag.query.all()
```

2. **数据库连接池**

```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

3. **异步任务处理**（使用 Celery）

```bash
pip install celery redis
```

```python
# 用于处理耗时的图片处理任务
celery = Celery(app.name, broker='redis://localhost:6379/0')

@celery.task
def process_image_async(image_id):
    # 图片处理逻辑
    pass
```

### 前端优化

1. **代码分割**

```javascript
const Gallery = lazy(() => import('./components/Gallery/Gallery'));
```

2. **图片懒加载**

```javascript
import LazyLoad from 'react-lazyload';

<LazyLoad height={200}>
  <img src={imageUrl} alt="..." />
</LazyLoad>
```

3. **PWA 配置**

```bash
npm install --save-dev workbox-webpack-plugin
```

---

## 监控和日志

### 后端日志

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 错误监控（Sentry）

```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
)
```

---

## 安全配置

### HTTPS 配置（Let's Encrypt）

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 环境变量管理

**永不将敏感信息提交到 Git！**

使用 `.env` 文件（已在 .gitignore 中）：

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=mysql://user:pass@host/db
```

---

## 备份策略

### 数据库备份

```bash
# MySQL 备份
mysqldump -u user -p imagedb > backup_$(date +%Y%m%d).sql

# 恢复
mysql -u user -p imagedb < backup_20240101.sql
```

### 文件备份

```bash
# 备份上传的图片
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/ thumbnails/

# 自动化备份（crontab）
0 2 * * * /path/to/backup_script.sh
```

---

## 故障排查

### 常见问题

1. **端口已被占用**

```bash
# 查找占用端口的进程
lsof -i :5000
# 或
netstat -tulpn | grep 5000

# 杀死进程
kill -9 <PID>
```

2. **数据库连接失败**

- 检查数据库服务是否运行
- 验证连接字符串是否正确
- 检查防火墙设置

3. **文件上传失败**

- 检查上传目录权限
- 验证 `MAX_CONTENT_LENGTH` 设置
- 查看 Nginx 的 `client_max_body_size`

4. **前端无法访问后端**

- 检查 CORS 配置
- 验证 API URL 是否正确
- 检查防火墙和安全组设置

---

## 维护建议

1. **定期更新依赖**

```bash
pip list --outdated
npm outdated
```

2. **监控磁盘空间**

```bash
df -h
du -sh uploads/ thumbnails/
```

3. **日志轮转**

使用 `logrotate` 管理日志文件大小

4. **性能监控**

- 使用 New Relic, DataDog 等 APM 工具
- 监控数据库查询性能
- 定期检查慢查询日志

---

## 总结

按照本指南，你可以：

✅ 在本地搭建完整的开发环境  
✅ 将应用部署到生产服务器  
✅ 使用 Docker 容器化部署  
✅ 部署到云平台（AWS, Azure, Heroku）  
✅ 配置 HTTPS 和安全设置  
✅ 实施备份和监控策略  

如有问题，请参考各平台的官方文档或提交 Issue。
