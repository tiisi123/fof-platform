"""
火富牛完整数据采集脚本
采集所有数据：基础数据 + 分析数据 + 风格归因
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.manager import Manager
from app.models.product import Product
from app.models.nav import NavData
from services.huofuniu_api import HuoFuNiuAPI
import time
import json


class ProgressBar:
    """进度条显示"""
    
    @staticmethod
    def show(current, total, prefix='', suffix='', length=50):
        """显示进度条"""
        percent = 100 * (current / float(total))
        filled = int(length * current // total)
        bar = '█' * filled + '-' * (length - filled)
        print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix}', end='', flush=True)
        if current == total:
            print()


class HuoFuNiuCompleteImporter:
    """火富牛完整数据导入器"""
    
    def __init__(self, api: HuoFuNiuAPI, db: Session):
        self.api = api
        self.db = db
        self.stats = {
            "funds_fetched": 0,
            "managers_created": 0,
            "products_created": 0,
            "products_updated": 0,
            "nav_records_created": 0,
            "analysis_collected": 0,
            "attribution_collected": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }
        self.manager_cache = {}
        self.refer_index = "ca6de5b04aa45f192202420cff2e9599"  # 沪深300
    
    @staticmethod
    def parse_date(date_str: str) -> date:
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
    
    def generate_manager_code(self, manager_name: str) -> str:
        """生成管理人编号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        name_prefix = manager_name[:3] if len(manager_name) >= 3 else manager_name
        return f"HFN_{name_prefix}_{timestamp}"
    
    def get_or_create_manager(self, manager_name: str) -> Manager:
        """获取或创建管理人"""
        if not manager_name or manager_name == "未知":
            return None
        
        if manager_name in self.manager_cache:
            return self.manager_cache[manager_name]
        
        manager = self.db.query(Manager).filter(
            Manager.manager_name == manager_name
        ).first()
        
        if not manager:
            manager_code = self.generate_manager_code(manager_name)
            manager = Manager(
                manager_code=manager_code,
                manager_name=manager_name,
                remark=f"火富牛导入 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.db.add(manager)
            self.db.flush()
            self.stats["managers_created"] += 1
        
        self.manager_cache[manager_name] = manager
        return manager
    
    def print_header(self, title):
        """打印标题"""
        print()
        print("=" * 80)
        print(f"  {title}")
        print("=" * 80)
        print()
    
    def print_step(self, step, total_steps, description):
        """打印步骤"""
        print(f"[步骤 {step}/{total_steps}] {description}")
        print("-" * 80)
    
    def import_fund_list(self, max_count: int = 500, delay: float = 1.0) -> list:
        """步骤1: 获取基金列表"""
        self.print_step(1, 3, "获取基金列表")
        
        all_funds = []
        page = 1
        pagesize = 100
        
        print(f"目标数量: {max_count} 个基金")
        print()
        
        while len(all_funds) < max_count:
            result = self.api.get_fund_list(page=page, pagesize=pagesize)
            
            if result.get("code") != 0:
                print(f"\n❌ 获取失败: {result.get('msg')}")
                break
            
            data = result.get("data", {})
            funds = data.get("list", [])
            
            if not funds:
                print("\n✓ 没有更多数据")
                break
            
            all_funds.extend(funds)
            
            current = min(len(all_funds), max_count)
            ProgressBar.show(current, max_count, 
                           prefix='获取进度', 
                           suffix=f'{current}/{max_count} 个基金')
            
            if len(all_funds) >= max_count:
                all_funds = all_funds[:max_count]
                break
            
            page += 1
            time.sleep(delay)
        
        self.stats["funds_fetched"] = len(all_funds)
        print(f"\n✓ 成功获取 {len(all_funds)} 个基金")
        print()
        
        return all_funds
    
    def import_fund_detail(self, fund_id: str, fund_basic: dict) -> dict:
        """获取基金详情"""
        result = self.api.get_fund_detail(fund_id)
        
        if result.get("code") != 0 and result.get("error_code") != 0:
            return None
        
        data = result.get("data", {})
        
        strategy = data.get("strategy") or fund_basic.get("strategy_one") or fund_basic.get("strategy")
        if isinstance(strategy, list) and strategy:
            strategy = strategy[0].get("strategy_name") if isinstance(strategy[0], dict) else str(strategy[0])
        elif not isinstance(strategy, str):
            strategy = None
        
        fund_info = {
            "fund_id": fund_id,
            "name": fund_basic.get("fund_name") or fund_basic.get("name") or data.get("name"),
            "manager_name": data.get("advisor") or fund_basic.get("manager_name"),
            "strategy": strategy,
            "establish_date": data.get("establish_date") or fund_basic.get("establish_date"),
            "nav": fund_basic.get("price_nav") or fund_basic.get("nav"),
            "nav_date": fund_basic.get("price_date"),
            "fund_manager": data.get("managers", [{}])[0].get("name") if data.get("managers") else None,
            "custodian": data.get("custodian"),
            "scale": data.get("scale"),
            "min_investment": data.get("min_investment"),
        }
        
        return fund_info
    
    def import_fund_nav(self, fund_id: str, product_id: int) -> int:
        """导入基金净值历史"""
        result = self.api.get_fund_nav_v2(fund_id)
        
        if result.get("error_code") != 0 and result.get("code") != 0:
            return 0
        
        data = result.get("data", {})
        fund_data = data.get("fund", {})
        nav_list = fund_data.get("excess_prices", [])
        
        if not nav_list:
            return 0
        
        new_count = 0
        
        for nav_item in nav_list:
            nav_date_str = nav_item.get("pd")
            nav_value = nav_item.get("cn")
            
            if not nav_date_str or not nav_value:
                continue
            
            nav_date = self.parse_date(nav_date_str)
            if not nav_date:
                continue
            
            existing = self.db.query(NavData).filter(
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
            self.db.add(nav)
            new_count += 1
        
        return new_count
    
    def collect_analysis_data(self, fund_id: str) -> dict:
        """采集分析数据"""
        analysis_data = {}
        
        try:
            # 1. 回撤分析
            drawdown = self.api.get_fund_drawdown_list(fund_id)
            if drawdown.get("error_code") == 0:
                analysis_data["drawdown"] = drawdown.get("data", {})
            
            time.sleep(0.5)
            
            # 2. 胜率分析（月度）
            positive = self.api.get_fund_positive_rate(fund_id, cycle=3)
            if positive.get("error_code") == 0:
                analysis_data["positive_rate"] = positive.get("data", {})
            
            time.sleep(0.5)
            
            # 3. 滚动分析（3个月波动率）
            roll_vol = self.api.get_fund_roll_analysis(fund_id, factor="vol", window="3m")
            if roll_vol.get("error_code") == 0:
                analysis_data["roll_vol_3m"] = roll_vol.get("data", {})
            
            time.sleep(0.5)
            
            # 4. 区间收益（季度）
            returns = self.api.get_fund_interval_returns(fund_id, interval="quarterly")
            if returns.get("error_code") == 0:
                analysis_data["interval_returns"] = returns.get("data", {})
            
            time.sleep(0.5)
            
            # 5. 相关系数
            corr = self.api.get_fund_correlation(fund_id, refer=self.refer_index)
            if corr.get("error_code") == 0:
                analysis_data["correlation"] = corr.get("data", {})
            
            time.sleep(0.5)
            
            # 6. 盈利概率（15%目标收益）
            prob = self.api.get_fund_roll_positive(fund_id, target_return=0.15)
            if prob.get("error_code") == 0:
                analysis_data["roll_positive"] = prob.get("data", {})
            
            time.sleep(0.5)
            
            # 添加更新时间
            analysis_data["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return analysis_data
            
        except Exception as e:
            print(f"\n  ⚠️  分析数据采集失败: {e}")
            return {}
    
    def collect_attribution_data(self, fund_id: str) -> dict:
        """采集风格归因数据"""
        try:
            attribution = self.api.get_fund_style_attribution(
                fund_id, 
                refer=self.refer_index,
                style_type="cne5_new"
            )
            
            if attribution.get("error_code") == 0:
                data = attribution.get("data", {})
                data["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return data
            
            return {}
            
        except Exception as e:
            print(f"\n  ⚠️  风格归因采集失败: {e}")
            return {}
    
    def import_all_details(
        self,
        fund_list: list,
        detail_delay: float = 1.5
    ) -> dict:
        """步骤2A: 批量获取所有详情"""
        self.print_step(2, 4, "批量获取所有详情")
        
        total = len(fund_list)
        print(f"总数: {total} 个基金")
        print(f"延迟: {detail_delay} 秒/个")
        print()
        
        fund_details = {}
        error_count = 0
        
        for i, fund_basic in enumerate(fund_list, 1):
            fund_id = fund_basic.get("id")
            fund_name = fund_basic.get("fund_name") or fund_basic.get("name")
            
            try:
                print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
                
                fund_info = self.import_fund_detail(fund_id, fund_basic)
                
                if fund_info:
                    fund_details[fund_id] = fund_info
                else:
                    error_count += 1
                
                time.sleep(detail_delay)
                
                if i % 50 == 0:
                    print(f"\n  ⏸️  已获取 {i} 个详情，休息 10 秒...")
                    time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  用户中断")
                raise
            except Exception as e:
                error_count += 1
                time.sleep(3.0)
        
        print(f"\n\n✓ 详情获取完成")
        print(f"  成功: {len(fund_details)} 个")
        print(f"  失败: {error_count} 个")
        print()
        
        return fund_details
    
    def import_all_products(
        self,
        fund_details: dict
    ):
        """步骤2B: 批量创建所有产品"""
        self.print_step(3, 4, "批量创建所有产品")
        
        total = len(fund_details)
        print(f"总数: {total} 个产品")
        print()
        
        products_map = {}  # fund_id -> product
        
        for i, (fund_id, fund_info) in enumerate(fund_details.items(), 1):
            fund_name = fund_info.get("name")
            
            try:
                print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
                
                # 获取或创建管理人
                manager = self.get_or_create_manager(fund_info.get("manager_name"))
                
                # 检查产品是否已存在
                product_code = f"HFN_{fund_id}"
                product = self.db.query(Product).filter(
                    Product.product_code == product_code
                ).first()
                
                if product:
                    product.product_name = fund_info.get("name")
                    product.manager_id = manager.id if manager else None
                    product.strategy_type = fund_info.get("strategy")
                    product.established_date = self.parse_date(fund_info.get("establish_date"))
                    product.remark = f"火富牛 - ID: {fund_id}"
                    self.stats["products_updated"] += 1
                else:
                    product = Product(
                        product_code=product_code,
                        product_name=fund_info.get("name"),
                        manager_id=manager.id if manager else None,
                        strategy_type=fund_info.get("strategy"),
                        established_date=self.parse_date(fund_info.get("establish_date")),
                        remark=f"火富牛 - ID: {fund_id}"
                    )
                    self.db.add(product)
                    self.db.flush()
                    self.stats["products_created"] += 1
                
                products_map[fund_id] = product
                
            except Exception as e:
                print(f"\n  ❌ 创建产品失败: {e}")
                continue
        
        # 批量提交
        self.db.commit()
        
        print(f"\n\n✓ 产品创建完成")
        print(f"  创建: {self.stats['products_created']} 个")
        print(f"  更新: {self.stats['products_updated']} 个")
        print()
        
        return products_map
    
    def import_all_navs(
        self,
        products_map: dict,
        nav_delay: float = 1.5
    ):
        """步骤2C: 批量获取所有净值"""
        self.print_step(4, 4, "批量获取所有净值")
        
        total = len(products_map)
        print(f"总数: {total} 个产品")
        print(f"延迟: {nav_delay} 秒/个")
        print()
        
        error_count = 0
        
        for i, (fund_id, product) in enumerate(products_map.items(), 1):
            fund_name = product.product_name
            
            try:
                print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
                
                nav_count = self.import_fund_nav(fund_id, product.id)
                self.stats["nav_records_created"] += nav_count
                
                # 每个产品提交一次
                self.db.commit()
                
                time.sleep(nav_delay)
                
                if i % 50 == 0:
                    print(f"\n  ⏸️  已获取 {i} 个净值，休息 10 秒...")
                    time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  用户中断，保存当前进度...")
                self.db.commit()
                raise
            except Exception as e:
                self.db.rollback()
                error_count += 1
                time.sleep(3.0)
        
        print(f"\n\n✓ 净值获取完成")
        print(f"  成功: {total - error_count} 个")
        print(f"  失败: {error_count} 个")
        print(f"  净值总数: {self.stats['nav_records_created']:,} 条")
        print()
    
    def import_analysis_data(
        self,
        analysis_delay: float = 4.0
    ):
        """步骤5: 导入分析数据"""
        self.print_step(5, 5, "导入分析数据（回撤、胜率、风格归因等）")
        
        # 获取所有火富牛产品
        products = self.db.query(Product).filter(
            Product.product_code.like("HFN_%")
        ).all()
        
        total = len(products)
        print(f"总数: {total} 个基金")
        print(f"延迟: {analysis_delay} 秒/个（7个接口）")
        print()
        
        success_count = 0
        error_count = 0
        
        for i, product in enumerate(products, 1):
            fund_id = product.product_code.replace("HFN_", "")
            fund_name = product.product_name
            
            try:
                print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
                
                # 采集分析数据
                analysis_data = self.collect_analysis_data(fund_id)
                
                # 采集风格归因数据
                attribution_data = self.collect_attribution_data(fund_id)
                
                # 更新产品
                if analysis_data:
                    product.analysis_data = json.dumps(analysis_data, ensure_ascii=False)
                    self.stats["analysis_collected"] += 1
                
                if attribution_data:
                    product.attribution_data = json.dumps(attribution_data, ensure_ascii=False)
                    self.stats["attribution_collected"] += 1
                
                if analysis_data or attribution_data:
                    product.last_analysis_update = datetime.now()
                
                self.db.commit()
                success_count += 1
                
                time.sleep(analysis_delay)
                
                if i % 50 == 0:
                    print(f"\n  ⏸️  已处理 {i} 个基金，休息 10 秒...")
                    time.sleep(10)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  用户中断，保存当前进度...")
                self.db.commit()
                raise
            except Exception as e:
                self.db.rollback()
                error_count += 1
                time.sleep(3.0)
        
        print(f"\n\n✓ 分析数据导入完成")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {error_count} 个")
        print()
    
    def import_complete(
        self, 
        max_funds: int = 500,
        list_delay: float = 1.0,
        detail_delay: float = 1.5,
        analysis_delay: float = 4.0,
        clear_existing: bool = False,
        skip_analysis: bool = False
    ):
        """完整导入流程"""
        self.stats["start_time"] = datetime.now()
        
        self.print_header("火富牛完整数据采集")
        
        print(f"📊 采集配置")
        print(f"  目标数量: {max_funds} 个基金")
        print(f"  列表延迟: {list_delay} 秒")
        print(f"  详情延迟: {detail_delay} 秒")
        print(f"  分析延迟: {analysis_delay} 秒")
        print(f"  清除旧数据: {'是' if clear_existing else '否'}")
        print(f"  跳过分析数据: {'是' if skip_analysis else '否'}")
        print()
        
        # 清除现有数据
        if clear_existing:
            print("🗑️  清除现有火富牛数据...")
            hfn_products = self.db.query(Product).filter(
                Product.remark.like("%火富牛%")
            ).all()
            
            for product in hfn_products:
                self.db.query(NavData).filter(
                    NavData.product_id == product.id
                ).delete()
            
            self.db.query(Product).filter(
                Product.remark.like("%火富牛%")
            ).delete()
            
            self.db.query(Manager).filter(
                Manager.remark.like("%火富牛%")
            ).delete()
            
            self.db.commit()
            print("  ✓ 清除完成")
            print()
        
        try:
            # 步骤1: 获取基金列表
            fund_list = self.import_fund_list(max_count=max_funds, delay=list_delay)
            
            if not fund_list:
                print("❌ 未获取到基金列表")
                return
            
            # 步骤2: 批量获取所有详情
            fund_details = self.import_all_details(fund_list, detail_delay=detail_delay)
            
            if not fund_details:
                print("❌ 未获取到详情数据")
                return
            
            # 步骤3: 批量创建所有产品
            products_map = self.import_all_products(fund_details)
            
            if not products_map:
                print("❌ 未创建产品")
                return
            
            # 步骤4: 批量获取所有净值
            self.import_all_navs(products_map, nav_delay=detail_delay)
            
            # 步骤5: 导入分析数据
            if not skip_analysis:
                self.import_analysis_data(analysis_delay=analysis_delay)
            else:
                print("⏭️  跳过分析数据采集")
                print()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  采集被中断")
        
        # 打印统计
        self.stats["end_time"] = datetime.now()
        self.print_summary()
    
    def print_summary(self):
        """打印统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.print_header("采集完成")
        
        print(f"📊 采集统计")
        print(f"  获取基金: {self.stats['funds_fetched']} 个")
        print(f"  创建管理人: {self.stats['managers_created']} 个")
        print(f"  创建产品: {self.stats['products_created']} 个")
        print(f"  更新产品: {self.stats['products_updated']} 个")
        print(f"  导入净值: {self.stats['nav_records_created']:,} 条")
        print(f"  采集分析数据: {self.stats['analysis_collected']} 个")
        print(f"  采集风格归因: {self.stats['attribution_collected']} 个")
        print(f"  错误数: {self.stats['errors']} 个")
        print()
        print(f"⏱️  耗时: {minutes} 分 {seconds} 秒")
        print()
        print("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='火富牛完整数据采集')
    parser.add_argument('--count', type=int, default=500, help='基金数量')
    parser.add_argument('--list-delay', type=float, default=1.0, help='列表请求延迟（秒）')
    parser.add_argument('--detail-delay', type=float, default=1.5, help='详情请求延迟（秒）')
    parser.add_argument('--analysis-delay', type=float, default=4.0, help='分析请求延迟（秒）')
    parser.add_argument('--clear', action='store_true', help='清除现有火富牛数据')
    parser.add_argument('--skip-analysis', action='store_true', help='跳过分析数据采集')
    
    args = parser.parse_args()
    
    api = HuoFuNiuAPI()
    db = SessionLocal()
    
    try:
        importer = HuoFuNiuCompleteImporter(api, db)
        importer.import_complete(
            max_funds=args.count,
            list_delay=args.list_delay,
            detail_delay=args.detail_delay,
            analysis_delay=args.analysis_delay,
            clear_existing=args.clear,
            skip_analysis=args.skip_analysis
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
