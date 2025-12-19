import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FiX, FiChevronLeft, FiChevronRight, FiDownload, FiEdit3, FiTrash2, FiShare2, FiPlay, FiPause } from 'react-icons/fi';
import axios from 'axios';
import './ImageGallery.css';

const ImageGallery = ({ photos, index, onClose, autoPlay = false, interval = 5000 }) => {
  const [currentIndex, setCurrentIndex] = useState(index);
  const [loading, setLoading] = useState(false);
  const [photoInfo, setPhotoInfo] = useState(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const intervalRef = useRef(null);

  useEffect(() => {
    setCurrentIndex(index);
  }, [index]);

  const handlePrevious = useCallback(() => {
    setCurrentIndex(prev => 
      prev > 0 ? prev - 1 : photos.length - 1
    );
    setIsPlaying(false);
  }, [photos.length]);

  const handleNext = useCallback(() => {
    setCurrentIndex(prev => 
      prev < photos.length - 1 ? prev + 1 : 0
    );
    setIsPlaying(false);
  }, [photos.length]);

  const togglePlay = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  useEffect(() => {
    if (isPlaying && photos.length > 1) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % photos.length);
      }, interval);
    } else {
      clearInterval(intervalRef.current);
    }

    return () => {
      clearInterval(intervalRef.current);
    };
  }, [isPlaying, photos.length, interval]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          handlePrevious();
          break;
        case 'ArrowRight':
          handleNext();
          break;
        case ' ':
          e.preventDefault();
          togglePlay();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, handlePrevious, handleNext, togglePlay]);

  const handleDelete = async () => {
    if (!window.confirm('确定要删除这张照片吗？')) {
      return;
    }

    try {
      await axios.delete(`/api/photo/${photos[currentIndex].id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      onClose();
    } catch (error) {
      console.error('删除照片失败:', error);
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = `/api/photo/${photos[currentIndex].id}`;
    link.download = photos[currentIndex].original_filename;
    link.click();
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

  if (!photos || photos.length === 0) {
    return null;
  }

  const currentPhoto = photos[currentIndex];
  const tokenParam = (() => {
    const t = localStorage.getItem('token');
    return t ? `?token=${t}` : '';
  })();

  return (
    <div className="gallery-overlay">
      <div className="gallery-container">
        {/* 关闭按钮 */}
        <button className="gallery-close" onClick={onClose}>
          <FiX />
        </button>

        {/* 导航按钮 */}
        {photos.length > 1 && (
          <>
            <button 
              className="gallery-nav gallery-nav-prev" 
              onClick={handlePrevious}
            >
              <FiChevronLeft />
            </button>
            <button 
              className="gallery-nav gallery-nav-next" 
              onClick={handleNext}
            >
              <FiChevronRight />
            </button>
          </>
        )}

        {/* 主图片区域 */}
        <div className="gallery-main">
          <div className="gallery-image-container">
            <img
              src={`/api/photo/${currentPhoto.id}${tokenParam}`}
              alt={currentPhoto.original_filename}
              className="gallery-image"
              onLoad={() => setLoading(false)}
              onError={() => setLoading(false)}
            />
            {loading && (
              <div className="gallery-loading">
                <div className="spinner"></div>
              </div>
            )}
          </div>
        </div>

        {/* 图片信息面板 */}
        <div className="gallery-info">
          <div className="gallery-header">
            <h3 className="gallery-title" title={currentPhoto.original_filename}>
              {currentPhoto.original_filename}
            </h3>
            <div className="gallery-counter">
              {currentIndex + 1} / {photos.length}
            </div>
          </div>

          <div className="gallery-details">
            <div className="detail-row">
              <span className="detail-label">尺寸:</span>
              <span className="detail-value">
                {currentPhoto.width} × {currentPhoto.height}
              </span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">文件大小:</span>
              <span className="detail-value">
                {formatFileSize(currentPhoto.file_size)}
              </span>
            </div>
            
            {currentPhoto.taken_at && (
              <div className="detail-row">
                <span className="detail-label">拍摄时间:</span>
                <span className="detail-value">
                  {formatDate(currentPhoto.taken_at)}
                </span>
              </div>
            )}
            
            {currentPhoto.location && (
              <div className="detail-row">
                <span className="detail-label">拍摄地点:</span>
                <span className="detail-value">
                  {currentPhoto.location}
                </span>
              </div>
            )}
            
            {currentPhoto.tags && currentPhoto.tags.length > 0 && (
              <div className="detail-row">
                <span className="detail-label">标签:</span>
                <div className="detail-tags">
                  {currentPhoto.tags.map((tag, index) => (
                    <span key={index} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="gallery-actions">
            {photos.length > 1 && (
              <button 
                className="action-btn"
                onClick={togglePlay}
                title={isPlaying ? "暂停 (空格)" : "播放 (空格)"}
              >
                {isPlaying ? <FiPause /> : <FiPlay />}
                {isPlaying ? '暂停' : '播放'}
              </button>
            )}
            
            <button 
              className="action-btn"
              onClick={handleDownload}
              title="下载"
            >
              <FiDownload />
              下载
            </button>
            
            <button 
              className="action-btn"
              onClick={() => {/* TODO: 编辑功能 */}}
              title="编辑"
            >
              <FiEdit3 />
              编辑
            </button>
            
            <button 
              className="action-btn"
              onClick={() => {/* TODO: 分享功能 */}}
              title="分享"
            >
              <FiShare2 />
              分享
            </button>
            
            <button 
              className="action-btn danger"
              onClick={handleDelete}
              title="删除"
            >
              <FiTrash2 />
              删除
            </button>
          </div>
        </div>

        {/* 缩略图导航 */}
        {photos.length > 1 && (
          <div className="gallery-thumbnails">
            {photos.map((photo, index) => (
              <div
                key={photo.id}
                className={`thumbnail ${index === currentIndex ? 'active' : ''}`}
                onClick={() => setCurrentIndex(index)}
              >
                <img
                  src={`/api/thumbnail/${photo.id}${tokenParam}`}
                  alt={photo.original_filename}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageGallery;
