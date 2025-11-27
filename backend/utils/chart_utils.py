#图表生成工具
#功能：提供后台看板所需的动态图表生成函数（基于 matplotlib）
import pandas as pd
import matplotlib.pyplot as plt
import base64
import os  # 新增：导入os模块
from io import BytesIO
from backend.config import Config

# 设置中文字体（避免中文乱码）
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def generate_action_distribution_chart():
    """生成用户行为分布饼图"""
    if not os.path.exists(Config.USER_ACTIONS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.USER_ACTIONS_CSV_PATH, encoding='utf-8-sig')
    action_counts = df['action_type'].value_counts()
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
    ax.pie(action_counts.values, labels=action_counts.index, autopct='%1.1f%%', colors=colors[:len(action_counts)], startangle=90)
    ax.set_title('用户行为分布', fontsize=14, fontweight='bold')
    
    # 转换为base64（前端可直接显示）
    return _fig_to_base64(fig)

def generate_top_products_chart():
    """生成热门商品TOP5柱状图"""
    if not os.path.exists(Config.USER_ACTIONS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.USER_ACTIONS_CSV_PATH, encoding='utf-8-sig')
    # 筛选浏览/购买行为，统计商品热度
    product_heat = df[df['action_type'].isin(['view', 'purchase'])]['product_name'].value_counts().head(5)
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    bars = ax.bar(range(len(product_heat)), product_heat.values, color='#45B7D1')
    ax.set_title('热门商品TOP5', fontsize=14, fontweight='bold')
    ax.set_xlabel('商品名称', fontsize=12)
    ax.set_ylabel('访问次数', fontsize=12)
    ax.set_xticks(range(len(product_heat)))
    ax.set_xticklabels(product_heat.index, rotation=45, ha='right')
    
    # 在柱子上显示数值
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}', ha='center', va='bottom')
    
    return _fig_to_base64(fig)

def generate_daily_trend_chart():
    """生成每日用户行为趋势折线图"""
    if not os.path.exists(Config.USER_ACTIONS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.USER_ACTIONS_CSV_PATH, encoding='utf-8-sig')
    df['date'] = pd.to_datetime(df['timestamp']).dt.date  # 提取日期
    daily_actions = df.groupby('date').size()
    
    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    ax.plot(daily_actions.index, daily_actions.values, marker='o', linewidth=2, color='#FF6B6B', markersize=6)
    ax.set_title('每日用户行为趋势', fontsize=14, fontweight='bold')
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('行为次数', fontsize=12)
    plt.xticks(rotation=45)
    ax.grid(True, alpha=0.3)
    
    return _fig_to_base64(fig)

def generate_order_amount_chart():
    """生成订单金额分布柱状图"""
    if not os.path.exists(Config.ORDERS_CSV_PATH):  # 现在os已定义
        return None
    
    df = pd.read_csv(Config.ORDERS_CSV_PATH, encoding='utf-8-sig')
    # 按金额区间分组
    amount_bins = [0, 1000, 3000, 5000, 10000, float('inf')]
    amount_labels = ['0-1000元', '1000-3000元', '3000-5000元', '5000-10000元', '10000元以上']
    df['amount_range'] = pd.cut(df['total_amount'], bins=amount_bins, labels=amount_labels, right=False)
    amount_counts = df['amount_range'].value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    bars = ax.bar(range(len(amount_counts)), amount_counts.values, color='#96CEB4')
    ax.set_title('订单金额分布', fontsize=14, fontweight='bold')
    ax.set_xlabel('金额区间', fontsize=12)
    ax.set_ylabel('订单数量', fontsize=12)
    ax.set_xticks(range(len(amount_counts)))
    ax.set_xticklabels(amount_counts.index)
    
    # 在柱子上显示数值
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}', ha='center', va='bottom')
    
    return _fig_to_base64(fig)

def _fig_to_base64(fig):
    """内部方法：将matplotlib图表转换为base64字符串"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)  # 关闭图表，释放内存
    return base64_str