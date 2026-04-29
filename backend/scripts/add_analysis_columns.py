"""
为products表添加分析数据相关列
"""
import sys
import os

# 确保可以导入 backend 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text

# 数据库连接：始终指向 backend/fof.db，而不是当前工作目录
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BACKEND_DIR, "fof.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL)

print("=" * 60)
print("为products表添加分析数据列")
print("=" * 60)

# 要添加的列
columns_to_add = [
    ("analysis_data", "TEXT", "分析数据（回撤、胜率、滚动分析等）JSON格式"),
    ("attribution_data", "TEXT", "风格归因数据JSON格式"),
    ("last_analysis_update", "DATETIME", "分析数据最后更新时间"),
]

with engine.connect() as conn:
    # 检查表结构
    result = conn.execute(text("PRAGMA table_info(products)"))
    existing_columns = {row[1] for row in result}
    
    print(f"\n现有列数: {len(existing_columns)}")
    
    # 添加缺失的列
    for col_name, col_type, comment in columns_to_add:
        if col_name not in existing_columns:
            try:
                sql = f"ALTER TABLE products ADD COLUMN {col_name} {col_type}"
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 已添加列: {col_name} ({comment})")
            except Exception as e:
                print(f"❌ 添加列 {col_name} 失败: {e}")
        else:
            print(f"⏭️  列已存在: {col_name}")

print("\n" + "=" * 60)
print("列添加完成")
print("=" * 60)
