"""
FOF管理平台 - 数据初始化脚本
生成所有模块的示例数据，覆盖完整业务场景。

使用方法: 在 backend/ 目录下运行
    python seed_data.py
"""
import sys
import os
import random
import numpy as np
from datetime import date, datetime, timedelta
from decimal import Decimal

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.manager import (
    Manager, ManagerContact, ManagerTeam, PoolTransfer, ManagerTag
)
from app.models.product import Product
from app.models.nav import NavData
from app.models.portfolio import (
    Portfolio, PortfolioComponent, PortfolioHolding, PortfolioNav, PortfolioAdjustment
)
from app.models.project import Project, ProjectFollowUp, ProjectStageChange
from app.models.project_cashflow import ProjectCashflow
from app.models.task import Task
from app.models.calendar_event import CalendarEvent
from app.models.comment import Comment
from app.models.news_article import NewsArticle
from app.models.due_diligence import DueDiligenceFlow
from app.models.ai_report import AIReport
from app.models.holdings_detail import HoldingsDetail

random.seed(42)
np.random.seed(42)


def generate_nav_series(
    start_date: date,
    end_date: date,
    annual_return: float = 0.10,
    annual_vol: float = 0.15,
    start_nav: float = 1.0,
    freq_days: int = 1,
) -> list:
    """生成模拟净值序列（几何布朗运动）
    返回 [(date, unit_nav, cumulative_nav), ...]
    freq_days=1 为日频，7为周频
    """
    dt = freq_days / 252
    daily_mu = annual_return * dt
    daily_sigma = annual_vol * np.sqrt(dt)

    current = start_date
    nav = start_nav
    series = []
    while current <= end_date:
        # 跳过周末
        if current.weekday() < 5:
            series.append((current, round(nav, 4), round(nav, 4)))
            ret = np.random.normal(daily_mu, daily_sigma)
            nav *= (1 + ret)
            nav = max(nav, 0.3)  # 最低净值保护
        current += timedelta(days=1 if freq_days == 1 else freq_days)
    return series


# ============ 基础数据定义 ============

MANAGER_DATA = [
    ("MGR001", "明远资本管理", "明远资本", "equity_long", "invested", "50-100亿"),
    ("MGR002", "量道投资管理", "量道投资", "quant_neutral", "invested", "20-50亿"),
    ("MGR003", "华鼎资产管理", "华鼎资产", "multi_strategy", "key_tracking", "100亿以上"),
    ("MGR004", "天弘量化投资", "天弘量化", "cta", "invested", "10-20亿"),
    ("MGR005", "盛世景资产", "盛世景", "equity_long", "key_tracking", "50-100亿"),
    ("MGR006", "中金汇理资管", "中金汇理", "bond", "observation", "100亿以上"),
    ("MGR007", "凯丰投资管理", "凯丰投资", "multi_strategy", "invested", "50-100亿"),
    ("MGR008", "九坤投资管理", "九坤投资", "quant_neutral", "key_tracking", "100亿以上"),
    ("MGR009", "永安国富资管", "永安国富", "cta", "observation", "20-50亿"),
    ("MGR010", "淡水泉投资", "淡水泉", "equity_long", "invested", "100亿以上"),
    ("MGR011", "思勰投资管理", "思勰投资", "quant_neutral", "observation", "10-20亿"),
    ("MGR012", "灵均投资管理", "灵均投资", "quant_neutral", "key_tracking", "50-100亿"),
    ("MGR013", "致远新兴产业", "致远产业", "equity_long", "observation", "5-10亿"),
    ("MGR014", "中欧瑞博投资", "中欧瑞博", "multi_strategy", "eliminated", "20-50亿"),
    ("MGR015", "鸣石投资管理", "鸣石投资", "cta", "key_tracking", "10-20亿"),
]

STRATEGY_PARAMS = {
    "equity_long":    (0.12, 0.22),
    "quant_neutral":  (0.08, 0.08),
    "cta":            (0.10, 0.18),
    "multi_strategy": (0.09, 0.12),
    "bond":           (0.05, 0.04),
    "arbitrage":      (0.06, 0.05),
}

PRODUCT_TEMPLATES = [
    ("成长精选{n}号", "equity_long"),
    ("量化对冲{n}号", "quant_neutral"),
    ("CTA趋势{n}号", "cta"),
    ("稳健增利{n}号", "bond"),
    ("多策略{n}号",   "multi_strategy"),
    ("中性增强{n}号", "quant_neutral"),
    ("价值优选{n}号", "equity_long"),
]

PROJECT_DATA = [
    ("PROJ001", "创新药研发平台项目", "healthcare", "sourcing"),
    ("PROJ002", "AI芯片设计项目", "tmt", "screening"),
    ("PROJ003", "新能源电池回收项目", "energy", "due_diligence"),
    ("PROJ004", "消费连锁品牌升级项目", "consumer", "ic"),
    ("PROJ005", "智能制造产线升级项目", "manufacturing", "post_investment"),
    ("PROJ006", "金融科技平台项目", "finance", "exit"),
    ("PROJ007", "半导体封测项目", "tmt", "rejected"),
    ("PROJ008", "医疗器械出海项目", "healthcare", "due_diligence"),
]

NEWS_TEMPLATES = [
    ("{mgr}旗下产品年内收益超{pct}%，领跑同策略",                   "positive", 0.85),
    ("{mgr}获得知名机构增资，管理规模突破新高",                       "positive", 0.82),
    ("{mgr}核心投研团队稳定，新增2名高级研究员",                      "positive", 0.75),
    ("{mgr}连续三个季度跑赢基准，超额收益显著",                       "positive", 0.88),
    ("{mgr}发布2025年度策略报告，看好科技和消费板块",                  "neutral",  0.55),
    ("{mgr}参加年度私募论坛，分享量化策略最新进展",                    "neutral",  0.50),
    ("{mgr}完成协会年度信息更新，合规运营状况良好",                    "neutral",  0.52),
    ("{mgr}近期净值波动加大，最大回撤接近预警线",                     "negative", 0.25),
    ("{mgr}被媒体报道存在利益输送嫌疑，公司回应称不实",               "negative", 0.15),
    ("{mgr}某基金经理离职，市场关注对业绩的影响",                     "negative", 0.30),
]


def seed_all():
    """执行完整数据初始化"""
    print("=" * 60)
    print("FOF管理平台 - 数据初始化")
    print("=" * 60)

    # 重建所有表
    print("\n[1/12] 重建数据库表...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ========== 1. 用户 ==========
        print("[2/12] 创建用户...")
        users = []
        user_data = [
            ("admin",    "系统管理员",  "super_admin"),
            ("zhangwei", "张伟(投资总监)", "director"),
            ("liming",   "李明(投资经理)", "manager"),
            ("wangfang", "王芳(风控)",     "risk"),
            ("liuyang",  "刘洋(运营)",     "operator"),
        ]
        seed_pwd = "admin123"
        for uname, rname, role in user_data:
            u = User(
                username=uname,
                password_hash=hash_password(seed_pwd),
                real_name=rname,
                role=role,
                status="active",
            )
            db.add(u)
            users.append(u)
        db.flush()
        print(f"   创建 {len(users)} 个用户 (密码均为 {seed_pwd})")

        # ========== 2. 管理人 ==========
        print("[3/12] 创建管理人...")
        managers = []
        contacts_names = [
            ("张三", "投资总监"), ("李四", "市场总监"), ("王五", "合规负责人"),
            ("赵六", "研究员"),   ("孙七", "渠道经理"), ("周八", "风控总监"),
        ]
        for i, (code, name, short, strategy, pool, aum_r) in enumerate(MANAGER_DATA):
            est_date = date(2015 + random.randint(0, 6), random.randint(1, 12), random.randint(1, 28))
            m = Manager(
                manager_code=code,
                manager_name=name,
                short_name=short,
                registration_no=f"P10{10000 + i}",
                established_date=est_date,
                registered_capital=random.choice([1000, 2000, 3000, 5000, 10000]),
                paid_capital=random.choice([1000, 2000, 3000, 5000]),
                aum_range=aum_r,
                aum=round(random.uniform(5, 150), 2),
                employee_count=random.randint(15, 120),
                registered_address=random.choice(["上海市浦东新区", "北京市朝阳区", "深圳市南山区", "杭州市西湖区"]),
                office_address=random.choice(["上海市浦东新区陆家嘴环路1000号", "北京市朝阳区国贸大厦", "深圳市南山区科技园"]),
                primary_strategy=strategy,
                secondary_strategy=random.choice(["价值型", "成长型", "均衡型", "趋势跟踪", "套利", "宏观对冲"]),
                pool_category=pool,
                assigned_user_id=random.choice([u.id for u in users[1:]]),
                team_size=random.randint(8, 50),
                strategy_type=strategy,
                rating=random.choice(["A", "B+", "B", "B-", "unrated"]),
                contact_person=contacts_names[i % len(contacts_names)][0],
                contact_phone=f"138{random.randint(10000000, 99999999)}",
                contact_email=f"contact@{short.lower().replace('(', '').replace(')', '')}.com",
                operation_status="normal",
                aum_scale=round(random.uniform(10, 200), 2),
                fund_count=random.randint(3, 20),
                compliance_status="compliant",
                status="active",
            )
            db.add(m)
            managers.append(m)
        db.flush()

        # 联系人 & 团队
        for m in managers:
            for j in range(random.randint(1, 3)):
                cn, cp = contacts_names[(managers.index(m) + j) % len(contacts_names)]
                db.add(ManagerContact(
                    manager_id=m.id, name=cn, position=cp,
                    phone=f"139{random.randint(10000000, 99999999)}",
                    email=f"{cn}@example.com", is_primary=(j == 0),
                ))
            for j in range(random.randint(2, 4)):
                db.add(ManagerTeam(
                    manager_id=m.id,
                    name=f"团队成员{j+1}",
                    position=random.choice(["基金经理", "研究员", "交易员", "风控", "合规"]),
                    years_of_experience=random.randint(3, 20),
                    education=random.choice(["清华大学 金融学硕士", "北京大学 数学博士", "复旦大学 经济学硕士", "上海交大 计算机硕士"]),
                ))

        # 标签
        tag_pool = [
            ("strategy", "高频量化", "#E6A23C"), ("strategy", "基本面选股", "#409EFF"),
            ("strategy", "商品趋势", "#67C23A"), ("progress", "已拜访", "#909399"),
            ("progress", "待尽调",  "#E6A23C"),  ("custom", "百亿规模", "#F56C6C"),
            ("custom", "华东地区", "#409EFF"),    ("custom", "华南地区", "#67C23A"),
            ("custom", "华北地区", "#E6A23C"),    ("custom", "海外背景", "#909399"),
        ]
        for m in managers:
            for _ in range(random.randint(1, 3)):
                tt, tn, tc = random.choice(tag_pool)
                db.add(ManagerTag(manager_id=m.id, tag_type=tt, tag_name=tn, tag_color=tc))

        # 池流转记录
        for m in managers[:8]:
            db.add(PoolTransfer(
                manager_id=m.id, from_pool="observation", to_pool=m.pool_category,
                reason="通过初步评估，移入当前池", operator_id=users[1].id,
            ))

        db.flush()
        print(f"   创建 {len(managers)} 个管理人（含联系人、团队、标签）")

        # ========== 3. 产品 & 净值 ==========
        print("[4/12] 创建产品与净值数据...")
        products = []
        nav_count = 0
        product_idx = 1
        nav_start = date(2023, 1, 6)
        nav_end = date.today()

        for m in managers:
            n_products = random.randint(2, 4)
            for _ in range(n_products):
                tmpl_name, tmpl_strategy = random.choice(PRODUCT_TEMPLATES)
                strategy = m.primary_strategy or tmpl_strategy
                p = Product(
                    product_code=f"PD{product_idx:04d}",
                    product_name=f"{m.short_name}{tmpl_name.format(n=product_idx)}",
                    manager_id=m.id,
                    strategy_type=strategy,
                    established_date=date(2022, 1, 1) + timedelta(days=random.randint(0, 700)),
                    management_fee=Decimal(str(round(random.uniform(0.5, 2.0), 2))),
                    performance_fee=Decimal(str(round(random.uniform(10, 25), 2))),
                    benchmark_code=random.choice(["000300.SH", "000905.SH", "000852.SH", "H11001.CSI"]),
                    benchmark_name=random.choice(["沪深300", "中证500", "中证1000", "南华商品"]),
                    is_invested=(m.pool_category == "invested"),
                    status="active",
                )
                db.add(p)
                db.flush()
                products.append(p)

                # 生成净值
                ann_ret, ann_vol = STRATEGY_PARAMS.get(strategy, (0.08, 0.12))
                ann_ret += random.uniform(-0.05, 0.05)
                ann_vol *= random.uniform(0.7, 1.3)
                series = generate_nav_series(nav_start, nav_end, ann_ret, ann_vol)
                for nav_date, unit, cum in series:
                    db.add(NavData(
                        product_id=p.id, nav_date=nav_date,
                        unit_nav=unit, cumulative_nav=cum, adjusted_nav=unit,
                        data_source="seed",
                    ))
                    nav_count += 1
                product_idx += 1

        db.flush()
        print(f"   创建 {len(products)} 个产品，{nav_count} 条净值记录")

        # ========== 4. 组合 ==========
        print("[5/12] 创建组合...")

        # 按策略分类产品
        invested_products = [p for p in products if p.is_invested]
        all_by_strategy = {}
        for p in products:
            all_by_strategy.setdefault(p.strategy_type, []).append(p)
        inv_by_strategy = {}
        for p in invested_products:
            inv_by_strategy.setdefault(p.strategy_type, []).append(p)

        portfolios = []
        pf_nav_total = 0

        # ------ PF001: 进取成长 (权益多头+CTA，高收益高波动) ------
        pf1 = Portfolio(
            portfolio_code="PF001", name="进取成长FOF1号", portfolio_type="invested",
            description="权益导向，配置股票多头和CTA策略，追求超额收益",
            status="active", start_date=date(2023, 6, 1),
            initial_amount=Decimal("200000000"),
            benchmark_code="000300.SH", benchmark_name="沪深300",
            created_by=users[1].id,
        )
        db.add(pf1)
        db.flush()
        portfolios.append(pf1)

        eq_list = inv_by_strategy.get("equity_long", [])
        cta_list = inv_by_strategy.get("cta", [])
        pf1_comps = eq_list[:3] + cta_list[:2]
        pf1_weights = [0.30, 0.25, 0.20, 0.15, 0.10][:len(pf1_comps)]
        for cp, w in zip(pf1_comps, pf1_weights):
            db.add(PortfolioComponent(
                portfolio_id=pf1.id, product_id=cp.id,
                weight=Decimal(str(w)), join_date=date(2023, 6, 1), is_active=True,
            ))

        pf1_series = generate_nav_series(date(2023, 6, 2), nav_end, 0.18, 0.25, 1.0)
        for nav_date, unit, _ in pf1_series:
            db.add(PortfolioNav(
                portfolio_id=pf1.id, nav_date=nav_date, unit_nav=unit,
                total_nav=Decimal(str(round(200_000_000 * unit, 2))),
                daily_return=Decimal(str(round(random.uniform(-0.03, 0.03), 6))),
                cumulative_return=Decimal(str(round(unit - 1, 6))),
            ))
            pf_nav_total += 1

        # ------ PF002: 稳健增长 (量化中性+多策略，低波动) ------
        pf2 = Portfolio(
            portfolio_code="PF002", name="稳健增长FOF2号", portfolio_type="invested",
            description="量化中性+多策略配置，追求低波动下的稳健回报",
            status="active", start_date=date(2023, 6, 1),
            initial_amount=Decimal("150000000"),
            benchmark_code="000510.SH", benchmark_name="中证A500",
            created_by=users[1].id,
        )
        db.add(pf2)
        db.flush()
        portfolios.append(pf2)

        qn_list = inv_by_strategy.get("quant_neutral", [])
        ms_list = inv_by_strategy.get("multi_strategy", [])
        # 如果投资池不够，也从全部产品中取
        qn_all = all_by_strategy.get("quant_neutral", [])
        ms_all = all_by_strategy.get("multi_strategy", [])
        bd_all = all_by_strategy.get("bond", [])
        pf2_comps = (qn_list[:2] or qn_all[:2]) + (ms_list[:2] or ms_all[:2]) + bd_all[:1]
        pf2_weights = [0.30, 0.25, 0.20, 0.15, 0.10][:len(pf2_comps)]
        for cp, w in zip(pf2_comps, pf2_weights):
            db.add(PortfolioComponent(
                portfolio_id=pf2.id, product_id=cp.id,
                weight=Decimal(str(w)), join_date=date(2023, 6, 1), is_active=True,
            ))

        pf2_series = generate_nav_series(date(2023, 6, 2), nav_end, 0.06, 0.06, 1.0)
        for nav_date, unit, _ in pf2_series:
            db.add(PortfolioNav(
                portfolio_id=pf2.id, nav_date=nav_date, unit_nav=unit,
                total_nav=Decimal(str(round(150_000_000 * unit, 2))),
                daily_return=Decimal(str(round(random.uniform(-0.005, 0.005), 6))),
                cumulative_return=Decimal(str(round(unit - 1, 6))),
            ))
            pf_nav_total += 1

        # ------ PF003: 全天候配置 (多策略均衡，模拟组合) ------
        pf3 = Portfolio(
            portfolio_code="PF003", name="全天候配置FOF", portfolio_type="simulated",
            description="模拟组合，均衡配置权益/量化/CTA/债券，分散风险",
            status="active", start_date=date(2023, 6, 1),
            initial_amount=Decimal("300000000"),
            benchmark_code="000905.SH", benchmark_name="中证500",
            created_by=users[2].id,
        )
        db.add(pf3)
        db.flush()
        portfolios.append(pf3)

        pf3_comps = (eq_list[1:2] or eq_list[:1]) + qn_all[:1] + cta_list[:1] + ms_all[:1] + bd_all[:1]
        # 如果仍不足就补
        if len(pf3_comps) < 3:
            for p in invested_products:
                if p not in pf3_comps:
                    pf3_comps.append(p)
                if len(pf3_comps) >= 5:
                    break
        pf3_weights_raw = np.random.dirichlet(np.ones(len(pf3_comps)) * 2)
        for cp, w in zip(pf3_comps, pf3_weights_raw):
            db.add(PortfolioComponent(
                portfolio_id=pf3.id, product_id=cp.id,
                weight=Decimal(str(round(float(w), 4))), join_date=date(2023, 6, 1), is_active=True,
            ))

        pf3_series = generate_nav_series(date(2023, 6, 2), nav_end, 0.10, 0.13, 1.0)
        for nav_date, unit, _ in pf3_series:
            db.add(PortfolioNav(
                portfolio_id=pf3.id, nav_date=nav_date, unit_nav=unit,
                total_nav=Decimal(str(round(300_000_000 * unit, 2))),
                daily_return=Decimal(str(round(random.uniform(-0.015, 0.015), 6))),
                cumulative_return=Decimal(str(round(unit - 1, 6))),
            ))
            pf_nav_total += 1

        # ------ PF004: 高频量化 (独立风格) ------
        pf4 = Portfolio(
            portfolio_code="PF004", name="高频量化FOF", portfolio_type="invested",
            description="配置高频量化和市场中性策略，追求低相关性绝对收益",
            status="active", start_date=date(2024, 1, 1),
            initial_amount=Decimal("80000000"),
            benchmark_code="000300.SH", benchmark_name="沪深300",
            created_by=users[2].id,
        )
        db.add(pf4)
        db.flush()
        portfolios.append(pf4)

        pf4_comps = qn_all[:3] + ms_all[1:2]
        if len(pf4_comps) < 2:
            pf4_comps = qn_all[:2] or invested_products[:2]
        pf4_weights = [0.35, 0.30, 0.20, 0.15][:len(pf4_comps)]
        for cp, w in zip(pf4_comps, pf4_weights):
            db.add(PortfolioComponent(
                portfolio_id=pf4.id, product_id=cp.id,
                weight=Decimal(str(w)), join_date=date(2024, 1, 1), is_active=True,
            ))

        pf4_series = generate_nav_series(date(2024, 1, 2), nav_end, 0.09, 0.05, 1.0)
        for nav_date, unit, _ in pf4_series:
            db.add(PortfolioNav(
                portfolio_id=pf4.id, nav_date=nav_date, unit_nav=unit,
                total_nav=Decimal(str(round(80_000_000 * unit, 2))),
                daily_return=Decimal(str(round(random.uniform(-0.003, 0.003), 6))),
                cumulative_return=Decimal(str(round(unit - 1, 6))),
            ))
            pf_nav_total += 1

        # ------ PF005: CTA趋势 (高波动独立走势) ------
        pf5 = Portfolio(
            portfolio_code="PF005", name="CTA趋势FOF", portfolio_type="simulated",
            description="纯CTA策略配置，趋势跟踪为主，与权益市场低相关",
            status="active", start_date=date(2024, 1, 1),
            initial_amount=Decimal("50000000"),
            benchmark_code="H11001.CSI", benchmark_name="南华商品",
            created_by=users[1].id,
        )
        db.add(pf5)
        db.flush()
        portfolios.append(pf5)

        cta_all = all_by_strategy.get("cta", [])
        pf5_comps = cta_list[:2] + cta_all[:2]
        # 去重
        seen = set()
        pf5_comps_unique = []
        for p in pf5_comps:
            if p.id not in seen:
                seen.add(p.id)
                pf5_comps_unique.append(p)
        pf5_comps = pf5_comps_unique[:4] or invested_products[:3]
        pf5_weights = [0.35, 0.30, 0.20, 0.15][:len(pf5_comps)]
        for cp, w in zip(pf5_comps, pf5_weights):
            db.add(PortfolioComponent(
                portfolio_id=pf5.id, product_id=cp.id,
                weight=Decimal(str(w)), join_date=date(2024, 1, 1), is_active=True,
            ))

        pf5_series = generate_nav_series(date(2024, 1, 2), nav_end, 0.12, 0.22, 1.0)
        for nav_date, unit, _ in pf5_series:
            db.add(PortfolioNav(
                portfolio_id=pf5.id, nav_date=nav_date, unit_nav=unit,
                total_nav=Decimal(str(round(50_000_000 * unit, 2))),
                daily_return=Decimal(str(round(random.uniform(-0.025, 0.025), 6))),
                cumulative_return=Decimal(str(round(unit - 1, 6))),
            ))
            pf_nav_total += 1

        db.flush()
        print(f"   创建 {len(portfolios)} 个组合（含成分、净值序列，共 {pf_nav_total} 条组合净值）")

        # ========== 4b. 组合持仓快照 & 调仓记录 ==========
        print("   创建组合持仓快照和调仓记录...")
        import json as _json
        holding_count = 0
        adj_count = 0

        # 每个组合的成分列表
        pf_comp_map = {
            pf1.id: (pf1_comps, pf1_weights, 200_000_000),
            pf2.id: (pf2_comps, pf2_weights, 150_000_000),
            pf3.id: (pf3_comps, list(pf3_weights_raw), 300_000_000),
            pf4.id: (pf4_comps, pf4_weights, 80_000_000),
            pf5.id: (pf5_comps, pf5_weights, 50_000_000),
        }

        # 生成多个日期的持仓快照（模拟月末快照）
        snapshot_dates = [
            date(2024, 12, 31), date(2025, 3, 31), date(2025, 6, 30),
            date(2025, 9, 30), date(2025, 12, 31), date(2026, 1, 31),
        ]

        for pf in portfolios:
            comps, weights, init_amount = pf_comp_map[pf.id]
            # 查询这个组合的净值序列用于估算市值
            for snap_date in snapshot_dates:
                if snap_date < pf.start_date:
                    continue
                # 查找最近的净值记录估算组合总市值
                nav_rec = db.query(PortfolioNav).filter(
                    PortfolioNav.portfolio_id == pf.id,
                    PortfolioNav.nav_date <= snap_date
                ).order_by(PortfolioNav.nav_date.desc()).first()
                unit_nav = float(nav_rec.unit_nav) if nav_rec else 1.0
                total_mv = init_amount * unit_nav

                for cp, w in zip(comps, weights[:len(comps)]):
                    w_f = float(w)
                    mv = round(total_mv * w_f, 2)
                    # 从产品净值表查单位净值
                    pnav = db.query(NavData).filter(
                        NavData.product_id == cp.id,
                        NavData.nav_date <= snap_date
                    ).order_by(NavData.nav_date.desc()).first()
                    p_unit = float(pnav.unit_nav) if pnav else 1.0
                    shares = round(mv / p_unit, 4) if p_unit > 0 else 0
                    cost = round(mv * random.uniform(0.85, 1.05), 2)
                    pnl = round(mv - cost, 2)
                    pnl_ratio = round(pnl / cost, 6) if cost > 0 else 0

                    db.add(PortfolioHolding(
                        portfolio_id=pf.id, product_id=cp.id,
                        holding_date=snap_date, shares=Decimal(str(shares)),
                        market_value=Decimal(str(mv)), weight=Decimal(str(round(w_f, 6))),
                        cost=Decimal(str(cost)), pnl=Decimal(str(pnl)),
                        pnl_ratio=Decimal(str(pnl_ratio)),
                    ))
                    holding_count += 1

        db.flush()

        # 调仓记录：每个组合生成3-5条历史调仓
        adj_types = ["rebalance", "weight_change", "add", "remove"]
        adj_reasons = [
            ("季度再平衡，调整成分权重回到目标配置", "rebalance"),
            ("增加权益类配置，由{old}%调整至{new}%", "weight_change"),
            ("新增产品纳入组合，丰富策略多样性", "add"),
            ("移除表现不佳产品，替换为同策略优质产品", "remove"),
            ("风控触发调仓，降低高波动策略权重", "weight_change"),
            ("投委会审批后调整，增配CTA策略对冲尾部风险", "rebalance"),
            ("年度策略调整，提高稳健型策略占比", "weight_change"),
        ]

        for pf in portfolios:
            comps, weights, _ = pf_comp_map[pf.id]
            n_adj = random.randint(3, 5)
            base = pf.start_date + timedelta(days=90)
            for j in range(n_adj):
                adj_date = base + timedelta(days=j * random.randint(60, 120))
                if adj_date > date.today():
                    break
                reason, atype = random.choice(adj_reasons)
                old_pct = random.randint(15, 35)
                new_pct = old_pct + random.choice([-5, -3, 3, 5])
                reason = reason.format(old=old_pct, new=new_pct)

                before = {str(cp.id): round(float(w), 4) for cp, w in zip(comps, weights[:len(comps)])}
                # 模拟调整后的权重变动
                after = {}
                for k, v in before.items():
                    delta = round(random.uniform(-0.03, 0.03), 4)
                    after[k] = round(max(0.01, v + delta), 4)

                db.add(PortfolioAdjustment(
                    portfolio_id=pf.id, adjust_date=adj_date,
                    adjust_type=atype, description=reason,
                    before_weights=_json.dumps(before),
                    after_weights=_json.dumps(after),
                    created_by=random.choice([users[1].id, users[2].id]),
                ))
                adj_count += 1

        db.flush()
        print(f"   创建 {holding_count} 条持仓快照，{adj_count} 条调仓记录")

        # ========== 5. 持仓明细 ==========
        print("[6/12] 创建持仓明细...")
        stock_pool = [
            ("600519", "贵州茅台", "stock", "食品饮料", "大盘"),
            ("000858", "五粮液",   "stock", "食品饮料", "大盘"),
            ("300750", "宁德时代", "stock", "电力设备", "大盘"),
            ("601318", "中国平安", "stock", "非银金融", "大盘"),
            ("600036", "招商银行", "stock", "银行",     "大盘"),
            ("000001", "平安银行", "stock", "银行",     "中盘"),
            ("002475", "立讯精密", "stock", "电子",     "中盘"),
            ("300059", "东方财富", "stock", "非银金融", "中盘"),
            ("688981", "中芯国际", "stock", "半导体",   "大盘"),
            ("603259", "药明康德", "stock", "医药生物", "大盘"),
            ("110044", "24国开10", "bond", None, None),
            ("110057", "24农发05", "bond", None, None),
        ]
        hd_count = 0
        for p in products[:10]:
            for rd in [date(2025, 9, 30), date(2025, 12, 31)]:
                chosen_stocks = random.sample(stock_pool, random.randint(5, 8))
                weights_arr = np.random.dirichlet(np.ones(len(chosen_stocks)))
                for (sc, sn, st, ind, mc), wt in zip(chosen_stocks, weights_arr):
                    mv = round(random.uniform(500000, 5000000), 2)
                    cost_val = round(mv * random.uniform(0.8, 1.1), 2)
                    db.add(HoldingsDetail(
                        product_id=p.id, holding_date=rd,
                        security_type=st, security_code=sc, security_name=sn,
                        quantity=round(random.uniform(1000, 50000), 0),
                        market_price=round(random.uniform(10, 500), 2),
                        market_value=mv,
                        cost=cost_val,
                        weight=round(float(wt), 4),
                        pnl=round(mv - cost_val, 2),
                        pnl_ratio=round((mv - cost_val) / cost_val if cost_val > 0 else 0, 4),
                        industry_l1=ind,
                        industry_l2=ind,
                        market_cap_type={'大盘': 'large', '中盘': 'mid', '小盘': 'small'}.get(mc, 'unknown') if mc else 'unknown',
                        level=1,
                    ))
                    hd_count += 1
        db.flush()
        print(f"   创建 {hd_count} 条持仓明细")

        # ========== 6. 一级项目 ==========
        print("[7/12] 创建一级项目...")
        projects = []
        for code, name, industry, stage in PROJECT_DATA:
            proj = Project(
                project_code=code, project_name=name, short_name=name[:6],
                industry=industry, sub_industry=random.choice(["创新药", "AI芯片", "储能", "消费电子", "SaaS"]),
                source=random.choice(["FA推荐", "直投", "被投企业推荐", "产业链调研"]),
                stage=stage,
                assigned_user_id=random.choice([u.id for u in users[1:4]]),
                contact_name=f"联系人{random.randint(1,9)}", contact_phone=f"135{random.randint(10000000,99999999)}",
                initial_intro=f"{name}的初步介绍，行业前景良好。",
                investment_amount=Decimal(str(random.randint(1000, 10000))),
                valuation=Decimal(str(random.randint(50000, 500000))),
            )
            db.add(proj)
            db.flush()
            projects.append(proj)

            # 跟进记录
            for k in range(random.randint(2, 5)):
                db.add(ProjectFollowUp(
                    project_id=proj.id,
                    follow_date=date(2025, 1, 1) + timedelta(days=k * 15 + random.randint(0, 10)),
                    follow_type=random.choice(["电话", "会议", "邮件", "现场拜访"]),
                    content=f"第{k+1}次跟进{name}，了解业务进展和融资需求。",
                    next_plan="安排下一次深入沟通。",
                    follow_user_id=proj.assigned_user_id,
                ))

            # 阶段变更
            stages_order = ["sourcing", "screening", "due_diligence", "ic", "post_investment", "exit"]
            idx = stages_order.index(stage) if stage in stages_order else 0
            prev = "sourcing"
            for s in stages_order[1:idx + 1]:
                db.add(ProjectStageChange(
                    project_id=proj.id, from_stage=prev, to_stage=s,
                    reason=f"项目推进至{s}阶段", operator_id=users[1].id,
                ))
                prev = s

        # 现金流
        for proj in projects[4:6]:
            db.add(ProjectCashflow(
                project_id=proj.id, cashflow_date=date(2024, 3, 15),
                cashflow_type="investment", amount=Decimal("-3000"), description="首轮投资",
            ))
            db.add(ProjectCashflow(
                project_id=proj.id, cashflow_date=date(2025, 6, 30),
                cashflow_type="distribution", amount=Decimal("1500"), description="年度分红",
            ))

        db.flush()
        print(f"   创建 {len(projects)} 个项目（含跟进记录、阶段变更、现金流）")

        # ========== 7. 任务 ==========
        print("[8/12] 创建任务...")
        task_templates = [
            ("审核{mgr}最新月报",          "medium", "pending"),
            ("跟进{mgr}年度尽调安排",       "high",   "in_progress"),
            ("更新产品净值数据",            "medium", "completed"),
            ("准备投委会材料-{mgr}",        "urgent", "pending"),
            ("核对{mgr}合同条款",          "high",   "in_progress"),
            ("撰写季度组合报告",           "medium", "pending"),
            ("安排{mgr}现场拜访",          "low",    "pending"),
            ("检查数据异常-净值偏离预警",   "urgent", "in_progress"),
        ]
        t_count = 0
        for tmpl, priority, status in task_templates:
            m = random.choice(managers)
            title = tmpl.format(mgr=m.short_name)
            db.add(Task(
                title=title,
                description=f"请及时完成：{title}",
                status=status, priority=priority,
                manager_id=m.id if "{mgr}" in tmpl else None,
                assigned_to=random.choice([u.id for u in users[1:]]),
                created_by=users[0].id,
                due_date=date.today() + timedelta(days=random.randint(1, 30)),
            ))
            t_count += 1
        db.flush()
        print(f"   创建 {t_count} 条任务")

        # ========== 8. 日历事件 ==========
        print("[9/12] 创建日历事件...")
        event_templates = [
            ("投委会例会",         "meeting",  "#409EFF"),
            ("季度绩效评审",       "review",   "#E6A23C"),
            ("{mgr}年度尽调",      "deadline", "#F56C6C"),
            ("月报提交截止",       "deadline", "#F56C6C"),
            ("{mgr}路演交流",      "meeting",  "#67C23A"),
            ("风控月度报告",       "report",   "#909399"),
        ]
        ev_count = 0
        base_date = date(2026, 2, 1)
        for tmpl, etype, color in event_templates:
            m = random.choice(managers)
            title = tmpl.format(mgr=m.short_name)
            ed = base_date + timedelta(days=random.randint(0, 60))
            db.add(CalendarEvent(
                title=title, description=f"事件详情: {title}",
                event_type=etype, event_date=ed,
                start_time="09:30" if etype == "meeting" else None,
                end_time="11:30" if etype == "meeting" else None,
                is_all_day=(etype != "meeting"), color=color,
                manager_id=m.id if "{mgr}" in tmpl else None,
                user_id=users[1].id,
            ))
            ev_count += 1
        db.flush()
        print(f"   创建 {ev_count} 条日历事件")

        # ========== 9. 评论/讨论 ==========
        print("[10/12] 创建评论讨论...")
        cm_count = 0
        comment_texts = [
            "该管理人近期业绩表现优秀，建议增加配置。",
            "风控指标需要进一步关注，最大回撤接近预设阈值。",
            "团队稳定性较好，核心人员从业经验丰富。",
            "建议安排下次现场尽调，重点关注合规运营。",
            "产品流动性需要评估，赎回条款较严格。",
            "同意上述观点，补充一点：费率偏高。",
        ]
        for m in managers[:8]:
            c1 = Comment(
                resource_type="manager", resource_id=m.id,
                content=random.choice(comment_texts),
                user_id=random.choice([u.id for u in users[1:]]),
            )
            db.add(c1)
            db.flush()
            cm_count += 1
            # 回复
            db.add(Comment(
                resource_type="manager", resource_id=m.id,
                content=random.choice(comment_texts),
                parent_id=c1.id,
                user_id=random.choice([u.id for u in users[1:]]),
            ))
            cm_count += 1

        for p in products[:5]:
            db.add(Comment(
                resource_type="product", resource_id=p.id,
                content="产品净值走势平稳，波动率控制良好。",
                user_id=users[2].id,
            ))
            cm_count += 1
        db.flush()
        print(f"   创建 {cm_count} 条评论")

        # ========== 10. 舆情新闻 ==========
        print("[11/12] 创建舆情新闻...")
        nw_count = 0
        sources = ["财联社", "私募排排网", "朝阳永续", "Wind资讯", "东方财富"]
        for m in managers:
            for tmpl, sent, score in random.sample(NEWS_TEMPLATES, min(4, len(NEWS_TEMPLATES))):
                pct = random.randint(5, 30)
                title = tmpl.format(mgr=m.short_name, pct=pct)
                db.add(NewsArticle(
                    title=title,
                    content=f"{title}。详细内容请参阅原文。这是一条由系统生成的模拟新闻数据，用于展示舆情监控功能。",
                    source=random.choice(sources),
                    url=f"https://example.com/news/{nw_count}",
                    publish_date=datetime(2025, random.randint(1, 12), random.randint(1, 28), 9, 0),
                    manager_id=m.id,
                    sentiment=sent,
                    sentiment_score=score + random.uniform(-0.05, 0.05),
                    keywords=[m.short_name, random.choice(["业绩", "规模", "团队", "策略", "合规"])],
                    summary=title[:50],
                    is_alert=1 if sent == "negative" else 0,
                ))
                nw_count += 1
        db.flush()
        print(f"   创建 {nw_count} 条舆情新闻")

        # ========== 11. 尽调工作流 ==========
        print("[12/12] 创建尽调工作流...")
        dd_data = [
            ("明远资本年度尽调",   0, "approved",    "annual"),
            ("量道投资初始尽调",   1, "in_progress", "initial"),
            ("华鼎资产跟踪尽调",  2, "review",      "follow_up"),
            ("凯丰投资年度尽调",  6, "draft",       "annual"),
        ]
        for title, mi, status, dd_type in dd_data:
            checklist = [
                {"item": "基本信息核实", "completed": status != "draft", "remark": "已完成"},
                {"item": "投资策略评估", "completed": status in ("approved", "review"), "remark": ""},
                {"item": "风控体系审查", "completed": status == "approved", "remark": ""},
                {"item": "合规检查",     "completed": status == "approved", "remark": ""},
                {"item": "运营尽调",     "completed": False, "remark": ""},
            ]
            db.add(DueDiligenceFlow(
                title=title, manager_id=managers[mi].id,
                status=status, dd_type=dd_type,
                start_date=date(2025, 6, 1),
                end_date=date(2025, 8, 31),
                actual_end_date=date(2025, 8, 15) if status == "approved" else None,
                checklist=checklist,
                conclusion="整体评估良好，建议维持当前配置。" if status == "approved" else None,
                risk_points="关注核心人员稳定性" if status in ("approved", "review") else None,
                lead_user_id=users[2].id,
                reviewer_id=users[1].id,
            ))
        db.flush()
        print(f"   创建 {len(dd_data)} 条尽调工作流")

        # ========== 提交 ==========
        db.commit()

        print("\n" + "=" * 60)
        print("数据初始化完成！")
        print("=" * 60)
        print(f"""
数据统计:
  用户:       {len(users)} 个
  管理人:     {len(managers)} 个 (含联系人、团队、标签、池流转)
  产品:       {len(products)} 个
  净值记录:   {nav_count} 条 (日频, 2023-至今)
  组合:       {len(portfolios)} 个 (含成分、净值，共 {pf_nav_total} 条组合净值)
  持仓明细:   {hd_count} 条
  一级项目:   {len(projects)} 个 (含跟进、阶段变更、现金流)
  任务:       {t_count} 条
  日历事件:   {ev_count} 条
  评论:       {cm_count} 条
  舆情新闻:   {nw_count} 条
  尽调工作流: {len(dd_data)} 条

登录账号:
  admin    / admin123 (超级管理员)
  zhangwei / admin123 (投资总监)
  liming   / admin123 (投资经理)
  wangfang / admin123 (风控)
  liuyang  / admin123 (运营)
""")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
