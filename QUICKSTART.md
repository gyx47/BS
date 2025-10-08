# 快速开始指南

## 概述

这是一个完整的图片管理网站项目，包含：
- ✅ 后端 API（Python Flask）
- ✅ 前端应用（React）
- ✅ 数据库（SQLite/MySQL）
- ✅ 完整文档

## 5分钟快速启动

### 1. 启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动后端服务
python app.py
```

后端将在 `http://localhost:5000` 启动。

### 2. 启动前端

```bash
# 打开新终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动前端服务
npm start
```

前端将在 `http://localhost:3000` 启动并自动打开浏览器。

### 3. 测试

1. 访问 `http://localhost:3000`
2. 注册一个新账号
3. 登录系统
4. 上传图片
5. 搜索和浏览图片

## 项目结构

```
BS/
├── backend/              # Python 后端
│   ├── app.py           # Flask 应用
│   ├── models.py        # 数据库模型
│   ├── routes/          # API 路由
│   ├── utils/           # 工具函数
│   └── requirements.txt # Python 依赖
│
├── frontend/            # React 前端
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── services/    # API 服务
│   │   └── App.js       # 应用主组件
│   └── package.json     # Node 依赖
│
├── database/            # 数据库脚本
│   ├── schema.sql       # 表结构
│   └── init_data.sql    # 初始数据
│
└── docs/               # 文档
    ├── API.md          # API 文档
    ├── IMPLEMENTATION.md  # 实现思路
    └── DEPLOYMENT.md   # 部署指南
```

## 核心功能

### 已实现 ✅

1. **用户认证**
   - 注册（用户名/密码/邮箱验证）
   - 登录（JWT 令牌认证）
   - 令牌刷新

2. **图片管理**
   - 上传图片
   - 查看图片列表
   - 删除图片
   - 查看图片详情

3. **EXIF 处理**
   - 自动提取 EXIF 信息
   - 提取拍摄时间、GPS、相机信息
   - 自动生成标签

4. **缩略图**
   - 自动生成缩略图
   - 保持宽高比
   - 优化加载性能

5. **标签系统**
   - 添加自定义标签
   - 删除标签
   - 标签搜索

6. **搜索功能**
   - 关键词搜索
   - 标签搜索
   - 日期范围搜索
   - EXIF 信息搜索

### 待完善 🚧

以下组件提供了实现思路和示例代码，需要进一步完善：

1. **前端组件**
   - ✅ Login/Register 组件（已实现）
   - 🚧 Gallery 组件（需要实现）
   - 🚧 Upload 组件（需要实现）
   - 🚧 Search 组件（需要实现）

2. **增强功能**
   - AI 图片分析（文档中提供实现方案）
   - MCP 接口（文档中提供实现思路）

## 开发指南

### 后端开发

- 查看 `docs/API.md` 了解 API 端点
- 查看 `docs/IMPLEMENTATION.md` 了解实现细节
- 修改 `backend/.env.example` 并重命名为 `.env` 配置环境变量

### 前端开发

- 查看 `frontend/src/components/README.md` 了解组件实现指南
- 已实现的组件：
  - `Auth/Login.js` - 登录组件
  - `Auth/Register.js` - 注册组件
- 参考示例代码实现剩余组件

### 数据库

- SQLite（默认）：无需配置，自动创建
- MySQL：修改 `.env` 中的 `DATABASE_URL`

## API 测试

### 使用 curl

```bash
# 注册
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# 上传图片（需要替换 TOKEN）
curl -X POST http://localhost:5000/api/images/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

### 使用 Python

```python
import requests

# 注册
response = requests.post('http://localhost:5000/api/auth/register', json={
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'password123'
})

# 登录
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'testuser',
    'password': 'password123'
})
token = response.json()['access_token']

# 上传图片
headers = {'Authorization': f'Bearer {token}'}
files = {'file': open('photo.jpg', 'rb')}
response = requests.post('http://localhost:5000/api/images/upload', 
                        headers=headers, files=files)
```

## 常见问题

### 后端问题

**Q: 端口 5000 被占用**
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Q: 数据库初始化失败**
```bash
# 删除旧数据库
rm backend/imagedb.sqlite

# 重新初始化
cd backend
python init_db.py
```

**Q: 依赖安装失败**
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存后重新安装
pip cache purge
pip install -r requirements.txt
```

### 前端问题

**Q: npm install 失败**
```bash
# 清理缓存
npm cache clean --force

# 删除 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install
```

**Q: 无法连接到后端**
- 确认后端服务正在运行
- 检查 `frontend/package.json` 的 proxy 配置
- 检查 CORS 设置

## 下一步

1. **完善前端组件**
   - 实现 Gallery 组件
   - 实现 Upload 组件
   - 实现 Search 组件

2. **增强功能**
   - 集成 AI 图片分析
   - 实现 MCP 接口
   - 添加更多 EXIF 信息显示

3. **优化**
   - 图片懒加载
   - 分页优化
   - 缓存策略

4. **部署**
   - 参考 `docs/DEPLOYMENT.md`
   - 配置生产环境
   - 设置 HTTPS

## 文档索引

- 📘 [API 文档](docs/API.md) - 所有 API 端点说明
- 📗 [实现思路](docs/IMPLEMENTATION.md) - 详细的实现方案和架构说明
- 📕 [部署指南](docs/DEPLOYMENT.md) - 本地/生产环境部署
- 📙 [前端组件指南](frontend/src/components/README.md) - React 组件实现

## 技术支持

- 查看文档目录下的详细说明
- 参考示例代码
- 阅读相关技术文档

## 许可证

MIT License

---

**祝您开发顺利！** 🚀
