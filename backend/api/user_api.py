#用户相关 API 接口
#功能：提供用户登录、充值、收藏、地址管理等接口
from flask import Blueprint, jsonify, request, session
import json
from backend.models.user_model import UserModel
from backend.models.address_model import AddressModel
from backend.models.product_model import ProductModel
from backend.utils.upload_utils import allowed_file

bp = Blueprint('user_api', __name__)

# 1. 用户登录
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username').strip() if data.get('username') else ''
    password = data.get('password', '').strip()  # 简化版：实际可添加密码加密逻辑
    
    # 调用用户模型验证登录
    user = UserModel.verify_login(username, password)
    if user:
        # 保存用户信息到session
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']
        return jsonify({'success': True, 'msg': f'欢迎您，{user["username"]}！', 'data': user})
    return jsonify({'success': False, 'msg': '用户名或密码错误'})

# 2. 用户退出登录
@bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({'success': True, 'msg': '退出登录成功'})

# 3. 模拟充值
@bp.route('/recharge', methods=['POST'])
def recharge():
    # 验证登录状态
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    data = request.json
    amount = float(data.get('amount', 0))
    pay_method = data.get('pay_method', '')  # 微信/支付宝/建设银行
    
    if amount <= 0:
        return jsonify({'success': False, 'msg': '充值金额必须大于0'})
    if not pay_method:
        return jsonify({'success': False, 'msg': '请选择支付方式'})
    
    # 调用用户模型更新余额
    success = UserModel.recharge_balance(user_id, amount)
    if success:
        # 记录充值行为（用户行为表）
        UserModel.record_user_action(
            user_id=user_id,
            product_id=0,  # 充值无商品ID，用0占位
            action_type='recharge',
            quantity=1,
            total_amount=amount
        )
        return jsonify({'success': True, 'msg': f'使用{pay_method}充值{amount}元成功！', 'new_balance': UserModel.get_user_balance(user_id)})
    return jsonify({'success': False, 'msg': '充值失败，请重试'})

# 4. 收藏商品
@bp.route('/add_favorite', methods=['POST'])
def add_favorite():
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    data = request.json
    product_id = int(data.get('product_id', 0))
    
    # 验证商品是否存在
    product = ProductModel.get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'msg': '商品不存在'})
    
    # 调用用户模型添加收藏
    success = UserModel.add_favorite(user_id, product_id)
    if success:
        # 记录收藏行为
        UserModel.record_user_action(
            user_id=user_id,
            product_id=product_id,
            product_name=product['name'],
            product_category=product['category'],
            action_type='favorite',
            quantity=1
        )
        return jsonify({'success': True, 'msg': f'收藏商品《{product["name"]}》成功！'})
    return jsonify({'success': False, 'msg': '该商品已在收藏夹中'})

# 5. 取消收藏
@bp.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    data = request.json
    product_id = int(data.get('product_id', 0))
    
    success = UserModel.remove_favorite(user_id, product_id)
    if success:
        return jsonify({'success': True, 'msg': '取消收藏成功'})
    return jsonify({'success': False, 'msg': '该商品不在收藏夹中'})

# 6. 获取用户收藏列表
@bp.route('/get_favorites', methods=['GET'])
def get_favorites():
    user_id = session.get('user_id', 'anonymous')
    favorites = UserModel.get_user_favorites(user_id)
    # 获取收藏商品的详细信息
    favorite_products = [ProductModel.get_product_by_id(pid) for pid in favorites if ProductModel.get_product_by_id(pid)]
    return jsonify({'success': True, 'data': favorite_products})

# 7. 添加收货地址
@bp.route('/address/add', methods=['POST'])
def add_address():
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    data = request.json
    address_data = {
        'receiver': data.get('receiver', ''),
        'phone': data.get('phone', ''),
        'province': data.get('province', ''),
        'city': data.get('city', ''),
        'detail_address': data.get('detail_address', ''),
        'is_default': data.get('is_default', False)
    }
    
    # 验证必填字段
    if not all([address_data['receiver'], address_data['phone'], address_data['detail_address']]):
        return jsonify({'success': False, 'msg': '收件人、电话、详细地址不能为空'})
    
    # 调用地址模型添加地址
    address_id = AddressModel.add_address(user_id, address_data)
    if address_id:
        return jsonify({'success': True, 'msg': '添加收货地址成功', 'address_id': address_id})
    return jsonify({'success': False, 'msg': '添加地址失败'})

# 8. 获取用户收货地址
@bp.route('/address/get', methods=['GET'])
def get_addresses():
    user_id = session.get('user_id', 'anonymous')
    addresses = AddressModel.get_addresses_by_user_id(user_id)
    return jsonify({'success': True, 'data': addresses})