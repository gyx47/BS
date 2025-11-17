import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiUpload, FiImage, FiTrendingUp, FiClock, FiTag } from 'react-icons/fi';
import axios from 'axios';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalPhotos: 0,
    totalSize: 0,
    recentPhotos: 0,
    totalTags: 0
  });
  const [recentPhotos, setRecentPhotos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // 获取统计数据
      const commonHeaders = { headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` } };
      const statsResponse = await axios.get('/api/photos?page=1&per_page=1', commonHeaders);
      const photosResponse = await axios.get('/api/photos?page=1&per_page=6', commonHeaders);
      const tagsResponse = await axios.get('/api/tags', commonHeaders);
      
      const totalPhotos = statsResponse.data.total;
      const totalSize = statsResponse.data.photos.reduce((sum, photo) => sum + photo.file_size, 0);
      const recentPhotos = photosResponse.data.photos;
      const totalTags = tagsResponse.data.tags.length;
      
      setStats({
        totalPhotos,
        totalSize,
        recentPhotos: recentPhotos.length,
        totalTags
      });
      
      setRecentPhotos(recentPhotos);
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const StatCard = ({ icon: Icon, title, value, color, link }) => (
    <div className="stat-card">
      <div className="stat-icon" style={{ backgroundColor: color }}>
        <Icon />
      </div>
      <div className="stat-content">
        <h3 className="stat-value">{value}</h3>
        <p className="stat-title">{title}</p>
      </div>
      {link && (
        <Link to={link} className="stat-link">
          查看详情 →
        </Link>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  const token = localStorage.getItem('token') || '';

  const getThumbnailSrc = (photoId) => {
    if (!token) return `/api/thumbnail/${photoId}`;
    return `/api/thumbnail/${photoId}?token=${encodeURIComponent(token)}`;
  };

  return (
    <div className="dashboard-container">
      <div className="container">
        <div className="dashboard-header">
          <h1>我的相册</h1>
          <p>管理您的照片收藏</p>
        </div>

        {/* 统计卡片 */}
        <div className="stats-grid">
          <StatCard
            icon={FiImage}
            title="总照片数"
            value={stats.totalPhotos}
            color="#007bff"
            link="/gallery"
          />
          <StatCard
            icon={FiTrendingUp}
            title="存储空间"
            value={formatFileSize(stats.totalSize)}
            color="#28a745"
          />
          <StatCard
            icon={FiClock}
            title="最近上传"
            value={stats.recentPhotos}
            color="#ffc107"
            link="/gallery"
          />
          <StatCard
            icon={FiTag}
            title="标签数量"
            value={stats.totalTags}
            color="#6f42c1"
          />
        </div>

        {/* 快速操作 */}
        <div className="quick-actions">
          <h2>快速操作</h2>
          <div className="actions-grid">
            <Link to="/upload" className="action-card primary">
              <div className="action-icon">
                <FiUpload />
              </div>
              <div className="action-content">
                <h3>上传照片</h3>
                <p>添加新的照片到您的相册</p>
              </div>
            </Link>
            
            <Link to="/gallery" className="action-card">
              <div className="action-icon">
                <FiImage />
              </div>
              <div className="action-content">
                <h3>浏览相册</h3>
                <p>查看和管理您的照片</p>
              </div>
            </Link>
          </div>
        </div>

        {/* 最近照片 */}
        {recentPhotos.length > 0 && (
          <div className="recent-photos">
            <div className="section-header">
              <h2>最近上传</h2>
              <Link to="/gallery" className="view-all-link">
                查看全部 →
              </Link>
            </div>
            <div className="photos-grid">
              {recentPhotos.map((photo) => (
                <div key={photo.id} className="photo-item">
                  <div className="photo-thumbnail">
                    <img 
                      src={getThumbnailSrc(photo.id)} 
                      alt={photo.original_filename}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src =
                          'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjgwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iODAiIGZpbGw9IiNFRkVGRTgiIHJ4PSIxMiIvPjxwYXRoIGQ9Ik02MCA1MC4yNWMtOC4zNCAwLTE1LjAzLTYuNjktMTUuMDMtMTUuMDNTNTEuNjYgMjAuMTggNjAgMjAuMThzMTUuMDMgNi42OSAxNS4wMyAxNS4wMy02LjY5IDE1LjA0LTE1LjAzIDE1LjA0bTAtMzUuMjVjLTExLjA4IDAtMjAuMTggOS4xLTIwLjE4IDIwLjE4UzQ4LjkyIDU1LjQ2IDYwIDU1LjQ2czIwLjE4LTkuMSAyMC4xOC0yMC4xOC05LjEtMjAuMTgtMjAuMTgtMjAuMThaIiBmaWxsPSIjQ0NDIi8+PC9zdmc+';
                      }}
                    />
                  </div>
                  <div className="photo-info">
                    <h4 className="photo-title" title={photo.original_filename}>
                      {photo.original_filename}
                    </h4>
                    <div className="photo-meta">
                      {photo.taken_at && (
                        <span className="photo-date">
                          {new Date(photo.taken_at).toLocaleDateString()}
                        </span>
                      )}
                      {photo.location && (
                        <span className="photo-location">
                          📍 {photo.location}
                        </span>
                      )}
                    </div>
                    <div className="photo-tags">
                      {photo.tags.slice(0, 3).map((tag, index) => (
                        <span key={index} className="tag">
                          #{tag}
                        </span>
                      ))}
                      {photo.tags.length > 3 && (
                        <span className="tag more">
                          +{photo.tags.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 空状态 */}
        {stats.totalPhotos === 0 && (
          <div className="empty-state">
            <div className="empty-icon">
              <FiImage />
            </div>
            <h3>还没有照片</h3>
            <p>开始上传您的第一张照片吧！</p>
            <Link to="/upload" className="btn btn-primary">
              立即上传
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
