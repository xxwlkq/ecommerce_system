from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file,abort,g
import pandas as pd
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import csv
import uuid
from collections import defaultdict
import sys
import re
import bcrypt
import pandas as pd
from functools import wraps

# 将backend目录添加到Python的搜索路径中
# 假设app.py在ecommerce_system根目录，backend是同级目录
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)  # 让Python能找到backend目录下的文件


# ---------------------- 关键修复：Matplotlib线程问题（避免GUI冲突）----------------------
plt.switch_backend('Agg')  # 使用非GUI后端，解决多线程资源冲突
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ---------------------- 核心路径配置（保持原结构，优化路径校验）----------------------
base_dir = os.path.abspath(os.path.dirname(__file__))

# 统一数据目录：ecommerce_system/data
ECOMMERCE_DATA_DIR = os.path.join(base_dir, 'data')
USER_ACTIONS_CSV = os.path.join(ECOMMERCE_DATA_DIR, 'user_actions.csv')
PRODUCTS_CSV = os.path.join(ECOMMERCE_DATA_DIR, 'products.csv')
FAVORITES_CSV = os.path.join(ECOMMERCE_DATA_DIR, 'user_favorites.csv')
ORDERS_CSV = os.path.join(ECOMMERCE_DATA_DIR, 'orders.csv')
USERS_CSV_PATH = os.path.join(ECOMMERCE_DATA_DIR, 'users.csv') 

# 模板/静态资源目录配置（确保路径存在）
template_dir = os.path.join(base_dir, 'frontend', 'templates')
static_dir = os.path.join(base_dir, 'frontend', 'static')

# 校验模板和静态目录是否存在（添加容错提示）
for dir_path in [template_dir, static_dir]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"警告：目录不存在，已自动创建 -> {dir_path}")

# ---------------------- 初始化Flask应用（仅创建一次，修复重复实例问题）----------------------
app = Flask(
    __name__,
    template_folder=template_dir,  # 模板路径：frontend/templates
    static_folder=static_dir,      # 静态文件路径：frontend/static
    static_url_path='/static'      # 明确静态文件URL路径（默认也是/static，显式写更清晰）
)
app.secret_key = 'ecommerce_2024_project_123'  # 会话加密密钥
app.config['JSON_AS_ASCII'] = False             # 支持中文JSON
app.config['TEMPLATES_AUTO_RELOAD'] = True      # 模板自动重载（开发模式）
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小（16MB）

# ---------------------- 目录自动创建（确保必要目录存在）----------------------
os.makedirs(ECOMMERCE_DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(static_dir, 'images'), exist_ok=True)
os.makedirs(os.path.join(static_dir, 'admin', 'uploads', 'products'), exist_ok=True)

# ---------------------- 登录/注册核心辅助函数（新增）----------------------
# 修改get_all_users函数，增加更健壮的错误处理
def get_all_users():
    """读取users.csv中所有用户数据（增强错误处理）"""
    users = []
    if not os.path.exists(USERS_CSV_PATH):
        print(f"警告：用户数据文件不存在 - {USERS_CSV_PATH}")
        return users
    
    try:
        with open(USERS_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # 验证CSV文件头是否正确
            required_fields = ['user_id', 'username', 'password', 'phone', 'balance', 'favorites', 'is_admin']
            if not all(field in reader.fieldnames for field in required_fields):
                print(f"错误：用户数据文件格式不正确，缺少必要字段")
                return users
                
            for row in reader:
                # 转换数据类型，增加容错处理
                try:
                    row['balance'] = float(row.get('balance', 0))
                except:
                    row['balance'] = 0.0
                    
                try:
                    row['favorites'] = eval(row['favorites']) if row.get('favorites') else []
                except:
                    row['favorites'] = []
                    
                row['is_admin'] = row.get('is_admin', 'false').lower() == 'true'
                row['phone'] = row.get('phone', '')
                users.append(row)
        return users
    except Exception as e:
        print(f"读取用户数据失败：{str(e)}")
        return []

def save_user(user):
    """保存新用户到users.csv（新增phone字段）"""
    file_exists = os.path.exists(USERS_CSV_PATH)
    with open(USERS_CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        # 字段名新增 phone（必须和表头一致）
        fieldnames = ['user_id', 'username', 'password', 'phone', 'balance', 'favorites', 'is_admin']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(user)

def login_required(f):
    """登录校验装饰器（原有逻辑，补充完整）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # 未登录
            return redirect('/login')  # 跳转到登录页
        # 把用户信息存入g对象，方便接口使用
        g.user_id = session['user_id']
        g.username = session['username']
        g.is_admin = session.get('is_admin', False)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限校验装饰器（新增）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 先校验是否登录（依赖login_required）
        if 'user_id' not in session:
            return redirect('/login')
        # 再校验是否为管理员
        if not session.get('is_admin', False):
            abort(403)  # 非管理员，返回403禁止访问（或跳转到首页并提示）
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- 基础工具函数（修复潜在bug，确保函数定义在调用前）----------------------
def load_products(category=None):
    if not os.path.exists(PRODUCTS_CSV):
        create_default_products()
    try:
        df = pd.read_csv(PRODUCTS_CSV, encoding='utf-8-sig')
        # 确保product_id为整数类型
        df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce').fillna(0).astype(int)
        if category and category != '全部商品':
            df = df[df['category'] == category]
        return df.to_dict('records')
    except Exception as e:
        print(f"加载商品失败：{e}")
        create_default_products()  # 读取失败时重新创建默认商品
        return load_products(category)

def create_default_products():
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
    pd.DataFrame(default_products).to_csv(PRODUCTS_CSV, index=False, encoding='utf-8-sig')
    print("默认商品创建成功")

def get_cart():
    return session.get('cart', {})

def get_cart_items():
    cart = get_cart()
    products = load_products()
    cart_items = []
    for pid_str, quantity in cart.items():
        # 确保pid_str能转换为整数
        try:
            product_id = int(pid_str)
        except:
            continue
        product = next((p for p in products if p['product_id'] == product_id), None)
        if product:
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
    try:
        product = next((p for p in load_products() if p['product_id'] == int(product_id)), None)
    except:
        product = None
    session_id = session.get('_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['_id'] = session_id
    
    action_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': user_id,
        'username': session.get('username', '匿名用户'),
        'product_id': product_id,
        'product_name': product['name'] if product else '',
        'product_category': product['category'] if product else '',
        'action_type': action_type,
        'session_id': session_id,
        'quantity': kwargs.get('quantity', 1),
        'total_amount': kwargs.get('total_amount', 0)
    }
    try:
        df = pd.read_csv(USER_ACTIONS_CSV, encoding='utf-8-sig') if os.path.exists(USER_ACTIONS_CSV) else pd.DataFrame(columns=action_data.keys())
        new_row = pd.DataFrame([action_data])
        pd.concat([df, new_row], ignore_index=True).to_csv(USER_ACTIONS_CSV, index=False, encoding='utf-8-sig')
    except Exception as e:
        print(f"行为记录失败：{e}")

def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def generate_charts(df):
    charts = {}
    try:
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
    except Exception as e:
        print(f"图表生成失败：{e}")
    return charts

# ---------------------- 收藏功能核心函数（确保定义在API调用前）----------------------
def init_favorites_file():
    if not os.path.exists(FAVORITES_CSV):
        try:
            with open(FAVORITES_CSV, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['user_id', 'product_id', 'add_time'])
            print(f"收藏文件初始化成功：{FAVORITES_CSV}")
        except Exception as e:
            print(f"初始化收藏文件失败：{str(e)}")

def add_user_favorite(user_id, product_id):
    init_favorites_file()
    try:
        existing_records = []
        with open(FAVORITES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                header = ['user_id', 'product_id', 'add_time']
            existing_records.append(header)
            
            is_already_favorite = False
            for row in reader:
                if len(row) >= 2 and row[0] == user_id and row[1] == str(product_id):
                    is_already_favorite = True
                existing_records.append(row)
        
        if is_already_favorite:
            print(f"已收藏：用户{user_id}，商品{product_id}")
            return False
        
        with open(FAVORITES_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(existing_records)
            writer.writerow([user_id, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        print(f"收藏成功：用户{user_id}，商品{product_id}")
        return True
    except Exception as e:
        print(f"添加收藏失败：{str(e)}")
        return False

def remove_user_favorite(user_id, product_id):
    init_favorites_file()
    try:
        remaining_records = []
        has_record = False
        with open(FAVORITES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                header = ['user_id', 'product_id', 'add_time']
            remaining_records.append(header)
            
            for row in reader:
                if len(row) >= 2 and row[0] == user_id and row[1] == str(product_id):
                    has_record = True
                else:
                    remaining_records.append(row)
        
        if not has_record:
            print(f"未收藏：用户{user_id}，商品{product_id}")
            return False
        
        with open(FAVORITES_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(remaining_records)
        print(f"取消收藏成功：用户{user_id}，商品{product_id}")
        return True
    except Exception as e:
        print(f"取消收藏失败：{str(e)}")
        return False

def load_user_favorites(user_id):
    init_favorites_file()
    favorite_ids = []
    print(f"\n===== 加载收藏：目标文件路径 = {FAVORITES_CSV} =====")
    try:
        with open(FAVORITES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                header = []
            print(f"收藏文件表头：{header}")
            print("收藏文件所有记录：")
            for row in reader:
                print(f"  - {row}")
                if len(row) >= 2 and row[0] == user_id and row[1].isdigit():
                    favorite_ids.append(int(row[1]))
        
        print(f"✅ 用户{user_id}的收藏ID列表：{favorite_ids}")
        return favorite_ids
    except Exception as e:
        print(f"❌ 加载收藏失败：{str(e)}")
        return []

# ---------------------- 订单迁移函数（确保定义在调用前）----------------------
def migrate_purchase_to_orders():
    import pandas as pd
    import os
    import json
    from datetime import datetime

    # 打印核心路径（确认文件位置）
    print("\n===== 订单迁移开始 =====")
    print(f"• user_actions.csv路径：{USER_ACTIONS_CSV}")
    print(f"• orders.csv目标路径：{ORDERS_CSV}")
    print(f"• user_actions.csv是否存在：{os.path.exists(USER_ACTIONS_CSV)}")

    # 1. 读取user_actions.csv（先读全量数据，不筛选）
    try:
        all_actions = pd.read_csv(USER_ACTIONS_CSV, encoding='utf-8-sig')
        print(f"• 读取到user_actions.csv共{len(all_actions)}条记录")
        print(f"• user_actions.csv的列名：{all_actions.columns.tolist()}")  # 确认字段名
        
        # 筛选purchase行为（严格匹配字段名）
        if 'action_type' not in all_actions.columns:
            print("❌ 错误：user_actions.csv缺少'action_type'列")
            return
        purchase_records = all_actions[all_actions['action_type'] == 'purchase'].copy()
        print(f"• 筛选出purchase记录数：{len(purchase_records)}")
        
        # 打印前2条purchase记录，确认数据格式
        if len(purchase_records) > 0:
            print("• 前2条purchase记录示例：")
            print(purchase_records.head(2))
    except Exception as e:
        print(f"❌ 读取user_actions.csv失败：{str(e)}")
        return

    # 2. 必须有13条purchase记录才继续（无则跳过，避免报错）
    if len(purchase_records) != 13:
        print(f"⚠️  警告：仅找到{len(purchase_records)}条purchase记录（需要13条），跳过迁移")
        return

    # 3. 逐行处理13条记录（打印每条进度）
    migrated_orders = []
    order_id_prefix = int(datetime.now().timestamp())  # 唯一ID前缀
    for idx, row in purchase_records.iterrows():
        try:
            # 生成订单ID
            order_id = f"USER_ORDER_{order_id_prefix}_{idx+1:03d}"
            
            # 提取字段（严格对应你的user_actions.csv列名）
            order_data = {
                'order_id': order_id,
                'user_id': row['user_id'],
                'username': row.get('username', '未知用户'),
                'total_amount': round(float(row['total_amount']), 2),
                'status': '已支付',
                'create_time': row['timestamp'],  # 直接用原时间
                'items': json.dumps([{  # 单商品订单
                    'product_id': int(row['product_id']),
                    'name': row['product_name'],
                    'image': f"{row['product_id']}.jpg",  # 图片名=商品ID
                    'quantity': int(row['quantity']),
                    'price': float(row['total_amount'])
                }])
            }
            migrated_orders.append(order_data)
            print(f"✅ 处理第{idx+1}条：订单ID={order_id}，商品={row['product_name']}")
        except Exception as e:
            print(f"❌ 处理第{idx+1}条失败：{str(e)}")

    # 4. 写入orders.csv（覆盖旧文件）
    if migrated_orders:
        orders_df = pd.DataFrame(migrated_orders)
        orders_df.to_csv(ORDERS_CSV, index=False, encoding='utf-8-sig')
        print(f"\n✅ 迁移完成：{len(migrated_orders)}条订单已写入orders.csv")
    else:
        print("❌ 无订单可写入")
    print("===== 订单迁移结束 =====\n")

# ---------------------- 所有路由定义（统一注册到同一个app实例，顺序无关）----------------------
# 1. 登录/注册路由（保留原模板路径，适配前端）
@app.route('/login')
def login_page():
    return render_template('user/login.html')

@app.route('/register')
def register_page():
    return render_template('user/register.html')

# 2. 首页/商品相关路由
@app.route('/')
def index():
    recommended_products = load_products()[:4]
    return render_template('user/index.html', recommended_products=recommended_products)

@app.route('/products')
def products():
    category = request.args.get('category', '全部商品')
    all_products = load_products(category=category)
    all_categories = ['全部商品'] + list(set(p['category'] for p in load_products()))
    return render_template('user/products.html', 
                         products=all_products,
                         current_category=category,
                         all_categories=all_categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in load_products() if p['product_id'] == product_id), None)
    if not product:
        return redirect(url_for('products'))
    record_user_action(
        user_id=session.get('user_id', 'anonymous'),
        product_id=product_id,
        action_type='view'
    )
    return render_template('user/product_detail.html', product=product)

# 3. 购物车/结算路由
@app.route('/cart')
def cart():
    cart_items = get_cart_items()
    total_quantity = sum(item['quantity'] for item in cart_items)
    total_amount = sum(item['subtotal'] for item in cart_items)
    return render_template('user/cart.html', 
                         cart_items=cart_items,
                         total_quantity=total_quantity,
                         total_amount=total_amount,
                         is_empty=len(cart_items) == 0)

@app.route('/checkout')
def checkout():
    cart_items = get_cart_items()
    if not cart_items:
        return redirect(url_for('cart'))
    
    total_quantity = sum(item['quantity'] for item in cart_items)
    total_amount = sum(item['subtotal'] for item in cart_items)
    
    address = session.get('default_address', {
        'name': session.get('username', '默认收货人'),
        'phone': '13800138000',
        'province': '北京市',
        'city': '北京市',
        'detail': '朝阳区xxx路xxx号'
    })
    
    return render_template('user/checkout.html',
                          cart_items=cart_items,
                          total_quantity=total_quantity,
                          total_amount=total_amount,
                          address=address)

# 4. 个人中心相关路由
# 修改用户中心路由，增加登录验证
@app.route('/profile')
@login_required  # 强制登录后才能访问
def profile():
    # 从session读取当前登录用户的信息（无默认值）
    user_info = {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'email': f"{session['user_id']}@example.com" if session.get('user_id') else '',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')
    }

    # 统计用户行为（仅当前登录用户）
    stats = {'view_count': 0, 'cart_count': 0, 'purchase_count': 0}
    if os.path.exists(USER_ACTIONS_CSV):
        try:
            df = pd.read_csv(USER_ACTIONS_CSV, encoding='utf-8-sig')
            user_actions = df[df['user_id'] == session['user_id']]  # 只统计当前用户
            stats = {
                'view_count': len(user_actions[user_actions['action_type'] == 'view']),
                'cart_count': len(user_actions[user_actions['action_type'] == 'add_to_cart']),
                'purchase_count': len(user_actions[user_actions['action_type'] == 'purchase'])
            }
        except Exception as e:
            print(f"统计用户行为失败：{e}")
    
    return render_template('user/profile/index.html', user_info=user_info, stats=stats)

@app.route('/profile/orders')
def profile_orders():
    user_id = session.get('user_id', 'anonymous')
    orders = []
    all_products = load_products()
    product_map = {p['product_id']: p for p in all_products}
    
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')
    }

    if os.path.exists(USER_ACTIONS_CSV):
        try:
            df = pd.read_csv(USER_ACTIONS_CSV, encoding='utf-8-sig')
            purchase_actions = df[(df['user_id'] == user_id) & (df['action_type'] == 'purchase')].copy()
            if not purchase_actions.empty:
                purchase_actions['product_id'] = pd.to_numeric(purchase_actions['product_id'], errors='coerce').fillna(0).astype(int)
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
                        'items': order_items,
                        'product_count': len(order_items)
                    })
                    order_id += 1
        except Exception as e:
            print(f"读取用户订单失败：{e}")

    if not orders:
        orders = [
            {
                'order_id': 'USER_ORDER_2001',
                'create_time': '2025-11-20 15:30:00',
                'total_amount': 9998.00,
                'status': '已支付',
                'product_count': 2,
                'items': [
                    {'name': 'iPhone 15 Pro', 'image': 'iphone15.jpg', 'quantity': 1, 'price': 7999},
                    {'name': 'AirPods Pro 2', 'image': 'airpods.jpg', 'quantity': 1, 'price': 1999}
                ]
            }
        ]

    fixed_orders = []
    for order in orders:
        if not isinstance(order, dict):
            order = {}
        order_items = order.get('items', [])
        if not isinstance(order_items, list):
            order_items = []
        fixed_order = {
            'order_id': order.get('order_id', f'ORDER_{len(fixed_orders)+1}'),
            'create_time': order.get('create_time', ''),
            'total_amount': order.get('total_amount', 0.00),
            'status': order.get('status', '未知状态'),
            'product_count': len(order_items),
            'items': order_items
        }
        fixed_orders.append(fixed_order)
    orders = fixed_orders

    return render_template('user/profile/orders.html', orders=orders, user_info=user_info)

@app.route('/profile/favorites')
def profile_favorites():
    user_id = session.get('user_id', 'anonymous')
    if user_id == 'anonymous':
        # 未登录跳转首页并提示
        return redirect(url_for('index', msg='请先登录查看收藏'))
    
    favorite_ids = load_user_favorites(user_id)
    all_products = load_products()
    favorite_products = [p for p in all_products if p['product_id'] in favorite_ids]
    
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
    }
    
    return render_template('user/profile/favorites.html', 
                         favorites=favorite_products,
                         user_info=user_info,
                         is_empty=len(favorite_products) == 0)

@app.route('/profile/addresses')
def profile_addresses():
    addresses = session.get('addresses', [
        {'id': 1, 'name': session.get('username', '游客'), 'phone': '13800138000', 'province': '北京市', 'city': '北京市', 'area': '朝阳区', 'detail': 'xxx路xxx号', 'is_default': True}
    ])
    
    user_id = session.get('user_id', 'anonymous')
    user_info = {
        'user_id': user_id,
        'username': session.get('username', '游客'),
        'email': session.get('email', f"{user_id}@example.com") if user_id != 'anonymous' else 'guest@example.com',
        'phone': session.get('phone', ''),
        'avatar': session.get('avatar', 'default_avatar.png')
    }
    
    return render_template('user/profile/addresses.html', addresses=addresses, user_info=user_info)

@app.route('/profile/recharge')
def profile_recharge():
    balance = session.get('balance', 0.00)
    return render_template('user/profile/recharge.html', balance=balance)

# 5. 后台管理路由
@app.route('/admin')
def admin_dashboard():
    total_products = len(load_products())
    stats = {'total_products': total_products}
    charts = {}
    
    if not os.path.exists(USER_ACTIONS_CSV):
        return render_template('admin/dashboard.html', 
                             has_data=False,
                             message="暂无用户行为数据，请先在前台进行操作",
                             stats=stats,
                             charts=charts)
    
    try:
        df = pd.read_csv(USER_ACTIONS_CSV, encoding='utf-8-sig')
        total_users = df['user_id'].nunique()
        total_actions = len(df)
        total_purchases = len(df[df['action_type'] == 'purchase'])
        total_revenue = df[df['action_type'] == 'purchase']['total_amount'].sum()
        
        views = len(df[df['action_type'] == 'view'])
        carts = len(df[df['action_type'] == 'add_to_cart'])
        conversion_rates = {
            'view_to_cart': round(carts/views*100, 2) if views > 0 else 0,
            'cart_to_purchase': round(total_purchases/carts*100, 2) if carts > 0 else 0,
            'view_to_purchase': round(total_purchases/views*100, 2) if views > 0 else 0
        }
        
        charts = generate_charts(df)
    except Exception as e:
        print(f"后台数据统计失败：{e}")
        total_users = 0
        total_actions = 0
        total_purchases = 0
        total_revenue = 0
        conversion_rates = {'view_to_cart': 0, 'cart_to_purchase': 0, 'view_to_purchase': 0}
    
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
    category = request.args.get('category', '全部商品')
    products = load_products(category=category)
    all_categories = ['全部商品'] + list(set(p['category'] for p in load_products()))
    return render_template('admin/product_manage.html', 
                         products=products,
                         current_category=category,
                         all_categories=all_categories)

@app.route('/admin/user_manage')
@login_required  # 先登录
@admin_required  # 再校验管理员权限
def user_manage():
    users = []
    if os.path.exists(USERS_CSV_PATH):
        try:
            # 读取CSV时包含phone字段（如果CSV已有phone列）
            df = pd.read_csv(USERS_CSV_PATH, encoding='utf-8-sig')
            for _, row in df.iterrows():
                if row['user_id'] != 'anonymous':
                    users.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'phone': row.get('phone', '未填写'),  # 显示手机号
                        'register_time': datetime.now().strftime('%Y-%m-%d')  # 简化处理，可后续优化为真实创建时间
                    })
        except Exception as e:
            print(f"加载用户数据失败：{e}")
    
    if not users:
        users = [
            {'user_id': 'user_demo1', 'username': '演示用户1', 'phone': '13800138000', 'register_time': '2025-11-01'},
            {'user_id': 'user_demo2', 'username': '演示用户2', 'phone': '13900139000', 'register_time': '2025-11-05'}
        ]
    return render_template('admin/user_manage.html', users=users)

@app.route('/admin/order_manage')
def order_manage():
    orders = []
    all_products = load_products()
    product_map = {p['product_id']: p for p in all_products}

    # 关键优化：添加详细日志，方便排查问题
    print("\n===== 后台订单读取日志 =====")
    print(f"1. 读取的订单文件路径：{ORDERS_CSV}")
    print(f"2. 订单文件是否存在：{os.path.exists(ORDERS_CSV)}")

    # 读取orders.csv（增强容错性）
    if os.path.exists(ORDERS_CSV):
        try:
            # 读取订单文件，添加 dtype 确保字段类型正确
            order_df = pd.read_csv(
                ORDERS_CSV,
                encoding='utf-8-sig',
                dtype={
                    'order_id': str,
                    'user_id': str,
                    'username': str,
                    'total_amount': float,
                    'status': str,
                    'create_time': str,
                    'items': str
                }
            )
            print(f"3. 成功读取订单文件，共{len(order_df)}条记录")

            # 遍历所有订单，增强字段容错
            for idx, row in order_df.iterrows():
                try:
                    # 解析订单项（捕获JSON解析错误）
                    if pd.notna(row['items']) and row['items'].strip():
                        items = json.loads(row['items'])
                    else:
                        items = []
                        print(f"⚠️  第{idx+1}条订单（{row['order_id']}）的items字段为空，跳过")
                        continue

                    # 构造订单数据（所有字段添加默认值，避免空值报错）
                    order = {
                        'order_id': row.get('order_id', f'UNKNOWN_{idx}'),  # 订单ID默认值
                        'user_id': row.get('user_id', 'unknown_user'),     # 用户ID默认值
                        'username': row.get('username', '未知用户'),       # 用户名默认值
                        'total_amount': float(row.get('total_amount', 0.0)),  # 金额默认0
                        'status': row.get('status', '待支付'),             # 状态默认值
                        'create_time': row.get('create_time', '2025-01-01 00:00:00'),  # 时间默认值
                        'product_count': len(items),
                        'items': items
                    }
                    orders.append(order)
                    print(f"✅ 加载第{idx+1}条订单：{order['order_id']}（用户：{order['username']}）")

                except json.JSONDecodeError:
                    print(f"❌ 第{idx+1}条订单（{row['order_id']}）的items字段格式错误，跳过")
                except Exception as e:
                    print(f"❌ 第{idx+1}条订单（{row['order_id']}）加载失败：{str(e)}，跳过")

            # 排序优化：处理时间格式异常，避免排序崩溃
            try:
                # 按时间倒序（最新订单在前），异常时间排最后
                orders.sort(
                    key=lambda x: pd.to_datetime(x['create_time'], errors='coerce'),
                    reverse=True
                )
                print(f"4. 订单排序完成，共加载{len(orders)}条有效订单")
            except Exception as e:
                print(f"⚠️  订单排序失败：{str(e)}，使用原始顺序")

        except FileNotFoundError:
            print(f"❌ 订单文件不存在：{ORDERS_CSV}")
        except Exception as e:
            print(f"❌ 读取订单文件失败：{str(e)}")
            orders = []
    else:
        print(f"❌ 订单文件不存在：{ORDERS_CSV}")

    # 若无有效订单，显示演示数据
    if not orders:
        print("⚠️  无有效订单，显示演示数据")
        orders = [
            {
                'order_id': 'USER_ORDER_DEMO_001',
                'user_id': 'demo_user',
                'username': '演示用户',
                'total_amount': 1299.00,
                'status': '已支付',
                'create_time': '2025-11-27 10:00:00',
                'product_count': 1,
                'items': [
                    {'name': 'Nike Air Max', 'image': 'nike_airmax.jpg', 'quantity': 1, 'price': 1299.00}
                ]
            }
        ]

    print("===== 后台订单读取结束 =====\n")
    return render_template('admin/order_manage.html', orders=orders)

@app.route('/admin/data_export')
def data_export():
    export_types = [
        {'key': 'products', 'name': '商品数据', 'file_name': '商品数据_2025.csv', 'desc': '包含所有商品的名称、分类、价格等信息'},
        {'key': 'user_actions', 'name': '用户行为数据', 'file_name': '用户行为数据_2025.csv', 'desc': '包含用户浏览、加购、购买等行为记录'},
        {'key': 'orders', 'name': '订单数据', 'file_name': '订单数据_2025.csv', 'desc': '包含所有订单的用户、金额、状态等信息'},
        {'key': 'users', 'name': '用户数据', 'file_name': '用户数据_2025.csv', 'desc': '包含所有注册用户的基本信息'}  # 新增用户数据导出
    ]
    return render_template('admin/data_export.html', export_types=export_types)

@app.route('/admin/export_file/<string:data_key>')
def export_file(data_key):
    export_config = {
        'products': {
            'path': PRODUCTS_CSV,
            'default_data': [{'product_id': '', 'name': '', 'category': '', 'price': '', 'stock': '', 'description': '', 'image': ''}]
        },
        'user_actions': {
            'path': USER_ACTIONS_CSV,
            'default_data': [{'timestamp': '', 'user_id': '', 'username': '', 'product_id': '', 'product_name': '', 'product_category': '', 'action_type': '', 'session_id': '', 'quantity': '', 'total_amount': ''}]
        },
        'orders': {
            'path': ORDERS_CSV,
            'default_data': [{'order_id': '', 'user_id': '', 'username': '', 'total_amount': '', 'status': '', 'create_time': '', 'product_count': ''}]
        },
        'users': {  # 新增用户数据导出配置
            'path': USERS_CSV_PATH,
            'default_data': [{'user_id': '', 'username': '', 'password': '', 'balance': '', 'favorites': '', 'is_admin': ''}]
        }
    }
    
    if data_key not in export_config:
        return jsonify({'success': False, 'msg': '不支持的数据类型'}), 400
    
    config = export_config[data_key]
    file_path = config['path']
    
    if not os.path.exists(file_path):
        pd.DataFrame(config['default_data']).to_csv(file_path, index=False, encoding='utf-8-sig')
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=export_config[data_key]['file_name'],
        mimetype='text/csv; charset=utf-8'
    )

# ---------------------- API接口定义 ----------------------
# 购物车相关API
@app.route('/api/add_to_cart', methods=['POST'])
def api_add_to_cart():
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity <= 0:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        cart = get_cart()
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session['cart'] = cart
        
        record_user_action(
            user_id=session.get('user_id', 'anonymous'),
            product_id=product_id,
            action_type='add_to_cart',
            quantity=quantity
        )
        
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
    try:
        product_id = request.json.get('product_id')
        cart = get_cart()
        pid_str = str(product_id)
        
        if pid_str in cart:
            del cart[pid_str]
            session['cart'] = cart
        
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

@app.route('/api/update_cart', methods=['POST'])
def api_update_cart():
    try:
        data = request.json
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id or quantity < 1:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        cart = get_cart()
        pid_str = str(product_id)
        
        if pid_str not in cart:
            return jsonify({'success': False, 'msg': '商品不在购物车中'})
        
        products = load_products()
        product = next((p for p in products if str(p['product_id']) == pid_str), None)
        if not product:
            return jsonify({'success': False, 'msg': '商品不存在'})
        if quantity > product['stock']:
            return jsonify({'success': False, 'msg': '库存不足'})
        
        cart[pid_str] = quantity
        session['cart'] = cart
        return jsonify({'success': True, 'msg': '更新成功'})
    
    except Exception as e:
        print('更新购物车错误：', e)
        return jsonify({'success': False, 'msg': '服务器错误'})

@app.route('/api/delete_cart', methods=['POST'])
def api_delete_cart():
    try:
        data = request.json
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'success': False, 'msg': '参数错误'})
        
        cart = get_cart()
        pid_str = str(product_id)
        
        if pid_str in cart:
            del cart[pid_str]
            session['cart'] = cart
        
        return jsonify({'success': True, 'msg': '删除成功'})
    
    except Exception as e:
        print('删除购物车错误：', e)
        return jsonify({'success': False, 'msg': '服务器错误'})

@app.route('/api/register', methods=['POST'])
def api_register():
    """注册接口：密码加密存储，保存手机号"""
    data = request.get_json()
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')

    # 验证参数
    if not all([username, phone, password]):
        return jsonify({"success": False, "msg": "请填写完整信息"})
    
    # 手机号格式验证
    if not re.fullmatch(r'^1[3-9]\d{9}$', phone):
        return jsonify({"success": False, "msg": "请输入正确的手机号"})
    
    # 密码格式验证
    if len(password) < 6 or len(password) > 16 or not re.search(r'\d', password) or not re.search(r'[a-zA-Z]', password):
        return jsonify({"success": False, "msg": "密码需6-16位，含字母和数字"})

    # 检查用户是否已存在（用户名/手机号/phone重复）
    users = get_all_users()
    for user in users:
        if user['username'] == username:
            return jsonify({"success": False, "msg": "用户名已被注册"})
        if user['phone'] == phone:
            return jsonify({"success": False, "msg": "手机号已被注册"})
        if user['user_id'] == phone:  # 兼容旧逻辑：user_id曾用手机号
            return jsonify({"success": False, "msg": "手机号已被注册"})

    # 密码加密（核心修改：明文→哈希）
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')  # 转为字符串存储

    # 创建新用户（user_id用手机号，和旧逻辑一致）
    new_user = {
        'user_id': phone,
        'username': username,
        'password': hashed_password,  # 存储加密后的密码
        'phone': phone,  # 新增：保存手机号
        'balance': 0.0,
        'favorites': [],
        'is_admin': False  # 新用户默认非管理员
    }

    save_user(new_user)
    return jsonify({"success": True, "msg": "注册成功，即将跳转到登录页"})

# 修改登录API，增加完整的异常处理
@app.route('/api/login', methods=['POST'])
def api_login():
    """登录接口：支持加密密码验证，保存管理员状态"""
    try:
        # 尝试解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "msg": "请求数据格式错误，需为JSON"})

        login_id = data.get('loginId', '').strip()  # 手机号/用户名/旧user_id
        password = data.get('password', '').strip()

        if not all([login_id, password]):
            return jsonify({"success": False, "msg": "请填写完整信息"})

        # 验证用户数据文件是否存在
        if not os.path.exists(USERS_CSV_PATH):
            return jsonify({"success": False, "msg": "用户数据文件不存在，请先注册"})

        # 读取用户数据
        users = get_all_users()
        if not users:
            return jsonify({"success": False, "msg": "暂无注册用户，请先注册"})

        # 查找匹配的用户
        for user in users:
            # 匹配条件：user_id/用户名/手机号 任一匹配
            match_condition = (
                user['user_id'] == login_id 
                or user['username'] == login_id 
                or user['phone'] == login_id
            )
            if not match_condition:
                continue

            # 密码验证
            try:
                password_bytes = password.encode('utf-8')
                if bcrypt.checkpw(password_bytes, user['password'].encode('utf-8')):
                    # 登录成功：保存用户信息
                    session['user_id'] = user['user_id']
                    session['username'] = user['username']
                    session['balance'] = user['balance']
                    session['favorites'] = user['favorites']
                    session['is_admin'] = user['is_admin']
                    return jsonify({
                        "success": True, 
                        "msg": f"欢迎您，{user['username']}！",
                        "is_admin": user['is_admin']
                    })
            except Exception as e:
                return jsonify({"success": False, "msg": f"密码验证失败：{str(e)}"})

        return jsonify({"success": False, "msg": "账号或密码错误"})
    
    except Exception as e:
        # 捕获所有异常，确保返回JSON格式
        print(f"登录接口异常：{str(e)}")  # 打印错误到控制台用于调试
        return jsonify({
            "success": False, 
            "msg": f"服务器内部错误：{str(e)}"
        }), 500  # 明确返回500状态码

@app.route('/api/logout')
def api_logout():
    """登出接口：清空session"""
    session.clear()
    return redirect(url_for('index'))

# 购买相关API
@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    try:
        cart_items = get_cart_items()
        if not cart_items:
            return jsonify({'success': False, 'msg': '购物车为空'})
        
        total_amount = sum(item['subtotal'] for item in cart_items)
        user_id = session.get('user_id', 'anonymous')
        username = session.get('username', '匿名用户')  # 获取当前登录用户名
        
        print(f"当前操作的商品文件：{PRODUCTS_CSV}")
        
        def load_products_abs():
            if not os.path.exists(PRODUCTS_CSV):
                create_default_products()
            df = pd.read_csv(PRODUCTS_CSV, encoding='utf-8-sig')
            df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce').fillna(0).astype(int)
            return df.to_dict('records')
        
        products = load_products_abs()
        
        # 库存校验与扣减（原逻辑保留）
        for item in cart_items:
            product = next((p for p in products if p['product_id'] == item['product_id']), None)
            if not product:
                return jsonify({'success': False, 'msg': f'商品《{item["name"]}》不存在'})
            if product['stock'] < item['quantity']:
                return jsonify({'success': False, 'msg': f'商品《{item["name"]}》库存不足，仅剩{product["stock"]}件'})
        
        for item in cart_items:
            for p in products:
                if p['product_id'] == item['product_id']:
                    p['stock'] -= item['quantity']
                    break
        
        pd.DataFrame(products).to_csv(
            PRODUCTS_CSV,
            index=False,
            encoding='utf-8-sig',
            mode='w'
        )
        print("库存更新成功！")
        
        # 构造订单数据并写入orders.csv
        order_id = f"USER_ORDER_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:4]}"
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order_data = {
            'order_id': order_id,
            'user_id': user_id,
            'username': username,
            'total_amount': total_amount,
            'status': '已支付',
            'create_time': create_time,
            'items': json.dumps([{
                'product_id': item['product_id'],
                'name': item['name'],
                'image': item['image'],
                'quantity': item['quantity'],
                'price': item['price']
            } for item in cart_items])
        }
        
        if os.path.exists(ORDERS_CSV):
            order_df = pd.read_csv(ORDERS_CSV, encoding='utf-8-sig')
            new_order_df = pd.DataFrame([order_data])
            order_df = pd.concat([order_df, new_order_df], ignore_index=True)
        else:
            order_df = pd.DataFrame([order_data])
        order_df.to_csv(ORDERS_CSV, index=False, encoding='utf-8-sig')
        print(f"订单{order_id}已写入文件：{ORDERS_CSV}")
        
        # 记录用户购买行为
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
        print(f"购买失败详细原因：{str(e)}")
        return jsonify({'success': False, 'msg': f'购买失败：{str(e)}'})

# 收藏相关API
@app.route('/api/edit_profile', methods=['POST'])
def api_edit_profile():
    try:
        data = request.json
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
    try:
        user_id = session.get('user_id', 'anonymous')
        if user_id == 'anonymous':
            return jsonify({'success': False, 'msg': '请先登录再收藏！'})
        
        data = request.json
        product_id = data.get('product_id')
        if not product_id or not str(product_id).isdigit():
            return jsonify({'success': False, 'msg': '商品ID无效！'})
        product_id = int(product_id)
        
        all_products = load_products()
        product_exists = any(p['product_id'] == product_id for p in all_products)
        if not product_exists:
            return jsonify({'success': False, 'msg': '商品不存在！'})
        
        success = add_user_favorite(user_id, product_id)
        if success:
            return jsonify({'success': True, 'msg': '收藏成功！'})
        else:
            return jsonify({'success': False, 'msg': '已收藏该商品，或操作失败（见控制台日志）'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'收藏失败：{str(e)}'})

@app.route('/api/remove_favorite', methods=['POST'])
def api_remove_favorite():
    try:
        user_id = session.get('user_id', 'anonymous')
        if user_id == 'anonymous':
            return jsonify({'success': False, 'msg': '请先登录！'})
        
        data = request.json
        product_id = data.get('product_id')
        if not product_id or not str(product_id).isdigit():
            return jsonify({'success': False, 'msg': '商品ID无效！'})
        product_id = int(product_id)
        
        success = remove_user_favorite(user_id, product_id)
        if success:
            return jsonify({'success': True, 'msg': '取消收藏成功！'})
        else:
            return jsonify({'success': False, 'msg': '未收藏该商品，或操作失败（见控制台日志）'})
    except Exception as e:
        return jsonify({'success': False, 'msg': f'取消收藏失败：{str(e)}'})

@app.route('/api/check_favorite', methods=['GET'])
def api_check_favorite():
    try:
        user_id = session.get('user_id', 'anonymous')
        product_id = request.args.get('product_id')
        print(f"\n===== 检查收藏状态 =====")
        print(f"当前用户ID：{user_id}")
        print(f"要检查的商品ID：{product_id}")
        
        if user_id == 'anonymous':
            print("❌ 未登录，返回未收藏")
            return jsonify({'success': True, 'is_favorite': False, 'msg': '未登录'})
        
        if not product_id or not str(product_id).isdigit():
            print("❌ 商品ID无效")
            return jsonify({'success': False, 'is_favorite': False, 'msg': '商品ID无效'})
        product_id = int(product_id)
        
        favorite_ids = load_user_favorites(user_id)
        is_favorite = product_id in favorite_ids
        print(f"✅ 商品{product_id}是否已收藏：{is_favorite}")
        return jsonify({
            'success': True,
            'is_favorite': is_favorite
        })
    except Exception as e:
        print(f"❌ 检查收藏状态失败：{str(e)}")
        return jsonify({'success': False, 'is_favorite': False, 'msg': f'查询失败：{str(e)}'})

@app.route('/api/get_favorites', methods=['GET'])
def api_get_favorites():
    try:
        user_id = session.get('user_id', 'anonymous')
        if user_id == 'anonymous':
            return jsonify({'success': False, 'msg': '请先登录！'})
        
        favorite_ids = load_user_favorites(user_id)
        if not favorite_ids:
            return jsonify({'success': True, 'data': [], 'msg': '暂无收藏'})
        
        all_products = load_products()
        favorite_products = [p for p in all_products if p['product_id'] in favorite_ids]
        
        return jsonify({
            'success': True,
            'data': favorite_products,
            'count': len(favorite_products)
        })
    except Exception as e:
        print(f"获取收藏列表失败：{str(e)}")
        return jsonify({'success': False, 'msg': '加载失败，请重试'})

# 其他API
@app.route('/api/recharge', methods=['POST'])
def api_recharge():
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        if amount <= 0:
            return jsonify({'success': False, 'msg': '充值金额必须大于0！'})
        
        current_balance = session.get('balance', 0.00)
        session['balance'] = round(current_balance + amount, 2)
        
        # 同步更新users.csv中的余额（核心修改：补充phone字段）
        users = get_all_users()  # 已修改：会读取phone字段
        updated = False
        with open(USERS_CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            # 1. 修改fieldnames：新增phone字段（和表头顺序一致）
            fieldnames = ['user_id', 'username', 'password', 'phone', 'balance', 'favorites', 'is_admin']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for user in users:
                if user['user_id'] == session['user_id']:
                    user['balance'] = session['balance']
                    updated = True
                # 2. 直接写入user（get_all_users已包含phone字段，无需额外处理）
                writer.writerow(user)
        
        if not updated:
            print(f"警告：未找到用户{session['user_id']}，余额未持久化")
        
        return jsonify({
            'success': True,
            'msg': f'充值成功！当前余额：¥{session["balance"]}',
            'balance': session['balance']
        })
    except Exception as e:
        return jsonify({'success': False, 'msg': f'充值失败：{str(e)}'})

@app.route('/api/add_address', methods=['POST'])
def api_add_address():
    try:
        data = request.json
        required_fields = ['name', 'phone', 'province', 'city', 'area', 'detail']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'success': False, 'msg': f'{field}不能为空！'})
        
        addresses = session.get('addresses', [])
        new_id = max([addr['id'] for addr in addresses], default=0) + 1
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

# ---------------------- 程序入口（合并重复的启动逻辑）----------------------
if __name__ == '__main__':
    # 首次启动时执行一次订单迁移（仅当orders.csv不存在或为空时）
    if not os.path.exists(ORDERS_CSV) or (os.path.exists(ORDERS_CSV) and pd.read_csv(ORDERS_CSV).empty):
        migrate_purchase_to_orders()
    
    # 启动Flask服务器（关闭自动重载，避免Matplotlib线程冲突）
    app.run(debug=True, use_reloader=False, port=5000)