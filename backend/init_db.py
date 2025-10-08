"""数据库初始化脚本"""
from app import create_app
from models import db

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功!")
        print("✓ Database tables created successfully!")
        
        # 可以在这里添加初始数据
        # 例如：创建管理员用户等
        
        db.session.commit()
        print("✓ 数据库初始化完成!")
        print("✓ Database initialization completed!")


if __name__ == '__main__':
    init_database()
