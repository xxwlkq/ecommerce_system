#订单相关 API 接口
#功能：提供订单创建、查询、取消等接口
from flask import Blueprint, jsonify, request, session
from backend.models.order_model import OrderModel
from backend.models.cart_model import CartModel  # 现在能正常导入
from backend.models.user_model import UserModel
from backend.models.product_model import ProductModel
from datetime import datetime

bp = Blueprint('order_api', __name__)

# 1. 创建订单（从购物车结算）
@bp.route('/create', methods=['POST'])
def create_order():
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    data = request.json
    address_id = int(data.get('address_id', 0))  # 收货地址ID
    
    # 1. 验证购物车是否为空
    cart_items = CartModel.get_cart_items(user_id)
    if not cart_items:
        return jsonify({'success': False, 'msg': '购物车为空，无法创建订单'})
    
    # 2. 验证收货地址
    from backend.models.address_model import AddressModel
    address = AddressModel.get_address_by_id(address_id, user_id)
    if not address:
        return jsonify({'success': False, 'msg': '请选择有效的收货地址'})
    
    # 3. 验证用户余额
    total_amount = CartModel.get_cart_total(user_id)
    user_balance = UserModel.get_user_balance(user_id)
    if user_balance < total_amount:
        return jsonify({'success': False, 'msg': f'余额不足（当前余额：{user_balance}元，订单金额：{total_amount}元）', 'need_recharge': True})
    
    # 4. 验证商品库存（防止超卖）
    for item in cart_items:
        product = ProductModel.get_product_by_id(item['product_id'])
        if not product or product['stock'] < item['quantity']:
            return jsonify({'success': False, 'msg': f'商品《{item["name"]}》库存不足，无法下单'})
    
    # 5. 调用订单模型创建订单
    order_data = {
        'user_id': user_id,
        'username': session.get('username', '匿名用户'),
        'product_ids': [item['product_id'] for item in cart_items],
        'product_names': [item['name'] for item in cart_items],
        'quantities': [item['quantity'] for item in cart_items],
        'total_amount': total_amount,
        'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': '已支付'  # 简化版：直接标记为已支付
    }
    order_id = OrderModel.create_order(order_data)
    if order_id:
        # 6. 扣减用户余额
        UserModel.recharge_balance(user_id, -total_amount)  # 负数表示扣减
        
        # 7. 扣减商品库存
        for item in cart_items:
            ProductModel.update_product_stock(item['product_id'], -item['quantity'])
        
        # 8. 记录购买行为
        for item in cart_items:
            UserModel.record_user_action(
                user_id=user_id,
                product_id=item['product_id'],
                product_name=item['name'],
                product_category=item['category'],
                action_type='purchase',
                quantity=item['quantity'],
                total_amount=item['subtotal']
            )
        
        # 9. 清空购物车
        CartModel.clear_cart(user_id)
        
        return jsonify({
            'success': True,
            'msg': '下单成功！',
            'order_id': order_id,
            'total_amount': total_amount,
            'new_balance': UserModel.get_user_balance(user_id)
        })
    return jsonify({'success': False, 'msg': '创建订单失败，请重试'})

# 2. 获取用户订单列表
@bp.route('/get_user_orders', methods=['GET'])
def get_user_orders():
    user_id = session.get('user_id', 'anonymous')
    orders = OrderModel.get_orders_by_user_id(user_id)
    return jsonify({'success': True, 'data': orders})

# 3. 获取订单详情
@bp.route('/get/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    user_id = session.get('user_id', 'anonymous')
    order = OrderModel.get_order_by_id(order_id)
    
    # 验证订单归属（普通用户只能看自己的订单，管理员可看所有）
    if not order:
        return jsonify({'success': False, 'msg': '订单不存在'})
    if not session.get('is_admin', False) and order['user_id'] != user_id:
        return jsonify({'success': False, 'msg': '无权限查看该订单'})
    
    return jsonify({'success': True, 'data': order})

# 4. 后台获取所有订单（仅管理员）
@bp.route('/admin/get_all', methods=['GET'])
def get_all_orders():
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'msg': '无管理员权限'})
    
    orders = OrderModel.get_all_orders()
    return jsonify({'success': True, 'data': orders})

# 5. 取消订单（仅未发货订单）
@bp.route('/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        return jsonify({'success': False, 'msg': '请先登录'})
    
    order = OrderModel.get_order_by_id(order_id)
    if not order:
        return jsonify({'success': False, 'msg': '订单不存在'})
    if order['user_id'] != user_id and not session.get('is_admin', False):
        return jsonify({'success': False, 'msg': '无权限取消该订单'})
    if order['status'] != '已支付':
        return jsonify({'success': False, 'msg': '只有已支付订单可取消'})
    
    # 调用订单模型取消订单
    success = OrderModel.update_order_status(order_id, '已取消')
    if success:
        # 返还用户余额
        UserModel.recharge_balance(user_id, order['total_amount'])
        
        # 返还商品库存
        product_ids = eval(order['product_ids'])  # 字符串转列表
        quantities = eval(order['quantities'])   # 字符串转列表
        for pid, qty in zip(product_ids, quantities):
            ProductModel.update_product_stock(pid, qty)
        
        return jsonify({'success': True, 'msg': '订单取消成功，余额已返还', 'new_balance': UserModel.get_user_balance(user_id)})
    return jsonify({'success': False, 'msg': '取消订单失败'})