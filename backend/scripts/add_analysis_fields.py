"""
添加分析数据字段到products表
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def add_analysis_fields():
    """添加分析数据字段"""
    
    print("=" * 70)
    print("添加分析数据字段到products表")
    print("=" * 70)
    print()
    
    with engine.connect() as conn:
        try:
            # 添加analysis_data字段（JSON类型）
            print("添加 analysis_data 字段...")
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN analysis_data TEXT
            """))
            print("  ✓ analysis_data 字段添加成功")
            
            # 添加attribution_data字段（JSON类型）
            print("添加 attribution_data 字段...")
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN attribution_data TEXT
            """))
            print("  ✓ attribution_data 字段添加成功")
            
            # 添加last_analysis_update字段
            print("添加 last_analysis_update 字段...")
            conn.execute(text("""
                ALTER TABLE products 
                ADD COLUMN last_analysis_update DATETIME
            """))
            print("  ✓ last_analysis_update 字段添加成功")
            
            conn.commit()
            
            print()
            print("=" * 70)
            print("字段添加完成！")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            print("提示: 如果字段已存在，可以忽略此错误")


if __name__ == "__main__":
    add_analysis_fields()
