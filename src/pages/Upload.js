import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import { FiUpload, FiX, FiImage, FiTag } from 'react-icons/fi';
import axios from 'axios';
import './Upload.css';

const Upload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [customTags, setCustomTags] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      preview: URL.createObjectURL(file),
      status: 'pending'
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    },
    maxSize: 16 * 1024 * 1024, // 16MB
    multiple: true
  });

  const removeFile = (fileId) => {
    setFiles(prev => {
      const updatedFiles = prev.filter(f => f.id !== fileId);
      // 清理预览URL
      const fileToRemove = prev.find(f => f.id === fileId);
      if (fileToRemove) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return updatedFiles;
    });
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('请选择要上传的图片');
      return;
    }

    setUploading(true);
    let successCount = 0;
    let errorCount = 0;

    try {
      for (const fileItem of files) {
        if (fileItem.status === 'pending') {
          const formData = new FormData();
          formData.append('file', fileItem.file);
          if (customTags.trim()) {
            formData.append('tags', customTags.trim());
          }

          try {
            await axios.post('/api/upload', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
                // 显式带上令牌，避免 401/422
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
              }
            });
            
            fileItem.status = 'success';
            successCount++;
          } catch (error) {
            fileItem.status = 'error';
            errorCount++;
            console.error('上传失败:', error);
          }
        }
      }

      setFiles([...files]);

      if (successCount > 0) {
        toast.success(`成功上传 ${successCount} 张图片`);
      }
      if (errorCount > 0) {
        toast.error(`${errorCount} 张图片上传失败`);
      }

      // 清空文件列表
      files.forEach(fileItem => {
        URL.revokeObjectURL(fileItem.preview);
      });
      setFiles([]);
      setCustomTags('');

    } catch (error) {
      toast.error('上传过程中发生错误');
      console.error('上传错误:', error);
    } finally {
      setUploading(false);
    }
  };

  const getFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'uploading':
        return '⏳';
      default:
        return '📷';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'success':
        return '上传成功';
      case 'error':
        return '上传失败';
      case 'uploading':
        return '上传中...';
      default:
        return '等待上传';
    }
  };

  return (
    <div className="upload-container">
      <div className="container">
        <div className="upload-header">
          <h1>上传图片</h1>
          <p>拖拽图片到下方区域，或点击选择文件</p>
        </div>

        <div className="upload-content">
          {/* 上传区域 */}
          <div
            {...getRootProps()}
            className={`upload-area ${isDragActive ? 'dragover' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="upload-icon">
              <FiUpload />
            </div>
            <div className="upload-text">
              {isDragActive ? '释放文件以上传' : '点击上传或拖拽文件到此处'}
            </div>
            <div className="upload-hint">
              支持 PNG, JPG, GIF 等格式，单个文件最大 16MB
            </div>
            <button type="button" className="btn btn-primary upload-btn">
              选择文件
            </button>
          </div>

          {/* 自定义标签 */}
          <div className="custom-tags-section">
            <h3>
              <FiTag className="section-icon" />
              添加自定义标签
            </h3>
            <input
              type="text"
              value={customTags}
              onChange={(e) => setCustomTags(e.target.value)}
              placeholder="例如：风景, 旅行, 家庭（用逗号分隔）"
              className="form-input"
            />
            <p className="tags-hint">用逗号分隔多个标签</p>
          </div>

          {/* 文件列表 */}
          {files.length > 0 && (
            <div className="files-section">
              <h3>
                <FiImage className="section-icon" />
                待上传文件 ({files.length})
              </h3>
              <div className="files-grid">
                {files.map((fileItem) => (
                  <div key={fileItem.id} className="file-item">
                    <div className="file-preview">
                      <img src={fileItem.preview} alt={fileItem.file.name} />
                      <div className="file-overlay">
                        <button
                          onClick={() => removeFile(fileItem.id)}
                          className="remove-btn"
                          disabled={uploading}
                        >
                          <FiX />
                        </button>
                      </div>
                    </div>
                    <div className="file-info">
                      <div className="file-name" title={fileItem.file.name}>
                        {fileItem.file.name}
                      </div>
                      <div className="file-size">
                        {getFileSize(fileItem.file.size)}
                      </div>
                      <div className={`file-status ${fileItem.status}`}>
                        <span className="status-icon">
                          {getStatusIcon(fileItem.status)}
                        </span>
                        <span className="status-text">
                          {getStatusText(fileItem.status)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          {files.length > 0 && (
            <div className="upload-actions">
              <button
                onClick={() => {
                  files.forEach(fileItem => URL.revokeObjectURL(fileItem.preview));
                  setFiles([]);
                  setCustomTags('');
                }}
                className="btn btn-secondary"
                disabled={uploading}
              >
                清空列表
              </button>
              <button
                onClick={handleUpload}
                className="btn btn-primary"
                disabled={uploading || files.every(f => f.status !== 'pending')}
              >
                {uploading ? '上传中...' : `上传 ${files.filter(f => f.status === 'pending').length} 张图片`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Upload;
