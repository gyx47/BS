import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiSave, FiRotateCw, FiRotateCcw, FiCornerUpLeft, FiCornerUpRight, FiRefreshCcw, FiRefreshCw, FiX } from 'react-icons/fi';
import { ChromePicker } from 'react-color';
import ReactCrop from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import axios from 'axios';
import { toast } from 'react-toastify';
import './PhotoEdit.css';

const PhotoEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [image, setImage] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [colorPickerType, setColorPickerType] = useState('brightness');
  const [adjustments, setAdjustments] = useState({
    brightness: 0,
    contrast: 0,
    saturation: 0,
    hue: 0,
    blur: 0,
    sharpness: 0
  });
  const [cropEnabled, setCropEnabled] = useState(false);
  const [crop, setCrop] = useState({ unit: 'px', x: 0, y: 0, width: 0, height: 0 });
  const [naturalSize, setNaturalSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    fetchPhoto();
  }, [id]);

  const fetchPhoto = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/photos?page=1&per_page=1000`);
      const foundPhoto = response.data.photos.find(p => p.id === parseInt(id));
      
      if (foundPhoto) {
        setPhoto(foundPhoto);
        loadImage(foundPhoto);
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

  const loadImage = (photoData) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      setImage(img);
      setNaturalSize({ width: img.naturalWidth || img.width, height: img.naturalHeight || img.height });
      drawImage(img);
      saveToHistory();
    };
    img.src = `/api/photo/${photoData.id}?token=${localStorage.getItem('token') || ''}`;
  };

  const drawImage = (img) => {
    const canvas = canvasRef.current;
    if (!canvas || !img) return;

    const ctx = canvas.getContext('2d');
    canvas.width = img.width;
    canvas.height = img.height;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    // 应用调整
    applyAdjustments(ctx, canvas.width, canvas.height);
  };

  const applyAdjustments = (ctx, width, height) => {
    if (!image) return;

    const imageData = ctx.getImageData(0, 0, width, height);
    const data = imageData.data;

    // 应用亮度调整
    if (adjustments.brightness !== 0) {
      const brightness = adjustments.brightness;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, data[i] + brightness));
        data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + brightness));
        data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + brightness));
      }
    }

    // 应用对比度调整
    if (adjustments.contrast !== 0) {
      const contrast = (adjustments.contrast + 100) / 100;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, (data[i] - 128) * contrast + 128));
        data[i + 1] = Math.max(0, Math.min(255, (data[i + 1] - 128) * contrast + 128));
        data[i + 2] = Math.max(0, Math.min(255, (data[i + 2] - 128) * contrast + 128));
      }
    }

    // 应用饱和度调整
    if (adjustments.saturation !== 0) {
      const saturation = (adjustments.saturation + 100) / 100;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const gray = 0.299 * r + 0.587 * g + 0.114 * b;
        
        data[i] = Math.max(0, Math.min(255, gray + (r - gray) * saturation));
        data[i + 1] = Math.max(0, Math.min(255, gray + (g - gray) * saturation));
        data[i + 2] = Math.max(0, Math.min(255, gray + (b - gray) * saturation));
      }
    }

    ctx.putImageData(imageData, 0, 0);
  };

  const saveToHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const imageData = canvas.toDataURL();
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(imageData);
    
    if (newHistory.length > 20) {
      newHistory.shift();
    } else {
      setHistoryIndex(historyIndex + 1);
    }
    
    setHistory(newHistory);
  };

  const handleAdjustmentChange = (type, value) => {
    setAdjustments(prev => ({
      ...prev,
      [type]: value
    }));
    
    // 重新绘制图片
    setTimeout(() => {
      if (image) {
        drawImage(image);
      }
    }, 100);
  };

  const handleRotate = (direction) => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    const isClockwise = direction === 'cw';
    
    if (isClockwise) {
      canvas.width = image.height;
      canvas.height = image.width;
      ctx.translate(canvas.width, 0);
      ctx.rotate(Math.PI / 2);
    } else {
      canvas.width = image.height;
      canvas.height = image.width;
      ctx.translate(0, canvas.height);
      ctx.rotate(-Math.PI / 2);
    }
    
    ctx.drawImage(image, 0, 0);
    saveToHistory();
  };

  const handleFlip = (direction) => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext('2d');
    
    if (direction === 'horizontal') {
      ctx.scale(-1, 1);
      ctx.translate(-canvas.width, 0);
    } else {
      ctx.scale(1, -1);
      ctx.translate(0, -canvas.height);
    }
    
    ctx.drawImage(image, 0, 0);
    saveToHistory();
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      loadImageFromHistory(history[newIndex]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      loadImageFromHistory(history[newIndex]);
    }
  };

  const loadImageFromHistory = (imageData) => {
    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = imageData;
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      const canvas = canvasRef.current;
      // 计算旋转/翻转状态（简单实现：仅保存时把旋转角和翻转标志传给后端；
      // 由于上面本地预览已绘制，后端会按该参数对源图再次变换）
      const payload = {
        brightness: adjustments.brightness,
        contrast: adjustments.contrast,
        saturation: adjustments.saturation,
        rotation_deg: 0,
        flip_horizontal: false,
        flip_vertical: false
      };

      if (cropEnabled && crop.width > 0 && crop.height > 0) {
        payload.crop = { x: Math.round(crop.x), y: Math.round(crop.y), width: Math.round(crop.width), height: Math.round(crop.height) };
      }

      await axios.post(`/api/photo/${id}/edit`, {
        ...payload
      }, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token') || ''}` }
      });
      
      toast.success('照片编辑成功');
      navigate(`/photo/${id}`);
      
    } catch (error) {
      console.error('保存失败:', error);
      toast.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setAdjustments({
      brightness: 0,
      contrast: 0,
      saturation: 0,
      hue: 0,
      blur: 0,
      sharpness: 0
    });
    
    if (image) {
      drawImage(image);
    }
  };

  if (loading) {
    return (
      <div className="photo-edit-container">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!photo) {
    return (
      <div className="photo-edit-container">
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
    <div className="photo-edit-container">
      <div className="container">
        {/* 头部工具栏 */}
        <div className="edit-header">
          <div className="header-left">
            <button 
              onClick={() => navigate(`/photo/${id}`)} 
              className="back-btn"
            >
              <FiX />
              取消编辑
            </button>
            <h1>编辑照片</h1>
          </div>
          
          <div className="header-actions">
            <button 
              onClick={handleUndo} 
              className="action-btn"
              disabled={historyIndex <= 0}
            >
              <FiCornerUpLeft />
              撤销
            </button>
            <button 
              onClick={handleRedo} 
              className="action-btn"
              disabled={historyIndex >= history.length - 1}
            >
              <FiCornerUpRight />
              重做
            </button>
            <button onClick={handleReset} className="action-btn">
              重置
            </button>
            <button 
              onClick={handleSave} 
              className="btn btn-primary"
              disabled={saving}
            >
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>

        <div className="edit-content">
          {/* 画布区域 */}
          <div className="canvas-section">
            <div className="canvas-container">
              {cropEnabled ? (
                <ReactCrop crop={crop} onChange={(c) => setCrop(c)}>
                  <img
                    src={`/api/photo/${photo.id}?token=${localStorage.getItem('token') || ''}`}
                    alt={photo.original_filename}
                    style={{ maxWidth: '100%', maxHeight: '70vh' }}
                  />
                </ReactCrop>
              ) : (
                <canvas
                  ref={canvasRef}
                  className="edit-canvas"
                  style={{ maxWidth: '100%', maxHeight: '70vh' }}
                />
              )}
            </div>
          </div>

          {/* 编辑面板 */}
          <div className="edit-panel">
            <div className="panel-section">
              <h3>变换</h3>
              <div className="transform-buttons">
                <button 
                  onClick={() => setCropEnabled(!cropEnabled)} 
                  className="transform-btn"
                >
                  {cropEnabled ? '退出裁剪' : '启用裁剪'}
                </button>
                <button 
                  onClick={() => handleRotate('ccw')} 
                  className="transform-btn"
                >
                  <FiRotateCcw />
                  逆时针旋转
                </button>
                <button 
                  onClick={() => handleRotate('cw')} 
                  className="transform-btn"
                >
                  <FiRotateCw />
                  顺时针旋转
                </button>
                <button 
                  onClick={() => handleFlip('horizontal')} 
                  className="transform-btn"
                >
                  <FiRefreshCw />
                  水平翻转
                </button>
                <button 
                  onClick={() => handleFlip('vertical')} 
                  className="transform-btn"
                >
                  <FiRefreshCcw />
                  垂直翻转
                </button>
              </div>
            </div>

            <div className="panel-section">
              <h3>调整</h3>
              <div className="adjustment-controls">
                <div className="control-group">
                  <label>亮度</label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={adjustments.brightness}
                    onChange={(e) => handleAdjustmentChange('brightness', parseInt(e.target.value))}
                    className="slider"
                  />
                  <span className="value">{adjustments.brightness}</span>
                </div>

                <div className="control-group">
                  <label>对比度</label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={adjustments.contrast}
                    onChange={(e) => handleAdjustmentChange('contrast', parseInt(e.target.value))}
                    className="slider"
                  />
                  <span className="value">{adjustments.contrast}</span>
                </div>

                <div className="control-group">
                  <label>饱和度</label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={adjustments.saturation}
                    onChange={(e) => handleAdjustmentChange('saturation', parseInt(e.target.value))}
                    className="slider"
                  />
                  <span className="value">{adjustments.saturation}</span>
                </div>

                <div className="control-group">
                  <label>色相</label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    value={adjustments.hue}
                    onChange={(e) => handleAdjustmentChange('hue', parseInt(e.target.value))}
                    className="slider"
                  />
                  <span className="value">{adjustments.hue}</span>
                </div>
              </div>
            </div>

            <div className="panel-section">
              <h3>滤镜</h3>
              <div className="filter-buttons">
                <button 
                  onClick={() => handleAdjustmentChange('blur', 5)} 
                  className="filter-btn"
                >
                  模糊
                </button>
                <button 
                  onClick={() => handleAdjustmentChange('sharpness', 20)} 
                  className="filter-btn"
                >
                  锐化
                </button>
                <button 
                  onClick={() => handleAdjustmentChange('brightness', 30)} 
                  className="filter-btn"
                >
                  增亮
                </button>
                <button 
                  onClick={() => handleAdjustmentChange('contrast', 30)} 
                  className="filter-btn"
                >
                  增强对比度
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhotoEdit;
