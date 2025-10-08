"""输入验证工具"""
import re


def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """验证用户名（至少6个字符）"""
    return len(username.encode('utf-8')) >= 6


def validate_password(password):
    """验证密码（至少6个字节）"""
    return len(password.encode('utf-8')) >= 6
