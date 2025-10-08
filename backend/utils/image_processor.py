"""图片处理工具"""
from PIL import Image
import os


def process_image(file_path):
    """
    处理图片，获取基本信息
    返回: (width, height, file_size, mime_type)
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            mime_type = f"image/{img.format.lower()}"
        
        file_size = os.path.getsize(file_path)
        
        return width, height, file_size, mime_type
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return None, None, None, None


def generate_thumbnail(input_path, output_path, size=(300, 300)):
    """
    生成缩略图
    
    参数:
        input_path: 原图路径
        output_path: 缩略图保存路径
        size: 缩略图尺寸，默认 (300, 300)
    """
    try:
        with Image.open(input_path) as img:
            # 转换 RGBA 到 RGB（处理 PNG 透明背景）
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 生成缩略图（保持宽高比）
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 保存缩略图
            img.save(output_path, quality=85, optimize=True)
            
        return True
    except Exception as e:
        print(f"生成缩略图时出错: {e}")
        return False


def resize_image(input_path, output_path, width=None, height=None):
    """
    调整图片大小
    
    参数:
        input_path: 原图路径
        output_path: 输出路径
        width: 目标宽度
        height: 目标高度
    """
    try:
        with Image.open(input_path) as img:
            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif width:
                ratio = width / img.width
                height = int(img.height * ratio)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif height:
                ratio = height / img.height
                width = int(img.width * ratio)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            img.save(output_path, quality=90, optimize=True)
        
        return True
    except Exception as e:
        print(f"调整图片大小时出错: {e}")
        return False
