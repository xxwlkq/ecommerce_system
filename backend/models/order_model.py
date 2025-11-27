#订单数据模型
#功能：封装订单创建、查询、状态更新等逻辑
import pandas as pd
import os
import json
from backend.config import Config

class OrderModel:
    @staticmethod
    def create_order(order_data):
        """创建新订单"""
        if not os.path.exists(Config.ORDERS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
        # 生成新订单ID（最大ID+1）
        new_id = df['order_id'].max() + 1 if not df.empty else 1
        order_data['order_id'] = new_id
        
        # 列表类型字段转换为字符串（CSV无法直接存储列表）
        order_data['product_ids'] = json.dumps(order_data['product_ids'])
        order_data['product_names'] = json.dumps(order_data['product_names'], ensure_ascii=False)
        order_data['quantities'] = json.dumps(order_data['quantities'])
        
        # 追加新订单
        new_order = pd.DataFrame([order_data])
        df = pd.concat([df, new_order], ignore_index=True)
        df.to_csv(Config.ORDERS_CSV_PATH, index=False, encoding='utf-8-sig')
        return new_id
    
    @staticmethod
    def get_order_by_id(order_id):
        """通过订单ID获取订单详情"""
        if not os.path.exists(Config.ORDERS_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
        order = df[df['order_id'] == order_id]
        if order.empty:
            return None
        
        # 字符串转列表（恢复原始数据格式）
        order_dict = order.to_dict('records')[0]
        try:
            order_dict['product_ids'] = json.loads(order_dict['product_ids'])
            order_dict['product_names'] = json.loads(order_dict['product_names'])
            order_dict['quantities'] = json.loads(order_dict['quantities'])
        except:
            pass
        
        return order_dict
    
    @staticmethod
    def get_orders_by_user_id(user_id):
        """获取用户的所有订单"""
        if not os.path.exists(Config.ORDERS_CSV_PATH):
            return []
        
        df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
        user_orders = df[df['user_id'] == user_id]
        if user_orders.empty:
            return []
        
        # 转换列表字段并排序（按创建时间倒序）
        orders = []
        for _, row in user_orders.iterrows():
            order_dict = row.to_dict()
            try:
                order_dict['product_ids'] = json.loads(order_dict['product_ids'])
                order_dict['product_names'] = json.loads(order_dict['product_names'])
                order_dict['quantities'] = json.loads(order_dict['quantities'])
            except:
                pass
            orders.append(order_dict)
        
        # 按创建时间倒序排序（最新订单在前）
        orders.sort(key=lambda x: x['create_time'], reverse=True)
        return orders
    
    @staticmethod
    def get_all_orders():
        """获取所有订单（后台管理用）"""
        if not os.path.exists(Config.ORDERS_CSV_PATH):
            return []
        
        df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
        if df.empty:
            return []
        
        # 转换列表字段并排序
        orders = []
        for _, row in df.iterrows():
            order_dict = row.to_dict()
            try:
                order_dict['product_ids'] = json.loads(order_dict['product_ids'])
                order_dict['product_names'] = json.loads(order_dict['product_names'])
                order_dict['quantities'] = json.loads(order_dict['quantities'])
            except:
                pass
            orders.append(order_dict)
        
        orders.sort(key=lambda x: x['create_time'], reverse=True)
        return orders
    
    @staticmethod
    def update_order_status(order_id, new_status):
        """更新订单状态（已支付/已取消/已发货等）"""
        if not os.path.exists(Config.ORDERS_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
        if order_id not in df['order_id'].values:
            return False
        
        df.loc[df['order_id'] == order_id, 'status'] = new_status
        df.to_csv(Config.ORDERS_CSV_PATH, index=False, encoding='utf-8-sig')
        return True