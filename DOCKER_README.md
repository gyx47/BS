# Docker 部署指南

## 快速开始

### 1. 前置要求

- Docker 20.10 或更高版本
- Docker Compose 1.29 或更高版本

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp env.example .env

# 编辑配置文件（至少修改数据库密码）
nano .env
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 访问系统

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:5000
- **MySQL数据库**: localhost:3306

### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（注意：会删除所有数据）
docker-compose down -v
```

## 服务说明

### MySQL 服务
- **容器名**: photo_mysql
- **数据持久化**: mysql_data 卷
- **自动初始化**: 自动执行 database_schema.sql

### 后端服务
- **容器名**: photo_backend
- **端口**: 5000
- **数据卷**: 
  - `./uploads` - 上传的图片
  - `./thumbnails` - 生成的缩略图
  - `./logs` - 日志文件

### 前端服务
- **容器名**: photo_frontend
- **端口**: 3000
- **Web服务器**: Nginx
- **API代理**: 自动代理 `/api` 请求到后端

## 环境变量配置

详细配置说明请参考 `env.example` 文件。

### 必需配置
- `DB_PASSWORD`: 数据库密码
- `DB_ROOT_PASSWORD`: MySQL root密码

### 可选配置
- `AI_PROVIDER`: AI服务提供商
- `ZHIPU_API_KEY`: 智谱AI密钥
- `OPENAI_API_KEY`: OpenAI密钥
- 等等...

## 数据备份

### 备份数据库
```bash
docker exec photo_mysql mysqldump -u root -p${DB_ROOT_PASSWORD} photo_management > backup.sql
```

### 备份上传文件
```bash
tar -czf uploads_backup.tar.gz uploads/ thumbnails/
```

## 故障排查

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 重建镜像
```bash
# 重新构建镜像
docker-compose build

# 重新构建并启动
docker-compose up -d --build
```

## 更多信息

详细的使用说明请参考：
- [使用手册.md](使用手册.md)
- [测试报告.md](测试报告.md)
- [开发体会.md](开发体会.md)
- [小结.md](小结.md)

