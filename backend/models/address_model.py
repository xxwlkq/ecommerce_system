#地址数据模型
#功能：封装用户收货地址的增删改查逻辑
import pandas as pd
import os
from backend.config import Config

class AddressModel:
    @staticmethod
    def add_address(user_id, address_data):
        """添加用户收货地址"""
        if not os.path.exists(Config.ADDRESSES_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.ADDRESSES_CSV_PATH, encoding='utf-8-sig')
        # 生成新地址ID
        new_id = df['address_id'].max() + 1 if not df.empty else 1
        
        # 如果设为默认地址，先取消其他默认地址
        if address_data['is_default']:
            df.loc[df['user_id'] == user_id, 'is_default'] = False
        
        # 构造地址数据
        new_address = {
            'address_id': new_id,
            'user_id': user_id,
            'receiver': address_data['receiver'],
            'phone': address_data['phone'],
            'province': address_data['province'],
            'city': address_data['city'],
            'detail_address': address_data['detail_address'],
            'is_default': address_data['is_default']
        }
        
        # 追加新地址
        df = pd.concat([df, pd.DataFrame([new_address])], ignore_index=True)
        df.to_csv(Config.ADDRESSES_CSV_PATH, index=False, encoding='utf-8-sig')
        return new_id
    
    @staticmethod
    def get_addresses_by_user_id(user_id):
        """获取用户的所有收货地址"""
        if not os.path.exists(Config.ADDRESSES_CSV_PATH):
            return []
        
        df = pd.read_csv(Config.ADDRESSES_CSV_PATH, encoding='utf-8-sig')
        addresses = df[df['user_id'] == user_id]
        return addresses.to_dict('records')
    
    @staticmethod
    def get_address_by_id(address_id, user_id):
        """通过地址ID获取地址详情（验证用户归属）"""
        if not os.path.exists(Config.ADDRESSES_CSV_PATH):
            return None
        
        df = pd.read_csv(Config.ADDRESSES_CSV_PATH, encoding='utf-8-sig')
        address = df[(df['address_id'] == address_id) & (df['user_id'] == user_id)]
        return address.to_dict('records')[0] if not address.empty else None
    
    @staticmethod
    def update_address(address_id, user_id, update_data):
        """修改收货地址"""
        if not os.path.exists(Config.ADDRESSES_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.ADDRESSES_CSV_PATH, encoding='utf-8-sig')
        mask = (df['address_id'] == address_id) & (df['user_id'] == user_id)
        if not mask.any():
            return False
        
        # 如果设为默认地址，先取消其他默认地址
        if update_data.get('is_default', False):
            df.loc[df['user_id'] == user_id, 'is_default'] = False
        
        # 更新字段
        for key, value in update_data.items():
            if key in df.columns:
                df.loc[mask, key] = value
        
        df.to_csv(Config.ADDRESSES_CSV_PATH, index=False, encoding='utf-8-sig')
        return True
    
    @staticmethod
    def delete_address(address_id, user_id):
        """删除收货地址"""
        if not os.path.exists(Config.ADDRESSES_CSV_PATH):
            return False
        
        df = pd.read_csv(Config.ADDRESSES_CSV_PATH, encoding='utf-8-sig')
        mask = (df['address_id'] == address_id) & (df['user_id'] == user_id)
        if not mask.any():
            return False
        
        # 过滤掉要删除的地址
        df = df[~mask]
        df.to_csv(Config.ADDRESSES_CSV_PATH, index=False, encoding='utf-8-sig')
        return True