"""
导入 daily_nav_modelb 实盘策略数据
"""
import sys
import os

# 确保可以导入同目录下的 app
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from decimal import Decimal

from app.models.manager import Manager
from app.models.product import Product
from app.models.nav import NavData

# 数据库连接：始终指向 backend/fof.db，而不是当前工作目录
BACKEND_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BACKEND_DIR, "fof.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=" * 80)
print("导入 daily_nav_modelb 实盘策略")
print("=" * 80)
print()

# 1. 创建或获取管理人
print("步骤1: 创建管理人...")
manager = db.query(Manager).filter(Manager.manager_name == "上海天市信息技术有限公司").first()

if not manager:
    manager = Manager(
        manager_code="SHTS_001",
        manager_name="上海天市信息技术有限公司",
        short_name="天市科技",
        registration_no="P1069999",
        primary_strategy="quant_neutral",  # 量化中性
        pool_category="invested",  # 在投池
        registered_address="上海市",
        remark="量化策略管理人"
    )
    db.add(manager)
    db.flush()
    print(f"  ✓ 创建管理人: {manager.manager_name} (ID: {manager.id})")
else:
    print(f"  ✓ 管理人已存在: {manager.manager_name} (ID: {manager.id})")

# 2. 创建或获取产品
print()
print("步骤2: 创建产品...")
product = db.query(Product).filter(Product.product_code == "TSKJ_QT_001").first()

if not product:
    product = Product(
        product_code="TSKJ_QT_001",
        product_name="天市量化1号私募证券投资基金",
        manager_id=manager.id,
        strategy_type="量化策略",
        established_date=date(2026, 1, 14),  # 根据第一条数据
        status="active",
        is_invested=True,
        remark="ModelB量化策略"
    )
    db.add(product)
    db.flush()
    print(f"  ✓ 创建产品: {product.product_name} (ID: {product.id})")
else:
    print(f"  ✓ 产品已存在: {product.product_name} (ID: {product.id})")

db.commit()

# 3. 读取CSV文件
print()
print("步骤3: 读取净值数据...")
csv_path = os.path.join(os.path.dirname(__file__), "..", "daily_nav_modelb.csv")

try:
    df = pd.read_csv(csv_path)
    print(f"  ✓ 读取到 {len(df)} 条记录")
    print(f"  日期范围: {df['date'].min()} 至 {df['date'].max()}")
except Exception as e:
    print(f"  ✗ 读取失败: {e}")
    db.close()
    sys.exit(1)

# 4. 导入净值数据
print()
print("步骤4: 导入净值数据...")

new_count = 0
update_count = 0
skip_count = 0

for idx, row in df.iterrows():
    try:
        # 解析日期
        nav_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
        
        # 获取净值
        nav_value = float(row['nav'])
        
        # 检查是否已存在
        existing = db.query(NavData).filter(
            NavData.product_id == product.id,
            NavData.nav_date == nav_date
        ).first()
        
        if existing:
            # 更新现有记录
            existing.unit_nav = Decimal(str(nav_value))
            existing.cumulative_nav = Decimal(str(nav_value))
            update_count += 1
        else:
            # 创建新记录
            nav_data = NavData(
                product_id=product.id,
                nav_date=nav_date,
                unit_nav=Decimal(str(nav_value)),
                cumulative_nav=Decimal(str(nav_value))
            )
            db.add(nav_data)
            new_count += 1
        
        # 每100条提交一次
        if (idx + 1) % 100 == 0:
            db.commit()
            print(f"  进度: {idx + 1}/{len(df)}")
    
    except Exception as e:
        print(f"  ✗ 第 {idx + 1} 行导入失败: {e}")
        skip_count += 1
        continue

# 最终提交
db.commit()

print()
print("=" * 80)
print("导入完成")
print("=" * 80)
print(f"  新增记录: {new_count}")
print(f"  更新记录: {update_count}")
print(f"  跳过记录: {skip_count}")
print(f"  总计: {new_count + update_count + skip_count}")

# 5. 计算并显示统计信息
print()
print("=" * 80)
print("产品统计信息")
print("=" * 80)

nav_records = db.query(NavData).filter(NavData.product_id == product.id).order_by(NavData.nav_date).all()

if nav_records:
    first_nav = nav_records[0]
    last_nav = nav_records[-1]
    
    # 计算收益率
    total_return = (float(last_nav.unit_nav) / float(first_nav.unit_nav) - 1) * 100
    
    # 计算年化收益率
    days = (last_nav.nav_date - first_nav.nav_date).days
    if days > 0:
        annual_return = ((float(last_nav.unit_nav) / float(first_nav.unit_nav)) ** (365 / days) - 1) * 100
    else:
        annual_return = 0
    
    print(f"产品名称: {product.product_name}")
    print(f"产品代码: {product.product_code}")
    print(f"管理人: {manager.manager_name}")
    print(f"策略类型: {product.strategy_type}")
    print()
    print(f"成立日期: {first_nav.nav_date}")
    print(f"最新日期: {last_nav.nav_date}")
    print(f"运行天数: {days} 天")
    print()
    print(f"初始净值: {first_nav.unit_nav}")
    print(f"最新净值: {last_nav.unit_nav}")
    print(f"累计收益率: {total_return:.2f}%")
    print(f"年化收益率: {annual_return:.2f}%")
    print()
    print(f"净值数据点: {len(nav_records)} 个")

db.close()

print()
print("=" * 80)
print("✓ 全部完成！")
print("=" * 80)
