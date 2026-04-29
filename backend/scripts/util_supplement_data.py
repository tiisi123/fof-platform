"""
补充采集漏掉的接口数据
- get_fund_correlation - 相关性分析
- get_fund_roll_positive - 滚动胜率
- get_fund_interval_returns - 区间收益（另一版本）
- get_manager_info - 管理人信息
- get_company_changes - 公司变更记录
- get_company_shareholders - 公司股东信息
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.manager import Manager
from app.models.fund_performance import FundPerformance, FundExtendedInfo
from services.huofuniu_api import HuoFuNiuAPI
import time
import json


class SupplementCollector:
    """补充数据采集器"""

    def __init__(self, api: HuoFuNiuAPI, db: Session):
        self.api = api
        self.db = db
        self.stats = {
            "processed": 0,
            "correlation": 0,
            "roll_positive": 0,
            "interval_returns": 0,
            "manager_info": 0,
            "company_changes": 0,
            "company_shareholders": 0,
            "errors": 0,
        }

    def collect_correlation(self, fund_id, refer="000300"):
        """获取相关性分析（默认对比沪深300）"""
        result = self.api.get_fund_correlation(fund_id, refer=refer)
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def collect_roll_positive(self, fund_id, target_return=0.0):
        """获取滚动胜率（默认目标收益率0%）"""
        result = self.api.get_fund_roll_positive(fund_id, target_return=target_return)
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def collect_interval_returns(self, fund_id):
        """获取区间收益（另一版本）"""
        result = self.api.get_fund_interval_returns(fund_id, interval="month")
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def collect_manager_info(self, manager_id):
        """获取管理人信息"""
        if not manager_id:
            return None
        result = self.api.get_manager_info(manager_id)
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def collect_company_changes(self, company_id):
        """获取公司变更记录"""
        if not company_id:
            return None
        result = self.api.get_company_changes(company_id, pagesize=50)
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def collect_company_shareholders(self, company_id):
        """获取公司股东信息"""
        if not company_id:
            return None
        result = self.api.get_company_shareholders(company_id, pagesize=50)
        if result.get("error_code") == 0 or result.get("code") == 0:
            return result.get("data", {})
        return None

    def process_one_product(self, i, total, product, delay):
        """处理单个产品"""
        print(f"\n[{i}/{total}] {product.product_name[:40]}")

        # 获取火富牛 ID
        ext_info = self.db.query(FundExtendedInfo).filter(
            FundExtendedInfo.product_id == product.id
        ).first()

        if not ext_info or not ext_info.hfn_fund_id:
            print("  -> 无火富牛ID，跳过")
            return

        fund_id = ext_info.hfn_fund_id
        company_id = ext_info.hfn_company_id

        # 获取现有业绩记录
        perf = self.db.query(FundPerformance).filter(
            FundPerformance.product_id == product.id
        ).first()

        if not perf:
            print("  -> 无业绩记录，跳过")
            return

        # 获取现有 raw_data
        raw_data = perf.raw_data or {}

        # 1) 相关性分析
        if "correlation" not in raw_data:
            corr_data = self.collect_correlation(fund_id)
            if corr_data:
                raw_data["correlation"] = corr_data
                self.stats["correlation"] += 1
            time.sleep(delay)

        # 2) 滚动胜率
        if "roll_positive" not in raw_data:
            roll_pos_data = self.collect_roll_positive(fund_id)
            if roll_pos_data:
                raw_data["roll_positive"] = roll_pos_data
                self.stats["roll_positive"] += 1
            time.sleep(delay)

        # 3) 区间收益（另一版本）
        if "interval_returns" not in raw_data:
            interval_data = self.collect_interval_returns(fund_id)
            if interval_data:
                raw_data["interval_returns"] = interval_data
                self.stats["interval_returns"] += 1
            time.sleep(delay)

        # 4) 管理人信息
        manager_id = None
        if raw_data.get("detail"):
            manager_id = raw_data["detail"].get("advisor_id")

        if manager_id and "manager_info" not in raw_data:
            mgr_data = self.collect_manager_info(manager_id)
            if mgr_data:
                raw_data["manager_info"] = mgr_data
                self.stats["manager_info"] += 1
            time.sleep(delay)

        # 5) 公司变更记录 - 从 detail 中获取 company_id
        detail_company_id = None
        if raw_data.get("detail"):
            detail_company_id = raw_data["detail"].get("company_id")

        if detail_company_id and "company_changes" not in raw_data:
            changes_data = self.collect_company_changes(detail_company_id)
            if changes_data:
                raw_data["company_changes"] = changes_data
                self.stats["company_changes"] += 1
            time.sleep(delay)

        # 6) 公司股东信息
        if detail_company_id and "company_shareholders" not in raw_data:
            shareholders_data = self.collect_company_shareholders(detail_company_id)
            if shareholders_data:
                raw_data["company_shareholders"] = shareholders_data
                self.stats["company_shareholders"] += 1
            time.sleep(delay)

        # 更新数据库
        perf.raw_data = raw_data
        self.db.commit()
        self.stats["processed"] += 1

        print(f"  [OK] corr:{1 if 'correlation' in raw_data else 0} "
              f"roll_pos:{1 if 'roll_positive' in raw_data else 0} "
              f"interval:{1 if 'interval_returns' in raw_data else 0} "
              f"mgr:{1 if 'manager_info' in raw_data else 0} "
              f"changes:{1 if 'company_changes' in raw_data else 0} "
              f"shareholders:{1 if 'company_shareholders' in raw_data else 0}")

    def run(self, delay=0.5):
        """运行补充采集"""
        print("=" * 70)
        print("补充数据采集")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 获取所有产品
        products = self.db.query(Product).filter(
            Product.product_code.like("HFN_%")
        ).all()

        total = len(products)
        print(f"\n共 {total} 个产品需要补充数据\n")

        start_time = datetime.now()

        for i, product in enumerate(products, 1):
            try:
                self.process_one_product(i, total, product, delay)
            except Exception as e:
                print(f"  [ERR] {e}")
                self.stats["errors"] += 1
                self.db.rollback()

            # 每10个产品提交一次
            if i % 10 == 0:
                self.db.commit()
                print(f"\n  === 已处理 {i}/{total}，进度 {i*100//total}% ===\n")

        # 最终提交
        self.db.commit()

        # 统计
        elapsed = datetime.now() - start_time
        print("\n" + "=" * 70)
        print("补充采集完成！")
        print("=" * 70)
        print(f"耗时: {elapsed}")
        print(f"处理产品: {self.stats['processed']}")
        print(f"相关性分析: {self.stats['correlation']}")
        print(f"滚动胜率: {self.stats['roll_positive']}")
        print(f"区间收益: {self.stats['interval_returns']}")
        print(f"管理人信息: {self.stats['manager_info']}")
        print(f"公司变更: {self.stats['company_changes']}")
        print(f"公司股东: {self.stats['company_shareholders']}")
        print(f"错误数: {self.stats['errors']}")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='补充采集漏掉的接口数据')
    parser.add_argument('--delay', type=float, default=0.5, help='请求延迟秒数')

    args = parser.parse_args()

    api = HuoFuNiuAPI()
    db = SessionLocal()

    try:
        collector = SupplementCollector(api, db)
        collector.run(delay=args.delay)
    finally:
        db.close()


if __name__ == "__main__":
    main()
