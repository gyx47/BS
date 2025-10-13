# 图片管理网站

一个基于React和Python Flask的现代化图片管理平台，支持图片上传、存储、编辑、AI分析和智能搜索功能。

## 功能特性

### 基础功能
- ✅ 用户注册、登录功能（用户名、密码、邮箱验证）
- ✅ 图片上传（支持拖拽上传，多种格式）
- ✅ EXIF信息自动提取（时间、地点、相机信息等）
- ✅ 自定义标签系统
- ✅ 缩略图自动生成
- ✅ 数据库存储和查询
- ✅ 多条件搜索和筛选
- ✅ 友好的图片展示界面
- ✅ 图片轮播播放
- ✅ 图片编辑功能（裁剪、色调调整、旋转、翻转）
- ✅ 图片删除功能
- ✅ 移动端适配

### 增强功能
- ✅ AI图片内容分析（对象识别、场景分类、颜色分析）
- ✅ MCP接口支持大模型对话检索
- ✅ 响应式设计，支持手机浏览器

## 技术栈

### 后端
- **Python Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **MySQL** - 关系型数据库
- **Pillow** - 图片处理
- **OpenCV** - 计算机视觉分析
- **EXIFRead** - 图片元数据提取
- **JWT** - 用户认证

### 前端
- **React 18** - 用户界面框架
- **React Router** - 路由管理
- **Axios** - HTTP客户端
- **React Dropzone** - 文件上传
- **React Color** - 颜色选择器
- **Framer Motion** - 动画效果
- **React Icons** - 图标库

### 数据库
- **MySQL** - 主数据库
- 支持用户、图片、标签、相册等表结构

## 项目结构

```
photo-management/
├── backend/
│   ├── server.py              # Flask后端服务器
│   ├── requirements.txt       # Python依赖
│   └── database_schema.sql    # 数据库结构
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/            # 页面组件
│   │   ├── contexts/         # 状态管理
│   │   └── App.js
│   └── package.json
├── mcp_server.py             # MCP接口服务器
└── README.md
```

## 安装和运行

### 1. 数据库设置

```sql
-- 创建数据库
CREATE DATABASE photo_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入数据库结构
mysql -u root -p photo_management < database_schema.sql
```

### 2. 后端设置

```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置数据库连接（修改server.py中的数据库URL）
# 启动后端服务器
python server.py
```

### 3. 前端设置

```bash
# 安装Node.js依赖
npm install

# 启动开发服务器
npm start
```

### 4. MCP服务器（可选）

```bash
# 安装MCP依赖
pip install mcp

# 启动MCP服务器
python mcp_server.py
```

## 主要功能说明

### 1. 用户认证
- 用户注册：用户名、密码、邮箱验证
- 用户登录：JWT令牌认证
- 密码加密存储

### 2. 图片管理
- **上传功能**：支持拖拽上传，多种图片格式
- **EXIF提取**：自动提取拍摄时间、地点、相机信息
- **缩略图生成**：自动生成300x300缩略图
- **标签系统**：支持自定义标签和AI自动标签

### 3. 图片编辑
- **基础调整**：亮度、对比度、饱和度、色相
- **变换操作**：旋转、翻转
- **滤镜效果**：模糊、锐化、增亮等
- **撤销重做**：支持操作历史记录

### 4. AI分析功能
- **内容识别**：基于文件名和OpenCV分析
- **颜色分析**：主要颜色检测
- **场景分类**：风景、人物、建筑等
- **自动标签**：AI生成的智能标签

### 5. 搜索和筛选
- **关键词搜索**：文件名、地点搜索
- **标签筛选**：按标签分类查看
- **排序功能**：按时间、大小、名称排序
- **分页加载**：支持大量图片的分页显示

### 6. MCP接口
- **工具调用**：搜索照片、获取详情、AI分析
- **资源访问**：照片列表、标签列表
- **大模型集成**：支持与大模型对话检索图片

## API接口

### 用户认证
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录

### 图片管理
- `POST /api/upload` - 上传图片
- `GET /api/photos` - 获取图片列表
- `GET /api/photo/:id` - 获取图片
- `GET /api/thumbnail/:id` - 获取缩略图
- `DELETE /api/photo/:id` - 删除图片

### 图片编辑
- `POST /api/photo/:id/edit` - 编辑图片

### AI分析
- `POST /api/photo/:id/analyze` - AI分析图片

## 部署说明

### 生产环境配置
1. 修改数据库连接配置
2. 设置JWT密钥
3. 配置文件存储路径
4. 启用HTTPS
5. 配置反向代理（Nginx）

### 移动端适配
- 响应式设计，支持各种屏幕尺寸
- 触摸友好的交互界面
- 移动端优化的上传体验

## 开发说明

### 添加新功能
1. 后端：在`server.py`中添加新的API端点
2. 前端：在`src/pages/`或`src/components/`中添加新组件
3. 数据库：更新`database_schema.sql`

### 自定义AI分析
在`analyze_image_with_ai`函数中集成真实的AI服务：
- OpenAI Vision API
- Google Vision API
- Azure Computer Vision
- 本地AI模型

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题，请通过GitHub Issues联系。
