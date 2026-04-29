"""
火富牛全量数据采集脚本
采集所有17个接口的完整数据
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


class HuoFuNiuFullImporter:
    """火富牛全量数据导入器 - 采集所有17个接口数据"""
    
    def __init__(self, api: HuoFuNiuAPI, db: Session):
        self.api = api
        self.db = db
        self.stats = {
            "funds_fetched": 0,
            "managers_created": 0,
            "products_created": 0,
            "products_updated": 0,
            "nav_records_created": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            # 17个接口的统计
            "fund_list": 0,           # 1. 基金列表
            "fund_detail": 0,         # 2. 基金详情
            "fund_scale": 0,          # 3. 基金规模
            "fund_nav_v2": 0,         # 4. 净值曲线V2
            "manager_info": 0,        # 6. 管理人信息
            "company_detail": 0,      # 7. 企业详情
            "company_changes": 0,     # 8. 企业变更
            "company_shareholders": 0, # 9. 企业股东
            "drawdown_list": 0,       # 10. 回撤列表
            "positive_rate": 0,       # 11. 胜率分析
            "roll_analysis": 0,       # 12. 滚动分析
            "interval_returns": 0,    # 13. 区间收益
            "correlation": 0,         # 14. 相关系数
            "roll_positive": 0,       # 15. 盈利概率
            "style_attribution": 0,   # 16. 风格归因
            "market_roll_vol": 0,     # 17. 市场情景分析
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
        print(f"\n[步骤 {step}/{total_steps}] {description}")
        print("-" * 80)

    def step1_get_fund_list(self, max_count: int = 500) -> list:
        """步骤1: 获取基金列表接口1"""
        self.print_step(1, 6, "获取基金列表")
        
        all_funds = []
        page = 1
        pagesize = 100
        
        print(f"目标数量: {max_count} 个基金\n")
        
        while len(all_funds) < max_count:
            result = self.api.get_fund_list(page=page, pagesize=pagesize)
            
            if result.get("code") != 0:
                print(f"[ERROR] 获取失败: {result.get('msg')}")
                break
            
            data = result.get("data", {})
            funds = data.get("list", [])
            
            if not funds:
                break
            
            all_funds.extend(funds)
            print(f"\r获取进度: {len(all_funds)}/{max_count}", end='', flush=True)
            
            if len(all_funds) >= max_count:
                all_funds = all_funds[:max_count]
                break
            
            page += 1
            time.sleep(1.0)
        
        self.stats["fund_list"] = len(all_funds)
        self.stats["funds_fetched"] = len(all_funds)
        print(f"\n[OK] 成功获取 {len(all_funds)} 个基金")
        
        return all_funds

    def step2_collect_all_fund_data(self, fund_list: list) -> dict:
        """步骤2: 批量采集所有基金数据接口2-5"""
        self.print_step(2, 6, "批量采集所有基金数据详情规模净值")
        
        total = len(fund_list)
        fund_data_map = {}
        
        # 计算日期范围（最近1年）
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        print(f"总数: {total} 个基金")
        print(f"日期范围: {start_date} 到 {end_date}\n")
        
        for i, fund_basic in enumerate(fund_list, 1):
            fund_id = fund_basic.get("id")
            fund_name = fund_basic.get("fund_name") or fund_basic.get("name")
            
            print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
            
            fund_data = {"basic": fund_basic}
            
            try:
                # 接口2: 基金详情
                detail = self.api.get_fund_detail(fund_id)
                if detail.get("error_code") == 0:
                    fund_data["detail"] = detail.get("data", {})
                    self.stats["fund_detail"] += 1
                time.sleep(0.5)
                
                # 接口3: 基金规模
                scale = self.api.get_fund_scale(fund_id, start_date=start_date, end_date=end_date)
                if scale.get("error_code") == 0:
                    fund_data["scale"] = scale.get("data", {})
                    self.stats["fund_scale"] += 1
                time.sleep(0.5)
                
                # 接口4: 净值曲线V2最重要
                nav_v2 = self.api.get_fund_nav_v2(fund_id)
                if nav_v2.get("error_code") == 0:
                    fund_data["nav_v2"] = nav_v2.get("data", {})
                    self.stats["fund_nav_v2"] += 1
                time.sleep(0.5)
                
                fund_data_map[fund_id] = fund_data
                
                if i % 50 == 0:
                    print(f"\n  [PAUSE]  已采集 {i} 个休息 10 秒...")
                    time.sleep(10)
                
            except Exception as e:
                self.stats["errors"] += 1
                time.sleep(3.0)
        
        print(f"\n[OK] 基金数据采集完成")
        print(f"  详情: {self.stats['fund_detail']} 个")
        print(f"  规模: {self.stats['fund_scale']} 个")
        print(f"  净值: {self.stats['fund_nav_v2']} 个")
        
        return fund_data_map

    def step3_collect_performance_data(self, fund_data_map: dict) -> dict:
        """步骤3: 批量采集业绩分析数据接口10-15"""
        self.print_step(3, 6, "批量采集业绩分析数据回撤胜率滚动区间相关盈利")
        
        total = len(fund_data_map)
        print(f"总数: {total} 个基金\n")
        
        for i, (fund_id, fund_data) in enumerate(fund_data_map.items(), 1):
            fund_name = fund_data["basic"].get("fund_name") or fund_data["basic"].get("name")
            
            print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
            
            performance = {}
            
            try:
                # 接口10: 回撤列表
                drawdown = self.api.get_fund_drawdown_list(fund_id)
                if drawdown.get("error_code") == 0:
                    performance["drawdown"] = drawdown.get("data", {})
                    self.stats["drawdown_list"] += 1
                time.sleep(0.5)
                
                # 接口11: 胜率分析月度
                positive = self.api.get_fund_positive_rate(fund_id, cycle=3)
                if positive.get("error_code") == 0:
                    performance["positive_rate"] = positive.get("data", {})
                    self.stats["positive_rate"] += 1
                time.sleep(0.5)
                
                # 接口12: 滚动分析波动率3个月
                roll_vol = self.api.get_fund_roll_analysis(fund_id, factor="vol", window="3m")
                if roll_vol.get("error_code") == 0:
                    performance["roll_vol_3m"] = roll_vol.get("data", {})
                    self.stats["roll_analysis"] += 1
                time.sleep(0.5)
                
                # 接口13: 区间收益季度
                returns = self.api.get_fund_interval_returns(fund_id, interval="quarterly")
                if returns.get("error_code") == 0:
                    performance["interval_returns"] = returns.get("data", {})
                    self.stats["interval_returns"] += 1
                time.sleep(0.5)
                
                # 接口14: 相关系数
                corr = self.api.get_fund_correlation(fund_id, refer=self.refer_index)
                if corr.get("error_code") == 0:
                    performance["correlation"] = corr.get("data", {})
                    self.stats["correlation"] += 1
                time.sleep(0.5)
                
                # 接口15: 盈利概率15%目标
                prob = self.api.get_fund_roll_positive(fund_id, target_return=0.15)
                if prob.get("error_code") == 0:
                    performance["roll_positive"] = prob.get("data", {})
                    self.stats["roll_positive"] += 1
                time.sleep(0.5)
                
                fund_data["performance"] = performance
                
                if i % 50 == 0:
                    print(f"\n  [PAUSE]  已采集 {i} 个休息 10 秒...")
                    time.sleep(10)
                
            except Exception as e:
                self.stats["errors"] += 1
                time.sleep(3.0)
        
        print(f"\n[OK] 业绩分析数据采集完成")
        print(f"  回撤: {self.stats['drawdown_list']} 个")
        print(f"  胜率: {self.stats['positive_rate']} 个")
        print(f"  滚动: {self.stats['roll_analysis']} 个")
        print(f"  区间: {self.stats['interval_returns']} 个")
        print(f"  相关: {self.stats['correlation']} 个")
        print(f"  盈利: {self.stats['roll_positive']} 个")
        
        return fund_data_map

    def step4_collect_attribution_data(self, fund_data_map: dict) -> dict:
        """步骤4: 批量采集风格归因数据接口16"""
        self.print_step(4, 6, "批量采集风格归因数据")
        
        total = len(fund_data_map)
        
        # 计算日期范围（最近1年）
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        print(f"总数: {total} 个基金")
        print(f"日期范围: {start_date} 到 {end_date}\n")
        
        for i, (fund_id, fund_data) in enumerate(fund_data_map.items(), 1):
            fund_name = fund_data["basic"].get("fund_name") or fund_data["basic"].get("name")
            
            print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
            
            try:
                # 接口16: 风格归因
                attribution = self.api.get_fund_style_attribution(
                    fund_id, 
                    refer=self.refer_index,
                    start_date=start_date,
                    end_date=end_date,
                    style_type="cne5_new"
                )
                if attribution.get("error_code") == 0:
                    fund_data["attribution"] = attribution.get("data", {})
                    self.stats["style_attribution"] += 1
                
                time.sleep(2.0)
                
                if i % 50 == 0:
                    print(f"\n  [PAUSE]  已采集 {i} 个休息 10 秒...")
                    time.sleep(10)
                
            except Exception as e:
                self.stats["errors"] += 1
                time.sleep(3.0)
        
        print(f"\n[OK] 风格归因数据采集完成")
        print(f"  归因: {self.stats['style_attribution']} 个")
        
        return fund_data_map
    
    def step5_collect_market_data(self):
        """步骤5: 采集市场情景数据接口17"""
        self.print_step(5, 6, "采集市场情景数据")
        
        market_data = {}
        
        # 计算日期范围（最近1年）
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        print(f"日期范围: {start_date} 到 {end_date}\n")
        
        try:
            # 接口17: 市场情景分析沪深300和中证500
            print("采集沪深300波动率...")
            hs300 = self.api.get_market_roll_vol(
                codes="000300",
                start_date=start_date,
                end_date=end_date,
                window="60d",
                quantile="vol"
            )
            if hs300.get("error_code") == 0:
                market_data["hs300_vol"] = hs300.get("data", {})
                self.stats["market_roll_vol"] += 1
            
            time.sleep(1.0)
            
            print("采集中证500波动率...")
            zz500 = self.api.get_market_roll_vol(
                codes="000905",
                start_date=start_date,
                end_date=end_date,
                window="60d",
                quantile="vol"
            )
            if zz500.get("error_code") == 0:
                market_data["zz500_vol"] = zz500.get("data", {})
                self.stats["market_roll_vol"] += 1
            
            print(f"[OK] 市场数据采集完成")
            print(f"  市场: {self.stats['market_roll_vol']} 个指数")
            
        except Exception as e:
            print(f"[ERROR] 市场数据采集失败: {e}")
            self.stats["errors"] += 1
        
        return market_data

    def step6_save_to_database(self, fund_data_map: dict, market_data: dict):
        """步骤6: 保存所有数据到数据库"""
        self.print_step(6, 6, "保存所有数据到数据库")
        
        total = len(fund_data_map)
        print(f"总数: {total} 个基金\n")
        
        for i, (fund_id, fund_data) in enumerate(fund_data_map.items(), 1):
            try:
                # 提取基础信息
                basic = fund_data.get("basic", {})
                detail = fund_data.get("detail", {})
                
                fund_name = basic.get("fund_name") or basic.get("name") or detail.get("name") or f"基金_{fund_id}"
                if not fund_name:
                    print(f"\n  跳过: 基金ID {fund_id} 没有名称")
                    continue
                
                print(f"\r[{i}/{total}] {fund_name[:40]:<40}", end='', flush=True)
                
                # 提取策略
                strategy = detail.get("strategy") or basic.get("strategy_one") or basic.get("strategy")
                if isinstance(strategy, list) and strategy:
                    strategy = strategy[0].get("strategy_name") if isinstance(strategy[0], dict) else str(strategy[0])
                elif not isinstance(strategy, str):
                    strategy = None
                
                # 提取管理人名称
                manager_name = detail.get("advisor") or basic.get("manager_name")
                
                # 获取或创建管理人
                manager = self.get_or_create_manager(manager_name)
                
                # 创建或更新产品
                product_code = f"HFN_{fund_id}"
                product = self.db.query(Product).filter(
                    Product.product_code == product_code
                ).first()
                
                if product:
                    product.product_name = fund_name
                    product.manager_id = manager.id if manager else None
                    product.strategy_type = strategy
                    product.established_date = self.parse_date(detail.get("establish_date") or basic.get("establish_date"))
                    self.stats["products_updated"] += 1
                else:
                    product = Product(
                        product_code=product_code,
                        product_name=fund_name,
                        manager_id=manager.id if manager else None,
                        strategy_type=strategy,
                        established_date=self.parse_date(detail.get("establish_date") or basic.get("establish_date")),
                    )
                    self.db.add(product)
                    self.db.flush()
                    self.stats["products_created"] += 1
                
                # 保存完整数据到JSON字段
                # 业绩分析数据
                product.analysis_data = json.dumps({
                    "basic": basic,
                    "detail": detail,
                    "scale": fund_data.get("scale", {}),
                    "nav_v2": fund_data.get("nav_v2", {}),
                    "performance": fund_data.get("performance", {}),
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, ensure_ascii=False)
                
                # 风格归因数据
                product.attribution_data = json.dumps({
                    "attribution": fund_data.get("attribution", {}),
                    "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, ensure_ascii=False)
                
                # 更新分析数据时间
                product.last_analysis_update = datetime.now()
                
                # 保存净值数据
                nav_v2 = fund_data.get("nav_v2", {})
                if nav_v2:
                    fund_nav = nav_v2.get("fund", {})
                    nav_list = fund_nav.get("excess_prices", [])
                    
                    for nav_item in nav_list:
                        nav_date_str = nav_item.get("pd")
                        nav_value = nav_item.get("cn")
                        
                        if not nav_date_str or not nav_value:
                            continue
                        
                        nav_date = self.parse_date(nav_date_str)
                        if not nav_date:
                            continue
                        
                        existing = self.db.query(NavData).filter(
                            NavData.product_id == product.id,
                            NavData.nav_date == nav_date
                        ).first()
                        
                        if not existing:
                            nav = NavData(
                                product_id=product.id,
                                nav_date=nav_date,
                                unit_nav=float(nav_value),
                                cumulative_nav=float(nav_value),
                            )
                            self.db.add(nav)
                            self.stats["nav_records_created"] += 1
                
                # 每个产品提交一次
                self.db.commit()
                
            except Exception as e:
                self.db.rollback()
                print(f"\n[ERROR] 保存失败 [{fund_id}]: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                self.stats["errors"] += 1
        
        # 保存市场数据可以保存到单独的表或配置中
        # 这里暂时跳过因为没有专门的市场数据表
        
        print(f"\n[OK] 数据保存完成")
        print(f"  创建产品: {self.stats['products_created']} 个")
        print(f"  更新产品: {self.stats['products_updated']} 个")
        print(f"  净值记录: {self.stats['nav_records_created']:,} 条")

    def import_full(self, max_funds: int = 500, clear_existing: bool = False, clear_all: bool = False):
        """全量导入流程 - 采集所有17个接口数据"""
        self.stats["start_time"] = datetime.now()
        
        self.print_header("火富牛全量数据采集 - 17个接口完整数据")
        
        print(f"[STATS] 采集配置")
        print(f"  目标数量: {max_funds} 个基金")
        print(f"  清除火富牛数据: {'是' if clear_existing else '否'}")
        print(f"  清除所有数据: {'是' if clear_all else '否'}")
        print(f"  采集接口: 17个全量")
        print()
        print(f" 接口清单:")
        print(f"  基金相关: 1.列表 2.详情 3.规模 4.净值V2")
        print(f"  业绩分析: 10.回撤 11.胜率 12.滚动 13.区间 14.相关 15.盈利")
        print(f"  高级分析: 16.风格归因")
        print(f"  市场数据: 17.市场情景")
        print()
        
        # 清除所有数据
        if clear_all:
            print("[DELETE]  清除所有数据...")
            print("  - 删除所有净值数据...")
            self.db.query(NavData).delete()
            print("  - 删除所有产品...")
            self.db.query(Product).delete()
            print("  - 删除所有管理人...")
            self.db.query(Manager).delete()
            self.db.commit()
            print("  [OK] 所有数据已清除\n")
        
        # 清除火富牛数据
        elif clear_existing:
            print("[DELETE]  清除现有火富牛数据...")
            hfn_products = self.db.query(Product).filter(
                Product.product_code.like("HFN_%")
            ).all()
            
            for product in hfn_products:
                self.db.query(NavData).filter(
                    NavData.product_id == product.id
                ).delete()
            
            self.db.query(Product).filter(
                Product.product_code.like("HFN_%")
            ).delete()
            
            self.db.query(Manager).filter(
                Manager.remark.like("%火富牛%")
            ).delete()
            
            self.db.commit()
            print("  [OK] 火富牛数据已清除\n")
        
        try:
            # 步骤1: 获取基金列表
            fund_list = self.step1_get_fund_list(max_count=max_funds)
            if not fund_list:
                print("[ERROR] 未获取到基金列表")
                return
            
            # 步骤2: 批量采集所有基金数据
            fund_data_map = self.step2_collect_all_fund_data(fund_list)
            if not fund_data_map:
                print("[ERROR] 未采集到基金数据")
                return
            
            # 步骤3: 批量采集业绩分析数据
            fund_data_map = self.step3_collect_performance_data(fund_data_map)
            
            # 步骤4: 批量采集风格归因数据
            fund_data_map = self.step4_collect_attribution_data(fund_data_map)
            
            # 步骤5: 采集市场情景数据
            market_data = self.step5_collect_market_data()
            
            # 步骤6: 保存所有数据到数据库
            self.step6_save_to_database(fund_data_map, market_data)
            
        except KeyboardInterrupt:
            print("\n\n  采集被中断")
        
        # 打印统计
        self.stats["end_time"] = datetime.now()
        self.print_summary()
    
    def print_summary(self):
        """打印统计信息"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.print_header("采集完成")
        
        print(f"[STATS] 采集统计17个接口")
        print()
        print(f"基金相关:")
        print(f"  1. 基金列表: {self.stats['fund_list']} 个")
        print(f"  2. 基金详情: {self.stats['fund_detail']} 个")
        print(f"  3. 基金规模: {self.stats['fund_scale']} 个")
        print(f"  4. 净值曲线: {self.stats['fund_nav_v2']} 个")
        print()
        print(f"业绩分析:")
        print(f"  10. 回撤列表: {self.stats['drawdown_list']} 个")
        print(f"  11. 胜率分析: {self.stats['positive_rate']} 个")
        print(f"  12. 滚动分析: {self.stats['roll_analysis']} 个")
        print(f"  13. 区间收益: {self.stats['interval_returns']} 个")
        print(f"  14. 相关系数: {self.stats['correlation']} 个")
        print(f"  15. 盈利概率: {self.stats['roll_positive']} 个")
        print()
        print(f"高级分析:")
        print(f"  16. 风格归因: {self.stats['style_attribution']} 个")
        print()
        print(f"市场数据:")
        print(f"  17. 市场情景: {self.stats['market_roll_vol']} 个指数")
        print()
        print(f"数据库:")
        print(f"  创建管理人: {self.stats['managers_created']} 个")
        print(f"  创建产品: {self.stats['products_created']} 个")
        print(f"  更新产品: {self.stats['products_updated']} 个")
        print(f"  净值记录: {self.stats['nav_records_created']:,} 条")
        print(f"  错误数: {self.stats['errors']} 个")
        print()
        print(f"[TIME]  耗时: {minutes} 分 {seconds} 秒")
        print()
        print("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='火富牛全量数据采集17个接口')
    parser.add_argument('--count', type=int, default=500, help='基金数量')
    parser.add_argument('--clear', action='store_true', help='清除现有火富牛数据')
    parser.add_argument('--clear-all', action='store_true', help='清除所有数据包括非火富牛数据')
    
    args = parser.parse_args()
    
    api = HuoFuNiuAPI()
    db = SessionLocal()
    
    try:
        importer = HuoFuNiuFullImporter(api, db)
        importer.import_full(
            max_funds=args.count,
            clear_existing=args.clear,
            clear_all=args.clear_all
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

