"""EXIF 信息提取工具"""
from PIL import Image
import piexif
from datetime import datetime


def extract_exif_data(image_path):
    """
    提取图片的 EXIF 信息
    
    返回一个字典，包含:
    - DateTime: 拍摄时间
    - Make: 相机制造商
    - Model: 相机型号
    - Orientation: 方向
    - XResolution, YResolution: 分辨率
    - GPS: GPS 坐标
    等等
    """
    try:
        exif_dict = {}
        
        # 使用 PIL 读取 EXIF 数据
        img = Image.open(image_path)
        
        if hasattr(img, '_getexif') and img._getexif():
            exif_data = img._getexif()
            
            # EXIF 标签映射
            exif_tags = {
                0x010f: 'Make',           # 制造商
                0x0110: 'Model',          # 型号
                0x0112: 'Orientation',    # 方向
                0x011a: 'XResolution',    # X 分辨率
                0x011b: 'YResolution',    # Y 分辨率
                0x0132: 'DateTime',       # 拍摄时间
                0x829a: 'ExposureTime',   # 曝光时间
                0x829d: 'FNumber',        # 光圈
                0x8827: 'ISOSpeedRatings', # ISO
                0x920a: 'FocalLength',    # 焦距
            }
            
            for tag_id, tag_name in exif_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    # 处理某些特殊值
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except:
                            value = str(value)
                    exif_dict[tag_name] = str(value)
        
        # 使用 piexif 提取更详细的信息
        try:
            exif_data = piexif.load(image_path)
            
            # 提取 GPS 信息
            if 'GPS' in exif_data and exif_data['GPS']:
                gps_data = exif_data['GPS']
                
                # GPS 纬度
                if piexif.GPSIFD.GPSLatitude in gps_data:
                    lat = gps_data[piexif.GPSIFD.GPSLatitude]
                    lat_ref = gps_data.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode('utf-8')
                    latitude = convert_to_degrees(lat)
                    if lat_ref == 'S':
                        latitude = -latitude
                    exif_dict['GPSLatitude'] = latitude
                
                # GPS 经度
                if piexif.GPSIFD.GPSLongitude in gps_data:
                    lon = gps_data[piexif.GPSIFD.GPSLongitude]
                    lon_ref = gps_data.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode('utf-8')
                    longitude = convert_to_degrees(lon)
                    if lon_ref == 'W':
                        longitude = -longitude
                    exif_dict['GPSLongitude'] = longitude
            
            # 提取相机信息
            if '0th' in exif_data:
                zero_ifd = exif_data['0th']
                
                if piexif.ImageIFD.Make in zero_ifd:
                    make = zero_ifd[piexif.ImageIFD.Make]
                    if isinstance(make, bytes):
                        exif_dict['Make'] = make.decode('utf-8').strip('\x00')
                
                if piexif.ImageIFD.Model in zero_ifd:
                    model = zero_ifd[piexif.ImageIFD.Model]
                    if isinstance(model, bytes):
                        exif_dict['Model'] = model.decode('utf-8').strip('\x00')
                
                if piexif.ImageIFD.DateTime in zero_ifd:
                    dt = zero_ifd[piexif.ImageIFD.DateTime]
                    if isinstance(dt, bytes):
                        exif_dict['DateTime'] = dt.decode('utf-8')
            
            # 提取 EXIF 信息
            if 'Exif' in exif_data:
                exif_ifd = exif_data['Exif']
                
                if piexif.ExifIFD.ISOSpeedRatings in exif_ifd:
                    exif_dict['ISO'] = str(exif_ifd[piexif.ExifIFD.ISOSpeedRatings])
                
                if piexif.ExifIFD.FNumber in exif_ifd:
                    f_number = exif_ifd[piexif.ExifIFD.FNumber]
                    if isinstance(f_number, tuple):
                        exif_dict['Aperture'] = f"f/{f_number[0] / f_number[1]:.1f}"
                
                if piexif.ExifIFD.ExposureTime in exif_ifd:
                    exp_time = exif_ifd[piexif.ExifIFD.ExposureTime]
                    if isinstance(exp_time, tuple):
                        exif_dict['ExposureTime'] = f"{exp_time[0]}/{exp_time[1]}"
                
                if piexif.ExifIFD.FocalLength in exif_ifd:
                    focal = exif_ifd[piexif.ExifIFD.FocalLength]
                    if isinstance(focal, tuple):
                        exif_dict['FocalLength'] = f"{focal[0] / focal[1]:.1f}mm"
        
        except Exception as e:
            print(f"piexif 提取失败: {e}")
        
        return exif_dict if exif_dict else None
        
    except Exception as e:
        print(f"提取 EXIF 信息时出错: {e}")
        return None


def convert_to_degrees(value):
    """
    将 GPS 坐标从度/分/秒格式转换为十进制度
    
    参数:
        value: ((degrees_num, degrees_den), (minutes_num, minutes_den), (seconds_num, seconds_den))
    
    返回:
        float: 十进制度数
    """
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    
    return d + (m / 60.0) + (s / 3600.0)
