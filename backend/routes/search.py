"""搜索路由"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Image, Tag
from datetime import datetime
import json

search_bp = Blueprint('search', __name__)


@search_bp.route('', methods=['GET'])
@jwt_required()
def search_images():
    """搜索图片"""
    current_user_id = get_jwt_identity()
    
    # 获取搜索参数
    keyword = request.args.get('q', '').strip()
    tag_names = request.args.get('tags', '').strip()
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 构建查询
    query = Image.query.filter_by(user_id=current_user_id)
    
    # 关键词搜索（文件名）
    if keyword:
        query = query.filter(
            (Image.original_name.ilike(f'%{keyword}%')) |
            (Image.filename.ilike(f'%{keyword}%'))
        )
    
    # 标签搜索
    if tag_names:
        tag_list = [t.strip() for t in tag_names.split(',') if t.strip()]
        for tag_name in tag_list:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                query = query.filter(Image.tags.contains(tag))
    
    # 日期范围搜索
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Image.upload_time >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Image.upload_time <= end)
        except ValueError:
            pass
    
    # 执行查询
    pagination = query.order_by(Image.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'images': [img.to_dict() for img in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@search_bp.route('/tags', methods=['GET'])
@jwt_required()
def get_all_tags():
    """获取所有标签"""
    tags = Tag.query.all()
    
    return jsonify({
        'tags': [tag.to_dict() for tag in tags]
    }), 200


@search_bp.route('/by-date', methods=['GET'])
@jwt_required()
def search_by_date():
    """按日期搜索"""
    current_user_id = get_jwt_identity()
    
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Image.query.filter_by(user_id=current_user_id)
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Image.upload_time >= start)
        except ValueError:
            return jsonify({'error': '开始日期格式不正确'}), 400
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Image.upload_time <= end)
        except ValueError:
            return jsonify({'error': '结束日期格式不正确'}), 400
    
    pagination = query.order_by(Image.upload_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'images': [img.to_dict() for img in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@search_bp.route('/by-exif', methods=['GET'])
@jwt_required()
def search_by_exif():
    """按 EXIF 信息搜索"""
    current_user_id = get_jwt_identity()
    
    camera_model = request.args.get('camera', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Image.query.filter_by(user_id=current_user_id)
    
    if camera_model:
        # 搜索 EXIF 数据中包含特定相机型号的图片
        query = query.filter(Image.exif_data.ilike(f'%{camera_model}%'))
    
    pagination = query.order_by(Image.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'images': [img.to_dict() for img in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200
