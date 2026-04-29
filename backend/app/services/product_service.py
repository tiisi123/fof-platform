"""
产品Service - 业务逻辑层
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from fastapi import HTTPException, status, UploadFile
import pandas as pd
from datetime import datetime
import io

from app.models.product import Product, ProductStatus
from app.models.manager import Manager
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    manager_id: Optional[int] = None,
    strategy_type: Optional[str] = None,
    status: Optional[str] = None
) -> tuple[List[Product], int]:
    """
    获取产品列表
    
    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        search: 搜索关键词（产品名称或代码）
        manager_id: 管理人ID筛选
        strategy_type: 策略类型筛选
        status: 状态筛选
    
    Returns:
        (产品列表, 总数)
    """
    query = db.query(Product)
    
    # 搜索过滤
    if search:
        query = query.filter(
            (Product.product_name.like(f"%{search}%")) |
            (Product.product_code.like(f"%{search}%"))
        )
    
    # 管理人过滤
    if manager_id:
        query = query.filter(Product.manager_id == manager_id)
    
    # 策略类型过滤
    if strategy_type:
        query = query.filter(Product.strategy_type == strategy_type)
    
    # 状态过滤 - 支持中英文
    if status:
        status_map = {
            '运行中': 'active',
            '已清盘': 'liquidated', 
            '暂停': 'suspended'
        }
        status_value = status_map.get(status, status)
        query = query.filter(Product.status == status_value)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    
    return products, total


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """
    根据ID获取产品
    
    Args:
        db: 数据库会话
        product_id: 产品ID
    
    Returns:
        产品对象或None
    """
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_code(db: Session, product_code: str) -> Optional[Product]:
    """
    根据代码获取产品
    
    Args:
        db: 数据库会话
        product_code: 产品代码
    
    Returns:
        产品对象或None
    """
    return db.query(Product).filter(Product.product_code == product_code).first()


def create_product(db: Session, product: ProductCreate) -> Product:
    """
    创建产品
    
    Args:
        db: 数据库会话
        product: 产品创建数据
    
    Returns:
        创建的产品对象
    
    Raises:
        HTTPException: 如果产品代码已存在或管理人不存在
    """
    # 检查代码是否已存在
    existing = get_product_by_code(db, product.product_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产品代码 {product.product_code} 已存在"
        )
    
    # 检查管理人是否存在
    from app.models.manager import Manager
    manager = db.query(Manager).filter(Manager.id == product.manager_id).first()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"管理人ID {product.manager_id} 不存在"
        )
    
    # 创建产品对象
    db_product = Product(
        product_code=product.product_code,
        product_name=product.product_name,
        manager_id=product.manager_id,
        strategy_type=product.strategy_type,
        established_date=product.established_date,
        liquidation_date=product.liquidation_date,
        management_fee=product.management_fee,
        performance_fee=product.performance_fee,
        benchmark_code=product.benchmark_code,
        benchmark_name=product.benchmark_name,
        is_invested=product.is_invested if product.is_invested is not None else False,
        status=ProductStatus.ACTIVE,
        remark=product.remark
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product


def update_product(
    db: Session,
    product_id: int,
    product_update: ProductUpdate
) -> Product:
    """
    更新产品
    
    Args:
        db: 数据库会话
        product_id: 产品ID
        product_update: 更新数据
    
    Returns:
        更新后的产品对象
    
    Raises:
        HTTPException: 如果产品不存在或管理人不存在
    """
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品ID {product_id} 不存在"
        )
    
    # 如果更新管理人ID，检查管理人是否存在
    update_data = product_update.model_dump(exclude_unset=True)
    if 'manager_id' in update_data:
        from app.models.manager import Manager
        manager = db.query(Manager).filter(Manager.id == update_data['manager_id']).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"管理人ID {update_data['manager_id']} 不存在"
            )
    
    # 更新字段（只更新提供的字段）
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    """
    删除产品（软删除，设置状态为liquidated）
    
    Args:
        db: 数据库会话
        product_id: 产品ID
    
    Returns:
        是否删除成功
    
    Raises:
        HTTPException: 如果产品不存在
    """
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品ID {product_id} 不存在"
        )
    
    # 软删除：设置状态为liquidated
    db_product.status = ProductStatus.LIQUIDATED
    db.commit()
    
    return True


def get_product_statistics(db: Session) -> dict:
    """
    获取产品统计信息
    
    Args:
        db: 数据库会话
    
    Returns:
        统计信息字典
    """
    total = db.query(Product).count()
    active = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
    liquidated = db.query(Product).filter(Product.status == ProductStatus.LIQUIDATED).count()
    
    # 按策略类型统计
    strategy_stats = db.query(
        Product.strategy_type,
        func.count(Product.id)
    ).group_by(Product.strategy_type).all()
    
    # 按管理人统计
    manager_stats = db.query(
        Product.manager_id,
        func.count(Product.id)
    ).group_by(Product.manager_id).all()
    
    return {
        "total": total,
        "active": active,
        "liquidated": liquidated,
        "suspended": total - active - liquidated,
        "by_strategy": {strategy: count for strategy, count in strategy_stats if strategy},
        "by_manager": {manager_id: count for manager_id, count in manager_stats}
    }


async def import_products_from_excel(
    db: Session,
    file: UploadFile,
    skip_duplicates: bool = True,
    update_existing: bool = False
) -> dict:
    """
    从Excel文件批量导入产品
    
    Args:
        db: 数据库会话
        file: 上传的Excel文件
        skip_duplicates: 是否跳过重复数据
        update_existing: 是否更新已存在的数据
    
    Returns:
        导入结果字典
    """
    try:
        # 读取Excel文件
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 验证必需列
        required_columns = ['产品代码', '产品名称']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel文件缺少必需列: {', '.join(missing_columns)}"
            )
        
        # 统计信息
        total_rows = len(df)
        imported_rows = 0
        skipped_rows = 0
        error_rows = 0
        errors = []
        
        # 获取或创建管理人的缓存
        manager_cache = {}
        
        # 逐行处理
        for index, row in df.iterrows():
            try:
                product_code = str(row['产品代码']).strip()
                product_name = str(row['产品名称']).strip()
                
                # 跳过空行
                if not product_code or not product_name or product_code == 'nan' or product_name == 'nan':
                    skipped_rows += 1
                    continue
                
                # 检查产品是否已存在
                existing_product = get_product_by_code(db, product_code)
                
                if existing_product:
                    if skip_duplicates and not update_existing:
                        skipped_rows += 1
                        continue
                    elif update_existing:
                        # 更新现有产品
                        _update_product_from_row(db, existing_product, row, manager_cache)
                        imported_rows += 1
                        continue
                
                # 创建新产品
                _create_product_from_row(db, row, manager_cache)
                imported_rows += 1
                
            except Exception as e:
                error_rows += 1
                errors.append(f"第{index + 2}行: {str(e)}")
                if len(errors) >= 100:  # 限制错误数量
                    errors.append("... (更多错误已省略)")
                    break
        
        # 提交事务
        db.commit()
        
        return {
            "success": True,
            "message": f"成功导入 {imported_rows} 条产品数据",
            "total_rows": total_rows,
            "imported_rows": imported_rows,
            "skipped_rows": skipped_rows,
            "error_rows": error_rows,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


def _get_or_create_manager(
    db: Session,
    manager_code: str,
    manager_name: str,
    manager_cache: dict
) -> int:
    """
    获取或创建管理人
    
    Args:
        db: 数据库会话
        manager_code: 管理人代码
        manager_name: 管理人名称
        manager_cache: 管理人缓存字典
    
    Returns:
        管理人ID
    """
    # 检查缓存
    cache_key = f"{manager_code}_{manager_name}"
    if cache_key in manager_cache:
        return manager_cache[cache_key]
    
    # 查找现有管理人
    manager = db.query(Manager).filter(Manager.manager_code == manager_code).first()
    
    if not manager:
        # 创建新管理人
        manager = Manager(
            manager_code=manager_code,
            manager_name=manager_name,
            status='active'
        )
        db.add(manager)
        db.flush()  # 获取ID但不提交
    
    # 缓存管理人ID
    manager_cache[cache_key] = manager.id
    return manager.id


def _create_product_from_row(
    db: Session,
    row: pd.Series,
    manager_cache: dict
) -> Product:
    """
    从Excel行创建产品
    
    Args:
        db: 数据库会话
        row: Excel行数据
        manager_cache: 管理人缓存
    
    Returns:
        创建的产品对象
    """
    product_code = str(row['产品代码']).strip()
    product_name = str(row['产品名称']).strip()
    
    # 获取或创建管理人
    manager_code = str(row.get('管理人代码', product_code)).strip()
    manager_name = str(row.get('管理人名称', '未知管理人')).strip()
    manager_id = _get_or_create_manager(db, manager_code, manager_name, manager_cache)
    
    # 解析日期
    established_date = None
    if '成立日期' in row and pd.notna(row['成立日期']):
        try:
            established_date = pd.to_datetime(row['成立日期']).date()
        except:
            pass
    
    liquidation_date = None
    if '清盘日期' in row and pd.notna(row['清盘日期']):
        try:
            liquidation_date = pd.to_datetime(row['清盘日期']).date()
        except:
            pass
    
    # 解析费率
    management_fee = None
    if '管理费率' in row and pd.notna(row['管理费率']):
        try:
            management_fee = float(row['管理费率'])
        except:
            pass
    
    performance_fee = None
    if '业绩报酬' in row and pd.notna(row['业绩报酬']):
        try:
            performance_fee = float(row['业绩报酬'])
        except:
            pass
    
    # 获取其他字段
    strategy_type = str(row.get('策略类型', '')).strip() if pd.notna(row.get('策略类型')) else None
    benchmark_code = str(row.get('基准代码', '')).strip() if pd.notna(row.get('基准代码')) else None
    benchmark_name = str(row.get('基准名称', '')).strip() if pd.notna(row.get('基准名称')) else None
    remark = str(row.get('备注', '')).strip() if pd.notna(row.get('备注')) else None
    
    # 根据运作状态设置产品状态
    status_value = ProductStatus.ACTIVE
    if '运作状态' in row and pd.notna(row['运作状态']):
        status_str = str(row['运作状态']).strip()
        if '清算' in status_str or '清盘' in status_str:
            status_value = ProductStatus.LIQUIDATED
        elif '暂停' in status_str or '注销' in status_str:
            status_value = ProductStatus.SUSPENDED
    
    # 创建产品
    product = Product(
        product_code=product_code,
        product_name=product_name,
        manager_id=manager_id,
        strategy_type=strategy_type,
        established_date=established_date,
        liquidation_date=liquidation_date,
        management_fee=management_fee,
        performance_fee=performance_fee,
        benchmark_code=benchmark_code,
        benchmark_name=benchmark_name,
        status=status_value,
        remark=remark
    )
    
    db.add(product)
    db.flush()
    
    return product


def _update_product_from_row(
    db: Session,
    product: Product,
    row: pd.Series,
    manager_cache: dict
) -> Product:
    """
    从Excel行更新产品
    
    Args:
        db: 数据库会话
        product: 现有产品对象
        row: Excel行数据
        manager_cache: 管理人缓存
    
    Returns:
        更新后的产品对象
    """
    # 更新产品名称
    if '产品名称' in row and pd.notna(row['产品名称']):
        product.product_name = str(row['产品名称']).strip()
    
    # 更新管理人
    if '管理人代码' in row and pd.notna(row['管理人代码']):
        manager_code = str(row['管理人代码']).strip()
        manager_name = str(row.get('管理人名称', '未知管理人')).strip()
        product.manager_id = _get_or_create_manager(db, manager_code, manager_name, manager_cache)
    
    # 更新其他字段
    if '策略类型' in row and pd.notna(row['策略类型']):
        product.strategy_type = str(row['策略类型']).strip()
    
    if '成立日期' in row and pd.notna(row['成立日期']):
        try:
            product.established_date = pd.to_datetime(row['成立日期']).date()
        except:
            pass
    
    if '清盘日期' in row and pd.notna(row['清盘日期']):
        try:
            product.liquidation_date = pd.to_datetime(row['清盘日期']).date()
        except:
            pass
    
    if '管理费率' in row and pd.notna(row['管理费率']):
        try:
            product.management_fee = float(row['管理费率'])
        except:
            pass
    
    if '业绩报酬' in row and pd.notna(row['业绩报酬']):
        try:
            product.performance_fee = float(row['业绩报酬'])
        except:
            pass
    
    if '基准代码' in row and pd.notna(row['基准代码']):
        product.benchmark_code = str(row['基准代码']).strip()
    
    if '基准名称' in row and pd.notna(row['基准名称']):
        product.benchmark_name = str(row['基准名称']).strip()
    
    if '备注' in row and pd.notna(row['备注']):
        product.remark = str(row['备注']).strip()
    
    # 更新状态
    if '运作状态' in row and pd.notna(row['运作状态']):
        status_str = str(row['运作状态']).strip()
        if '清算' in status_str or '清盘' in status_str:
            product.status = ProductStatus.LIQUIDATED
        elif '暂停' in status_str or '注销' in status_str:
            product.status = ProductStatus.SUSPENDED
        else:
            product.status = ProductStatus.ACTIVE
    
    db.flush()
    
    return product
