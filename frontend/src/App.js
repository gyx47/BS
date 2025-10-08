import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// 组件（需要创建）
// import Login from './components/Auth/Login';
// import Register from './components/Auth/Register';
// import Gallery from './components/Gallery/Gallery';
// import Upload from './components/Upload/Upload';
// import Search from './components/Search/Search';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div className="App">
          <h1 style={{ textAlign: 'center', padding: '20px' }}>
            图片管理网站
          </h1>
          <p style={{ textAlign: 'center' }}>
            前端应用框架已搭建完成。请实现各个组件：
          </p>
          <ul style={{ maxWidth: '600px', margin: '0 auto' }}>
            <li>登录/注册组件 (Auth/Login.js, Auth/Register.js)</li>
            <li>图片展示组件 (Gallery/Gallery.js)</li>
            <li>上传组件 (Upload/Upload.js)</li>
            <li>搜索组件 (Search/Search.js)</li>
            <li>API 服务 (services/api.js)</li>
          </ul>
          {/* 
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/gallery" element={<Gallery />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/search" element={<Search />} />
            <Route path="/" element={<Navigate to="/login" />} />
          </Routes>
          */}
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
