#商品相关 API 接口
#功能：提供商品查询、分类筛选、后台商品管理（增删改查）接口
from flask import Blueprint, jsonify, request, session
from backend.models.product_model import ProductModel
from backend.utils.upload_utils import allowed_file, save_uploaded_file
from backend.config import Config
import os

bp = Blueprint('product_api', __name__)

# 1. 获取所有商品（支持分类筛选）
@bp.route('/get_all', methods=['GET'])
def get_all_products():
    category = request.args.get('category', '全部商品')
    products = ProductModel.get_all_products(category=category)
    return jsonify({'success': True, 'data': products})

# 2. 获取商品详情
@bp.route('/get/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = ProductModel.get_product_by_id(product_id)
    if product:
        # 记录浏览行为（匿名用户也记录）
        user_id = session.get('user_id', 'anonymous')
        username = session.get('username', '匿名用户')
        ProductModel.record_user_action(
            user_id=user_id,
            username=username,
            product_id=product_id,
            product_name=product['name'],
            product_category=product['category'],
            action_type='view'
        )
        return jsonify({'success': True, 'data': product})
    return jsonify({'success': False, 'msg': '商品不存在'})

# 3. 后台新增商品（仅管理员可操作）
@bp.route('/admin/add', methods=['POST'])
def add_product():
    # 验证管理员权限
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'msg': '无管理员权限'})
    
    # 获取表单数据
    product_data = {
        'name': request.form.get('name', '').strip(),
        'category': request.form.get('category', '').strip(),
        'price': float(request.form.get('price', 0)),
        'stock': int(request.form.get('stock', 0)),
        'description': request.form.get('description', '').strip()
    }
    
    # 验证必填字段
    if not all([product_data['name'], product_data['category'], product_data['price'] > 0]):
        return jsonify({'success': False, 'msg': '商品名称、分类、价格不能为空，价格需大于0'})
    
    # 处理图片上传
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # 保存图片到上传目录
            image_filename = save_uploaded_file(file, Config.PRODUCT_UPLOAD_FOLDER)
            product_data['image'] = image_filename
        else:
            return jsonify({'success': False, 'msg': '图片格式不支持（仅支持png/jpg/jpeg/gif）'})
    else:
        # 无图片时使用默认图
        product_data['image'] = 'default_product.jpg'
    
    # 调用商品模型新增商品
    product_id = ProductModel.add_product(product_data)
    if product_id:
        return jsonify({'success': True, 'msg': '新增商品成功', 'product_id': product_id})
    return jsonify({'success': False, 'msg': '新增商品失败'})

# 4. 后台修改商品（仅管理员可操作）
@bp.route('/admin/update/<int:product_id>', methods=['POST'])
def update_product(product_id):
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'msg': '无管理员权限'})
    
    # 获取更新数据
    update_data = {}
    if request.form.get('name'):
        update_data['name'] = request.form.get('name').strip()
    if request.form.get('category'):
        update_data['category'] = request.form.get('category').strip()
    if request.form.get('price'):
        update_data['price'] = float(request.form.get('price'))
    if request.form.get('stock'):
        update_data['stock'] = int(request.form.get('stock'))
    if request.form.get('description'):
        update_data['description'] = request.form.get('description').strip()
    
    # 处理图片更新（可选）
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            image_filename = save_uploaded_file(file, Config.PRODUCT_UPLOAD_FOLDER)
            update_data['image'] = image_filename
    
    # 调用模型修改商品
    success = ProductModel.update_product(product_id, update_data)
    if success:
        return jsonify({'success': True, 'msg': '修改商品成功'})
    return jsonify({'success': False, 'msg': '商品不存在或修改失败'})

# 5. 后台删除商品（仅管理员可操作）
@bp.route('/admin/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'msg': '无管理员权限'})
    
    success = ProductModel.delete_product(product_id)
    if success:
        return jsonify({'success': True, 'msg': '删除商品成功'})
    return jsonify({'success': False, 'msg': '商品不存在或删除失败'})

# 6. 获取所有商品分类（用于前端筛选）
@bp.route('/get_categories', methods=['GET'])
def get_categories():
    categories = ProductModel.get_all_categories()
    return jsonify({'success': True, 'data': categories})