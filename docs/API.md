# API 文档

## 基础信息

- **基础 URL**: `http://localhost:5000/api`
- **认证方式**: JWT (JSON Web Token)
- **内容类型**: `application/json` (文件上传时使用 `multipart/form-data`)

## 认证 (Authentication)

### 1. 用户注册

**端点**: `POST /auth/register`

**请求体**:
```json
{
  "username": "用户名（至少6个字符）",
  "email": "email@example.com",
  "password": "密码（至少6个字符）"
}
```

**响应**:
```json
{
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "email@example.com",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**状态码**:
- `201`: 注册成功
- `400`: 验证失败（用户名/密码长度不足、邮箱格式错误、用户名/邮箱已存在）

---

### 2. 用户登录

**端点**: `POST /auth/login`

**请求体**:
```json
{
  "username": "用户名或邮箱",
  "password": "密码"
}
```

**响应**:
```json
{
  "message": "登录成功",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "用户名",
    "email": "email@example.com",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**状态码**:
- `200`: 登录成功
- `401`: 用户名或密码错误

---

### 3. 刷新令牌

**端点**: `POST /auth/refresh`

**请求头**:
```
Authorization: Bearer {refresh_token}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 4. 获取当前用户信息

**端点**: `GET /auth/me`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "username": "用户名",
  "email": "email@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

---

## 图片管理 (Images)

### 1. 上传图片

**端点**: `POST /images/upload`

**请求头**:
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**请求体**:
```
file: [图片文件]
```

**响应**:
```json
{
  "message": "上传成功",
  "image": {
    "id": 1,
    "user_id": 1,
    "filename": "abc123.jpg",
    "original_name": "photo.jpg",
    "file_path": "/path/to/file",
    "thumbnail_path": "/path/to/thumbnail",
    "width": 1920,
    "height": 1080,
    "file_size": 524288,
    "mime_type": "image/jpeg",
    "exif_data": "{...}",
    "upload_time": "2024-01-01T00:00:00",
    "tags": [
      {"id": 1, "name": "date:2024-01-01"}
    ]
  }
}
```

**状态码**:
- `201`: 上传成功
- `400`: 文件类型不支持或没有上传文件

---

### 2. 获取图片列表

**端点**: `GET /images?page=1&per_page=20`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "images": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

---

### 3. 获取图片详情

**端点**: `GET /images/{image_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "user_id": 1,
  "filename": "abc123.jpg",
  "original_name": "photo.jpg",
  ...
}
```

---

### 4. 删除图片

**端点**: `DELETE /images/{image_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "message": "删除成功"
}
```

---

### 5. 添加标签

**端点**: `POST /images/{image_id}/tags`

**请求头**:
```
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "tag": "风景"
}
```

**响应**:
```json
{
  "message": "标签添加成功",
  "image": {...}
}
```

---

### 6. 删除标签

**端点**: `DELETE /images/{image_id}/tags/{tag_id}`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "message": "标签删除成功"
}
```

---

### 7. 获取图片文件

**端点**: `GET /images/file/{filename}`

直接返回图片文件（用于 `<img>` 标签的 src）

---

### 8. 获取缩略图

**端点**: `GET /images/thumbnail/{filename}`

直接返回缩略图文件

---

## 搜索 (Search)

### 1. 搜索图片

**端点**: `GET /search?q=keyword&tags=tag1,tag2&start_date=2024-01-01&end_date=2024-12-31&page=1&per_page=20`

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
- `q`: 关键词（搜索文件名）
- `tags`: 标签（逗号分隔）
- `start_date`: 开始日期（ISO 8601 格式）
- `end_date`: 结束日期（ISO 8601 格式）
- `page`: 页码
- `per_page`: 每页数量

**响应**:
```json
{
  "images": [...],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### 2. 获取所有标签

**端点**: `GET /search/tags`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "tags": [
    {"id": 1, "name": "风景", "created_at": "2024-01-01T00:00:00"},
    {"id": 2, "name": "人物", "created_at": "2024-01-01T00:00:00"}
  ]
}
```

---

### 3. 按日期搜索

**端点**: `GET /search/by-date?start=2024-01-01&end=2024-12-31&page=1&per_page=20`

**请求头**:
```
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "images": [...],
  "total": 30,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

---

### 4. 按 EXIF 信息搜索

**端点**: `GET /search/by-exif?camera=Canon&page=1&per_page=20`

**请求头**:
```
Authorization: Bearer {access_token}
```

**查询参数**:
- `camera`: 相机型号

**响应**:
```json
{
  "images": [...],
  "total": 25,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

---

## 错误响应

所有错误响应都遵循以下格式：

```json
{
  "error": "错误描述信息"
}
```

常见状态码：
- `400`: 请求参数错误
- `401`: 未授权（未登录或 token 失效）
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 使用示例

### Python 示例

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

# 搜索图片
response = requests.get('http://localhost:5000/api/search?q=风景', 
                       headers=headers)
```

### JavaScript 示例

```javascript
// 登录
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    password: 'password123'
  })
});
const { access_token } = await response.json();

// 上传图片
const formData = new FormData();
formData.append('file', fileInput.files[0]);

await fetch('http://localhost:5000/api/images/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
```
