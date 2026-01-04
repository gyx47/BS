from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageFilter
import exifread
import magic
import cv2
import numpy as np
import requests
from sqlalchemy import or_, and_
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os
from pathlib import Path
from utils.ai_analyzer import analyze_image_with_ai

# 显式加载项目根目录下的 .env（确保在读取 env 之前执行）
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# 从环境变量读取（有默认值以便本地测试）
DB_USER = os.getenv("DB_USER", "photo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "photo")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "photo_management")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "5000"))
# 对密码进行 URL 编码以避免特殊字符问题
DB_PASSWORD_Q = quote_plus(DB_PASSWORD)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD_Q}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
app.config['JWT_QUERY_STRING_NAME'] = 'token'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['THUMBNAIL_FOLDER'] = 'thumbnails'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

# 初始化扩展
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# 数据库模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    camera_make = db.Column(db.String(100))
    camera_model = db.Column(db.String(100))
    taken_at = db.Column(db.DateTime)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref=db.backref('photos', lazy=True))
    tags = db.relationship('Tag', secondary='photo_tags', backref='photos')

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.Enum('auto', 'custom'), default='custom')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PhotoTag(db.Model):
    __tablename__ = 'photo_tags'
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cover_photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AlbumPhoto(db.Model):
    __tablename__ = 'album_photos'
    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey('albums.id'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 工具函数
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """生成缩略图"""
    try:
        with Image.open(image_path) as img:
            # 确保图片是RGB模式
            if img.mode in ('RGBA', 'LA', 'P'):
                # 如果有透明通道，转换为RGB（白色背景）
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                    img = background
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 生成缩略图
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 根据缩略图文件扩展名确定保存格式
            thumb_ext = os.path.splitext(thumbnail_path)[1].lower()
            save_kwargs = {'optimize': True}
            if thumb_ext in ['.jpg', '.jpeg']:
                save_kwargs['quality'] = 85
            
            img.save(thumbnail_path, **save_kwargs)
        return True
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def convert_to_degrees(value):
    """将GPS坐标从度/分/秒格式转换为小数格式"""
    try:
        d = float(value.values[0].num) / float(value.values[0].den)
        m = float(value.values[1].num) / float(value.values[1].den)
        s = float(value.values[2].num) / float(value.values[2].den)
        return d + (m / 60.0) + (s / 3600.0)
    except:
        try:
            # 如果已经是小数格式
            return float(value)
        except:
            return None

def extract_exif_data(image_path):
    """提取EXIF数据，支持多种格式和字段"""
    exif_data = {}
    
    # 方法1: 使用exifread库
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        # 调试：打印所有可用的EXIF标签（仅前20个，避免输出过多）
        available_tags = list(tags.keys())[:20]
        print(f"可用EXIF标签（前20个）: {available_tags}")
        
        # 提取拍摄时间（尝试多个字段）
        taken_at = None
        date_fields = [
            'EXIF DateTimeOriginal',
            'EXIF DateTimeDigitized', 
            'Image DateTime',
            'EXIF DateTime',
            'EXIF SubSecTimeOriginal',  # 子秒时间
            'EXIF SubSecTimeDigitized'
        ]
        for field in date_fields:
            if field in tags:
                try:
                    date_str = str(tags[field])
                    print(f"找到日期字段 {field}: {date_str}")
                    # 处理不同的日期格式
                    for fmt in ['%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                        try:
                            taken_at = datetime.strptime(date_str, fmt)
                            print(f"成功解析日期: {taken_at}")
                            break
                        except ValueError:
                            continue
                    if taken_at:
                        break
                except Exception as e:
                    print(f"解析日期字段 {field} 失败: {e}")
                    continue
        
        if taken_at:
            exif_data['taken_at'] = taken_at
            print(f"设置拍摄时间: {taken_at}")
        
        # 提取更多EXIF拍摄参数
        # ISO感光度
        if 'EXIF ISOSpeedRatings' in tags:
            try:
                exif_data['iso'] = int(str(tags['EXIF ISOSpeedRatings']))
            except:
                pass
        elif 'EXIF ISO' in tags:
            try:
                exif_data['iso'] = int(str(tags['EXIF ISO']))
            except:
                pass
        
        # 光圈值
        if 'EXIF FNumber' in tags:
            fnumber = tags['EXIF FNumber']
            try:
                if hasattr(fnumber, 'values'):
                    exif_data['f_number'] = float(fnumber.values[0].num) / float(fnumber.values[0].den)
                else:
                    exif_data['f_number'] = float(str(fnumber))
            except:
                pass
        
        # 快门速度
        if 'EXIF ExposureTime' in tags:
            exposure = tags['EXIF ExposureTime']
            try:
                if hasattr(exposure, 'values'):
                    exif_data['exposure_time'] = float(exposure.values[0].num) / float(exposure.values[0].den)
                else:
                    exif_data['exposure_time'] = float(str(exposure))
            except:
                pass
        
        # 焦距
        if 'EXIF FocalLength' in tags:
            focal = tags['EXIF FocalLength']
            try:
                if hasattr(focal, 'values'):
                    exif_data['focal_length'] = float(focal.values[0].num) / float(focal.values[0].den)
                else:
                    exif_data['focal_length'] = float(str(focal))
            except:
                pass
        
        # 白平衡
        if 'EXIF WhiteBalance' in tags:
            exif_data['white_balance'] = str(tags['EXIF WhiteBalance']).strip()
        
        # 闪光灯
        if 'EXIF Flash' in tags:
            exif_data['flash'] = str(tags['EXIF Flash']).strip()
        
        # 拍摄模式
        if 'EXIF ExposureMode' in tags:
            exif_data['exposure_mode'] = str(tags['EXIF ExposureMode']).strip()
        
        # 测光模式
        if 'EXIF MeteringMode' in tags:
            exif_data['metering_mode'] = str(tags['EXIF MeteringMode']).strip()
        
        # 提取相机品牌
        if 'Image Make' in tags:
            exif_data['camera_make'] = str(tags['Image Make']).strip()
        elif 'EXIF Make' in tags:
            exif_data['camera_make'] = str(tags['EXIF Make']).strip()
        
        # 提取相机型号
        if 'Image Model' in tags:
            exif_data['camera_model'] = str(tags['Image Model']).strip()
        elif 'EXIF Model' in tags:
            exif_data['camera_model'] = str(tags['EXIF Model']).strip()
        
        # 提取GPS坐标（需要正确转换度/分/秒格式）
        gps_tags = [tag for tag in tags.keys() if 'GPS' in tag]
        if gps_tags:
            print(f"找到GPS相关标签: {gps_tags}")
            # 打印所有GPS标签的详细信息
            for gps_tag in gps_tags:
                print(f"  {gps_tag}: {tags[gps_tag]}")
        
        # 尝试多种可能的GPS标签名称格式
        lat_tag = None
        lon_tag = None
        lat_ref_tag = None
        lon_ref_tag = None
        
        # 常见的GPS标签名称变体
        possible_lat_tags = ['GPS GPSLatitude', 'GPS Latitude', 'GPSLatitude']
        possible_lon_tags = ['GPS GPSLongitude', 'GPS Longitude', 'GPSLongitude']
        possible_lat_ref_tags = ['GPS GPSLatitudeRef', 'GPS LatitudeRef', 'GPSLatitudeRef']
        possible_lon_ref_tags = ['GPS GPSLongitudeRef', 'GPS LongitudeRef', 'GPSLongitudeRef']
        
        # 查找实际的标签名称
        for tag_name in tags.keys():
            tag_upper = tag_name.upper()
            if 'LATITUDE' in tag_upper and 'REF' not in tag_upper:
                lat_tag = tag_name
            elif 'LONGITUDE' in tag_upper and 'REF' not in tag_upper:
                lon_tag = tag_name
            elif 'LATITUDE' in tag_upper and 'REF' in tag_upper:
                lat_ref_tag = tag_name
            elif 'LONGITUDE' in tag_upper and 'REF' in tag_upper:
                lon_ref_tag = tag_name
        
        print(f"检测到的GPS标签: lat={lat_tag}, lon={lon_tag}, lat_ref={lat_ref_tag}, lon_ref={lon_ref_tag}")
        
        # 使用找到的标签名称提取GPS坐标
        if lat_tag and lon_tag:
            try:
                lat_ref = str(tags.get(lat_ref_tag, 'N')).upper() if lat_ref_tag else 'N'
                lon_ref = str(tags.get(lon_ref_tag, 'E')).upper() if lon_ref_tag else 'E'
                
                print(f"GPS纬度原始值: {tags[lat_tag]}, 参考: {lat_ref}")
                print(f"GPS经度原始值: {tags[lon_tag]}, 参考: {lon_ref}")
                
                lat = convert_to_degrees(tags[lat_tag])
                lon = convert_to_degrees(tags[lon_tag])
                
                if lat is not None and lon is not None:
                    # 根据方向调整正负
                    if lat_ref == 'S':
                        lat = -lat
                    if lon_ref == 'W':
                        lon = -lon
                    
                    exif_data['latitude'] = lat
                    exif_data['longitude'] = lon
                    print(f"成功提取GPS坐标: ({lat}, {lon})")
                else:
                    print(f"GPS坐标转换失败: lat={lat}, lon={lon}")
            except Exception as e:
                print(f"提取GPS坐标失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"未找到GPS坐标标签 (lat_tag={lat_tag}, lon_tag={lon_tag})")
        
        # 如果已经提取到数据，直接返回
        if exif_data:
            return exif_data
            
    except Exception as e:
        print(f"使用exifread提取EXIF数据失败: {e}")
    
    # 方法2: 使用PIL的EXIF功能作为备选
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if exif:
                print(f"PIL EXIF包含 {len(exif)} 个字段")
                # 打印所有EXIF字段（用于调试）
                if len(exif) > 0:
                    print(f"PIL EXIF字段示例: {list(exif.items())[:10]}")
                
                # 提取拍摄时间
                date_fields = {
                    36867: 'EXIF DateTimeOriginal',
                    36868: 'EXIF DateTimeDigitized',
                    306: 'DateTime',
                    36880: 'EXIF SubSecTimeOriginal',
                    36881: 'EXIF SubSecTimeDigitized'
                }
                for field_code, field_name in date_fields.items():
                    if field_code in exif:
                        try:
                            date_str = exif[field_code]
                            print(f"PIL找到日期字段 {field_name} ({field_code}): {date_str}")
                            for fmt in ['%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']:
                                try:
                                    taken_at = datetime.strptime(date_str, fmt)
                                    exif_data['taken_at'] = taken_at
                                    print(f"PIL成功解析日期: {taken_at}")
                                    break
                                except ValueError:
                                    continue
                            if 'taken_at' in exif_data:
                                break
                        except Exception as e:
                            print(f"解析PIL EXIF日期字段 {field_name} 失败: {e}")
                            continue
                
                # 提取相机品牌和型号
                if 271 in exif and not exif_data.get('camera_make'):
                    exif_data['camera_make'] = str(exif[271]).strip()
                    print(f"PIL提取相机品牌: {exif_data['camera_make']}")
                if 272 in exif and not exif_data.get('camera_model'):
                    exif_data['camera_model'] = str(exif[272]).strip()
                    print(f"PIL提取相机型号: {exif_data['camera_model']}")
                
                # PIL也可以提取GPS信息（通过EXIF GPS IFD）
                # 尝试从PIL的EXIF中提取GPS
                try:
                    from PIL.ExifTags import GPS
                    gps_info = exif.get_ifd(0x8825)  # GPS IFD
                    if gps_info:
                        print(f"PIL找到GPS信息: {gps_info}")
                        # GPS标签代码
                        GPS_LAT = 2  # GPSLatitude
                        GPS_LAT_REF = 1  # GPSLatitudeRef
                        GPS_LON = 4  # GPSLongitude
                        GPS_LON_REF = 3  # GPSLongitudeRef
                        
                        if GPS_LAT in gps_info and GPS_LON in gps_info:
                            lat_ref = gps_info.get(GPS_LAT_REF, 'N')
                            lon_ref = gps_info.get(GPS_LON_REF, 'E')
                            
                            # PIL返回的GPS坐标是元组格式 (度, 分, 秒)
                            lat_tuple = gps_info[GPS_LAT]
                            lon_tuple = gps_info[GPS_LON]
                            
                            # 转换为小数
                            lat = lat_tuple[0] + lat_tuple[1]/60.0 + lat_tuple[2]/3600.0
                            lon = lon_tuple[0] + lon_tuple[1]/60.0 + lon_tuple[2]/3600.0
                            
                            if lat_ref == 'S':
                                lat = -lat
                            if lon_ref == 'W':
                                lon = -lon
                            
                            if 'latitude' not in exif_data:  # 如果exifread没有提取到，使用PIL的结果
                                exif_data['latitude'] = lat
                                exif_data['longitude'] = lon
                                print(f"PIL成功提取GPS坐标: ({lat}, {lon})")
                except Exception as e:
                    print(f"PIL提取GPS信息失败: {e}")
                
    except Exception as e:
        print(f"使用PIL提取EXIF数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 注意：如果没有从EXIF提取到拍摄时间，不设置taken_at
    # 因为文件修改时间通常是上传时间，不是拍摄时间
    # 这样可以避免将上传时间误识别为拍摄时间
    
    return exif_data

# analyze_image_with_ai 函数已移至 utils/ai_analyzer.py
# 现在从 utils 模块导入使用

def ensure_tags_for_photo(photo, tag_names, tag_type='auto'):
    """确保给定标签已创建并与照片关联"""
    attached = []
    for tag_name in tag_names:
        cleaned = (tag_name or '').strip()
        if not cleaned:
            continue
        
        # 如果标签包含顿号，按顿号分割成多个标签
        # 例如："夜晚的天空、飞机、深蓝色和白色" -> ["夜晚的天空", "飞机", "深蓝色和白色"]
        if '、' in cleaned:
            sub_tags = [sub_tag.strip() for sub_tag in cleaned.split('、') if sub_tag.strip()]
            # 递归处理分割后的标签
            attached.extend(ensure_tags_for_photo(photo, sub_tags, tag_type))
        else:
            # 单个标签，直接处理
            tag = Tag.query.filter_by(name=cleaned).first()
            if not tag:
                tag = Tag(name=cleaned, type=tag_type)
                db.session.add(tag)
                db.session.flush()
            relation_exists = PhotoTag.query.filter_by(photo_id=photo.id, tag_id=tag.id).first()
            if not relation_exists:
                db.session.add(PhotoTag(photo_id=photo.id, tag_id=tag.id))
                attached.append(cleaned)
    return attached

def generate_exif_tag_names(exif_data, width=None, height=None):
    """基于EXIF信息和图片属性生成标签名称"""
    tag_names = []
    
    # 日期相关标签
    taken_at = exif_data.get('taken_at')
    if isinstance(taken_at, datetime):
        tag_names.append(f"日期:{taken_at.strftime('%Y-%m-%d')}")
        tag_names.append(f"年份:{taken_at.year}")
        tag_names.append(f"月份:{taken_at.strftime('%Y-%m')}")
        # 添加星期标签
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        tag_names.append(f"星期:{weekdays[taken_at.weekday()]}")
        # 添加时间段标签
        hour = taken_at.hour
        if 5 <= hour < 12:
            tag_names.append("时间段:上午")
        elif 12 <= hour < 14:
            tag_names.append("时间段:中午")
        elif 14 <= hour < 18:
            tag_names.append("时间段:下午")
        elif 18 <= hour < 22:
            tag_names.append("时间段:晚上")
        else:
            tag_names.append("时间段:深夜")

    # 相机信息标签
    camera_model = (exif_data.get('camera_model') or '').strip()
    camera_make = (exif_data.get('camera_make') or '').strip()
    if camera_make and camera_model:
        tag_names.append(f"相机:{camera_make} {camera_model}")
        # 单独添加品牌标签
        tag_names.append(f"品牌:{camera_make}")
    elif camera_model:
        tag_names.append(f"相机:{camera_model}")
    elif camera_make:
        tag_names.append(f"相机品牌:{camera_make}")
    
    # 拍摄参数标签
    iso = exif_data.get('iso')
    if iso:
        tag_names.append(f"ISO:{iso}")
        # ISO等级分类
        if iso < 200:
            tag_names.append("ISO:低感光度")
        elif iso < 800:
            tag_names.append("ISO:中感光度")
        elif iso < 3200:
            tag_names.append("ISO:高感光度")
        else:
            tag_names.append("ISO:超高感光度")
    
    f_number = exif_data.get('f_number')
    if f_number:
        tag_names.append(f"光圈:f/{f_number:.1f}")
        # 光圈分类
        if f_number <= 2.8:
            tag_names.append("光圈:大光圈")
        elif f_number <= 5.6:
            tag_names.append("光圈:中等光圈")
        else:
            tag_names.append("光圈:小光圈")
    
    exposure_time = exif_data.get('exposure_time')
    if exposure_time:
        if exposure_time < 1:
            tag_names.append(f"快门:1/{int(1/exposure_time)}秒")
        else:
            tag_names.append(f"快门:{exposure_time:.1f}秒")
        # 快门速度分类
        if exposure_time < 1/60:
            tag_names.append("快门:高速")
        elif exposure_time < 1/15:
            tag_names.append("快门:中速")
        else:
            tag_names.append("快门:慢速")
    
    focal_length = exif_data.get('focal_length')
    if focal_length:
        tag_names.append(f"焦距:{focal_length:.0f}mm")
        # 焦距分类
        if focal_length < 24:
            tag_names.append("焦距:超广角")
        elif focal_length < 35:
            tag_names.append("焦距:广角")
        elif focal_length < 85:
            tag_names.append("焦距:标准")
        elif focal_length < 135:
            tag_names.append("焦距:中长焦")
        else:
            tag_names.append("焦距:长焦")
    
    white_balance = exif_data.get('white_balance')
    if white_balance:
        tag_names.append(f"白平衡:{white_balance}")
    
    flash = exif_data.get('flash')
    if flash:
        if '0' in str(flash) or 'No' in str(flash) or '否' in str(flash):
            tag_names.append("闪光灯:关闭")
        else:
            tag_names.append("闪光灯:开启")
    
    exposure_mode = exif_data.get('exposure_mode')
    if exposure_mode:
        tag_names.append(f"拍摄模式:{exposure_mode}")
    
    metering_mode = exif_data.get('metering_mode')
    if metering_mode:
        tag_names.append(f"测光模式:{metering_mode}")

    # 地理位置标签
    latitude = exif_data.get('latitude')
    longitude = exif_data.get('longitude')
    if latitude is not None and longitude is not None:
        tag_names.append("含地理位置")
        
        # 添加GPS坐标标签（保留2位小数）
        tag_names.append(f"GPS:({latitude:.2f},{longitude:.2f})")
        
        # 根据经纬度添加粗略位置标签（中国主要城市）
        if 39.0 <= latitude <= 41.0 and 116.0 <= longitude <= 118.0:
            tag_names.append("地区:北京")
        elif 31.0 <= latitude <= 32.0 and 120.0 <= longitude <= 122.0:
            tag_names.append("地区:上海")
        elif 22.0 <= latitude <= 24.0 and 113.0 <= longitude <= 115.0:
            tag_names.append("地区:广东")
        elif 30.0 <= latitude <= 31.0 and 104.0 <= longitude <= 105.0:
            tag_names.append("地区:成都")
        elif 29.0 <= latitude <= 30.0 and 106.0 <= longitude <= 107.0:
            tag_names.append("地区:重庆")
        elif 36.0 <= latitude <= 37.0 and 117.0 <= longitude <= 118.0:
            tag_names.append("地区:济南")
        elif 34.0 <= latitude <= 35.0 and 108.0 <= longitude <= 109.0:
            tag_names.append("地区:西安")
        elif 32.0 <= latitude <= 33.0 and 118.0 <= longitude <= 119.0:
            tag_names.append("地区:南京")
        elif 30.0 <= latitude <= 31.0 and 120.0 <= longitude <= 121.0:
            tag_names.append("地区:杭州")
        elif 38.0 <= latitude <= 40.0 and 117.0 <= longitude <= 118.0:
            tag_names.append("地区:天津")
        # 国际主要城市
        elif 40.0 <= latitude <= 42.0 and -75.0 <= longitude <= -73.0:
            tag_names.append("地区:纽约")
        elif 48.0 <= latitude <= 49.0 and 2.0 <= longitude <= 3.0:
            tag_names.append("地区:巴黎")
        elif 51.0 <= latitude <= 52.0 and -1.0 <= longitude <= 0.0:
            tag_names.append("地区:伦敦")
        elif 35.0 <= latitude <= 36.0 and 139.0 <= longitude <= 140.0:
            tag_names.append("地区:东京")
        elif 43.0 <= latitude <= 44.0 and 11.0 <= longitude <= 12.0:
            tag_names.append("地区:意大利")
        elif 52.0 <= latitude <= 53.0 and 13.0 <= longitude <= 14.0:
            tag_names.append("地区:柏林")
        elif 37.0 <= latitude <= 38.0 and -123.0 <= longitude <= -122.0:
            tag_names.append("地区:旧金山")
        elif 34.0 <= latitude <= 35.0 and -119.0 <= longitude <= -118.0:
            tag_names.append("地区:洛杉矶")
        # 根据纬度判断大致地区
        if latitude > 0:
            if latitude > 50:
                tag_names.append("北半球:高纬度")
            elif latitude > 30:
                tag_names.append("北半球:中纬度")
            else:
                tag_names.append("北半球:低纬度")
        else:
            if latitude < -50:
                tag_names.append("南半球:高纬度")
            elif latitude < -30:
                tag_names.append("南半球:中纬度")
            else:
                tag_names.append("南半球:低纬度")

    # 分辨率相关标签
    if width and height:
        # 添加分辨率标签
        if width >= 3840 or height >= 2160:
            tag_names.append("分辨率:4K")
        elif width >= 1920 or height >= 1080:
            tag_names.append("分辨率:1080p")
        elif width >= 1280 or height >= 720:
            tag_names.append("分辨率:720p")
        
        # 添加宽高比标签
        ratio = width / height if height > 0 else 1
        if abs(ratio - 16/9) < 0.1:
            tag_names.append("比例:16:9")
        elif abs(ratio - 4/3) < 0.1:
            tag_names.append("比例:4:3")
        elif abs(ratio - 1) < 0.1:
            tag_names.append("比例:1:1")
        elif abs(ratio - 9/16) < 0.1:
            tag_names.append("比例:9:16")
        
        # 添加方向标签
        if width > height:
            tag_names.append("方向:横向")
        elif height > width:
            tag_names.append("方向:纵向")
        else:
            tag_names.append("方向:正方形")

    return [name for name in tag_names if name]

# API路由
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证输入
    if not data.get('username') or len(data['username']) < 6:
        return jsonify({'error': '用户名必须至少6个字符'}), 400
    
    if not data.get('password') or len(data['password']) < 6:
        return jsonify({'error': '密码必须至少6个字符'}), 400
    
    if not data.get('email') or '@' not in data['email']:
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    # 创建用户
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        # Flask-JWT-Extended 要求 subject 为字符串，避免 422: Subject must be a string
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
    
    return jsonify({'error': '用户名或密码错误'}), 401

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_photo():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    try:
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 保存文件
        file.save(file_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        mime_type = magic.from_file(file_path, mime=True)
        
        # 获取图片尺寸
        with Image.open(file_path) as img:
            width, height = img.size
        
        # 提取EXIF数据
        exif_data = extract_exif_data(file_path)
        # 打印提取到的EXIF数据用于调试
        if exif_data:
            print(f"提取到EXIF数据: {exif_data}")
        else:
            print(f"未提取到EXIF数据，文件: {file.filename}")
        
        # 生成缩略图
        thumbnail_filename = 'thumb_' + filename
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
        generate_thumbnail(file_path, thumbnail_path)
        
        # 保存到数据库
        user_id = get_jwt_identity()
        
        # 只提取Photo模型中存在的字段
        photo_fields = {
            'taken_at': exif_data.get('taken_at'),
            'camera_make': exif_data.get('camera_make'),
            'camera_model': exif_data.get('camera_model'),
            'latitude': exif_data.get('latitude'),
            'longitude': exif_data.get('longitude'),
            'location_name': exif_data.get('location_name')
        }
        # 移除None值
        photo_fields = {k: v for k, v in photo_fields.items() if v is not None}
        
        photo = Photo(
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height,
            **photo_fields
        )
        
        db.session.add(photo)
        db.session.commit()
        
        # 基于EXIF的信息生成标签（包含分辨率信息）
        exif_tag_names = generate_exif_tag_names(exif_data, width=width, height=height)
        ensure_tags_for_photo(photo, exif_tag_names, tag_type='auto')

        # AI分析图片内容
        ai_tags = analyze_image_with_ai(file_path)
        ensure_tags_for_photo(photo, ai_tags, tag_type='auto')
        
        # 添加自定义标签
        custom_tags = request.form.get('tags', '')
        if custom_tags:
            ensure_tags_for_photo(
                photo,
                [name.strip() for name in custom_tags.split(',') if name.strip()],
                tag_type='custom'
            )
        
        db.session.commit()
        
        return jsonify({
            'message': '上传成功',
            'photo': {
                'id': photo.id,
                'filename': photo.filename,
                'original_filename': photo.original_filename,
                'width': photo.width,
                'height': photo.height,
                'file_size': photo.file_size,
                'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
                'location': photo.location_name
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/photos', methods=['GET'])
@jwt_required()
def get_photos():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    tag = request.args.get('tag', '')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    query = Photo.query.filter_by(user_id=user_id)
    
    # 搜索功能
    if search:
        query = query.filter(
            or_(
                Photo.original_filename.contains(search),
                Photo.location_name.contains(search)
            )
        )
    
    # 标签筛选
    if tag:
        query = query.join(PhotoTag).join(Tag).filter(Tag.name == tag)
    
    # 日期范围筛选（基于拍摄时间）
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            start_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        except ValueError:
            end_date = None
    
    if start_date:
        query = query.filter(Photo.taken_at >= start_date)
    if end_date:
        query = query.filter(Photo.taken_at < end_date)
    
    # 排序
    if sort_by == 'taken_at':
        query = query.order_by(getattr(Photo.taken_at, order)())
    else:
        query = query.order_by(getattr(Photo, sort_by).desc() if order == 'desc' else getattr(Photo, sort_by).asc())
    
    photos = query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = []
    for photo in photos.items:
        photo_tags = [tag.name for tag in photo.tags]
        result.append({
            'id': photo.id,
            'filename': photo.filename,
            'original_filename': photo.original_filename,
            'width': photo.width,
            'height': photo.height,
            'file_size': photo.file_size,
            'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
            'location': photo.location_name,
            'tags': photo_tags,
            'thumbnail_url': f'/api/thumbnail/{photo.id}'
        })
    
    return jsonify({
        'photos': result,
        'total': photos.total,
        'page': page,
        'per_page': per_page,
        'pages': photos.pages
    })

@app.route('/api/thumbnail/<int:photo_id>')
@jwt_required()
def get_thumbnail(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': '图片不存在'}), 404
    
    if not os.path.exists(photo.thumbnail_path):
        return jsonify({'error': '缩略图不存在'}), 404
    
    return send_file(photo.thumbnail_path)

@app.route('/api/photo/<int:photo_id>')
@jwt_required()
def get_photo(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': '图片不存在'}), 404
    
    if not os.path.exists(photo.file_path):
        return jsonify({'error': '图片文件不存在'}), 404
    
    return send_file(photo.file_path)

@app.route('/api/photo/<int:photo_id>/edit', methods=['POST'])
@jwt_required()
def edit_photo(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': '图片不存在'}), 404
    
    data = request.get_json()
    
    try:
        # 打开图片
        with Image.open(photo.file_path) as img:
            # 确保图片是RGB模式（对于JPEG格式必须）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 如果有透明通道，转换为RGB（白色背景）
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                    img = background
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 裁剪
            if 'crop' in data:
                crop_data = data['crop']
                try:
                    # 确保裁剪坐标在图片范围内
                    x = max(0, int(crop_data.get('x', 0)))
                    y = max(0, int(crop_data.get('y', 0)))
                    width = int(crop_data.get('width', 0))
                    height = int(crop_data.get('height', 0))
                    
                    # 确保裁剪区域不超出图片边界
                    width = min(width, img.width - x)
                    height = min(height, img.height - y)
                    
                    if width > 0 and height > 0 and x < img.width and y < img.height:
                        img = img.crop((
                            x,
                            y,
                            x + width,
                            y + height
                        ))
                        print(f"裁剪成功: ({x}, {y}) -> ({x+width}, {y+height}), 新尺寸: {img.size}")
                    else:
                        print(f"裁剪参数无效: x={x}, y={y}, width={width}, height={height}, 图片尺寸={img.size}")
                except Exception as e:
                    print(f"裁剪处理失败: {e}")
                    import traceback
                    traceback.print_exc()

            # 旋转（按 90 度步进）
            rotation_deg = int(data.get('rotation_deg', 0)) % 360
            if rotation_deg != 0:
                # PIL 的 rotate 正角度为逆时针，这里保持与前端一致（顺时针为正）
                img = img.rotate(-rotation_deg, expand=True)

            # 翻转
            if data.get('flip_horizontal'):
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            if data.get('flip_vertical'):
                img = img.transpose(Image.FLIP_TOP_BOTTOM)

            # 色调调整前确保图片是RGB模式
            if img.mode != 'RGB':
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                    img = background
                else:
                    img = img.convert('RGB')
            
            # 使用像素级处理，与前端算法保持一致
            # 将图片转换为numpy数组进行像素级操作
            img_array = np.array(img, dtype=np.float32)
            
            # 应用亮度调整（与前端算法一致）
            if 'brightness' in data:
                brightness_value = float(data['brightness'])
                if brightness_value != 0:
                    img_array[:, :, :3] = np.clip(img_array[:, :, :3] + brightness_value, 0, 255)
            
            # 应用对比度调整（与前端算法一致）
            if 'contrast' in data:
                contrast_value = float(data['contrast'])
                if contrast_value != 0:
                    contrast_factor = (contrast_value + 100) / 100.0
                    img_array[:, :, :3] = np.clip((img_array[:, :, :3] - 128) * contrast_factor + 128, 0, 255)
            
            # 应用饱和度调整（与前端算法一致）
            if 'saturation' in data:
                saturation_value = float(data['saturation'])
                if saturation_value != 0:
                    saturation_factor = (saturation_value + 100) / 100.0
                    # 计算灰度值（使用与前端相同的权重）
                    gray = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
                    gray = np.stack([gray, gray, gray], axis=2)
                    # 应用饱和度调整
                    img_array[:, :, :3] = np.clip(gray + (img_array[:, :, :3] - gray) * saturation_factor, 0, 255)
            
            # 应用色相调整（与前端算法一致，使用HSL）
            if 'hue' in data:
                hue_shift = float(data['hue'])
                if hue_shift != 0:
                    try:
                        # RGB转HSL（与前端算法一致）
                        def rgb_to_hsl(rgb_array):
                            """将RGB数组转换为HSL"""
                            r, g, b = rgb_array[:, :, 0] / 255.0, rgb_array[:, :, 1] / 255.0, rgb_array[:, :, 2] / 255.0
                            max_val = np.maximum(np.maximum(r, g), b)
                            min_val = np.minimum(np.minimum(r, g), b)
                            delta = max_val - min_val
                            
                            l = (max_val + min_val) / 2.0
                            s = np.zeros_like(l)
                            h = np.zeros_like(l)
                            
                            # 计算饱和度
                            mask = delta != 0
                            s[mask] = np.where(l[mask] > 0.5, delta[mask] / (2 - max_val[mask] - min_val[mask]), 
                                               delta[mask] / (max_val[mask] + min_val[mask]))
                            
                            # 计算色相
                            mask_r = (delta != 0) & (max_val == r)
                            mask_g = (delta != 0) & (max_val == g)
                            mask_b = (delta != 0) & (max_val == b)
                            
                            h[mask_r] = ((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6
                            h[mask_g] = ((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2
                            h[mask_b] = ((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4
                            
                            h = h / 6.0
                            return np.stack([h, s, l], axis=2)
                        
                        def hsl_to_rgb(hsl_array):
                            """将HSL数组转换为RGB"""
                            h, s, l = hsl_array[:, :, 0], hsl_array[:, :, 1], hsl_array[:, :, 2]
                            
                            def hue2rgb(p, q, t):
                                # 与前端算法完全一致
                                t = np.where(t < 0, t + 1, t)
                                t = np.where(t > 1, t - 1, t)
                                result = np.zeros_like(t)
                                # 分段处理，与前端hue2rgb函数一致
                                mask1 = t < 1/6
                                mask2 = (t >= 1/6) & (t < 1/2)
                                mask3 = (t >= 1/2) & (t < 2/3)
                                mask4 = t >= 2/3
                                result[mask1] = p[mask1] + (q[mask1] - p[mask1]) * 6 * t[mask1]
                                result[mask2] = q[mask2]
                                result[mask3] = p[mask3] + (q[mask3] - p[mask3]) * (2/3 - t[mask3]) * 6
                                result[mask4] = p[mask4]  # t >= 2/3 的情况
                                return result
                            
                            r = np.zeros_like(l)
                            g = np.zeros_like(l)
                            b = np.zeros_like(l)
                            
                            mask = s != 0
                            q = np.where(l[mask] < 0.5, l[mask] * (1 + s[mask]), l[mask] + s[mask] - l[mask] * s[mask])
                            p = 2 * l[mask] - q
                            
                            r[mask] = hue2rgb(p, q, h[mask] + 1/3)
                            g[mask] = hue2rgb(p, q, h[mask])
                            b[mask] = hue2rgb(p, q, h[mask] - 1/3)
                            
                            # 无饱和度的情况
                            r[~mask] = l[~mask]
                            g[~mask] = l[~mask]
                            b[~mask] = l[~mask]
                            
                            return np.stack([r * 255, g * 255, b * 255], axis=2)
                        
                        # 转换为HSL
                        hsl_array = rgb_to_hsl(img_array)
                        
                        # 应用色相偏移
                        hsl_array[:, :, 0] = (hsl_array[:, :, 0] + hue_shift / 360.0) % 1.0
                        
                        # 转换回RGB
                        img_array[:, :, :3] = hsl_to_rgb(hsl_array)
                        
                    except Exception as e:
                        print(f"色相调整失败: {e}")
                        import traceback
                        traceback.print_exc()
            
            # 转换回PIL Image
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array, 'RGB')

            # 确保最终图片是RGB模式（在保存前再次确认）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 验证图片尺寸有效
            if img.size[0] <= 0 or img.size[1] <= 0:
                raise ValueError(f"无效的图片尺寸: {img.size}")

            # 保存编辑后的图片
            # 根据文件扩展名确定保存格式
            file_ext = os.path.splitext(photo.file_path)[1].lower()
            save_kwargs = {}
            if file_ext in ['.jpg', '.jpeg']:
                save_kwargs = {'quality': 95, 'optimize': True, 'format': 'JPEG'}
            elif file_ext == '.png':
                save_kwargs = {'optimize': True, 'format': 'PNG'}
            else:
                # 默认使用JPEG格式
                save_kwargs = {'quality': 95, 'optimize': True, 'format': 'JPEG'}
            
            try:
                img.save(photo.file_path, **save_kwargs)
                print(f"图片保存成功: {photo.file_path}, 尺寸: {img.size}, 模式: {img.mode}")
            except Exception as e:
                print(f"保存图片失败: {e}")
                import traceback
                traceback.print_exc()
                raise

            # 重新生成缩略图
            generate_thumbnail(photo.file_path, photo.thumbnail_path)

            # 更新数据库中的尺寸信息
            photo.width, photo.height = img.size
            db.session.commit()

        return jsonify({'message': '编辑成功'}), 200
        
    except Exception as e:
        return jsonify({'error': f'编辑失败: {str(e)}'}), 500

@app.route('/api/photo/<int:photo_id>', methods=['DELETE'])
@jwt_required()
def delete_photo(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': '图片不存在'}), 404
    
    try:
        # 删除文件
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        
        if os.path.exists(photo.thumbnail_path):
            os.remove(photo.thumbnail_path)
        
        # 删除数据库记录
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({'message': '删除成功'}), 200
        
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/tags', methods=['GET'])
@jwt_required()
def get_tags():
    user_id = get_jwt_identity()
    
    # 获取用户的所有标签
    tags = db.session.query(Tag).join(PhotoTag).join(Photo).filter(Photo.user_id == user_id).distinct().all()
    
    result = []
    for tag in tags:
        result.append({
            'id': tag.id,
            'name': tag.name,
            'type': tag.type
        })
    
    return jsonify({'tags': result})

@app.route('/api/photo/<int:photo_id>/tags', methods=['POST', 'DELETE'])
@jwt_required()
def manage_photo_tags(photo_id):
    """为指定图片添加或删除自定义标签"""
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    if not photo:
        return jsonify({'error': '图片不存在'}), 404

    data = request.get_json() or {}
    tags = data.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    if not tags:
        return jsonify({'error': '标签不能为空'}), 400

    try:
        if request.method == 'POST':
            # 添加标签（自定义）
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, type='custom')
                    db.session.add(tag)
                    db.session.flush()

                exists = PhotoTag.query.filter_by(photo_id=photo.id, tag_id=tag.id).first()
                if not exists:
                    db.session.add(PhotoTag(photo_id=photo.id, tag_id=tag.id))

        elif request.method == 'DELETE':
            # 删除与该图片的标签关系（不删除全局标签）
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    PhotoTag.query.filter_by(photo_id=photo.id, tag_id=tag.id).delete()

        db.session.commit()

        # 返回最新标签
        return jsonify({
            'message': '操作成功',
            'tags': [t.name for t in photo.tags]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'操作失败: {str(e)}'}), 500

@app.route('/api/slideshow', methods=['POST'])
@jwt_required()
def create_slideshow():
    data = request.get_json()
    photo_ids = data.get('photo_ids', [])
    
    if not photo_ids:
        return jsonify({'error': '请选择图片'}), 400
    
    user_id = get_jwt_identity()
    photos = Photo.query.filter(Photo.id.in_(photo_ids), Photo.user_id == user_id).all()
    
    if len(photos) != len(photo_ids):
        return jsonify({'error': '部分图片不存在'}), 400
    
    result = []
    for photo in photos:
        result.append({
            'id': photo.id,
            'filename': photo.filename,
            'original_filename': photo.original_filename,
            'width': photo.width,
            'height': photo.height,
            'taken_at': photo.taken_at.isoformat() if photo.taken_at else None,
            'location': photo.location_name,
            'url': f'/api/photo/{photo.id}'
        })
    
    return jsonify({'slideshow': result})

@app.route('/api/photo/<int:photo_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_photo(photo_id):
    user_id = get_jwt_identity()
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': '图片不存在'}), 404
    
    try:
        # 使用AI分析图片
        ai_tags = analyze_image_with_ai(photo.file_path)
        
        # 添加AI标签到数据库
        for tag_name in ai_tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, type='auto')
                db.session.add(tag)
                db.session.flush()
            
            # 检查是否已存在关联
            existing_relation = PhotoTag.query.filter_by(
                photo_id=photo.id, 
                tag_id=tag.id
            ).first()
            
            if not existing_relation:
                photo_tag = PhotoTag(photo_id=photo.id, tag_id=tag.id)
                db.session.add(photo_tag)
        
        db.session.commit()
        
        return jsonify({
            'message': 'AI分析完成',
            'tags': ai_tags,
            'analysis': {
                'objects': ai_tags[:3],  # 前3个标签作为主要对象
                'scene': ai_tags[0] if ai_tags else '未知',
                'colors': [tag for tag in ai_tags if any(color in tag for color in ['红', '黄', '绿', '蓝', '紫', '黑', '白'])],
                'mood': '自然' if any(word in ' '.join(ai_tags) for word in ['自然', '风景', '天空']) else '其他'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'AI分析失败: {str(e)}'}), 500

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=BACKEND_PORT)
