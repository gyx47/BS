import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系：一个用户有多张图片
    images = db.relationship('Image', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Image(db.Model):
    """图片模型"""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(50))
    exif_data = db.Column(db.Text)  # JSON 格式存储
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系：一张图片有多个标签
    tags = db.relationship('Tag', secondary='image_tags', backref='images', lazy='dynamic')
    
    def to_dict(self, include_tags=True):
        """转换为字典"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'thumbnail_path': self.thumbnail_path,
            'width': self.width,
            'height': self.height,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'exif_data': self.exif_data,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_tags:
            result['tags'] = [tag.to_dict() for tag in self.tags]
        return result


class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# 图片标签关联表
image_tags = db.Table('image_tags',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('image_id', db.Integer, db.ForeignKey('images.id'), nullable=False),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), nullable=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
