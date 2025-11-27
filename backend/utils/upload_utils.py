#图片上传工具
#功能：提供图片上传验证、保存等通用工具函数
import os
import uuid
from backend.config import Config

def allowed_file(filename):
    """验证文件是否为允许的图片格式"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder):
    """保存上传的图片（重命名避免冲突）"""
    # 生成唯一文件名（避免重复）
    # 错误修正：将filename改为file.filename（文件对象的文件名属性）
    file_ext = file.filename.rsplit('.', 1)[1].lower()  # 原错误：filename → file.filename
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
    # 保存文件
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    return unique_filename

def get_uploaded_file_path(filename):
    """获取上传图片的完整路径"""
    return os.path.join(Config.PRODUCT_UPLOAD_FOLDER, filename)