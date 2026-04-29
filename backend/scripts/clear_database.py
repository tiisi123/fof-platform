"""
清理数据库脚本
清空所有管理人、产品、净值数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.manager import Manager
from app.models.product import Product
from app.models.nav import NavData


def clear_database():
    """清空数据库"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("清理数据库")
        print("=" * 60)
        print()
        
        # 统计当前数据
        nav_count = db.query(NavData).count()
        product_count = db.query(Product).count()
        manager_count = db.query(Manager).count()
        
        print(f"当前数据:")
        print(f"  管理人: {manager_count} 个")
        print(f"  产品: {product_count} 个")
        print(f"  净值: {nav_count:,} 条")
        print()
        
        # 确认
        confirm = input("确认清空所有数据？(输入 YES 确认): ")
        
        if confirm != "YES":
            print("\n操作已取消")
            return
        
        print()
        print("开始清理...")
        
        # 删除净值数据
        print("  删除净值数据...")
        db.query(NavData).delete()
        
        # 删除产品
        print("  删除产品...")
        db.query(Product).delete()
        
        # 删除管理人
        print("  删除管理人...")
        db.query(Manager).delete()
        
        # 提交
        db.commit()
        
        print()
        print("=" * 60)
        print("✓ 数据库已清空")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 清理失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()
