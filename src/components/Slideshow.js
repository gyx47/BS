import React, { useState, useEffect, useRef } from 'react';
import { FiX, FiChevronLeft, FiChevronRight, FiPlay, FiPause, FiMaximize, FiMinimize } from 'react-icons/fi';
import './Slideshow.css';

const Slideshow = ({ photos, index = 0, onClose, autoPlay = true, interval = 3000 }) => {
  const [currentIndex, setCurrentIndex] = useState(index);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const intervalRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    setCurrentIndex(index);
  }, [index]);

  useEffect(() => {
    if (isPlaying && photos.length > 1) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % photos.length);
        setImageLoaded(false);
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
        case 'f':
        case 'F':
          toggleFullscreen();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, isPlaying]);

  const handlePrevious = () => {
    setCurrentIndex(prev => (prev > 0 ? prev - 1 : photos.length - 1));
    setImageLoaded(false);
    setIsPlaying(false);
  };

  const handleNext = () => {
    setCurrentIndex(prev => (prev < photos.length - 1 ? prev + 1 : 0));
    setImageLoaded(false);
    setIsPlaying(false);
  };

  const togglePlay = () => {
    setIsPlaying(prev => !prev);
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      } else if (containerRef.current.webkitRequestFullscreen) {
        containerRef.current.webkitRequestFullscreen();
      } else if (containerRef.current.msRequestFullscreen) {
        containerRef.current.msRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('msfullscreenchange', handleFullscreenChange);
    };
  }, []);

  const handleThumbnailClick = (index) => {
    setCurrentIndex(index);
    setImageLoaded(false);
    setIsPlaying(false);
  };

  if (!photos || photos.length === 0) {
    return null;
  }

  const currentPhoto = photos[currentIndex];
  const token = localStorage.getItem('token') || '';
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';

  return (
    <div className="slideshow-overlay" ref={containerRef}>
      <div className="slideshow-container">
        {/* 关闭按钮 */}
        <button className="slideshow-close" onClick={onClose} title="关闭 (ESC)">
          <FiX />
        </button>

        {/* 导航按钮 */}
        {photos.length > 1 && (
          <>
            <button 
              className="slideshow-nav slideshow-nav-prev" 
              onClick={handlePrevious}
              title="上一张 (←)"
            >
              <FiChevronLeft />
            </button>
            <button 
              className="slideshow-nav slideshow-nav-next" 
              onClick={handleNext}
              title="下一张 (→)"
            >
              <FiChevronRight />
            </button>
          </>
        )}

        {/* 主图片区域 */}
        <div className="slideshow-main">
          <div className="slideshow-image-container">
            {!imageLoaded && (
              <div className="slideshow-loading">
                <div className="spinner"></div>
              </div>
            )}
            <img
              src={`/api/photo/${currentPhoto.id}${tokenParam}`}
              alt={currentPhoto.original_filename}
              className="slideshow-image"
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageLoaded(true)}
            />
          </div>
        </div>

        {/* 控制栏 */}
        <div className="slideshow-controls">
          <div className="slideshow-info">
            <h3 className="slideshow-title" title={currentPhoto.original_filename}>
              {currentPhoto.original_filename}
            </h3>
            <div className="slideshow-counter">
              {currentIndex + 1} / {photos.length}
            </div>
          </div>

          <div className="slideshow-actions">
            {photos.length > 1 && (
              <button 
                className="slideshow-btn"
                onClick={togglePlay}
                title={isPlaying ? "暂停 (空格)" : "播放 (空格)"}
              >
                {isPlaying ? <FiPause /> : <FiPlay />}
                <span>{isPlaying ? '暂停' : '播放'}</span>
              </button>
            )}
            
            <button 
              className="slideshow-btn"
              onClick={toggleFullscreen}
              title={isFullscreen ? "退出全屏 (F)" : "全屏 (F)"}
            >
              {isFullscreen ? <FiMinimize /> : <FiMaximize />}
              <span>{isFullscreen ? '退出全屏' : '全屏'}</span>
            </button>
          </div>

          {/* 进度条 */}
          {photos.length > 1 && (
            <div className="slideshow-progress">
              <div className="slideshow-progress-bar">
                {photos.map((_, idx) => (
                  <div
                    key={idx}
                    className={`slideshow-progress-item ${idx === currentIndex ? 'active' : ''} ${idx < currentIndex ? 'completed' : ''}`}
                    onClick={() => handleThumbnailClick(idx)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 缩略图导航 */}
        {photos.length > 1 && (
          <div className="slideshow-thumbnails">
            {photos.map((photo, idx) => (
              <div
                key={photo.id}
                className={`slideshow-thumbnail ${idx === currentIndex ? 'active' : ''}`}
                onClick={() => handleThumbnailClick(idx)}
              >
                <img
                  src={`/api/thumbnail/${photo.id}${tokenParam}`}
                  alt={photo.original_filename}
                />
                {idx === currentIndex && (
                  <div className="slideshow-thumbnail-indicator"></div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Slideshow;

