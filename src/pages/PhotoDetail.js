import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiEdit3, FiTrash2, FiDownload, FiShare2, FiCalendar, FiMapPin, FiTag, FiCamera, FiPlus } from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'react-toastify';
import './PhotoDetail.css';

const PhotoDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [imageLoading, setImageLoading] = useState(true);
  const [newTag, setNewTag] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchPhoto();
  }, [id]);

  const fetchPhoto = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/photos?page=1&per_page=1000`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      const foundPhoto = response.data.photos.find(p => p.id === parseInt(id));
      
      if (foundPhoto) {
        setPhoto(foundPhoto);
      } else {
        toast.error('照片不存在');
        navigate('/gallery');
      }
    } catch (error) {
      console.error('获取照片失败:', error);
      toast.error('获取照片失败');
      navigate('/gallery');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('确定要删除这张照片吗？')) {
      return;
    }

    try {
      await axios.delete(`/api/photo/${id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      toast.success('照片删除成功');
      navigate('/gallery');
    } catch (error) {
      console.error('删除照片失败:', error);
      toast.error('删除照片失败');
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = `/api/photo/${id}`;
    link.download = photo.original_filename;
    link.click();
  };

  const handleEdit = () => {
    navigate(`/photo/${id}/edit`);
  };

  const handleAddTag = async () => {
    const tag = newTag.trim();
    if (!tag) return;
    try {
      setAdding(true);
      await axios.post(`/api/photo/${id}/tags`, { tags: [tag] }, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      setPhoto({ ...photo, tags: [...(photo.tags || []), tag] });
      setNewTag('');
    } catch (e) {
      // no-op
    } finally {
      setAdding(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleString('zh-CN');
  };

  if (loading) {
    return (
      <div className="photo-detail-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!photo) {
    return (
      <div className="photo-detail-container">
        <div className="error-state">
          <h3>照片不存在</h3>
          <button onClick={() => navigate('/gallery')} className="btn btn-primary">
            返回相册
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="photo-detail-container">
      <div className="container">
        {/* 头部导航 */}
        <div className="detail-header">
          <button 
            onClick={() => navigate('/gallery')} 
            className="back-btn"
          >
            <FiArrowLeft />
            返回相册
          </button>
          
          <div className="header-actions">
            <button onClick={handleEdit} className="action-btn">
              <FiEdit3 />
              编辑
            </button>
            <button onClick={handleDownload} className="action-btn">
              <FiDownload />
              下载
            </button>
            <button onClick={() => {/* TODO: 分享功能 */}} className="action-btn">
              <FiShare2 />
              分享
            </button>
            <button onClick={handleDelete} className="action-btn danger">
              <FiTrash2 />
              删除
            </button>
          </div>
        </div>

        <div className="detail-content">
          {/* 图片区域 */}
          <div className="image-section">
            <div className="image-container">
              {imageLoading && (
                <div className="image-loading">
                  <div className="spinner"></div>
                </div>
              )}
              <img
                src={`/api/photo/${photo.id}?token=${localStorage.getItem('token') || ''}`}
                alt={photo.original_filename}
                className="detail-image"
                onLoad={() => setImageLoading(false)}
                onError={() => setImageLoading(false)}
              />
            </div>
          </div>

          {/* 信息面板 */}
          <div className="info-section">
            <div className="info-card">
              <h2 className="photo-title" title={photo.original_filename}>
                {photo.original_filename}
              </h2>
              
              <div className="photo-meta">
                <div className="meta-group">
                  <h3 className="meta-title">
                    <FiCamera className="meta-icon" />
                    基本信息
                  </h3>
                  <div className="meta-items">
                    <div className="meta-item">
                      <span className="meta-label">文件名:</span>
                      <span className="meta-value">{photo.original_filename}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">尺寸:</span>
                      <span className="meta-value">{photo.width} × {photo.height}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">文件大小:</span>
                      <span className="meta-value">{formatFileSize(photo.file_size)}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">上传时间:</span>
                      <span className="meta-value">{formatDate(photo.created_at)}</span>
                    </div>
                  </div>
                </div>

                {photo.taken_at && (
                  <div className="meta-group">
                    <h3 className="meta-title">
                      <FiCalendar className="meta-icon" />
                      拍摄信息
                    </h3>
                    <div className="meta-items">
                      <div className="meta-item">
                        <span className="meta-label">拍摄时间:</span>
                        <span className="meta-value">{formatDate(photo.taken_at)}</span>
                      </div>
                      {photo.location && (
                        <div className="meta-item">
                          <span className="meta-label">拍摄地点:</span>
                          <span className="meta-value">
                            <FiMapPin className="location-icon" />
                            {photo.location}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="meta-group">
                  <h3 className="meta-title">
                    <FiTag className="meta-icon" />
                    标签
                  </h3>
                  <div className="tags-container" style={{ marginBottom: 12 }}>
                    {(photo.tags || []).map((tag, index) => (
                      <span key={index} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      className="form-input"
                      placeholder="输入标签后点击添加"
                      style={{ maxWidth: 240 }}
                    />
                    <button onClick={handleAddTag} className="btn btn-primary" disabled={adding || !newTag.trim()}>
                      <FiPlus /> 添加
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhotoDetail;
