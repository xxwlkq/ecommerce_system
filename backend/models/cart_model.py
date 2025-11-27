import pandas as pd
import os
import json
from backend.config import Config

class CartModel:
    @staticmethod
    def get_cart_items(user_id):
        """获取用户购物车所有商品（含商品详情）"""
        if not os.path.exists(Config.CART_CSV_PATH):
            return []
        
        # 读取购物车数据
        cart_df = pd.read_csv(Config.CART_CSV_PATH, encoding='utf-8-sig')
        user_cart = cart_df[cart_df['user_id'] == user_id]
        if user_cart.empty:
            return []
        
        # 关联商品详情（从products.csv获取）
        from backend.models.product_model import ProductModel
        cart_items = []
        for _, row in user_cart.iterrows():
            product = ProductModel.get_product_by_id(row['product_id'])
            if product:
                # 计算小计金额
                subtotal = round(product['price'] * row['quantity'], 2)
                cart_items.append({
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'category': product['category'],
                    'price': product['price'],
                    'image': product['image'],
                    'quantity': row['quantity'],
                    'subtotal': subtotal
                })
        return cart_items
    
    @staticmethod
    def add_to_cart(user_id, product_id, quantity):
        """添加商品到购物车（已存在则更新数量）"""
        if not os.path.exists(Config.CART_CSV_PATH):
            return False
        
        cart_df = pd.read_csv(Config.CART_CSV_PATH, encoding='utf-8-sig')
        # 检查商品是否已在购物车
        mask = (cart_df['user_id'] == user_id) & (cart_df['product_id'] == product_id)
        
        if mask.any():
            # 已存在：更新数量
            cart_df.loc[mask, 'quantity'] += quantity
        else:
            # 不存在：新增记录
            new_item = pd.DataFrame([{
                'user_id': user_id,
                'product_id': product_id,
                'quantity': quantity
            }])
            cart_df = pd.concat([cart_df, new_item], ignore_index=True)
        
        cart_df.to_csv(Config.CART_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def remove_from_cart(user_id, product_id):
        """从购物车移除商品"""
        if not os.path.exists(Config.CART_CSV_PATH):
            return False
        
        cart_df = pd.read_csv(Config.CART_CSV_PATH, encoding='utf-8-sig')
        mask = (cart_df['user_id'] == user_id) & (cart_df['product_id'] == product_id)
        if not mask.any():
            return False
        
        # 过滤掉要移除的商品
        cart_df = cart_df[~mask]
        cart_df.to_csv(Config.CART_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def update_cart_quantity(user_id, product_id, new_quantity):
        """更新购物车商品数量"""
        if not os.path.exists(Config.CART_CSV_PATH):
            return False
        
        cart_df = pd.read_csv(Config.CART_CSV_PATH, encoding='utf-8-sig')
        mask = (cart_df['user_id'] == user_id) & (cart_df['product_id'] == product_id)
        if not mask.any():
            return False
        
        cart_df.loc[mask, 'quantity'] = new_quantity
        cart_df.to_csv(Config.CART_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def clear_cart(user_id):
        """清空用户购物车"""
        if not os.path.exists(Config.CART_CSV_PATH):
            return
        
        cart_df = pd.read_csv(Config.CART_CSV_PATH, encoding='utf-8-sig')
        # 保留非当前用户的购物车数据
        cart_df = cart_df[cart_df['user_id'] != user_id]
        cart_df.to_csv(Config.CART_CSV_PATH, index=False, encoding='utf-8-sig')
    
    @staticmethod
    def get_cart_total(user_id):
        """计算购物车总金额"""
        cart_items = CartModel.get_cart_items(user_id)
        return round(sum(item['subtotal'] for item in cart_items), 2)