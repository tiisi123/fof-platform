"""
补充采集缺失的净值数据
针对已有产品但没有净值数据的情况
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.nav import NavData
from services.huofuniu_api import HuoFuNiuAPI
import time

def parse_date(date_str: str):
    """解析日期"""
    if not date_str:
        return None
    try:
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None
    except:
        return None

def import_fund_nav(api: HuoFuNiuAPI, db: Session, fund_id: str, product_id: int) -> tuple:
    """
    导入基金净值历史
    返回: (成功数量, 错误信息)
    """
    try:
        result = api.get_fund_nav_v2(fund_id)
        
        if result.get("error_code") != 0 and result.get("code") != 0:
            return 0, f"API错误: {result.get('msg', '未知错误')}"
        
        data = result.get("data", {})
        fund_data = data.get("fund", {})
        nav_list = fund_data.get("excess_prices", [])
        
        if not nav_list:
            return 0, "无净值数据"
        
        new_count = 0
        
        for nav_item in nav_list:
            nav_date_str = nav_item.get("pd")
            nav_value = nav_item.get("cn")
            
            if not nav_date_str or not nav_value:
                continue
            
            nav_date = parse_date(nav_date_str)
            if not nav_date:
                continue
            
            # 检查是否已存在
            existing = db.query(NavData).filter(
                NavData.product_id == product_id,
                NavData.nav_date == nav_date
            ).first()
            
            if existing:
                continue
            
            nav = NavData(
                product_id=product_id,
                nav_date=nav_date,
                unit_nav=float(nav_value),
                cumulative_nav=float(nav_value),
            )
            db.add(nav)
            new_count += 1
        
        if new_count > 0:
            db.commit()
        
        return new_count, None
        
    except Exception as e:
        db.rollback()
        return 0, str(e)

def main():
    print("=" * 80)
    print("补充采集缺失的净值数据")
    print("=" * 80)
    
    # 初始化
    api = HuoFuNiuAPI()
    db = SessionLocal()
    
    # 查找没有净值数据的产品
    print("\n正在查找缺失净值数据的产品...")
    
    products_without_nav = db.query(Product).outerjoin(
        NavData, Product.id == NavData.product_id
    ).group_by(Product.id).having(
        func.count(NavData.id) == 0
    ).filter(
        Product.product_code.like("HFN_%")  # 只处理火富牛产品
    ).all()
    
    total = len(products_without_nav)
    
    if total == 0:
        print("✓ 所有产品都有净值数据，无需补充")
        db.close()
        return
    
    print(f"\n找到 {total} 个产品缺失净值数据")
    print("\n开始补充采集...")
    print("-" * 80)
    
    success_count = 0
    failed_products = []
    
    for i, product in enumerate(products_without_nav, 1):
        fund_id = product.product_code.replace("HFN_", "")
        fund_name = product.product_name[:40]
        
        print(f"\r[{i}/{total}] {fund_name:<40}", end='', flush=True)
        
        nav_count, error = import_fund_nav(api, db, fund_id, product.id)
        
        if nav_count > 0:
            success_count += 1
        elif error:
            failed_products.append({
                "id": product.id,
                "name": product.product_name,
                "code": product.product_code,
                "error": error
            })
        
        # 延迟，避免请求过快（增加到3秒避免限流）
        time.sleep(3.0)
        
        # 每30个休息一下（减少批次大小）
        if i % 30 == 0:
            print(f"\n  已处理 {i}/{total}，休息15秒...")
            time.sleep(15)
    
    print("\n\n" + "=" * 80)
    print("补充采集完成")
    print("=" * 80)
    print(f"\n成功补充: {success_count} 个产品")
    print(f"仍然缺失: {len(failed_products)} 个产品")
    
    if failed_products:
        print("\n缺失原因统计:")
        error_stats = {}
        for p in failed_products:
            error = p["error"]
            if error not in error_stats:
                error_stats[error] = 0
            error_stats[error] += 1
        
        for error, count in sorted(error_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error}: {count} 个")
        
        print("\n详细列表（前20个）:")
        for p in failed_products[:20]:
            print(f"  ID {p['id']}: {p['name']}")
            print(f"    原因: {p['error']}")
    
    # 统计最终结果
    total_products = db.query(Product).filter(
        Product.product_code.like("HFN_%")
    ).count()
    
    products_with_nav = db.query(Product.id).join(
        NavData, Product.id == NavData.product_id
    ).filter(
        Product.product_code.like("HFN_%")
    ).distinct().count()
    
    print(f"\n最终统计:")
    print(f"  总产品数: {total_products}")
    print(f"  有净值数据: {products_with_nav} ({products_with_nav/total_products*100:.1f}%)")
    print(f"  无净值数据: {total_products - products_with_nav} ({(total_products - products_with_nav)/total_products*100:.1f}%)")
    
    db.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
