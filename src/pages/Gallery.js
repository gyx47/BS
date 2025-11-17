import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiFilter, FiGrid, FiList, FiPlay, FiTrash2, FiEdit3, FiEye } from 'react-icons/fi';
import axios from 'axios';
import PhotoItem from '../components/PhotoItem';
import ImageGallery from '../components/ImageGallery';
import './Gallery.css';

const Gallery = () => {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [showGallery, setShowGallery] = useState(false);
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [tags, setTags] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalPhotos, setTotalPhotos] = useState(0);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const navigate = useNavigate();

  const fetchPhotos = useCallback(async (pageNum = 1, reset = false) => {
    try {
      setLoading(true);
      
      const params = {
        page: pageNum,
        per_page: 20,
        search: searchTerm,
        tag: selectedTag,
        sort_by: sortBy,
        order: sortOrder
      };
      if (startDate) {
        params.start_date = startDate;
      }
      if (endDate) {
        params.end_date = endDate;
      }

      const response = await axios.get('/api/photos', { 
        params,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      
      if (reset) {
        setPhotos(response.data.photos);
      } else {
        setPhotos(prev => [...prev, ...response.data.photos]);
      }
      
      setTotalPhotos(response.data.total);
      setHasMore(response.data.page < response.data.pages);
      
    } catch (error) {
      console.error('获取照片失败:', error);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedTag, sortBy, sortOrder, startDate, endDate]);

  const fetchTags = async () => {
    try {
      const response = await axios.get('/api/tags', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      setTags(response.data.tags);
    } catch (error) {
      console.error('获取标签失败:', error);
    }
  };

  useEffect(() => {
    fetchPhotos(1, true);
  }, [fetchPhotos]);

  useEffect(() => {
    fetchTags();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchPhotos(1, true);
  };

  const handleTagFilter = (tag) => {
    setSelectedTag(selectedTag === tag ? '' : tag);
    setPage(1);
  };

  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const handleDateChange = (type, value) => {
    if (type === 'start') {
      setStartDate(value);
    } else {
      setEndDate(value);
    }
    setPage(1);
  };

  const handleResetDate = () => {
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchPhotos(nextPage, false);
  };

  const handlePhotoSelect = (photoId) => {
    setSelectedPhotos(prev => 
      prev.includes(photoId) 
        ? prev.filter(id => id !== photoId)
        : [...prev, photoId]
    );
  };

  const handleSelectAll = () => {
    if (selectedPhotos.length === photos.length) {
      setSelectedPhotos([]);
    } else {
      setSelectedPhotos(photos.map(photo => photo.id));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedPhotos.length === 0) return;
    
    if (!window.confirm(`确定要删除选中的 ${selectedPhotos.length} 张照片吗？`)) {
      return;
    }

    try {
      for (const photoId of selectedPhotos) {
        await axios.delete(`/api/photo/${photoId}`);
      }
      
      setPhotos(prev => prev.filter(photo => !selectedPhotos.includes(photo.id)));
      setSelectedPhotos([]);
      setTotalPhotos(prev => prev - selectedPhotos.length);
      
    } catch (error) {
      console.error('删除照片失败:', error);
    }
  };

  const handleSlideshow = () => {
    if (selectedPhotos.length === 0) return;
    
    const selectedPhotoObjects = photos.filter(photo => selectedPhotos.includes(photo.id));
    setPhotos(selectedPhotoObjects);
    setGalleryIndex(0);
    setShowGallery(true);
  };

  const handlePhotoClick = (photo, index) => {
    // 跳到详情页，便于添加标签和编辑
    navigate(`/photo/${photo.id}`);
  };

  const handleEditPhoto = (photoId) => {
    navigate(`/photo/${photoId}/edit`);
  };

  const sortOptions = [
    { value: 'created_at', label: '上传时间' },
    { value: 'taken_at', label: '拍摄时间' },
    { value: 'original_filename', label: '文件名' },
    { value: 'file_size', label: '文件大小' }
  ];

  return (
    <div className="gallery-container">
      <div className="container">
        <div className="gallery-header">
          <h1>我的相册</h1>
          <div className="gallery-actions">
            <button
              onClick={() => setViewMode('grid')}
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            >
              <FiGrid />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            >
              <FiList />
            </button>
          </div>
        </div>

        {/* 搜索和筛选 */}
        <div className="search-filters">
          <form onSubmit={handleSearch} className="search-bar">
            <div className="search-input-container">
              <FiSearch className="search-icon" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索照片..."
                className="search-input"
              />
            </div>
            <button type="submit" className="btn btn-primary">
              搜索
            </button>
          </form>

          <div className="filters-row">
            <div className="filter-group">
              <label className="filter-label">排序方式:</label>
              <div className="sort-buttons">
                {sortOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => handleSortChange(option.value)}
                    className={`sort-btn ${sortBy === option.value ? 'active' : ''}`}
                  >
                    {option.label}
                    {sortBy === option.value && (
                      <span className="sort-order">
                        {sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group">
              <label className="filter-label">标签筛选:</label>
              <div className="tag-filters">
                <button
                  onClick={() => handleTagFilter('')}
                  className={`tag-filter ${selectedTag === '' ? 'active' : ''}`}
                >
                  全部
                </button>
                {tags.map(tag => (
                  <button
                    key={tag.id}
                    onClick={() => handleTagFilter(tag.name)}
                    className={`tag-filter ${selectedTag === tag.name ? 'active' : ''}`}
                  >
                    {tag.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-group date-filter">
              <label className="filter-label">日期范围:</label>
              <div className="date-inputs">
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  className="date-input"
                />
                <span className="date-separator">至</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  className="date-input"
                  min={startDate || undefined}
                />
                {(startDate || endDate) && (
                  <button
                    type="button"
                    className="btn btn-secondary clear-date-btn"
                    onClick={handleResetDate}
                  >
                    清除
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 选择操作 */}
        {selectedPhotos.length > 0 && (
          <div className="selection-actions">
            <div className="selection-info">
              <span>已选择 {selectedPhotos.length} 张照片</span>
              <button
                onClick={handleSelectAll}
                className="btn btn-secondary"
              >
                {selectedPhotos.length === photos.length ? '取消全选' : '全选'}
              </button>
            </div>
            <div className="selection-buttons">
              <button
                onClick={handleSlideshow}
                className="btn btn-primary"
                disabled={selectedPhotos.length === 0}
              >
                <FiPlay />
                幻灯片播放
              </button>
              <button
                onClick={handleDeleteSelected}
                className="btn btn-danger"
                disabled={selectedPhotos.length === 0}
              >
                <FiTrash2 />
                删除选中
              </button>
            </div>
          </div>
        )}

        {/* 照片网格 */}
        {loading && photos.length === 0 ? (
          <div className="loading">
            <div className="spinner"></div>
          </div>
        ) : photos.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <FiSearch />
            </div>
            <h3>没有找到照片</h3>
            <p>尝试调整搜索条件或上传新照片</p>
          </div>
        ) : (
          <div className={`photos-container ${viewMode}`}>
            {photos.map((photo, index) => (
              <PhotoItem
                key={photo.id}
                photo={photo}
                isSelected={selectedPhotos.includes(photo.id)}
                onSelect={() => handlePhotoSelect(photo.id)}
                onClick={() => handlePhotoClick(photo, index)}
                onEdit={() => handleEditPhoto(photo.id)}
                viewMode={viewMode}
              />
            ))}
          </div>
        )}

        {/* 加载更多 */}
        {hasMore && photos.length > 0 && (
          <div className="load-more">
            <button
              onClick={handleLoadMore}
              className="btn btn-secondary"
              disabled={loading}
            >
              {loading ? '加载中...' : '加载更多'}
            </button>
          </div>
        )}

        {/* 统计信息 */}
        <div className="gallery-stats">
          <p>共 {totalPhotos} 张照片</p>
        </div>
      </div>

      {/* 图片画廊 */}
      {showGallery && (
        <ImageGallery
          photos={photos}
          index={galleryIndex}
          onClose={() => setShowGallery(false)}
        />
      )}
    </div>
  );
};

export default Gallery;
