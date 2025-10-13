import React from 'react';
import { FiEye, FiEdit3, FiTrash2, FiCalendar, FiMapPin, FiTag } from 'react-icons/fi';
import './PhotoItem.css';

const PhotoItem = ({ 
  photo, 
  isSelected, 
  onSelect, 
  onClick, 
  onEdit, 
  viewMode = 'grid' 
}) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('zh-CN');
  };

  const handleClick = (e) => {
    e.stopPropagation();
    onClick();
  };

  const handleSelect = (e) => {
    e.stopPropagation();
    onSelect();
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    onEdit();
  };

  const tokenParam = (() => {
    const t = localStorage.getItem('token');
    return t ? `?token=${t}` : '';
  })();

  if (viewMode === 'list') {
    return (
      <div className={`photo-item list ${isSelected ? 'selected' : ''}`}>
        <div className="photo-checkbox">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleSelect}
            className="checkbox"
          />
        </div>
        
        <div className="photo-thumbnail" onClick={handleClick}>
          <img 
            src={`/api/thumbnail/${photo.id}${tokenParam}`} 
            alt={photo.original_filename}
            loading="lazy"
          />
        </div>
        
        <div className="photo-info">
          <h4 className="photo-title" title={photo.original_filename}>
            {photo.original_filename}
          </h4>
          
          <div className="photo-meta">
            {photo.taken_at && (
              <div className="meta-item">
                <FiCalendar className="meta-icon" />
                <span>{formatDate(photo.taken_at)}</span>
              </div>
            )}
            
            {photo.location && (
              <div className="meta-item">
                <FiMapPin className="meta-icon" />
                <span>{photo.location}</span>
              </div>
            )}
            
            <div className="meta-item">
              <span>{photo.width} × {photo.height}</span>
            </div>
            
            <div className="meta-item">
              <span>{formatFileSize(photo.file_size)}</span>
            </div>
          </div>
          
          {photo.tags && photo.tags.length > 0 && (
            <div className="photo-tags">
              {photo.tags.slice(0, 3).map((tag, index) => (
                <span key={index} className="tag">
                  <FiTag className="tag-icon" />
                  {tag}
                </span>
              ))}
              {photo.tags.length > 3 && (
                <span className="tag more">
                  +{photo.tags.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
        
        <div className="photo-actions">
          <button
            onClick={handleClick}
            className="action-btn"
            title="查看"
          >
            <FiEye />
          </button>
          <button
            onClick={handleEdit}
            className="action-btn"
            title="编辑"
          >
            <FiEdit3 />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`photo-item grid ${isSelected ? 'selected' : ''}`}>
      <div className="photo-checkbox">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={handleSelect}
          className="checkbox"
        />
      </div>
      
      <div className="photo-thumbnail" onClick={handleClick}>
        <img 
          src={`/api/thumbnail/${photo.id}${tokenParam}`} 
          alt={photo.original_filename}
          loading="lazy"
        />
        <div className="photo-overlay">
          <a
            href={`/photo/${photo.id}`}
            onClick={(e) => { e.preventDefault(); onClick(); }}
            className="view-btn"
            title="查看"
          >
            <FiEye />
          </a>
          <button
            onClick={handleEdit}
            className="edit-btn"
            title="编辑"
          >
            <FiEdit3 />
          </button>
        </div>
      </div>
      
      <div className="photo-info">
        <h4 className="photo-title" title={photo.original_filename}>
          {photo.original_filename}
        </h4>
        
        <div className="photo-meta">
          {photo.taken_at && (
            <span className="meta-item">
              <FiCalendar className="meta-icon" />
              {formatDate(photo.taken_at)}
            </span>
          )}
          
          {photo.location && (
            <span className="meta-item">
              <FiMapPin className="meta-icon" />
              {photo.location}
            </span>
          )}
        </div>
        
        {photo.tags && photo.tags.length > 0 && (
          <div className="photo-tags">
            {photo.tags.slice(0, 2).map((tag, index) => (
              <span key={index} className="tag">
                {tag}
              </span>
            ))}
            {photo.tags.length > 2 && (
              <span className="tag more">
                +{photo.tags.length - 2}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PhotoItem;
