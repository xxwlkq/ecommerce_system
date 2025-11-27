from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import pandas as pd
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import csv
import uuid

# ---------------------- 核心路径配置（关键修改！）----------------------
# 获取项目根目录绝对路径（兼容Windows/Mac/Linux）
base_dir = os.path.dirname(os.path.abspath(__file__))

# 配置模板目录（指向 frontend/templates）
template_dir = os.path.join(base_dir, 'frontend', 'templates')
# 配置静态资源目录（指向 frontend/static）
static_dir = os.path.join(base_dir, 'frontend', 'static')

# 初始化应用（指定模板和静态资源路径）
app = Flask(
    __name__,
    template_folder=template_dir,  # 告诉Flask模板在这里
    static_folder=static_dir,      # 告诉Flask静态资源在这里
    static_url_path='/static'      # 前端引用静态资源仍用 /static 前缀（和你前端代码一致）
)
app.secret_key = 'ecommerce_2024_project_123'  # 加密session
app.config['JSON_AS_ASCII'] = False  # 解决中文乱码
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 模板热更新

# ---------------------- 目录创建（修正静态资源路径！）----------------------
# 确保 data 目录存在（存储CSV数据）
os.makedirs('data', exist_ok=True)
# 确保静态资源的 images 目录存在（修正为 frontend/static/images）
os.makedirs(os.path.join(static_dir, 'images'), exist_ok=True)
# 确保后台商品图片上传目录存在（frontend/static/admin/uploads/products）
os.makedirs(os.path.join(static_dir, 'admin', 'uploads', 'products'), exist_ok=True)

# ---------------------- 基础工具函数 ----------------------
def load_products(category=None):
    """加载商品数据（支持分类筛选）"""
    product_path = r"D:\code1\ruanjiangongcheng\ecommerce_system\data\products.csv"
    if not os.path.exists(product_path):
        create_default_products()  # 无数据时创建默认商品
    
    df = pd.read_csv(product_path, encoding='utf-8-sig')
    # 分类筛选
    if category and category != '全部商品':
        df = df[df['category'] == category]
    return df.to_dict('records')

def create_default_products():
    """创建默认商品（首次运行自动生成）"""
    default_products = [
        {'product_id': 1, 'name': 'iPhone 15 Pro', 'category': '手机数码', 'price': 7999, 'stock': 100, 'description': 'A17 Pro芯片，超视网膜XDR显示屏，IP68防水', 'image': 'iphone15.jpg'},
        {'product_id': 2, 'name': 'MacBook Air', 'category': '电脑办公', 'price': 8999, 'stock': 50, 'description': 'M2芯片，13.6英寸Liquid视网膜屏，续航18小时', 'image': 'macbook.jpg'},
        {'product_id': 3, 'name': 'AirPods Pro 2', 'category': '手机数码', 'price': 1999, 'stock': 200, 'description': '主动降噪，空间音频，MagSafe充电盒', 'image': 'airpods.jpg'},
        {'product_id': 4, 'name': '华为Mate 60 Pro', 'category': '手机数码', 'price': 6999, 'stock': 80, 'description': '麒麟9000S芯片，卫星通信，超光变XMO摄影', 'image': 'huawei_mate60.jpg'},
        {'product_id': 5, 'name': '小米平板6', 'category': '电脑办公', 'price': 2499, 'stock': 150, 'description': '2.8K LCD屏，骁龙870处理器，支持触控笔', 'image': 'mi_pad6.jpg'},
        {'product_id': 6, 'name': '戴森吹风机', 'category': '家居用品', 'price': 2790, 'stock': 60, 'description': '负离子护发，6档风速调节，快速干发', 'image': 'dyson_hairdryer.jpg'},
        {'product_id': 7, 'name': 'SK-II神仙水', 'category': '美妆护肤', 'price': 1590, 'stock': 90, 'description': 'PITERA™核心成分，调节肌肤水油平衡', 'image': 'sk2.jpg'},
        {'product_id': 8, 'name': 'Nike Air Max', 'category': '服装鞋帽', 'price': 1299, 'stock': 120, 'description': '全掌气垫缓震，网面透气，经典配色', 'image': 'nike_airmax.jpg'},
    ]
    pd.DataFrame(default_products).to_csv('data/products.csv', index=False, encoding='utf-8-sig')

def get_cart():
    """获取购物车（session存储，格式：{product_id_str: 数量}）"""
    return session.get('cart', {})

def get_cart_items():
    """获取购物车商品详情（含名称、价格、小计）"""
    cart = get_cart()
    products = load_products()
    cart_items = []
    
    for pid_str, quantity in cart.items():
        product = next((p for p in products if p['product_id'] == int(pid_str)), None)
        if product:  # 这行你已经有了，不用加！
            cart_items.append({
                'product_id': product['product_id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity,
                'subtotal': product['price'] * quantity,
                'stock': product['stock']  
            })
    return cart_items

def record_user_action(user_id, product_id, action_type, **kwargs):
    """记录用户行为到user_actions.csv（修复session_id的获取）"""
    product = next((p for p in load_products() if p['product_id'] == int(product_id)), None)
    # 修复：Flask默认Session没有sid，改用session的内置_id（或手动生成唯一标识）
    session_id = session.get('_id')  # 若不存在，生成一个唯一标识并存入session
    if not session_id:
        session_id = str(uuid.uuid4())  # 生成UUID作为Session标识
        session['_id'] = session_id
    
    action_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': user_id,
        'username': session.get('username', '匿名用户'),
        'product_id': product_id,
        'product_name': product['name'] if product else '',
        'product_category': product['category'] if product else '',
        'action_type': action_type,
        'session_id': session_id,  # 改用修复后的session_id
        'quantity': kwargs.get('quantity', 1),
        'total_amount': kwargs.get('total_amount', 0)
    }
    # 写入CSV
    csv_path = 'data/user_actions.csv'
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig') if os.path.exists(csv_path) else pd.DataFrame(columns=action_data.keys())
        new_row = pd.DataFrame([action_data])
        pd.concat([df, new_row], ignore_index=True).to_csv(csv_path, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"行为记录失败：{e}")

def fig_to_base64(fig):
    """matplotlib图表转base64（用于前端展示）"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def generate_charts(df):
    """生成4类核心分析图表"""
    charts = {}
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    # 1. 用户行为分布饼图
    action_counts = df['action_type'].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(action_counts.values, labels=action_counts.index, autopct='%1.1f%%', startangle=90)
    ax.set_title('用户行为分布')
    charts['action_distribution'] = fig_to_base64(fig)
    plt.close()
    
    # 2. 热门商品TOP5柱状图
    top_products = df[df['action_type'] == 'view']['product_name'].value_counts().head(5)
    fig, ax = plt.subplots(figsize=(8, 4))
    top_products.plot(kind='bar', ax=ax, color='#3498db')
    ax.set_title('热门商品浏览TOP5')
    ax.set_xlabel('商品名称')
    ax.set_ylabel('浏览次数')
    plt.xticks(rotation=45, ha='right')
    charts['top_products'] = fig_to_base64(fig)
    plt.close()
    
    # 3. 每日行为趋势折线图
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_actions = df.groupby('date').size()
    fig, ax = plt.subplots(figsize=(10, 4))
    daily_actions.plot(kind='line', ax=ax, marker='o', color='#e74c3c')
    ax.set_title('每日用户行为趋势')
    ax.set_xlabel('日期')
    ax.set_ylabel('行为次数')
    plt.xticks(rotation=45)
    charts['daily_trend'] = fig_to_base64(fig)
    plt.close()
    
    # 4. 商品分类占比饼图
    category_counts = df['product_category'].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
    ax.set_title('商品分类访问占比')
    charts['category_distribution'] = fig_to_base64(fig)
    plt.close()
    
    return charts

# ---------------------- 页面路由（修正模板路径！）----------------------
@app.route('/')
def index():
    """系统首页（欢迎+推荐商品）"""
    recommended_products = load_products()[:4]  # 前4个商品作为推荐
    return render_template('user/index.html', recommended_products=recommended_products)

@app.route('/products')
def products():
    """商品列表页（支持分类筛选）"""
    category = request.args.get('category', '全部商品')
    all_products = load_products(category=category)
    # 获取所有分类（去重）
    all_categories = ['全部商品'] + list(set(p['category'] for p in load_products()))
    return render_template('user/products.html', 
                         products=all_products,
                         current_category=category,
                         all_categories=all_categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """商品详情页（修复属性错误）"""
    product = next((p for p in load_products() if p['product_id'] == product_id), None)
    if not product:
        return redirect(url_for('products'))  # 商品不存在跳转到列表页
    
    # 记录“浏览”行为（已修复session_id问题）
    record_user_action(
        user_id=session.get('user_id', 'anonymous'),
        product_id=product_id,
        action_type='view'
    )
    return render_template('user/product_detail.html', product=product)

@app.route('/cart')
def cart():
    """购物车页面（空购物车不跳转，显示提示）"""
    cart_items = get_cart_items()
    total_quantity = sum(item['quantity'] for item in cart_items)
    total_amount = sum(item['subtotal'] for item in cart_items)
    return render_template('user/cart.html', 
                         cart_items=cart_items,
                         total_quantity=total_quantity,
                         total_amount=total_amount,
                         is_empty=len(cart_items) == 0)  # 传递空购物车标识，模板显示提示

@app.route('/profile')
def profile():
    """个人中心（用户信息+行为统计）"""
    user_id = session.get('user_id', 'anonymous')
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')  # 默认头像
    }
    
    # 个人行为统计
    stats = {'view_count': 0, 'cart_count': 0, 'purchase_count': 0}
    if os.path.exists('data/user_actions.csv'):
        df = pd.read_csv('data/user_actions.csv', encoding='utf-8-sig')
        user_actions = df[df['user_id'] == user_id]
        stats = {
            'view_count': len(user_actions[user_actions['action_type'] == 'view']),
            'cart_count': len(user_actions[user_actions['action_type'] == 'add_to_cart']),
            'purchase_count': len(user_actions[user_actions['action_type'] == 'purchase'])
        }
    return render_template('user/profile/index.html', user_info=user_info, stats=stats)

# ---------------------- 新增：个人中心子页面路由（解决404）----------------------
@app.route('/profile/orders')
def profile_orders():
    """个人中心 - 我的订单（强化items字段校验）"""
    user_id = session.get('user_id', 'anonymous')
    orders = []
    all_products = load_products()
    product_map = {p['product_id']: p for p in all_products}
    
    # 构建user_info（保留）
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')
    }

    # 从CSV读取订单（保留原有逻辑）
    if os.path.exists('data/user_actions.csv'):
        df = pd.read_csv('data/user_actions.csv', encoding='utf-8-sig')
        purchase_actions = df[(df['user_id'] == user_id) & (df['action_type'] == 'purchase')].copy()
        if not purchase_actions.empty:
            purchase_actions['product_id'] = purchase_actions['product_id'].astype(int)
            order_groups = purchase_actions.groupby('timestamp')
            order_id = 2000
            for timestamp, group in order_groups:
                order_items = []
                for _, action in group.iterrows():
                    product = product_map.get(action['product_id'], {})
                    order_items.append({
                        'name': product.get('name', '未知商品'),
                        'image': product.get('image', 'default.jpg'),
                        'quantity': int(action.get('quantity', 1)),
                        'price': product.get('price', 0)
                    })
                orders.append({
                    'order_id': f'USER_ORDER_{order_id}',
                    'create_time': timestamp,
                    'total_amount': round(group['total_amount'].sum(), 2),
                    'status': '已支付',
                    'items': order_items,  # 确保是列表
                    'product_count': len(order_items)
                })
                order_id += 1

    # 无订单时的示例（保留）
    if not orders:
        orders = [
            {
                'order_id': 'USER_ORDER_2001',
                'create_time': '2025-11-20 15:30:00',
                'total_amount': 9998.00,
                'status': '已支付',
                'product_count': 2,
                'items': [  # 确保是列表
                    {'name': 'iPhone 15 Pro', 'image': 'iphone15.jpg', 'quantity': 1, 'price': 7999},
                    {'name': 'AirPods Pro 2', 'image': 'airpods.jpg', 'quantity': 1, 'price': 1999}
                ]
            }
        ]

    # ---------------------- 强化校验：强制所有订单的items是列表 ----------------------
    fixed_orders = []
    for order in orders:
        # 确保order是字典（避免非字典对象）
        if not isinstance(order, dict):
            order = {}
        # 强制设置items为列表（不管原来是什么类型）
        order_items = order.get('items', [])
        if not isinstance(order_items, list):
            order_items = []  # 非列表类型直接转为空列表
        # 重新构建订单，确保字段完整
        fixed_order = {
            'order_id': order.get('order_id', f'ORDER_{len(fixed_orders)+1}'),
            'create_time': order.get('create_time', ''),
            'total_amount': order.get('total_amount', 0.00),
            'status': order.get('status', '未知状态'),
            'product_count': len(order_items),  # 用实际商品数量
            'items': order_items  # 确保是列表
        }
        fixed_orders.append(fixed_order)
    # 替换为修复后的订单列表
    orders = fixed_orders
    # --------------------------------------------------------------------------------

    return render_template('user/profile/orders.html', orders=orders, user_info=user_info)

@app.route('/profile/favorites')
def profile_favorites():
    """个人中心 - 我的收藏"""
    # 收藏数据存储在session中，格式：[product_id1, product_id2, ...]
    favorite_ids = session.get('favorites', [])
    all_products = load_products()
    # 筛选收藏的商品
    favorite_products = [p for p in all_products if p['product_id'] in favorite_ids]
    return render_template('user/profile/favorites.html', favorites=favorite_products)
  
@app.route('/profile/addresses')
def profile_addresses():
    """个人中心 - 收货地址"""
    # 地址数据存储在session中
    addresses = session.get('addresses', [
        {'id': 1, 'name': session.get('username', '游客'), 'phone': '13800138000', 'province': '北京市', 'city': '北京市', 'area': '朝阳区', 'detail': 'xxx路xxx号', 'is_default': True}
    ])
    
    # 补充用户信息（和个人中心路由保持一致）
    user_id = session.get('user_id', 'anonymous')
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')
    }
    
    # 传递user_info到模板
    return render_template('user/profile/addresses.html', addresses=addresses, user_info=user_info)

@app.route('/profile/recharge')
def profile_recharge():
    """个人中心 - 余额充值"""
    # 余额存储在session中
    balance = session.get('balance', 0.00)
    return render_template('user/profile/recharge.html', balance=balance)

# ---------------------- 后台管理路由 ----------------------
@app.route('/admin')
def admin_dashboard():
    """后台管理页（数据统计+图表）"""
    # 1. 定义商品统计信息（必传）
    total_products = len(load_products())
    stats = {'total_products': total_products}
    
    # 2. 初始化 charts 变量（无论有没有数据，都确保存在）
    charts = {}  # 无数据时默认为空字典
    
    if not os.path.exists('data/user_actions.csv'):
        # 无用户行为数据时，传空 charts + 提示信息
        return render_template('admin/dashboard.html', 
                             has_data=False,
                             message="暂无用户行为数据，请先在前台进行操作",
                             stats=stats,
                             charts=charts)  # 关键：传 charts=charts
    
    # 3. 有数据时，生成图表并赋值给 charts
    df = pd.read_csv('data/user_actions.csv', encoding='utf-8-sig')
    total_users = df['user_id'].nunique()
    total_actions = len(df)
    total_purchases = len(df[df['action_type'] == 'purchase'])
    total_revenue = df[df['action_type'] == 'purchase']['total_amount'].sum()
    
    # 转化率计算
    views = len(df[df['action_type'] == 'view'])
    carts = len(df[df['action_type'] == 'add_to_cart'])
    conversion_rates = {
        'view_to_cart': round(carts/views*100, 2) if views > 0 else 0,
        'cart_to_purchase': round(total_purchases/carts*100, 2) if carts > 0 else 0,
        'view_to_purchase': round(total_purchases/views*100, 2) if views > 0 else 0
    }
    
    # 生成图表（覆盖上面的空字典）
    charts = generate_charts(df)
    
    # 4. 有数据时，传生成的 charts
    return render_template('admin/dashboard.html',
                         has_data=True,
                         total_users=total_users,
                         total_actions=total_actions,
                         total_purchases=total_purchases,
                         total_revenue=total_revenue,
                         conversion_rates=conversion_rates,
                         stats=stats,
                         charts=charts)

@app.route('/admin/product_manage')
def product_manage():
    """后台商品管理页面（展示+支持筛选）"""
    # 支持按分类筛选
    category = request.args.get('category', '全部商品')
    products = load_products(category=category)
    # 获取所有分类（用于筛选下拉框）
    all_categories = ['全部商品'] + list(set(p['category'] for p in load_products()))
    return render_template('admin/product_manage.html', 
                         products=products,
                         current_category=category,
                         all_categories=all_categories)

@app.route('/admin/user_manage')
def user_manage():
    """后台用户管理页面（模拟用户数据）"""
    # 实际项目中可从数据库读取，这里用模拟数据
    users = []
    # 从user_actions.csv中提取唯一用户（去重）
    if os.path.exists('data/user_actions.csv'):
        df = pd.read_csv('data/user_actions.csv', encoding='utf-8-sig')
        # 提取唯一用户信息
        unique_users = df[['user_id', 'username']].drop_duplicates().to_dict('records')
        # 补充模拟字段
        for user in unique_users:
            users.append({
                'user_id': user['user_id'],
                'username': user['username'] if user['username'] != '匿名用户' else '未登录用户',
                'email': f"{user['user_id']}@example.com",
                'register_time': df[df['user_id'] == user['user_id']]['timestamp'].min().split(' ')[0]  # 首次行为时间作为注册时间
            })
    # 若无用户数据，添加默认示例
    if not users:
        users = [
            {'user_id': 'user_demo1', 'username': '演示用户1', 'email': 'demo1@example.com', 'register_time': '2025-11-01'},
            {'user_id': 'user_demo2', 'username': '演示用户2', 'email': 'demo2@example.com', 'register_time': '2025-11-05'}
        ]
    return render_template('admin/user_manage.html', users=users)

@app.route('/admin/order_manage')
def order_manage():
    """后台订单管理页面（强制添加items字段，避免模板报错）"""
    orders = []
    all_products = load_products()
    product_map = {p['product_id']: p for p in all_products}  # 商品ID映射表

    # 从CSV读取真实订单数据
    if os.path.exists('data/user_actions.csv'):
        try:
            df = pd.read_csv('data/user_actions.csv', encoding='utf-8-sig')
            purchase_actions = df[df['action_type'] == 'purchase'].copy()
            # 确保product_id是整数（避免匹配失败）
            purchase_actions['product_id'] = purchase_actions['product_id'].astype(int)
            
            # 按时间+用户分组生成订单
            order_groups = purchase_actions.groupby(['timestamp', 'user_id', 'username'])
            order_id = 1000

            for (timestamp, user_id, username), group in order_groups:
                order_items = []
                for _, action in group.iterrows():
                    product = product_map.get(action['product_id'], {})
                    # 构建商品明细（确保每个字段都存在）
                    order_items.append({
                        'name': product.get('name', '未知商品'),
                        'image': product.get('image', 'default.jpg'),
                        'quantity': int(action.get('quantity', 1)),
                        'price': product.get('price', 0)
                    })
                
                # 强制添加 items 字段（核心）
                orders.append({
                    'order_id': f'ORDER_{order_id}',
                    'user_id': user_id,
                    'username': username if username != '匿名用户' else '未登录用户',
                    'total_amount': round(group['total_amount'].sum(), 2),
                    'status': '已支付',
                    'create_time': timestamp,
                    'product_count': len(order_items),
                    'items': order_items  # 100% 存在的商品明细列表
                })
                order_id += 1
        except Exception as e:
            print(f"读取真实订单失败：{e}")
            # 异常时也添加默认订单，避免页面空白
            orders = []

    # 无真实订单时，添加带items的默认订单（兜底）
    if not orders:
        orders = [
            {
                'order_id': 'ORDER_1001',
                'user_id': 'user_demo1',
                'username': '演示用户1',
                'total_amount': 9998.00,
                'status': '已支付',
                'create_time': '2025-11-20 14:30:00',
                'product_count': 2,
                'items': [  # 强制添加items
                    {'name': 'iPhone 15 Pro', 'image': 'iphone15.jpg', 'quantity': 1, 'price': 7999},
                    {'name': 'AirPods Pro 2', 'image': 'airpods.jpg', 'quantity': 1, 'price': 1999}
                ]
            },
            {
                'order_id': 'ORDER_1002',
                'user_id': 'user_demo2',
                'username': '演示用户2',
                'total_amount': 2790.00,
                'status': '已支付',
                'create_time': '2025-11-21 10:15:00',
                'product_count': 1,
                'items': [  # 强制添加items
                    {'name': '戴森吹风机', 'image': 'dyson_hairdryer.jpg', 'quantity': 1, 'price': 2790}
                ]
            }
        ]

    return render_template('admin/order_manage.html', orders=orders)

@app.route('/admin/data_export')
def data_export():
    """后台数据导出页面（支持导出商品、用户行为、订单数据）"""
    # 可导出的数据类型
    export_types = [
        {'key': 'products', 'name': '商品数据', 'file_name': '商品数据_2025.csv', 'desc': '包含所有商品的名称、分类、价格等信息'},
        {'key': 'user_actions', 'name': '用户行为数据', 'file_name': '用户行为数据_2025.csv', 'desc': '包含用户浏览、加购、购买等行为记录'},
        {'key': 'orders', 'name': '订单数据', 'file_name': '订单数据_2025.csv', 'desc': '包含所有订单的用户、金额、状态等信息'}
    ]
    return render_template('admin/data_export.html', export_types=export_types)

@app.route('/admin/export_file/<string:data_key>')
def export_file(data_key):
    """导出文件接口（根据data_key返回对应CSV文件）"""
    # 定义各类型数据的文件路径和处理逻辑
    export_config = {
        'products': {
            'path': 'data/products.csv',
            'default_data': [{'product_id': '', 'name': '', 'category': '', 'price': '', 'stock': '', 'description': '', 'image': ''}]
        },
        'user_actions': {
            'path': 'data/user_actions.csv',
            'default_data': [{'timestamp': '', 'user_id': '', 'username': '', 'product_id': '', 'product_name': '', 'product_category': '', 'action_type': '', 'session_id': '', 'quantity': '', 'total_amount': ''}]
        },
        'orders': {
            'path': 'data/orders.csv',
            'default_data': [{'order_id': '', 'user_id': '', 'username': '', 'total_amount': '', 'status': '', 'create_time': '', 'product_count': ''}]
        }
    }
    
    # 检查数据类型是否合法
    if data_key not in export_config:
        return jsonify({'success': False, 'msg': '不支持的数据类型'}), 400
    
    config = export_config[data_key]
    file_path = config['path']
    
    # 若文件不存在，创建默认空文件
    if not os.path.exists(file_path):
        pd.DataFrame(config['default_data']).to_csv(file_path, index=False, encoding='utf-8-sig')
    
    # 返回文件下载
    return send_file(
        file_path,
        as_attachment=True,
        download_name=export_config[data_key]['file_name'],
        mimetype='text/csv; charset=utf-8'
    )

# ---------------------- API路由（新增个人中心相关API）----------------------
@app.route('/api/add_to_cart', methods=['POST'])
def api_add_to_cart():
    """加入购物车API"""
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity <= 0:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        # 更新购物车
        cart = get_cart()
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session['cart'] = cart
        
        # 记录行为
        record_user_action(
            user_id=session.get('user_id', 'anonymous'),
            product_id=product_id,
            action_type='add_to_cart',
            quantity=quantity
        )
        
        # 返回更新后的购物车信息
        cart_items = get_cart_items()
        return jsonify({
            'success': True,
            'msg': '加入购物车成功',
            'cart_count': len(cart_items),
            'total_amount': sum(item['subtotal'] for item in cart_items)
        })
    except Exception as e:
        return jsonify({'success': False, 'msg': f'失败：{str(e)}'})

@app.route('/api/remove_from_cart', methods=['POST'])
def api_remove_from_cart():
    """移除购物车商品API"""
    try:
        product_id = request.json.get('product_id')
        cart = get_cart()
        pid_str = str(product_id)
        
        if pid_str in cart:
            del cart[pid_str]
            session['cart'] = cart
        
        # 记录行为
        record_user_action(
            user_id=session.get('user_id', 'anonymous'),
            product_id=product_id,
            action_type='remove_from_cart'
        )
        
        cart_items = get_cart_items()
        return jsonify({
            'success': True,
            'msg': '移除成功',
            'cart_count': len(cart_items),
            'total_amount': sum(item['subtotal'] for item in cart_items)
        })
    except Exception as e:
        return jsonify({'success': False, 'msg': f'失败：{str(e)}'})

@app.route('/api/login', methods=['POST'])
def api_login():
    """模拟登录API"""
    data = request.json
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'msg': '用户名不能为空'})
    
    # 保存用户信息到session
    session['user_id'] = f'user_{hash(username)}'
    session['username'] = username
    return jsonify({'success': True, 'msg': f'欢迎您，{username}！'})

@app.route('/api/logout')
def api_logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    """模拟购买API（修复绝对路径+库存减少）"""
    try:
        cart_items = get_cart_items()
        if not cart_items:
            return jsonify({'success': False, 'msg': '购物车为空'})
        
        total_amount = sum(item['subtotal'] for item in cart_items)
        user_id = session.get('user_id', 'anonymous')
        
        # ---------------------- 关键1：用你的绝对路径（r前缀避免转义）----------------------
        product_path = r"D:\code1\ruanjiangongcheng\ecommerce_system\data\products.csv"
        print(f"当前操作的商品文件：{product_path}")  # 运行后看终端是否输出正确路径
        
        # ---------------------- 关键2：确保load_products也读取同一个文件（避免读/写不一致）----------------------
        # 重新定义load_products（或修改原函数，确保读取绝对路径）
        def load_products_abs():
            if not os.path.exists(product_path):
                create_default_products()  # 无文件时创建默认商品
            return pd.read_csv(product_path, encoding='utf-8-sig').to_dict('records')
        
        # 加载商品数据（用绝对路径读取）
        products = load_products_abs()
        
        # 检查库存是否充足
        for item in cart_items:
            product = next((p for p in products if p['product_id'] == item['product_id']), None)
            if not product:
                return jsonify({'success': False, 'msg': f'商品《{item["name"]}》不存在'})
            if product['stock'] < item['quantity']:
                return jsonify({'success': False, 'msg': f'商品《{item["name"]}》库存不足，仅剩{product["stock"]}件'})
        
        # 减少库存
        for item in cart_items:
            for p in products:
                if p['product_id'] == item['product_id']:
                    p['stock'] -= item['quantity']  # 库存更新
                    break
        
        # 写入文件（绝对路径，确保权限）
        pd.DataFrame(products).to_csv(
            product_path, 
            index=False, 
            encoding='utf-8-sig',
            mode='w'  # 强制覆盖写入（避免追加重复数据）
        )
        print("库存更新成功！")  # 成功后终端会打印
        
        # 记录购买行为
        for item in cart_items:
            record_user_action(
                user_id=user_id,
                product_id=item['product_id'],
                action_type='purchase',
                quantity=item['quantity'],
                total_amount=item['subtotal']
            )
        
        # 清空购物车
        session['cart'] = {}
        return jsonify({'success': True, 'msg': f'购买成功！总金额：¥{total_amount}'})
    except Exception as e:
        # 打印详细错误（方便排查）
        print(f"购买失败详细原因：{str(e)}")
        return jsonify({'success': False, 'msg': f'购买失败：{str(e)}'})

# 假设你的购物车数据存储在session中（key为'cart'）
# cart结构：[{product_id, name, price, quantity, image, stock}, ...]

# 更新购物车商品数量API
@app.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity < 1:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        # 获取购物车数据（字典结构：{product_id_str: 数量}）
        cart = get_cart()  # 用已有的get_cart()函数，返回字典
        pid_str = str(product_id)
        
        # 检查商品是否在购物车中
        if pid_str not in cart:
            return jsonify({'success': False, 'msg': '商品不在购物车中'})
        
        # 校验库存
        products = load_products()
        product = next((p for p in products if str(p['product_id']) == pid_str), None)
        if not product:
            return jsonify({'success': False, 'msg': '商品不存在'})
        if quantity > product['stock']:
            return jsonify({'success': False, 'msg': '库存不足'})
        
        # 更新数量（字典直接赋值）
        cart[pid_str] = quantity
        session['cart'] = cart  # 保存到session
        return jsonify({'success': True, 'msg': '更新成功'})
    
    except Exception as e:
        print('更新购物车错误：', e)
        return jsonify({'success': False, 'msg': '服务器错误'})

# 删除购物车商品API
@app.route('/api/cart/delete', methods=['POST'])
def api_delete_cart():
    try:
        data = request.json
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        # 获取购物车数据（字典结构）
        cart = get_cart()
        pid_str = str(product_id)
        
        # 删除商品（字典操作）
        if pid_str in cart:
            del cart[pid_str]
            session['cart'] = cart
        
        return jsonify({'success': True, 'msg': '删除成功'})
    
    except Exception as e:
        print('删除购物车错误：', e)
        return jsonify({'success': False, 'msg': '服务器错误'})

# 结算页面路由（需要先创建checkout.html模板）
@app.route('/checkout')
def checkout():
    cart_items = get_cart_items()  # 复用你之前的“获取购物车商品详情”函数
    if not cart_items:
        return redirect(url_for('cart'))  # 购物车为空跳回购物车
    
    # 1. 计算模板需要的“商品总数”“实付款”
    total_quantity = sum(item['quantity'] for item in cart_items)
    total_amount = sum(item['subtotal'] for item in cart_items)  # 对应模板里的total_amount
    
    # 2. 补充“收货地址”数据（从session获取，或模拟默认地址）
    # （如果你的地址功能还没做，先模拟一个默认地址，后续可以关联真实地址数据）
    address = session.get('default_address', {
        'name': session.get('username', '默认收货人'),
        'phone': '13800138000',
        'province': '北京市',
        'city': '北京市',
        'detail': '朝阳区xxx路xxx号'
    })
    
    # 3. 传递模板需要的所有变量（和你现有checkout.html的变量名完全匹配）
    return render_template('user/checkout.html',
                          cart_items=cart_items,
                          total_quantity=total_quantity,
                          total_amount=total_amount,
                          address=address)
# ---------------------- 新增：个人中心相关API ----------------------
@app.route('/api/edit_profile', methods=['POST'])
def api_edit_profile():
    """编辑个人信息API（解决“编辑没反应”）"""
    try:
        data = request.json
        # 更新session中的用户信息
        if 'username' in data:
            session['username'] = data['username'].strip()
        if 'email' in data:
            session['email'] = data['email'].strip()
        if 'phone' in data:
            session['phone'] = data['phone'].strip()
        return jsonify({'success': True, 'msg': '个人信息编辑成功！'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'编辑失败：{str(e)}'})

@app.route('/api/add_favorite', methods=['POST'])
def api_add_favorite():
    """添加收藏API"""
    try:
        data = request.json
        product_id = int(data.get('product_id', 0))
        if not product_id:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        # 获取现有收藏，去重
        favorites = session.get('favorites', [])
        if product_id not in favorites:
            favorites.append(product_id)
            session['favorites'] = favorites
            return jsonify({'success': True, 'msg': '收藏成功！'})
        return jsonify({'success': False, 'msg': '已收藏该商品！'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'收藏失败：{str(e)}'})

@app.route('/api/remove_favorite', methods=['POST'])
def api_remove_favorite():
    """取消收藏API"""
    try:
        data = request.json
        product_id = int(data.get('product_id', 0))
        favorites = session.get('favorites', [])
        if product_id in favorites:
            favorites.remove(product_id)
            session['favorites'] = favorites
            return jsonify({'success': True, 'msg': '取消收藏成功！'})
        return jsonify({'success': False, 'msg': '未收藏该商品！'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'取消收藏失败：{str(e)}'})

@app.route('/api/recharge', methods=['POST'])
def api_recharge():
    """余额充值API"""
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'success': False, 'msg': '充值金额必须大于0！'})
        
        # 更新余额
        current_balance = session.get('balance', 0.00)
        session['balance'] = round(current_balance + amount, 2)
        return jsonify({
            'success': True,
            'msg': f'充值成功！当前余额：¥{session["balance"]}',
            'balance': session['balance']
        })
    except Exception as e:
        return jsonify({'success': False, 'msg': f'充值失败：{str(e)}'})

@app.route('/api/add_address', methods=['POST'])
def api_add_address():
    """添加收货地址API"""
    try:
        data = request.json
        # 验证必填字段
        required_fields = ['name', 'phone', 'province', 'city', 'area', 'detail']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'success': False, 'msg': f'{field}不能为空！'})
        
        # 获取现有地址，生成新ID
        addresses = session.get('addresses', [])
        new_id = max([addr['id'] for addr in addresses], default=0) + 1
        # 添加新地址
        new_address = {
            'id': new_id,
            'name': data['name'].strip(),
            'phone': data['phone'].strip(),
            'province': data['province'].strip(),
            'city': data['city'].strip(),
            'area': data['area'].strip(),
            'detail': data['detail'].strip(),
            'is_default': data.get('is_default', False)
        }
        addresses.append(new_address)
        session['addresses'] = addresses
        return jsonify({'success': True, 'msg': '地址添加成功！', 'addresses': addresses})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'添加失败：{str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)