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
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
        return True
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return False

def extract_exif_data(image_path):
    """提取EXIF数据"""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        
        exif_data = {}
        
        # 提取基本信息
        if 'EXIF DateTimeOriginal' in tags:
            exif_data['taken_at'] = datetime.strptime(str(tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
        
        if 'Image Make' in tags:
            exif_data['camera_make'] = str(tags['Image Make'])
        
        if 'Image Model' in tags:
            exif_data['camera_model'] = str(tags['Image Model'])
        
        if 'EXIF GPS GPSLatitude' in tags and 'EXIF GPS GPSLongitude' in tags:
            lat = float(tags['EXIF GPS GPSLatitude'])
            lon = float(tags['EXIF GPS GPSLongitude'])
            exif_data['latitude'] = lat
            exif_data['longitude'] = lon
        
        return exif_data
    except Exception as e:
        print(f"提取EXIF数据失败: {e}")
        return {}

# analyze_image_with_ai 函数已移至 utils/ai_analyzer.py
# 现在从 utils 模块导入使用

def ensure_tags_for_photo(photo, tag_names, tag_type='auto'):
    """确保给定标签已创建并与照片关联"""
    attached = []
    for tag_name in tag_names:
        cleaned = (tag_name or '').strip()
        if not cleaned:
            continue
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

def generate_exif_tag_names(exif_data):
    """基于EXIF信息生成标签名称"""
    tag_names = []
    taken_at = exif_data.get('taken_at')
    if isinstance(taken_at, datetime):
        tag_names.append(f"日期:{taken_at.strftime('%Y-%m-%d')}")
        tag_names.append(f"年份:{taken_at.year}")
        tag_names.append(f"月份:{taken_at.strftime('%Y-%m')}")

    camera_model = (exif_data.get('camera_model') or '').strip()
    camera_make = (exif_data.get('camera_make') or '').strip()
    if camera_make and camera_model:
        tag_names.append(f"相机:{camera_make} {camera_model}")
    elif camera_model:
        tag_names.append(f"相机:{camera_model}")
    elif camera_make:
        tag_names.append(f"相机品牌:{camera_make}")

    latitude = exif_data.get('latitude')
    longitude = exif_data.get('longitude')
    if latitude is not None and longitude is not None:
        tag_names.append("含地理位置")

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
        
        # 生成缩略图
        thumbnail_filename = 'thumb_' + filename
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
        generate_thumbnail(file_path, thumbnail_path)
        
        # 保存到数据库
        user_id = get_jwt_identity()
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
            **exif_data
        )
        
        db.session.add(photo)
        db.session.commit()
        
        # 基于EXIF的信息生成标签
        exif_tag_names = generate_exif_tag_names(exif_data)
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
            # 裁剪
            if 'crop' in data:
                crop_data = data['crop']
                img = img.crop((
                    int(crop_data['x']),
                    int(crop_data['y']),
                    int(crop_data['x'] + crop_data['width']),
                    int(crop_data['y'] + crop_data['height'])
                ))

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

            # 色调调整
            if 'brightness' in data:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(float(data['brightness']))
            if 'contrast' in data:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(float(data['contrast']))
            if 'saturation' in data:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(float(data['saturation']))
            if 'hue' in data:
                hue_shift = float(data['hue'])
                if hue_shift != 0:
                    hsv_img = img.convert('HSV')
                    hsv_array = np.array(hsv_img, dtype=np.uint16)
                    shift_value = int(((hue_shift % 360) / 360) * 255)
                    hsv_array[:, :, 0] = (hsv_array[:, :, 0] + shift_value) % 255
                    img = Image.fromarray(hsv_array.astype('uint8'), 'HSV').convert('RGB')

            # 保存编辑后的图片
            img.save(photo.file_path, quality=95)

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
    app.run(debug=True, host='0.0.0.0', port=5000)
