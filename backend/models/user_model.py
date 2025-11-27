#用户数据模型
#功能：封装用户登录验证、余额充值、收藏管理、行为记录等逻辑
import pandas as pd
import os
import json
from backend.config import Config
from datetime import datetime

class UserModel:
    @staticmethod
    def get_user_by_id(user_id):
        """通过user_id获取用户信息"""
        if not os.path.exists(Config.USERS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.USERS_CSV_PATH, encoding='utf-8-sig')
        user = df[df['user_id'] == user_id]
        return user.to_dict('records')[0] if not user.empty else None
    
    @staticmethod
    def get_user_by_username(username):
        """通过用户名获取用户信息"""
        if not os.path.exists(Config.USERS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.USERS_CSV_PATH, encoding='utf-8-sig')
        user = df[df['username'] == username]
        return user.to_dict('records')[0] if not user.empty else None
    
    @staticmethod
    def verify_login(username, password):
        """验证用户登录（简化版：密码直接存储，实际应加密）"""
        user = UserModel.get_user_by_username(username)
        if not user:
            return None
        
        # 匿名用户无需密码，管理员/普通用户验证密码（此处简化：密码统一为123456）
        if user['user_id'] == 'anonymous':
            return user
        if user['password'] == password:  # 实际项目中需用bcrypt加密
            return user
        return None
    
    @staticmethod
    def get_user_balance(user_id):
        """获取用户余额"""
        user = UserModel.get_user_by_id(user_id)
        return user['balance'] if user else 0.0
    
    @staticmethod
    def recharge_balance(user_id, amount):
        """充值/扣减用户余额（amount为正充值，为负扣减）"""
        if not os.path.exists(Config.USERS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.USERS_CSV_PATH, encoding='utf-8-sig')
        if user_id not in df['user_id'].values:
            return False
        
        # 计算新余额（不能小于0）
        current_balance = df.loc[df['user_id'] == user_id, 'balance'].iloc[0]
        new_balance = max(current_balance + amount, 0.0)
        df.loc[df['user_id'] == user_id, 'balance'] = new_balance
        
        df.to_csv(Config.USERS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def get_user_favorites(user_id):
        """获取用户收藏的商品ID列表"""
        user = UserModel.get_user_by_id(user_id)
        if not user or pd.isna(user['favorites']):
            return []
        
        # 收藏列表存储为JSON字符串，需解析为列表
        try:
            favorites = json.loads(user['favorites'])
            return [int(pid) for pid in favorites if str(pid).isdigit()]
        except:
            return []
    
    @staticmethod
    def add_favorite(user_id, product_id):
        """添加商品到收藏夹"""
        favorites = UserModel.get_user_favorites(user_id)
        if product_id in favorites:
            return False  # 已收藏
        
        # 更新收藏列表
        favorites.append(product_id)
        return UserModel._update_favorites(user_id, favorites)
    
    @staticmethod
    def remove_favorite(user_id, product_id):
        """从收藏夹移除商品"""
        favorites = UserModel.get_user_favorites(user_id)
        if product_id not in favorites:
            return False  # 未收藏
        
        # 更新收藏列表
        favorites.remove(product_id)
        return UserModel._update_favorites(user_id, favorites)
    
    @staticmethod
    def _update_favorites(user_id, favorites):
        """内部方法：更新用户收藏列表到CSV"""
        if not os.path.exists(Config.USERS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.USERS_CSV_PATH, encoding='utf-8-sig')
        if user_id not in df['user_id'].values:
            return False
        
        # 转换为JSON字符串存储
        favorites_str = json.dumps(favorites, ensure_ascii=False)
        df.loc[df['user_id'] == user_id, 'favorites'] = favorites_str
        
        df.to_csv(Config.USERS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def record_user_action(user_id, product_id, action_type, quantity=1, total_amount=0, product_name='', product_category=''):
        """记录用户行为（复用商品模型的记录方法，简化代码）"""
        from backend.models.product_model import ProductModel
        username = UserModel.get_user_by_id(user_id)['username'] if UserModel.get_user_by_id(user_id) else '匿名用户'
        
        # 如果未传商品名称和分类，自动获取
        if not product_name and product_id != 0:
            product = ProductModel.get_product_by_id(product_id)
            if product:
                product_name = product['name']
                product_category = product['category']
        
        return ProductModel.record_user_action(
            user_id=user_id,
            username=username,
            product_id=product_id,
            product_name=product_name,
            product_category=product_category,
            action_type=action_type,
            quantity=quantity,
            total_amount=total_amount
        )