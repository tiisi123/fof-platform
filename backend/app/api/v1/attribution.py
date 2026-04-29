"""
Barra多因子归因分析 API
"""
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import pandas as pd
import io

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.attribution_service import AttributionService

router = APIRouter(prefix="/attribution", tags=["因子归因"])


@router.get("/product/{product_id}", summary="获取产品因子归因分析")
async def get_product_attribution(
    product_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    对指定产品进行Barra多因子归因分析
    
    返回内容包括：
    - 因子暴露：市场、规模、价值、动量、波动率、质量、成长、流动性
    - 回归统计：R²、Alpha、跟踪误差等
    - 业绩归因：各因子贡献、Alpha贡献
    - 累计归因走势数据
    - 风格摘要和标签
    """
    service = AttributionService(db)
    result = service.analyze_product(product_id, start_date, end_date)
    
    if "error" in result and result.get("error") == "产品不存在":
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/factors", summary="获取因子列表")
async def get_factor_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有可用的因子及其说明
    
    因子包括：
    - market: 市场因子
    - size: 规模因子
    - value: 价值因子
    - momentum: 动量因子
    - volatility: 波动率因子
    - quality: 质量因子
    - growth: 成长因子
    - liquidity: 流动性因子
    """
    service = AttributionService(db)
    return service.get_factor_list()


@router.get("/compare", summary="比较多个产品的因子暴露")
async def compare_products_attribution(
    product_ids: str = Query(..., description="产品ID列表，逗号分隔"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    比较多个产品的因子暴露情况
    
    用于分析不同产品之间的风格差异
    """
    try:
        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的产品ID格式")
    
    if len(ids) < 1:
        raise HTTPException(status_code=400, detail="至少需要一个产品")
    if len(ids) > 10:
        raise HTTPException(status_code=400, detail="最多比较10个产品")
    
    service = AttributionService(db)
    return service.compare_products(ids, start_date, end_date)


@router.post("/import-factors", summary="导入因子数据")
async def import_factor_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导入Barra因子收益率数据（Excel/CSV格式）
    
    格式要求：
    - 列: 日期(date) | 因子代码(factor_code) | 因子收益率(factor_return)
    """
    content = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
    
    # 列名映射
    col_map = {
        '日期': 'date', '因子代码': 'factor_code', '因子收益率': 'factor_return',
        'date': 'date', 'factor_code': 'factor_code', 'factor_return': 'factor_return',
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)
    
    required = {'date', 'factor_code', 'factor_return'}
    if not required.issubset(set(df.columns)):
        raise HTTPException(status_code=400, detail=f"缺少必要列: {required - set(df.columns)}")
    
    count = len(df)
    # TODO: 将数据存储到 factor_returns 表（待创建）
    # 当前作为预留接口，返回成功信息
    
    return {
        "message": f"已解析{count}条因子数据记录",
        "count": count,
        "factors": df['factor_code'].unique().tolist() if 'factor_code' in df.columns else [],
        "date_range": {
            "start": str(df['date'].min()) if 'date' in df.columns else None,
            "end": str(df['date'].max()) if 'date' in df.columns else None,
        }
    }
