#配置文件，集中管理路径 / 密钥
#功能：定义所有配置项（路径、密钥、上传规则），避免硬编码

import os

# 项目根目录（自动计算，无需手动修改）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ---------------------- 数据文件路径配置 ----------------------
DATA_DIR = os.path.join(ROOT_DIR, 'data')
PRODUCTS_CSV_PATH = os.path.join(DATA_DIR, 'products.csv')
USERS_CSV_PATH = os.path.join(DATA_DIR, 'users.csv')
ORDERS_CSV_PATH = os.path.join(DATA_DIR, 'orders.csv')
USER_ACTIONS_CSV_PATH = os.path.join(DATA_DIR, 'user_actions.csv')
ADDRESSES_CSV_PATH = os.path.join(DATA_DIR, 'addresses.csv')
CART_CSV_PATH = os.path.join(DATA_DIR, 'cart.csv')  # 新增：购物车数据文件路径

# ---------------------- 图片上传配置 ----------------------
# 商品图片上传目录（前端静态资源目录）
PRODUCT_UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'frontend/static/admin/uploads/products')
# 允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 最大上传文件大小（5MB）
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

# ---------------------- Flask配置 ----------------------
SECRET_KEY = 'ecommerce_2024_project_secret_key_123'  # 加密session用
JSON_AS_ASCII = False  # 解决中文乱码

# ---------------------- 初始化必要目录（程序启动时自动创建） ----------------------
def init_dirs():
    # 创建数据目录
    os.makedirs(DATA_DIR, exist_ok=True)
    # 创建图片上传目录
    os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)
    # 创建默认CSV文件（避免读取时报错）
    create_default_csvs()

def create_default_csvs():
    # 1. 默认商品表
    if not os.path.exists(PRODUCTS_CSV_PATH):
        import pandas as pd
        default_products = pd.DataFrame([{
            'product_id': 1,
            'name': '默认商品（后台可修改）',
            'category': '测试分类',
            'price': 99.0,
            'stock': 100,
            'description': '这是默认商品，管理员可在后台修改/新增商品',
            'image': 'default_product.jpg'
        }])
        default_products.to_csv(PRODUCTS_CSV_PATH, index=False, encoding='utf-8-sig')
    
    # 2. 默认用户表（含匿名用户）
    if not os.path.exists(USERS_CSV_PATH):
        import pandas as pd
        default_users = pd.DataFrame([{
            'user_id': 'anonymous',
            'username': '匿名用户',
            'password': '',  # 匿名用户无密码
            'balance': 0.0,
            'favorites': '[]',  # 收藏商品ID列表（JSON字符串）
            'is_admin': False
        }])
        default_users.to_csv(USERS_CSV_PATH, index=False, encoding='utf-8-sig')
    
    # 3. 其他空表（含购物车表）
    # 格式：(文件路径, 表头列名列表)
    csv_configs = [
        (ORDERS_CSV_PATH, ['order_id', 'user_id', 'username', 'product_ids', 'product_names', 'quantities', 'total_amount', 'create_time', 'status']),
        (USER_ACTIONS_CSV_PATH, ['timestamp', 'user_id', 'username', 'product_id', 'product_name', 'product_category', 'action_type', 'session_id', 'quantity', 'total_amount']),
        (ADDRESSES_CSV_PATH, ['address_id', 'user_id', 'receiver', 'phone', 'province', 'city', 'detail_address', 'is_default']),
        (CART_CSV_PATH, ['user_id', 'product_id', 'quantity'])  # 新增：购物车表结构
    ]
    
    # 循环创建空表
    import pandas as pd
    for path, columns in csv_configs:
        if not os.path.exists(path):
            pd.DataFrame(columns=columns).to_csv(path, index=False, encoding='utf-8-sig')

# 程序启动时自动初始化目录和默认文件
init_dirs()