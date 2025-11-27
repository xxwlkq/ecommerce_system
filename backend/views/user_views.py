#用户端页面路由
#功能：提供用户端所有页面的访问路由（前端页面渲染入口）
from flask import Blueprint, render_template, session

bp = Blueprint('user_views', __name__)

# 1. 首页
@bp.route('/')
def index():
    return render_template('user/index.html')

# 2. 商品列表页
@bp.route('/products')
def products():
    return render_template('user/products.html')

# 3. 商品详情页
@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    return render_template('user/product_detail.html', product_id=product_id)

# 4. 购物车页面
@bp.route('/cart')
def cart():
    return render_template('user/cart.html')

# 5. 确认下单页
@bp.route('/checkout')
def checkout():
    return render_template('user/checkout.html')

# 6. 个人中心-首页
@bp.route('/profile')
def profile_index():
    return render_template('user/profile/index.html')

# 7. 个人中心-我的订单
@bp.route('/profile/orders')
def profile_orders():
    return render_template('user/profile/orders.html')

# 8. 个人中心-我的收藏
@bp.route('/profile/favorites')
def profile_favorites():
    return render_template('user/profile/favorites.html')

# 9. 个人中心-收货地址
@bp.route('/profile/addresses')
def profile_addresses():
    return render_template('user/profile/addresses.html')

# 10. 个人中心-充值页面
@bp.route('/profile/recharge')
def profile_recharge():
    return render_template('user/profile/recharge.html')