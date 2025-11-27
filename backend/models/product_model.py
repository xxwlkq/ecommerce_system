#商品数据模型
#功能：封装商品的增删改查、库存更新、行为记录等逻辑
import pandas as pd
import os
from backend.config import Config
from datetime import datetime

class ProductModel:
    @staticmethod
    def get_all_products(category=None):
        """获取所有商品（支持分类筛选）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return []
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        # 分类筛选
        if category and category != '全部商品':
            df = df[df['category'] == category]
        return df.to_dict('records')
    
    @staticmethod
    def get_product_by_id(product_id):
        """通过ID获取商品详情"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        product = df[df['product_id'] == product_id]
        return product.to_dict('records')[0] if not product.empty else None
    
    @staticmethod
    def get_all_categories():
        """获取所有商品分类（去重）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return ['测试分类']
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        categories = df['category'].unique().tolist()
        return ['全部商品'] + categories  # 增加"全部商品"选项
    
    @staticmethod
    def add_product(product_data):
        """新增商品（后台管理用）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        # 生成新商品ID（最大ID+1）
        new_id = df['product_id'].max() + 1 if not df.empty else 1
        product_data['product_id'] = new_id
        
        # 追加新商品
        new_product = pd.DataFrame([product_data])
        df = pd.concat([df, new_product], ignore_index=True)
        df.to_csv(Config.PRODUCTS_CSV_PATH, index=False, encoding='utf-8-sig')
        return new_id
    
    @staticmethod
    def update_product(product_id, update_data):
        """修改商品信息（后台管理用）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        if product_id not in df['product_id'].values:
            return False
        
        # 更新指定字段
        for key, value in update_data.items():
            if key in df.columns:
                df.loc[df['product_id'] == product_id, key] = value
        
        df.to_csv(Config.PRODUCTS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def update_product_stock(product_id, stock_change):
        """更新商品库存（正数增加，负数减少）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        if product_id not in df['product_id'].values:
            return False
        
        # 计算新库存（不能小于0）
        current_stock = df.loc[df['product_id'] == product_id, 'stock'].iloc[0]
        new_stock = max(current_stock + stock_change, 0)
        df.loc[df['product_id'] == product_id, 'stock'] = new_stock
        
        df.to_csv(Config.PRODUCTS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def delete_product(product_id):
        """删除商品（后台管理用）"""
        if not os.path.exists(Config.PRODUCTS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
        if product_id not in df['product_id'].values:
            return False
        
        # 过滤掉要删除的商品
        df = df[df['product_id'] != product_id]
        df.to_csv(Config.PRODUCTS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def record_user_action(user_id, username, product_id, product_name, product_category, action_type, quantity=1, total_amount=0):
        """记录用户行为（浏览/加购等）到user_actions.csv"""
        action_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'username': username,
            'product_id': product_id,
            'product_name': product_name,
            'product_category': product_category,
            'action_type': action_type,
            'session_id': '',  # 简化版：session_id可从Flask session获取，此处留空
            'quantity': quantity,
            'total_amount': total_amount
        }
        
        # 写入CSV
        if os.path.exists(Config.USER_ACTIONS_CSV_PATH):
            df = pd.read_csv(Config.USER_ACTIONS_CSV_PATH, encoding='utf-8-sig')
        else:
            df = pd.DataFrame(columns=action_data.keys())
        
        new_row = pd.DataFrame([action_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(Config.USER_ACTIONS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True