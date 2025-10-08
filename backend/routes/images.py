"""图片管理路由"""
import os
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import db, Image, Tag
from utils.image_processor import process_image, generate_thumbnail
from utils.exif_extractor import extract_exif_data
import uuid
import json

images_bp = Blueprint('images', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@images_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    """上传图片"""
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    try:
        # 生成唯一文件名
        original_name = secure_filename(file.filename)
        ext = original_name.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 保存原图
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # 获取图片信息
        width, height, file_size, mime_type = process_image(file_path)
        
        # 生成缩略图
        thumbnail_folder = current_app.config['THUMBNAIL_FOLDER']
        thumbnail_path = os.path.join(thumbnail_folder, f"thumb_{filename}")
        generate_thumbnail(file_path, thumbnail_path)
        
        # 提取 EXIF 信息
        exif_data = extract_exif_data(file_path)
        exif_json = json.dumps(exif_data) if exif_data else None
        
        # 保存到数据库
        image = Image(
            user_id=current_user_id,
            filename=filename,
            original_name=original_name,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            file_size=file_size,
            mime_type=mime_type,
            exif_data=exif_json
        )
        
        db.session.add(image)
        
        # 从 EXIF 自动生成标签
        auto_tags = []
        if exif_data:
            # 添加日期标签
            if 'DateTime' in exif_data:
                date_str = exif_data['DateTime'].split()[0].replace(':', '-')
                auto_tags.append(f"date:{date_str}")
            
            # 添加相机标签
            if 'Model' in exif_data:
                auto_tags.append(f"camera:{exif_data['Model']}")
        
        # 添加自动标签
        for tag_name in auto_tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            image.tags.append(tag)
        
        db.session.commit()
        
        return jsonify({
            'message': '上传成功',
            'image': image.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # 删除已保存的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        if 'thumbnail_path' in locals() and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@images_bp.route('', methods=['GET'])
@jwt_required()
def get_images():
    """获取图片列表"""
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Image.query.filter_by(user_id=current_user_id).order_by(
        Image.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'images': [img.to_dict() for img in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@images_bp.route('/<int:image_id>', methods=['GET'])
@jwt_required()
def get_image(image_id):
    """获取图片详情"""
    current_user_id = get_jwt_identity()
    
    image = Image.query.filter_by(id=image_id, user_id=current_user_id).first()
    
    if not image:
        return jsonify({'error': '图片不存在'}), 404
    
    return jsonify(image.to_dict()), 200


@images_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    """删除图片"""
    current_user_id = get_jwt_identity()
    
    image = Image.query.filter_by(id=image_id, user_id=current_user_id).first()
    
    if not image:
        return jsonify({'error': '图片不存在'}), 404
    
    try:
        # 删除文件
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        if image.thumbnail_path and os.path.exists(image.thumbnail_path):
            os.remove(image.thumbnail_path)
        
        # 删除数据库记录
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': '删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@images_bp.route('/<int:image_id>/tags', methods=['POST'])
@jwt_required()
def add_tag(image_id):
    """添加标签"""
    current_user_id = get_jwt_identity()
    
    image = Image.query.filter_by(id=image_id, user_id=current_user_id).first()
    
    if not image:
        return jsonify({'error': '图片不存在'}), 404
    
    data = request.get_json()
    tag_name = data.get('tag', '').strip()
    
    if not tag_name:
        return jsonify({'error': '标签名不能为空'}), 400
    
    # 查找或创建标签
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.session.add(tag)
    
    # 添加标签到图片
    if tag not in image.tags:
        image.tags.append(tag)
        db.session.commit()
    
    return jsonify({
        'message': '标签添加成功',
        'image': image.to_dict()
    }), 200


@images_bp.route('/<int:image_id>/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def remove_tag(image_id, tag_id):
    """删除标签"""
    current_user_id = get_jwt_identity()
    
    image = Image.query.filter_by(id=image_id, user_id=current_user_id).first()
    
    if not image:
        return jsonify({'error': '图片不存在'}), 404
    
    tag = Tag.query.get(tag_id)
    
    if not tag:
        return jsonify({'error': '标签不存在'}), 404
    
    if tag in image.tags:
        image.tags.remove(tag)
        db.session.commit()
    
    return jsonify({'message': '标签删除成功'}), 200


@images_bp.route('/file/<filename>', methods=['GET'])
def get_file(filename):
    """获取图片文件"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(file_path)


@images_bp.route('/thumbnail/<filename>', methods=['GET'])
def get_thumbnail(filename):
    """获取缩略图"""
    thumbnail_folder = current_app.config['THUMBNAIL_FOLDER']
    file_path = os.path.join(thumbnail_folder, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    return send_file(file_path)
