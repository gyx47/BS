import axios from 'axios';

// API 基础 URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加 JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // 如果是 401 错误且有 refresh token，尝试刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (err) {
          // 刷新失败，清除 token 并跳转到登录页
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(err);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// 认证 API
export const authAPI = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),
  
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  
  refresh: () =>
    api.post('/auth/refresh'),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
};

// 图片 API
export const imageAPI = {
  upload: (formData) =>
    api.post('/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  getImages: (page = 1, perPage = 20) =>
    api.get('/images', { params: { page, per_page: perPage } }),
  
  getImage: (imageId) =>
    api.get(`/images/${imageId}`),
  
  deleteImage: (imageId) =>
    api.delete(`/images/${imageId}`),
  
  addTag: (imageId, tag) =>
    api.post(`/images/${imageId}/tags`, { tag }),
  
  removeTag: (imageId, tagId) =>
    api.delete(`/images/${imageId}/tags/${tagId}`),
  
  getImageUrl: (filename) =>
    `${API_BASE_URL}/images/file/${filename}`,
  
  getThumbnailUrl: (filename) =>
    `${API_BASE_URL}/images/thumbnail/${filename}`,
};

// 搜索 API
export const searchAPI = {
  search: (query, page = 1, perPage = 20) =>
    api.get('/search', { params: { q: query, page, per_page: perPage } }),
  
  searchByTags: (tags, page = 1, perPage = 20) =>
    api.get('/search', { params: { tags, page, per_page: perPage } }),
  
  searchByDate: (startDate, endDate, page = 1, perPage = 20) =>
    api.get('/search/by-date', { 
      params: { start: startDate, end: endDate, page, per_page: perPage } 
    }),
  
  getAllTags: () =>
    api.get('/search/tags'),
  
  searchByExif: (camera, page = 1, perPage = 20) =>
    api.get('/search/by-exif', { params: { camera, page, per_page: perPage } }),
};

export default api;
