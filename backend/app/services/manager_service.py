"""
管理人Service V2 - 业务逻辑层
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc
from typing import Optional, List
from fastapi import HTTPException, status
from datetime import date, timedelta
import math

from app.models.manager import (
    Manager, ManagerStatus, ManagerContact, ManagerTeam, 
    PoolTransfer, PoolCategory, PrimaryStrategy, ManagerTag
)
from app.models.manager_edit_history import ManagerEditHistory
from app.models.product import Product, ProductStatus
from app.models.nav import NavData
from app.schemas.manager import (
    ManagerCreate, ManagerUpdate, ManagerContactCreate, 
    ManagerTeamCreate, PoolTransferCreate, ManagerListParams,
    ManagerTagCreate
)
import uuid


def get_managers(
    db: Session,
    params: ManagerListParams
) -> tuple[List[Manager], int]:
    """获取管理人列表（支持多条件筛选）"""
    query = db.query(Manager).filter(Manager.is_deleted == False)
    
    # 关键词搜索
    if params.keyword:
        keyword = f"%{params.keyword}%"
        query = query.filter(
            or_(
                Manager.manager_name.like(keyword),
                Manager.manager_code.like(keyword),
                Manager.short_name.like(keyword),
                Manager.registration_no.like(keyword)
            )
        )
    
    # 跟踪池分类筛选
    if params.pool_categories:
        query = query.filter(Manager.pool_category.in_(params.pool_categories))
    
    # 一级策略筛选
    if params.primary_strategies:
        query = query.filter(Manager.primary_strategy.in_(params.primary_strategies))
    
    # 负责人筛选
    if params.assigned_user_ids:
        query = query.filter(Manager.assigned_user_id.in_(params.assigned_user_ids))
    
    # 标签筛选（支持区域等自定义标签）
    if params.tag_names:
        query = query.filter(
            Manager.id.in_(
                db.query(ManagerTag.manager_id).filter(
                    ManagerTag.tag_name.in_(params.tag_names)
                )
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 排序
    sort_column = getattr(Manager, params.sort_by, Manager.created_at)
    if params.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    # 分页
    skip = (params.page - 1) * params.page_size
    managers = query.offset(skip).limit(params.page_size).all()
    
    return managers, total


def get_managers_simple(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    strategy_type: Optional[str] = None,
    rating: Optional[str] = None,
    status_filter: Optional[str] = None
) -> tuple[List[Manager], int]:
    """获取管理人列表（兼容V1接口）"""
    query = db.query(Manager).filter(Manager.is_deleted == False)
    
    if search:
        query = query.filter(
            or_(
                Manager.manager_name.like(f"%{search}%"),
                Manager.manager_code.like(f"%{search}%")
            )
        )
    
    if strategy_type:
        query = query.filter(Manager.strategy_type == strategy_type)
    
    if rating:
        query = query.filter(Manager.rating == rating)
    
    if status_filter:
        query = query.filter(Manager.status == status_filter)
    
    total = query.count()
    managers = query.order_by(Manager.created_at.desc()).offset(skip).limit(limit).all()
    
    return managers, total


def get_manager_by_id(db: Session, manager_id: int) -> Optional[Manager]:
    """根据ID获取管理人（包含关联数据）"""
    return db.query(Manager).options(
        joinedload(Manager.contacts),
        joinedload(Manager.team_members),
        joinedload(Manager.products)
    ).filter(
        Manager.id == manager_id,
        Manager.is_deleted == False
    ).first()


def get_manager_by_code(db: Session, manager_code: str) -> Optional[Manager]:
    """根据编号获取管理人"""
    return db.query(Manager).filter(
        Manager.manager_code == manager_code,
        Manager.is_deleted == False
    ).first()


def create_manager(db: Session, manager: ManagerCreate) -> Manager:
    """创建管理人（包含联系人和团队）"""
    # 检查编号是否已存在
    existing = get_manager_by_code(db, manager.manager_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"管理人编号 {manager.manager_code} 已存在"
        )
    
    # 创建管理人
    manager_data = manager.model_dump(exclude={"contacts", "team_members"})
    db_manager = Manager(**manager_data)
    db_manager.status = ManagerStatus.ACTIVE
    db_manager.is_deleted = False
    
    db.add(db_manager)
    db.flush()  # 获取ID
    
    # 创建联系人
    if manager.contacts:
        for contact in manager.contacts:
            db_contact = ManagerContact(
                manager_id=db_manager.id,
                **contact.model_dump()
            )
            db.add(db_contact)
    
    # 创建核心团队
    if manager.team_members:
        for member in manager.team_members:
            db_member = ManagerTeam(
                manager_id=db_manager.id,
                **member.model_dump()
            )
            db.add(db_member)
    
    db.commit()
    db.refresh(db_manager)
    
    return db_manager


# 字段中文名映射
FIELD_LABELS = {
    "manager_name": "管理人名称", "short_name": "管理人简称", "registration_no": "备案编号",
    "established_date": "成立日期", "registered_capital": "注册资本", "paid_capital": "实缴资本",
    "aum_range": "管理规模", "employee_count": "员工人数", "registered_address": "注册地址",
    "office_address": "办公地址", "website": "官网", "primary_strategy": "一级策略",
    "secondary_strategy": "二级策略", "investment_style": "投资风格", "benchmark_index": "基准指数",
    "cooperation_start_date": "合作开始日期", "cooperation_end_date": "合作结束日期",
    "rating": "内部评级", "contact_person": "联系人", "contact_phone": "联系电话",
    "contact_email": "联系邮箱", "remark": "备注", "pool_category": "跟踪池",
}


def update_manager(db: Session, manager_id: int, manager_update: ManagerUpdate, operator_id: Optional[int] = None) -> Manager:
    """更新管理人（带版本历史记录）"""
    db_manager = get_manager_by_id(db, manager_id)
    if not db_manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"管理人ID {manager_id} 不存在"
        )
    
    update_data = manager_update.model_dump(exclude_unset=True)
    batch_id = uuid.uuid4().hex[:12]
    
    # 记录变更历史
    for field, new_value in update_data.items():
        old_value = getattr(db_manager, field, None)
        old_str = str(old_value) if old_value is not None else ""
        new_str = str(new_value) if new_value is not None else ""
        if old_str != new_str:
            history = ManagerEditHistory(
                manager_id=manager_id,
                field_name=field,
                field_label=FIELD_LABELS.get(field, field),
                old_value=old_str,
                new_value=new_str,
                operator_id=operator_id,
                batch_id=batch_id,
            )
            db.add(history)
    
    for field, value in update_data.items():
        setattr(db_manager, field, value)
    
    db.commit()
    db.refresh(db_manager)
    
    return db_manager


def delete_manager(db: Session, manager_id: int) -> bool:
    """删除管理人（软删除）"""
    db_manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not db_manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"管理人ID {manager_id} 不存在"
        )
    
    db_manager.is_deleted = True
    db_manager.status = ManagerStatus.INACTIVE
    db.commit()
    
    return True


# ========== 联系人管理 ==========
def add_contact(db: Session, manager_id: int, contact: ManagerContactCreate) -> ManagerContact:
    """添加联系人"""
    db_manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not db_manager:
        raise HTTPException(status_code=404, detail="管理人不存在")
    
    db_contact = ManagerContact(manager_id=manager_id, **contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, contact_id: int, contact: ManagerContactCreate) -> ManagerContact:
    """更新联系人"""
    db_contact = db.query(ManagerContact).filter(ManagerContact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    
    for field, value in contact.model_dump().items():
        setattr(db_contact, field, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, contact_id: int) -> bool:
    """删除联系人"""
    db_contact = db.query(ManagerContact).filter(ManagerContact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="联系人不存在")
    
    db.delete(db_contact)
    db.commit()
    return True


# ========== 核心团队管理 ==========
def add_team_member(db: Session, manager_id: int, member: ManagerTeamCreate) -> ManagerTeam:
    """添加核心团队成员"""
    db_manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not db_manager:
        raise HTTPException(status_code=404, detail="管理人不存在")
    
    db_member = ManagerTeam(manager_id=manager_id, **member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def delete_team_member(db: Session, member_id: int) -> bool:
    """删除核心团队成员"""
    db_member = db.query(ManagerTeam).filter(ManagerTeam.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="团队成员不存在")
    
    db.delete(db_member)
    db.commit()
    return True


# ========== 跟踪池流转 ==========
def transfer_pool(
    db: Session, 
    manager_id: int, 
    transfer: PoolTransferCreate,
    operator_id: Optional[int] = None
) -> PoolTransfer:
    """跟踪池流转"""
    db_manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not db_manager:
        raise HTTPException(status_code=404, detail="管理人不存在")
    
    # 记录流转
    db_transfer = PoolTransfer(
        manager_id=manager_id,
        from_pool=db_manager.pool_category,
        to_pool=transfer.to_pool,
        reason=transfer.reason,
        operator_id=operator_id
    )
    db.add(db_transfer)
    
    # 更新管理人分类
    db_manager.pool_category = transfer.to_pool
    
    db.commit()
    db.refresh(db_transfer)
    return db_transfer


def get_pool_transfers(db: Session, manager_id: int) -> List[PoolTransfer]:
    """获取管理人的流转历史"""
    return db.query(PoolTransfer).filter(
        PoolTransfer.manager_id == manager_id
    ).order_by(PoolTransfer.created_at.desc()).all()


def batch_transfer_pool(
    db: Session,
    manager_ids: List[int],
    transfer: PoolTransferCreate,
    operator_id: Optional[int] = None
) -> int:
    """批量流转"""
    count = 0
    for manager_id in manager_ids:
        try:
            transfer_pool(db, manager_id, transfer, operator_id)
            count += 1
        except:
            continue
    return count


# ========== 统计 ==========
def get_manager_statistics(db: Session) -> dict:
    """获取管理人统计信息"""
    query = db.query(Manager).filter(Manager.is_deleted == False)
    
    total = query.count()
    
    # 按跟踪池统计
    pool_stats = db.query(
        Manager.pool_category,
        func.count(Manager.id)
    ).filter(Manager.is_deleted == False).group_by(Manager.pool_category).all()
    
    # 按策略统计
    strategy_stats = db.query(
        Manager.primary_strategy,
        func.count(Manager.id)
    ).filter(Manager.is_deleted == False).group_by(Manager.primary_strategy).all()
    
    return {
        "total": total,
        "by_pool": [
            {"category": cat if cat else "unknown", "count": count}
            for cat, count in pool_stats
        ],
        "by_strategy": {
            (s if s else "unknown"): count 
            for s, count in strategy_stats
        }
    }


# ========== 编辑历史 ==========
def get_edit_history(db: Session, manager_id: int, skip: int = 0, limit: int = 50) -> tuple[list, int]:
    """获取管理人编辑历史"""
    query = db.query(ManagerEditHistory).filter(ManagerEditHistory.manager_id == manager_id)
    total = query.count()
    items = query.order_by(ManagerEditHistory.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


# ========== 批量导入 ==========
def batch_import_managers(db: Session, managers: List[ManagerCreate]) -> dict:
    """批量导入管理人"""
    success_count = 0
    fail_count = 0
    errors = []
    
    for i, manager in enumerate(managers):
        try:
            # 检查是否已存在
            existing = get_manager_by_code(db, manager.manager_code)
            if existing:
                # 更新现有记录
                update_data = manager.model_dump(exclude={"contacts", "team_members"})
                for field, value in update_data.items():
                    if value is not None:
                        setattr(existing, field, value)
                success_count += 1
            else:
                # 创建新记录
                create_manager(db, manager)
                success_count += 1
        except Exception as e:
            fail_count += 1
            errors.append({"row": i + 1, "code": manager.manager_code, "error": str(e)})
    
    db.commit()
    
    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors
    }


# ========== 旗下产品 ==========
def get_manager_products(db: Session, manager_id: int) -> List[dict]:
    """获取管理人旗下产品列表（含最新净值和绩效）"""
    # 获取管理人旗下所有产品
    products = db.query(Product).filter(
        Product.manager_id == manager_id
    ).order_by(Product.created_at.desc()).all()
    
    result = []
    for product in products:
        # 查询最新净值
        latest_nav = db.query(NavData).filter(
            NavData.product_id == product.id
        ).order_by(NavData.nav_date.desc()).first()
        
        # 查询第一条净值（用于计算累计收益）
        first_nav = db.query(NavData).filter(
            NavData.product_id == product.id
        ).order_by(NavData.nav_date.asc()).first()
        
        # 净值总数
        nav_count = db.query(func.count(NavData.id)).filter(
            NavData.product_id == product.id
        ).scalar() or 0
        
        cumulative_return = None
        annualized_return = None
        
        if latest_nav and first_nav and first_nav.cumulative_nav and latest_nav.cumulative_nav:
            first_val = float(first_nav.cumulative_nav)
            last_val = float(latest_nav.cumulative_nav)
            if first_val > 0:
                cumulative_return = (last_val / first_val - 1)
                # 年化收益
                days = (latest_nav.nav_date - first_nav.nav_date).days
                if days > 0:
                    annualized_return = (last_val / first_val) ** (365.0 / days) - 1
        
        result.append({
            "id": product.id,
            "product_code": product.product_code,
            "product_name": product.product_name,
            "strategy_type": product.strategy_type,
            "established_date": product.established_date,
            "status": product.status or None,
            "latest_nav": float(latest_nav.unit_nav) if latest_nav and latest_nav.unit_nav else None,
            "latest_nav_date": latest_nav.nav_date if latest_nav else None,
            "cumulative_nav": float(latest_nav.cumulative_nav) if latest_nav and latest_nav.cumulative_nav else None,
            "cumulative_return": round(cumulative_return, 6) if cumulative_return is not None else None,
            "annualized_return": round(annualized_return, 6) if annualized_return is not None else None,
            "nav_count": nav_count
        })
    
    return result


# ========== 业绩汇总 ==========
def get_manager_performance_summary(db: Session, manager_id: int) -> dict:
    """获取管理人业绩汇总"""
    manager = db.query(Manager).filter(
        Manager.id == manager_id, Manager.is_deleted == False
    ).first()
    if not manager:
        raise HTTPException(status_code=404, detail="管理人不存在")
    
    products = db.query(Product).filter(
        Product.manager_id == manager_id
    ).all()
    
    total_products = len(products)
    active_products = sum(1 for p in products if p.status == "active")
    
    products_comparison = []
    all_returns = []
    all_drawdowns = []
    all_sharpes = []
    all_vols = []
    
    for product in products:
        # 获取产品净值序列
        navs = db.query(NavData).filter(
            NavData.product_id == product.id
        ).order_by(NavData.nav_date.asc()).all()
        
        if len(navs) < 2:
            products_comparison.append({
                "product_name": product.product_name,
                "cumulative_return": None,
                "annualized_return": None,
                "max_drawdown": None,
                "sharpe_ratio": None,
                "volatility": None
            })
            continue
        
        # 计算日收益率序列
        nav_values = []
        for n in navs:
            val = n.cumulative_nav or n.unit_nav
            if val:
                nav_values.append(float(val))
        
        if len(nav_values) < 2:
            products_comparison.append({
                "product_name": product.product_name,
                "cumulative_return": None, "annualized_return": None,
                "max_drawdown": None, "sharpe_ratio": None, "volatility": None
            })
            continue
        
        daily_returns = [(nav_values[i] / nav_values[i-1] - 1) for i in range(1, len(nav_values))]
        
        # 累计收益
        cum_return = nav_values[-1] / nav_values[0] - 1
        
        # 年化收益
        days = (navs[-1].nav_date - navs[0].nav_date).days
        ann_return = (nav_values[-1] / nav_values[0]) ** (365.0 / max(days, 1)) - 1
        
        # 最大回撤
        peak = nav_values[0]
        max_dd = 0
        for v in nav_values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
        
        # 波动率和夏普
        import numpy as np
        dr = np.array(daily_returns)
        vol = float(np.std(dr) * math.sqrt(252)) if len(dr) > 1 else None
        sharpe = float((np.mean(dr) * 252 - 0.02) / (np.std(dr) * math.sqrt(252))) if vol and vol > 0 else None
        
        comp = {
            "product_name": product.product_name,
            "cumulative_return": round(cum_return, 6),
            "annualized_return": round(ann_return, 6),
            "max_drawdown": round(-max_dd, 6),
            "sharpe_ratio": round(sharpe, 4) if sharpe else None,
            "volatility": round(vol, 6) if vol else None
        }
        products_comparison.append(comp)
        all_returns.append(cum_return)
        if max_dd > 0:
            all_drawdowns.append(-max_dd)
        if sharpe is not None:
            all_sharpes.append(sharpe)
        if vol is not None:
            all_vols.append(vol)
    
    # 综合净值曲线：等权平均所有产品的归一化净值
    nav_dates = []
    nav_values_combined = []
    
    # 获取所有产品的净值日期并展，简化为取第一个有效产品的净值曲线
    if products:
        # 取所有active产品的净值数据，计算等权平均
        active_prods = [p for p in products if p.status == "active"]
        if not active_prods:
            active_prods = products[:1]
        
        # 简化：取第一个产品的净值序列作为展示
        main_product = active_prods[0]
        main_navs = db.query(NavData).filter(
            NavData.product_id == main_product.id
        ).order_by(NavData.nav_date.asc()).all()
        
        if main_navs:
            first_val = float(main_navs[0].cumulative_nav or main_navs[0].unit_nav or 1)
            for n in main_navs:
                val = float(n.cumulative_nav or n.unit_nav or 1)
                nav_dates.append(str(n.nav_date))
                nav_values_combined.append(round(val / first_val, 6))
    
    return {
        "manager_id": manager_id,
        "manager_name": manager.manager_name,
        "total_products": total_products,
        "active_products": active_products,
        "weighted_cumulative_return": round(sum(all_returns) / len(all_returns), 6) if all_returns else None,
        "weighted_annualized_return": round(
            sum(c.get("annualized_return", 0) or 0 for c in products_comparison if c.get("annualized_return")) / 
            max(sum(1 for c in products_comparison if c.get("annualized_return")), 1), 6
        ) if products_comparison else None,
        "avg_max_drawdown": round(sum(all_drawdowns) / len(all_drawdowns), 6) if all_drawdowns else None,
        "avg_sharpe_ratio": round(sum(all_sharpes) / len(all_sharpes), 4) if all_sharpes else None,
        "avg_volatility": round(sum(all_vols) / len(all_vols), 6) if all_vols else None,
        "products_comparison": products_comparison,
        "nav_dates": nav_dates,
        "nav_values": nav_values_combined
    }


# ========== 标签管理 ==========
def get_manager_tags(db: Session, manager_id: int) -> List[ManagerTag]:
    """获取管理人标签"""
    return db.query(ManagerTag).filter(
        ManagerTag.manager_id == manager_id
    ).order_by(ManagerTag.tag_type, ManagerTag.created_at).all()


def add_manager_tag(db: Session, manager_id: int, tag: ManagerTagCreate) -> ManagerTag:
    """添加标签"""
    # 检查管理人是否存在
    manager = db.query(Manager).filter(Manager.id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="管理人不存在")
    
    # 检查是否重复
    existing = db.query(ManagerTag).filter(
        ManagerTag.manager_id == manager_id,
        ManagerTag.tag_type == tag.tag_type,
        ManagerTag.tag_name == tag.tag_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="标签已存在")
    
    db_tag = ManagerTag(
        manager_id=manager_id,
        tag_type=tag.tag_type,
        tag_name=tag.tag_name,
        tag_color=tag.tag_color
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_manager_tag(db: Session, tag_id: int) -> bool:
    """删除标签"""
    db_tag = db.query(ManagerTag).filter(ManagerTag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(db_tag)
    db.commit()
    return True


def get_all_unique_tags(db: Session, tag_type: Optional[str] = None) -> List[dict]:
    """获取所有唯一标签（用于筛选下拉）"""
    query = db.query(
        ManagerTag.tag_type,
        ManagerTag.tag_name,
        ManagerTag.tag_color,
        func.count(ManagerTag.id).label('count')
    )
    if tag_type:
        query = query.filter(ManagerTag.tag_type == tag_type)
    
    results = query.group_by(
        ManagerTag.tag_type, ManagerTag.tag_name, ManagerTag.tag_color
    ).order_by(ManagerTag.tag_type, ManagerTag.tag_name).all()
    
    return [
        {
            "tag_type": r.tag_type,
            "tag_name": r.tag_name,
            "tag_color": r.tag_color,
            "count": r.count
        }
        for r in results
    ]


def export_managers(db: Session, manager_ids: Optional[List[int]] = None) -> List[dict]:
    """导出管理人数据"""
    query = db.query(Manager).filter(Manager.is_deleted == False)
    
    if manager_ids:
        query = query.filter(Manager.id.in_(manager_ids))
    
    managers = query.all()
    
    result = []
    for m in managers:
        result.append({
            "管理人编号": m.manager_code,
            "管理人名称": m.manager_name,
            "管理人简称": m.short_name,
            "协会备案编号": m.registration_no,
            "成立日期": str(m.established_date) if m.established_date else "",
            "注册资本(万元)": float(m.registered_capital) if m.registered_capital else "",
            "管理规模": m.aum_range,
            "一级策略": m.primary_strategy.value if m.primary_strategy else "",
            "二级策略": m.secondary_strategy,
            "跟踪池分类": m.pool_category.value if m.pool_category else "",
            "联系人": m.contact_person,
            "联系电话": m.contact_phone,
            "联系邮箱": m.contact_email,
            "备注": m.remark
        })
    
    return result
