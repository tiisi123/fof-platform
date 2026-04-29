"""
净值数据相关API - V2升级版
支持4种格式智能识别、预览、批量导入
"""
from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.nav import (
    NavDataCreate,
    NavDataResponse,
    NavDataListResponse,
    NavDataImportResponse,
    NavDataStatistics
)
from app.services import nav_service

router = APIRouter()


@router.get("", response_model=NavDataListResponse, summary="获取净值数据列表")
async def get_nav_data_list(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    product_id: Optional[int] = Query(None, description="产品ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取净值数据列表
    
    - **skip**: 跳过的记录数（分页）
    - **limit**: 返回的记录数（分页）
    - **product_id**: 按产品ID筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    nav_data, total = nav_service.get_nav_data_list(
        db=db,
        skip=skip,
        limit=limit,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "total": total,
        "items": nav_data
    }


@router.get("/{nav_id}", response_model=NavDataResponse, summary="获取净值数据详情")
async def get_nav_data(
    nav_id: int = Path(..., description="净值数据ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取净值数据详情
    
    - **nav_id**: 净值数据ID
    """
    nav_data = nav_service.get_nav_data_by_id(db, nav_id)
    if not nav_data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"净值数据ID {nav_id} 不存在"
        )
    
    return nav_data


@router.post("", response_model=NavDataResponse, status_code=201, summary="创建净值数据")
async def create_nav_data(
    nav_data: NavDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的净值数据
    
    - **product_id**: 产品ID（必填）
    - **nav_date**: 净值日期（必填）
    - **unit_nav**: 单位净值（必填）
    - **cumulative_nav**: 累计净值（可选）
    """
    return nav_service.create_nav_data(db, nav_data)


@router.delete("/{nav_id}", summary="删除净值数据")
async def delete_nav_data(
    nav_id: int = Path(..., description="净值数据ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除净值数据
    
    - **nav_id**: 净值数据ID
    """
    nav_service.delete_nav_data(db, nav_id)
    return {"message": "净值数据删除成功"}


@router.post("/import", response_model=NavDataImportResponse, summary="导入净值数据")
async def import_nav_data(
    file: UploadFile = File(..., description="Excel文件"),
    product_id: Optional[int] = Form(None, description="产品ID"),
    product_code: Optional[str] = Form(None, description="产品代码"),
    skip_duplicates: bool = Form(True, description="跳过重复数据"),
    update_existing: bool = Form(False, description="更新已存在数据"),
    auto_detect_product: bool = Form(False, description="自动识别产品"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从Excel文件导入净值数据（支持4种格式智能识别）
    
    - **file**: Excel文件（.xls或.xlsx）
    - **product_id**: 产品ID（与product_code二选一）
    - **product_code**: 产品代码（与product_id二选一）
    - **skip_duplicates**: 是否跳过重复数据
    - **update_existing**: 是否更新已存在的数据
    - **auto_detect_product**: 是否从文件中自动识别产品
    
    支持的Excel格式：
    - 格式A: 标题行+数据行（第一行是"产品净值数据"）
    - 格式B: 直接数据行（列名可能带单位）
    - 格式C: 列顺序不同（产品名称在前）
    - 格式D: 中英文双语表头
    """
    # 检查文件类型
    if not file.filename.endswith(('.xls', '.xlsx')):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持.xls和.xlsx格式的Excel文件"
        )
    
    result = nav_service.import_nav_data_from_excel(
        db=db,
        file=file,
        product_id=product_id,
        product_code=product_code,
        skip_duplicates=skip_duplicates,
        update_existing=update_existing,
        auto_detect_product=auto_detect_product
    )
    
    return result


@router.post("/preview", summary="预览净值文件解析结果")
async def preview_nav_file(
    file: UploadFile = File(..., description="Excel文件"),
    preview_rows: int = Form(10, description="预览行数"),
    current_user: User = Depends(get_current_user)
):
    """
    预览净值文件解析结果（不导入数据库）
    
    - **file**: Excel文件（.xls或.xlsx）
    - **preview_rows**: 预览行数（默认10行）
    
    返回信息包括：
    - 识别的文件格式
    - 解析的列名
    - 日期范围
    - 产品代码/名称
    - 预览数据
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持.xls和.xlsx格式的Excel文件"
        )
    
    file_content = await file.read()
    result = nav_service.preview_nav_file(file_content, file.filename, preview_rows)
    
    return result


@router.post("/batch-import", summary="批量导入净值文件")
async def batch_import_nav_files(
    files: List[UploadFile] = File(..., description="Excel文件列表"),
    skip_duplicates: bool = Form(True, description="跳过重复数据"),
    update_existing: bool = Form(False, description="更新已存在数据"),
    auto_detect_product: bool = Form(True, description="自动识别产品"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量导入多个净值文件
    
    - **files**: Excel文件列表
    - **skip_duplicates**: 是否跳过重复数据
    - **update_existing**: 是否更新已存在的数据
    - **auto_detect_product**: 是否从文件中自动识别产品（默认开启）
    
    注意：批量导入时建议开启auto_detect_product，系统会自动从文件中识别产品代码
    """
    # 检查文件类型
    for file in files:
        if not file.filename.endswith(('.xls', '.xlsx')):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件 {file.filename} 格式不支持，只支持.xls和.xlsx格式"
            )
    
    result = nav_service.batch_import_nav_files(
        db=db,
        files=files,
        skip_duplicates=skip_duplicates,
        update_existing=update_existing,
        auto_detect_product=auto_detect_product
    )
    
    return result


@router.get("/statistics/{product_id}", response_model=NavDataStatistics, summary="获取产品净值统计")
async def get_nav_statistics(
    product_id: int = Path(..., description="产品ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取产品净值统计信息
    
    - **product_id**: 产品ID
    
    返回信息包括：
    - 总记录数
    - 日期范围
    - 最新净值
    """
    return nav_service.get_nav_statistics(db, product_id)


# ========== 数据质量 ==========
@router.get("/data-quality/{product_id}", summary="分析净值数据质量")
async def analyze_data_quality(
    product_id: int = Path(..., description="产品ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析产品净值数据质量（重复值、异常值、缺失值、跳跃值检测）"""
    from app.services.data_cleaning_service import DataCleaningService
    service = DataCleaningService(db)
    return service.analyze_data_quality(product_id)


@router.post("/clean/{product_id}", summary="执行数据清洗")
async def clean_nav_data(
    product_id: int = Path(..., description="产品ID"),
    remove_duplicates: bool = Query(True, description="删除重复数据"),
    remove_outliers: bool = Query(False, description="删除异常值"),
    fill_missing: bool = Query(False, description="线性插值填充缺失值"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行净值数据清洗操作"""
    from app.services.data_cleaning_service import DataCleaningService
    service = DataCleaningService(db)
    return service.clean_data(
        product_id=product_id,
        remove_duplicates=remove_duplicates,
        remove_outliers=remove_outliers,
        fill_missing=fill_missing
    )
