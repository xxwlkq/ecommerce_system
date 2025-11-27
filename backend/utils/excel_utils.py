#excel导出工具
#功能：提供 CSV 数据导出为 Excel 的通用工具函数
import pandas as pd
import os  # 新增：导入os模块
from io import BytesIO
from flask import send_file
from backend.config import Config

def export_orders_to_excel():
    """导出订单数据为Excel"""
    if not os.path.exists(Config.ORDERS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
    return _df_to_excel(df, '订单数据.xlsx')

def export_user_actions_to_excel():
    """导出用户行为数据为Excel"""
    if not os.path.exists(Config.USER_ACTIONS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.USER_ACTIONS_CSV_PATH, encoding='utf-8-sig')
    return _df_to_excel(df, '用户行为数据.xlsx')

def export_products_to_excel():
    """导出商品数据为Excel"""
    if not os.path.exists(Config.PRODUCTS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.PRODUCTS_CSV_PATH, encoding='utf-8-sig')
    return _df_to_excel(df, '商品数据.xlsx')

def _df_to_excel(df, filename):
    """内部方法：将DataFrame转换为Excel文件流"""
    output = BytesIO()
    # 使用openpyxl引擎保存Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=filename.split('.')[0])
    # 重置文件指针到开头
    output.seek(0)
    # 返回Flask send_file对象
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )