#后台段页面路由
#功能：提供后台端所有页面的访问路由（需管理员权限）
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('admin_views', __name__)

# 权限验证装饰器（简化版）
def admin_required(func):
    def wrapper(*args, **kwargs):
        if not session.get('is_admin', False):
            # 非管理员跳转到首页
            return redirect(url_for('user_views.index'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 1. 后台数据看板
@bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# 2. 商品管理页面
@bp.route('/product_manage')
@admin_required
def product_manage():
    return render_template('admin/product_manage.html')

# 3. 用户管理页面
@bp.route('/user_manage')
@admin_required
def user_manage():
    return render_template('admin/user_manage.html')

# 4. 订单管理页面
@bp.route('/order_manage')
@admin_required
def order_manage():
    return render_template('admin/order_manage.html')

# 5. 数据导出页面
@bp.route('/data_export')
@admin_required
def data_export():
    return render_template('admin/data_export.html')