#购物车相关 API 接口
#功能：提供购物车添加、移除、更新数量、查询等接口

from flask import Blueprint, jsonify, request, session
from backend.models.cart_model import CartModel  # 现在能正常导入
from backend.models.product_model import ProductModel
from backend.models.user_model import UserModel

bp = Blueprint('cart_api', __name__)

# 1. 添加商品到购物车
@bp.route('/add', methods=['POST'])
def add_to_cart():
    user_id = session.get('user_id', 'anonymous')
    username = session.get('username', '匿名用户')
    
    data = request.json
    product_id = int(data.get('product_id', 0))
    quantity = int(data.get('quantity', 1))
    
    # 验证商品
    product = ProductModel.get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'msg': '商品不存在'})
    if quantity <= 0 or quantity > product['stock']:
        return jsonify({'success': False, 'msg': f'购买数量无效（库存{product["stock"]}件）'})
    
    # 调用购物车模型添加商品
    success = CartModel.add_to_cart(user_id, product_id, quantity)
    if success:
        # 记录加购行为
        UserModel.record_user_action(
            user_id=user_id,
            username=username,
            product_id=product_id,
            product_name=product['name'],
            product_category=product['category'],
            action_type='add_to_cart',
            quantity=quantity
        )
        # 返回更新后的购物车信息
        cart_items = CartModel.get_cart_items(user_id)
        return jsonify({
            'success': True,
            'msg': f'添加{product["name"]}×{quantity}到购物车成功',
            'cart_count': len(cart_items),
            'total_amount': CartModel.get_cart_total(user_id)
        })
    return jsonify({'success': False, 'msg': '添加购物车失败'})

# 2. 从购物车移除商品
@bp.route('/remove', methods=['POST'])
def remove_from_cart():
    user_id = session.get('user_id', 'anonymous')
    data = request.json
    product_id = int(data.get('product_id', 0))
    
    success = CartModel.remove_from_cart(user_id, product_id)
    if success:
        # 记录移除行为
        product = ProductModel.get_product_by_id(product_id)
        if product:
            UserModel.record_user_action(
                user_id=user_id,
                product_id=product_id,
                product_name=product['name'],
                action_type='remove_from_cart',
                quantity=1
            )
        # 返回更新后的购物车信息
        cart_items = CartModel.get_cart_items(user_id)
        return jsonify({
            'success': True,
            'msg': '移除商品成功',
            'cart_count': len(cart_items),
            'total_amount': CartModel.get_cart_total(user_id)
        })
    return jsonify({'success': False, 'msg': '商品不在购物车中'})

# 3. 更新购物车商品数量
@bp.route('/update_quantity', methods=['POST'])
def update_quantity():
    user_id = session.get('user_id', 'anonymous')
    data = request.json
    product_id = int(data.get('product_id', 0))
    new_quantity = int(data.get('quantity', 1))
    
    # 验证数量和库存
    product = ProductModel.get_product_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'msg': '商品不存在'})
    if new_quantity <= 0 or new_quantity > product['stock']:
        return jsonify({'success': False, 'msg': f'数量无效（库存{product["stock"]}件）'})
    
    success = CartModel.update_cart_quantity(user_id, product_id, new_quantity)
    if success:
        # 记录更新行为
        UserModel.record_user_action(
            user_id=user_id,
            product_id=product_id,
            product_name=product['name'],
            action_type='update_cart_quantity',
            quantity=new_quantity
        )
        # 返回更新后的购物车信息
        cart_items = CartModel.get_cart_items(user_id)
        return jsonify({
            'success': True,
            'msg': '更新数量成功',
            'cart_count': len(cart_items),
            'total_amount': CartModel.get_cart_total(user_id)
        })
    return jsonify({'success': False, 'msg': '更新数量失败'})

# 4. 获取用户购物车
@bp.route('/get', methods=['GET'])
def get_cart():
    user_id = session.get('user_id', 'anonymous')
    cart_items = CartModel.get_cart_items(user_id)
    total_amount = CartModel.get_cart_total(user_id)
    return jsonify({
        'success': True,
        'data': cart_items,
        'cart_count': len(cart_items),
        'total_amount': total_amount
    })

# 5. 清空购物车
@bp.route('/clear', methods=['POST'])
def clear_cart():
    user_id = session.get('user_id', 'anonymous')
    CartModel.clear_cart(user_id)
    return jsonify({'success': True, 'msg': '清空购物车成功'})