import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiX } from 'react-icons/fi';
import ReactCrop from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import axios from 'axios';
import { toast } from 'react-toastify';
import './PhotoEdit.css';

const clampChannel = (value) => Math.max(0, Math.min(255, value));

const rgbToHsl = (r, g, b) => {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h;
  let s;
  const l = (max + min) / 2;

  if (max === min) {
    h = 0;
    s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      default:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }

  return [h, s, l];
};

const hslToRgb = (h, s, l) => {
  let r;
  let g;
  let b;

  if (s === 0) {
    r = g = b = l; // achromatic
  } else {
    const hue2rgb = (p, q, t) => {
      let tempT = t;
      if (tempT < 0) tempT += 1;
      if (tempT > 1) tempT -= 1;
      if (tempT < 1 / 6) return p + (q - p) * 6 * tempT;
      if (tempT < 1 / 2) return q;
      if (tempT < 2 / 3) return p + (q - p) * (2 / 3 - tempT) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
};

const PhotoEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [image, setImage] = useState(null);
  const [adjustments, setAdjustments] = useState({
    brightness: 0,
    contrast: 0,
    saturation: 0,
    hue: 0
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
        data[i] = clampChannel(data[i] + brightness);
        data[i + 1] = clampChannel(data[i + 1] + brightness);
        data[i + 2] = clampChannel(data[i + 2] + brightness);
      }
    }

    // 应用对比度调整
    if (adjustments.contrast !== 0) {
      const contrast = (adjustments.contrast + 100) / 100;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = clampChannel((data[i] - 128) * contrast + 128);
        data[i + 1] = clampChannel((data[i + 1] - 128) * contrast + 128);
        data[i + 2] = clampChannel((data[i + 2] - 128) * contrast + 128);
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

        data[i] = clampChannel(gray + (r - gray) * saturation);
        data[i + 1] = clampChannel(gray + (g - gray) * saturation);
        data[i + 2] = clampChannel(gray + (b - gray) * saturation);
      }
    }

    // 应用色相调整
    if (adjustments.hue !== 0) {
      const hueShift = adjustments.hue;
      for (let i = 0; i < data.length; i += 4) {
        const [h, s, l] = rgbToHsl(data[i], data[i + 1], data[i + 2]);
        let newHue = h + hueShift / 360;
        if (newHue < 0) newHue += 1;
        if (newHue > 1) newHue -= 1;
        const [nr, ng, nb] = hslToRgb(newHue, s, l);
        data[i] = nr;
        data[i + 1] = ng;
        data[i + 2] = nb;
      }
    }

    ctx.putImageData(imageData, 0, 0);
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

  const handleSave = async () => {
    try {
      setSaving(true);
      
      const canvas = canvasRef.current;
      const payload = {
        brightness: adjustments.brightness,
        contrast: adjustments.contrast,
        saturation: adjustments.saturation,
        hue: adjustments.hue
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
      hue: 0
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
              <h3>裁剪</h3>
              <button 
                onClick={() => setCropEnabled(!cropEnabled)} 
                className="transform-btn"
              >
                {cropEnabled ? '退出裁剪' : '启用裁剪'}
              </button>
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhotoEdit;
