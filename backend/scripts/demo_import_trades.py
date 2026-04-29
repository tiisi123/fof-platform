"""
导入历史成交数据作为持仓明细示例数据
从 data/20260227_历史成交查询.xls 导入
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.holdings_detail import HoldingsDetail
from app.models.product import Product


def clean_excel_value(val):
    """清理Excel中的公式格式 ="xxx" """
    if isinstance(val, str) and val.startswith('="') and val.endswith('"'):
        return val[2:-1]
    return val


def parse_trade_data(file_path: str):
    """解析历史成交数据"""
    print(f"读取文件: {file_path}")
    
    # 读取Excel文件
    df = pd.read_excel(file_path, dtype=str)
    
    # 清理列名和数据中的Excel公式格式
    df.columns = [clean_excel_value(col) for col in df.columns]
    for col in df.columns:
        df[col] = df[col].apply(clean_excel_value)
    
    print(f"总行数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    
    return df


def aggregate_holdings_by_date(df: pd.DataFrame):
    """按日期聚合持仓数据"""
    # 过滤掉指数登记等非实际持仓
    df = df[df['证券类别'] == '证券买卖'].copy()
    
    # 转换数据类型
    df['成交日期'] = pd.to_datetime(df['成交日期'], format='%Y%m%d')
    df['成交数量'] = pd.to_numeric(df['成交数量'], errors='coerce')
    df['成交价格'] = pd.to_numeric(df['成交价格'], errors='coerce')
    df['成交金额'] = pd.to_numeric(df['成交金额'], errors='coerce')
    
    # 按证券代码和日期聚合，计算累计持仓
    holdings = []
    
    # 获取所有唯一的证券和日期
    securities = df[['证券代码', '证券名称']].drop_duplicates()
    dates = sorted(df['成交日期'].unique())
    
    print(f"\n处理 {len(securities)} 只证券，{len(dates)} 个交易日")
    
    # 按证券分组计算持仓
    for _, sec in securities.iterrows():
        code = sec['证券代码']
        name = sec['证券名称']
        
        # 获取该证券的所有交易
        sec_trades = df[df['证券代码'] == code].sort_values('成交日期')
        
        cumulative_qty = 0
        cumulative_cost = 0
        
        for date in dates:
            # 获取该日期的交易
            day_trades = sec_trades[sec_trades['成交日期'] == date]
            
            if len(day_trades) > 0:
                # 更新累计持仓
                for _, trade in day_trades.iterrows():
                    qty = trade['成交数量']
                    price = trade['成交价格']
                    amount = trade['成交金额']
                    
                    cumulative_qty += qty
                    cumulative_cost += amount
            
            # 如果有持仓，记录
            if cumulative_qty != 0:
                avg_cost = cumulative_cost / cumulative_qty if cumulative_qty > 0 else 0
                
                holdings.append({
                    'holding_date': date,
                    'security_code': code,
                    'security_name': name,
                    'quantity': cumulative_qty,
                    'cost_price': avg_cost,
                    'cost': cumulative_cost,
                })
    
    return pd.DataFrame(holdings)


def import_to_database(holdings_df: pd.DataFrame, product_id: int, db: Session):
    """导入到数据库"""
    print(f"\n开始导入数据到产品 ID: {product_id}")
    
    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        print(f"错误: 产品 ID {product_id} 不存在")
        return
    
    print(f"产品: {product.product_name} ({product.product_code})")
    
    # 删除该产品的旧持仓数据
    deleted = db.query(HoldingsDetail).filter(
        HoldingsDetail.product_id == product_id
    ).delete()
    print(f"删除旧数据: {deleted} 条")
    
    # 导入新数据
    count = 0
    for _, row in holdings_df.iterrows():
        holding = HoldingsDetail(
            product_id=product_id,
            holding_date=row['holding_date'].date(),
            security_type='stock',  # 股票
            security_code=row['security_code'],
            security_name=row['security_name'],
            quantity=float(row['quantity']),
            cost_price=float(row['cost_price']),
            cost=float(row['cost']),
            level=1,  # 一级持仓
        )
        db.add(holding)
        count += 1
        
        if count % 100 == 0:
            print(f"已处理 {count} 条...")
    
    db.commit()
    print(f"\n成功导入 {count} 条持仓记录")
    
    # 统计信息
    dates = holdings_df['holding_date'].unique()
    securities = holdings_df['security_code'].unique()
    print(f"日期范围: {min(dates).strftime('%Y-%m-%d')} 至 {max(dates).strftime('%Y-%m-%d')}")
    print(f"证券数量: {len(securities)}")


def main():
    """主函数"""
    # 文件路径
    file_path = "data/20260227_历史成交查询.xls"
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return
    
    # 解析数据
    df = parse_trade_data(file_path)
    
    # 聚合持仓
    holdings_df = aggregate_holdings_by_date(df)
    
    if len(holdings_df) == 0:
        print("警告: 没有生成持仓数据")
        return
    
    print(f"\n生成持仓记录: {len(holdings_df)} 条")
    print("\n示例数据:")
    print(holdings_df.head(10))
    
    # 导入数据库
    db = SessionLocal()
    try:
        # 这里需要指定一个产品ID，可以从命令行参数获取
        # 或者创建一个测试产品
        product_id = int(input("\n请输入产品ID (或输入0创建测试产品): "))
        
        if product_id == 0:
            # 创建测试产品
            from app.models.manager import Manager
            
            # 查找或创建测试管理人
            manager = db.query(Manager).filter(Manager.name.like('%测试%')).first()
            if not manager:
                manager = Manager(
                    manager_code="TEST001",
                    name="测试管理人",
                    short_name="测试",
                    primary_strategy="股票多头",
                    cooperation_status="已投资",
                )
                db.add(manager)
                db.commit()
                db.refresh(manager)
            
            # 创建测试产品
            product = Product(
                product_code="TEST_PRODUCT_001",
                product_name="历史成交测试产品",
                manager_id=manager.id,
                strategy_type="股票多头",
                is_invested=True,
                status="active",
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            product_id = product.id
            print(f"\n创建测试产品: {product.product_name} (ID: {product_id})")
        
        import_to_database(holdings_df, product_id, db)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
