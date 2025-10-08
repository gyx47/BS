# 前端组件实现指南

本目录包含了前端 React 组件。以下是需要实现的组件清单和说明。

## 已实现的组件

### Auth/Login.js ✅
用户登录组件，已完成实现。

### Auth/Register.js ✅
用户注册组件，已完成实现。

## 待实现的组件

### Gallery/Gallery.js
图片展示组件

**功能要求：**
- 网格布局展示图片（使用 Material-UI Grid）
- 响应式设计（手机/平板/桌面不同列数）
- 显示缩略图
- 点击放大查看原图
- 显示图片信息（文件名、尺寸、上传时间等）
- 显示和管理标签
- 删除图片功能
- 分页或无限滚动

**参考实现思路：**
```javascript
import React, { useState, useEffect } from 'react';
import { Grid, Card, CardMedia, CardContent, Chip, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { imageAPI } from '../../services/api';

function Gallery() {
  const [images, setImages] = useState([]);
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadImages();
  }, [page]);

  const loadImages = async () => {
    const response = await imageAPI.getImages(page);
    setImages(response.data.images);
  };

  const handleDelete = async (imageId) => {
    if (window.confirm('确定要删除这张图片吗？')) {
      await imageAPI.deleteImage(imageId);
      loadImages();
    }
  };

  return (
    <Grid container spacing={2}>
      {images.map(image => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={image.id}>
          <Card>
            <CardMedia
              component="img"
              height="200"
              image={imageAPI.getThumbnailUrl(image.filename)}
              alt={image.original_name}
            />
            <CardContent>
              <Typography>{image.original_name}</Typography>
              {image.tags.map(tag => (
                <Chip key={tag.id} label={tag.name} size="small" />
              ))}
              <IconButton onClick={() => handleDelete(image.id)}>
                <DeleteIcon />
              </IconButton>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
}
```

---

### Upload/Upload.js
图片上传组件

**功能要求：**
- 拖拽上传（使用 react-dropzone）
- 点击选择文件
- 多文件上传
- 显示上传进度
- 预览待上传的图片
- 上传成功/失败提示

**参考实现思路：**
```javascript
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, LinearProgress, Typography } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { imageAPI } from '../../services/api';

function Upload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = async (acceptedFiles) => {
    setUploading(true);
    
    for (const file of acceptedFiles) {
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        await imageAPI.upload(formData);
        setProgress(prev => prev + (100 / acceptedFiles.length));
      } catch (error) {
        console.error('上传失败:', error);
      }
    }
    
    setUploading(false);
    setProgress(0);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif']
    }
  });

  return (
    <Box
      {...getRootProps()}
      sx={{
        border: '2px dashed #ccc',
        borderRadius: 2,
        p: 4,
        textAlign: 'center',
        cursor: 'pointer'
      }}
    >
      <input {...getInputProps()} />
      <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main' }} />
      <Typography>
        {isDragActive ? '放开以上传文件' : '拖拽文件到此处或点击选择'}
      </Typography>
      {uploading && <LinearProgress variant="determinate" value={progress} />}
    </Box>
  );
}
```

---

### Search/Search.js
搜索组件

**功能要求：**
- 关键词搜索输入框
- 标签多选（使用 Autocomplete）
- 日期范围选择器
- 相机型号输入
- 搜索按钮
- 显示搜索结果
- 清空搜索条件

**参考实现思路：**
```javascript
import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Autocomplete,
  Box,
  Grid
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { searchAPI } from '../../services/api';

function Search() {
  const [keyword, setKeyword] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [allTags, setAllTags] = useState([]);
  const [results, setResults] = useState([]);

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    const response = await searchAPI.getAllTags();
    setAllTags(response.data.tags);
  };

  const handleSearch = async () => {
    const tagNames = selectedTags.map(tag => tag.name).join(',');
    const response = await searchAPI.search(keyword, tagNames);
    setResults(response.data.images);
  };

  return (
    <Box>
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="搜索关键词"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <Autocomplete
            multiple
            options={allTags}
            getOptionLabel={(option) => option.name}
            value={selectedTags}
            onChange={(e, newValue) => setSelectedTags(newValue)}
            renderInput={(params) => (
              <TextField {...params} label="选择标签" />
            )}
          />
        </Grid>
        <Grid item xs={12}>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={handleSearch}
          >
            搜索
          </Button>
        </Grid>
      </Grid>
      
      {/* 显示搜索结果 */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        {results.map(image => (
          <Grid item xs={12} sm={6} md={4} key={image.id}>
            {/* 图片卡片 */}
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

---

## 组件集成

### 更新 App.js

需要在 `App.js` 中导入并使用这些组件：

```javascript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Gallery from './components/Gallery/Gallery';
import Upload from './components/Upload/Upload';
import Search from './components/Search/Search';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/gallery" element={<Gallery />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/search" element={<Search />} />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
```

---

## 路由保护

需要实现路由保护，防止未登录用户访问受保护的页面：

```javascript
// 创建 PrivateRoute.js
import { Navigate } from 'react-router-dom';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    return <Navigate to="/login" />;
  }
  
  return children;
}

// 在 App.js 中使用
<Route 
  path="/gallery" 
  element={
    <PrivateRoute>
      <Gallery />
    </PrivateRoute>
  } 
/>
```

---

## 导航栏组件

建议创建一个导航栏组件用于页面导航：

```javascript
// Navbar.js
import React from 'react';
import { AppBar, Toolbar, Button, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          图片管理
        </Typography>
        <Button color="inherit" onClick={() => navigate('/gallery')}>
          图库
        </Button>
        <Button color="inherit" onClick={() => navigate('/upload')}>
          上传
        </Button>
        <Button color="inherit" onClick={() => navigate('/search')}>
          搜索
        </Button>
        <Button color="inherit" onClick={handleLogout}>
          退出
        </Button>
      </Toolbar>
    </AppBar>
  );
}
```

---

## 移动端优化

### 响应式布局

使用 Material-UI 的 Grid 系统：

```javascript
<Grid container spacing={2}>
  <Grid item xs={12} sm={6} md={4} lg={3}>
    {/* xs: 手机 12列（全宽） */}
    {/* sm: 平板 6列（半宽） */}
    {/* md: 小桌面 4列（1/3宽） */}
    {/* lg: 大桌面 3列（1/4宽） */}
  </Grid>
</Grid>
```

### 移动端菜单

使用 Drawer 组件创建侧边栏菜单：

```javascript
import { Drawer, List, ListItem, IconButton } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';

function MobileMenu() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <IconButton onClick={() => setOpen(true)}>
        <MenuIcon />
      </IconButton>
      <Drawer open={open} onClose={() => setOpen(false)}>
        <List>
          <ListItem button onClick={() => navigate('/gallery')}>
            图库
          </ListItem>
          {/* 更多菜单项 */}
        </List>
      </Drawer>
    </>
  );
}
```

---

## 测试

### 单元测试示例

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import Login from './Login';

test('renders login form', () => {
  render(<Login />);
  expect(screen.getByLabelText(/用户名/i)).toBeInTheDocument();
});

test('shows error for short password', () => {
  render(<Login />);
  const passwordInput = screen.getByLabelText(/密码/i);
  fireEvent.change(passwordInput, { target: { value: '123' } });
  fireEvent.submit(screen.getByRole('button'));
  expect(screen.getByText(/密码至少6个字符/i)).toBeInTheDocument();
});
```

---

## 参考资源

- [React 文档](https://react.dev/)
- [Material-UI 文档](https://mui.com/)
- [React Router 文档](https://reactrouter.com/)
- [React Dropzone 文档](https://react-dropzone.js.org/)
- [Axios 文档](https://axios-http.com/)

---

## 开发流程

1. ✅ 实现登录和注册组件（已完成）
2. 实现图库展示组件
3. 实现上传组件
4. 实现搜索组件
5. 添加导航栏
6. 添加路由保护
7. 移动端测试和优化
8. 编写单元测试

祝开发顺利！
