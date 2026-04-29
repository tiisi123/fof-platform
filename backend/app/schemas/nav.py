"""
净值数据Schema - 数据验证模型
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class NavDataBase(BaseModel):
    """净值数据基础模型"""
    product_id: int = Field(..., description="产品ID", gt=0)
    nav_date: date = Field(..., description="净值日期")
    unit_nav: Decimal = Field(..., description="单位净值", gt=0)
    cumulative_nav: Optional[Decimal] = Field(None, description="累计净值", gt=0)


class NavDataCreate(NavDataBase):
    """创建净值数据"""
    pass


class NavDataBatchCreate(BaseModel):
    """批量创建净值数据"""
    product_id: int = Field(..., description="产品ID", gt=0)
    data: List[dict] = Field(..., description="净值数据列表")


class NavDataUpdate(BaseModel):
    """更新净值数据（所有字段可选）"""
    product_id: Optional[int] = Field(None, description="产品ID", gt=0)
    nav_date: Optional[date] = Field(None, description="净值日期")
    unit_nav: Optional[Decimal] = Field(None, description="单位净值", gt=0)
    cumulative_nav: Optional[Decimal] = Field(None, description="累计净值", gt=0)


class NavDataResponse(NavDataBase):
    """净值数据响应模型"""
    id: int = Field(..., description="净值数据ID")
    # 覆盖父类 Decimal 类型为 float，避免 JSON 序列化为字符串
    unit_nav: float = Field(..., description="单位净值")
    cumulative_nav: Optional[float] = Field(None, description="累计净值")
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


class NavDataListResponse(BaseModel):
    """净值数据列表响应"""
    total: int = Field(..., description="总数")
    items: List[NavDataResponse] = Field(..., description="净值数据列表")


class NavDataImportRequest(BaseModel):
    """净值数据导入请求"""
    product_code: Optional[str] = Field(None, description="产品代码（用于匹配产品）")
    product_id: Optional[int] = Field(None, description="产品ID（直接指定）")
    skip_duplicates: bool = Field(True, description="是否跳过重复数据")
    update_existing: bool = Field(False, description="是否更新已存在的数据")


class NavDataImportResponse(BaseModel):
    """净值数据导入响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    format_detected: Optional[str] = Field(None, description="识别的文件格式")
    total_rows: int = Field(..., description="总行数")
    imported_rows: int = Field(..., description="导入行数")
    updated_rows: Optional[int] = Field(0, description="更新行数")
    skipped_rows: int = Field(..., description="跳过行数")
    error_rows: int = Field(..., description="错误行数")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息列表")
    date_range: Optional[dict] = Field(None, description="日期范围")
    saved_file: Optional[str] = Field(None, description="保存的文件路径")


class NavPreviewItem(BaseModel):
    """净值预览数据项"""
    nav_date: Optional[str] = Field(None, description="净值日期")
    unit_nav: Optional[float] = Field(None, description="单位净值")
    cumulative_nav: Optional[float] = Field(None, description="累计净值")
    product_code: Optional[str] = Field(None, description="产品代码")
    product_name: Optional[str] = Field(None, description="产品名称")


class NavPreviewResponse(BaseModel):
    """净值文件预览响应"""
    success: bool = Field(..., description="是否成功")
    format_detected: Optional[str] = Field(None, description="识别的文件格式")
    total_rows: Optional[int] = Field(None, description="总行数")
    columns: List[str] = Field(default_factory=list, description="列名列表")
    date_range: Optional[dict] = Field(None, description="日期范围")
    product_codes: List[str] = Field(default_factory=list, description="产品代码列表")
    product_names: List[str] = Field(default_factory=list, description="产品名称列表")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    preview_data: List[NavPreviewItem] = Field(default_factory=list, description="预览数据")


class BatchImportResult(BaseModel):
    """单个文件导入结果"""
    filename: str = Field(..., description="文件名")
    success: bool = Field(..., description="是否成功")
    imported_rows: int = Field(..., description="导入行数")
    message: str = Field(..., description="消息")


class BatchImportResponse(BaseModel):
    """批量导入响应"""
    success: bool = Field(..., description="是否全部成功")
    total_files: int = Field(..., description="总文件数")
    successful_files: int = Field(..., description="成功文件数")
    failed_files: int = Field(..., description="失败文件数")
    total_imported_rows: int = Field(..., description="总导入行数")
    results: List[BatchImportResult] = Field(default_factory=list, description="各文件导入结果")


class NavDataStatistics(BaseModel):
    """净值数据统计"""
    product_id: int = Field(..., description="产品ID")
    product_name: str = Field(..., description="产品名称")
    total_records: int = Field(..., description="总记录数")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    latest_unit_nav: Optional[Decimal] = Field(None, description="最新单位净值")
    latest_cumulative_nav: Optional[Decimal] = Field(None, description="最新累计净值")
    latest_nav_date: Optional[date] = Field(None, description="最新净值日期")
