"""
产品相关API
"""
from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.services import product_service

router = APIRouter()


@router.get("", response_model=ProductListResponse, summary="获取产品列表")
async def get_products(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词（名称或代码）"),
    manager_id: Optional[int] = Query(None, description="管理人ID"),
    strategy_type: Optional[str] = Query(None, description="策略类型"),
    status: Optional[str] = Query(None, description="状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品列表
    
    - **skip**: 跳过的记录数（分页）
    - **limit**: 返回的记录数（分页）
    - **search**: 搜索关键词，支持产品名称和代码
    - **manager_id**: 按管理人ID筛选
    - **strategy_type**: 按策略类型筛选
    - **status**: 按状态筛选
    """
    products, total = product_service.get_products(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        manager_id=manager_id,
        strategy_type=strategy_type,
        status=status
    )
    
    return {
        "total": total,
        "items": products
    }


@router.get("/{product_id}", response_model=ProductResponse, summary="获取产品详情")
async def get_product(
    product_id: int = Path(..., description="产品ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取产品详情
    
    - **product_id**: 产品ID
    """
    product = product_service.get_product_by_id(db, product_id)
    if not product:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品ID {product_id} 不存在"
        )
    
    return product


@router.post("", response_model=ProductResponse, status_code=201, summary="创建产品")
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的产品
    
    - **product_code**: 产品代码（必填，唯一）
    - **product_name**: 产品名称（必填）
    - **manager_id**: 管理人ID（必填）
    - 其他字段可选
    """
    return product_service.create_product(db, product)


@router.put("/{product_id}", response_model=ProductResponse, summary="更新产品")
async def update_product(
    product_id: int = Path(..., description="产品ID"),
    product_update: ProductUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新产品信息
    
    - **product_id**: 产品ID
    - 只需提供要更新的字段
    """
    return product_service.update_product(db, product_id, product_update)


@router.delete("/{product_id}", summary="删除产品")
async def delete_product(
    product_id: int = Path(..., description="产品ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除产品（软删除）
    
    - **product_id**: 产品ID
    """
    product_service.delete_product(db, product_id)
    return {"message": "产品删除成功"}


@router.get("/statistics/summary", summary="获取产品统计信息")
async def get_product_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品统计信息
    
    包括：
    - 总数
    - 运行中/已清盘/暂停数量
    - 按策略类型统计
    - 按管理人统计
    """
    return product_service.get_product_statistics(db)


@router.post("/import", summary="批量导入产品")
async def import_products(
    file: UploadFile = File(..., description="Excel文件"),
    skip_duplicates: bool = Form(True, description="跳过重复数据"),
    update_existing: bool = Form(False, description="更新已存在数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从Excel文件批量导入产品
    
    - **file**: Excel文件（.xls或.xlsx）
    - **skip_duplicates**: 是否跳过重复数据
    - **update_existing**: 是否更新已存在的数据
    
    支持的Excel格式：
    - 必需列：产品代码、产品名称
    - 可选列：管理人代码、管理人名称、策略类型、成立日期、清盘日期、管理费率、业绩报酬、基准代码、基准名称、备注
    """
    # 检查文件类型
    if not file.filename.endswith(('.xls', '.xlsx')):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持.xls和.xlsx格式的Excel文件"
        )
    
    result = await product_service.import_products_from_excel(
        db=db,
        file=file,
        skip_duplicates=skip_duplicates,
        update_existing=update_existing
    )
    
    return result
