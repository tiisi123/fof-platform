"""
产品Schema - 数据验证模型
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """产品基础模型"""
    product_name: str = Field(..., description="产品名称", min_length=1, max_length=200)
    manager_id: int = Field(..., description="管理人ID", gt=0)
    strategy_type: Optional[str] = Field(None, description="策略类型", max_length=50)
    established_date: Optional[date] = Field(None, description="成立日期")
    liquidation_date: Optional[date] = Field(None, description="清盘日期")
    management_fee: Optional[Decimal] = Field(None, description="管理费率(%)", ge=0, le=100)
    performance_fee: Optional[Decimal] = Field(None, description="业绩报酬(%)", ge=0, le=100)
    benchmark_code: Optional[str] = Field(None, description="基准代码", max_length=50)
    benchmark_name: Optional[str] = Field(None, description="基准名称", max_length=100)
    is_invested: Optional[bool] = Field(None, description="是否在投")
    remark: Optional[str] = Field(None, description="备注", max_length=1000)


class ProductCreate(ProductBase):
    """创建产品"""
    product_code: str = Field(..., description="产品代码", min_length=1, max_length=50)


class ProductUpdate(BaseModel):
    """更新产品（所有字段可选）"""
    product_name: Optional[str] = Field(None, description="产品名称", min_length=1, max_length=200)
    manager_id: Optional[int] = Field(None, description="管理人ID", gt=0)
    strategy_type: Optional[str] = Field(None, description="策略类型", max_length=50)
    established_date: Optional[date] = Field(None, description="成立日期")
    liquidation_date: Optional[date] = Field(None, description="清盘日期")
    management_fee: Optional[Decimal] = Field(None, description="管理费率(%)", ge=0, le=100)
    performance_fee: Optional[Decimal] = Field(None, description="业绩报酬(%)", ge=0, le=100)
    benchmark_code: Optional[str] = Field(None, description="基准代码", max_length=50)
    benchmark_name: Optional[str] = Field(None, description="基准名称", max_length=100)
    is_invested: Optional[bool] = Field(None, description="是否在投")
    remark: Optional[str] = Field(None, description="备注", max_length=1000)
    status: Optional[str] = Field(None, description="状态")


class ProductResponse(ProductBase):
    """产品响应模型"""
    id: int = Field(..., description="产品ID")
    product_code: str = Field(..., description="产品代码")
    status: str = Field(..., description="状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime], _info):
        """序列化datetime为字符串"""
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """产品列表响应"""
    total: int = Field(..., description="总数")
    items: list[ProductResponse] = Field(..., description="产品列表")
