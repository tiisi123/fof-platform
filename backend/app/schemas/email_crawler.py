"""
邮箱爬虫 Schema
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EmailTypeEnum(str, Enum):
    QQ = "qq"
    NETEASE_163 = "163"
    NETEASE_126 = "126"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    EXCHANGE = "exchange"
    OTHER = "other"


class ScanStatusEnum(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportStatusEnum(str, Enum):
    PENDING = "pending"
    IMPORTED = "imported"
    SKIPPED = "skipped"
    FAILED = "failed"


# ========== EmailAccount ==========

class EmailAccountBase(BaseModel):
    """邮箱账号基础"""
    email_address: str = Field(..., description="邮箱地址")
    email_type: EmailTypeEnum = Field(default=EmailTypeEnum.OTHER, description="邮箱类型")
    description: Optional[str] = Field(None, description="备注说明")
    imap_server: Optional[str] = Field(None, description="IMAP服务器（不填则使用预设）")
    imap_port: Optional[int] = Field(None, description="IMAP端口")
    use_ssl: bool = Field(default=True, description="是否使用SSL")
    username: str = Field(..., description="登录用户名")
    scan_folder: str = Field(default="INBOX", description="扫描文件夹")
    filter_sender: Optional[str] = Field(None, description="发件人过滤（多个用逗号分隔）")
    filter_subject: Optional[str] = Field(None, description="主题关键词过滤（多个用逗号分隔）")
    scan_days: int = Field(default=7, ge=1, le=365, description="扫描最近N天的邮件")


class EmailAccountCreate(EmailAccountBase):
    """创建邮箱账号"""
    password: str = Field(..., description="邮箱密码/授权码")


class EmailAccountUpdate(BaseModel):
    """更新邮箱账号"""
    email_address: Optional[str] = None
    email_type: Optional[EmailTypeEnum] = None
    description: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    use_ssl: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, description="不填则不更新密码")
    scan_folder: Optional[str] = None
    filter_sender: Optional[str] = None
    filter_subject: Optional[str] = None
    scan_days: Optional[int] = Field(None, ge=1, le=365)
    is_active: Optional[bool] = None


class EmailAccountResponse(BaseModel):
    """邮箱账号响应"""
    id: int
    email_address: str
    email_type: EmailTypeEnum
    description: Optional[str]
    imap_server: str
    imap_port: int
    use_ssl: bool
    username: str
    scan_folder: str
    filter_sender: Optional[str]
    filter_subject: Optional[str]
    scan_days: int
    is_active: bool
    last_scan_at: Optional[datetime]
    last_scan_status: Optional[ScanStatusEnum]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmailAccountListResponse(BaseModel):
    """邮箱账号列表响应"""
    items: List[EmailAccountResponse]
    total: int


# ========== ScanLog ==========

class ScanLogResponse(BaseModel):
    """扫描日志响应"""
    id: int
    email_account_id: int
    scan_start: datetime
    scan_end: Optional[datetime]
    emails_found: int
    attachments_found: int
    parsed_success: int
    parsed_failed: int
    status: ScanStatusEnum
    error_message: Optional[str]
    
    # 额外信息
    email_address: Optional[str] = None  # 关联的邮箱地址
    
    class Config:
        from_attributes = True


class ScanLogListResponse(BaseModel):
    """扫描日志列表响应"""
    items: List[ScanLogResponse]
    total: int


# ========== PendingImport ==========

class PendingImportResponse(BaseModel):
    """待导入数据响应"""
    id: int
    scan_log_id: int
    email_subject: Optional[str]
    email_from: Optional[str]
    email_date: Optional[datetime]
    attachment_name: str
    attachment_size: Optional[int]
    product_code: Optional[str]
    product_name: Optional[str]
    product_id: Optional[int]
    nav_records_count: int
    parse_warnings: Optional[str]
    status: ImportStatusEnum
    import_result: Optional[str]
    imported_at: Optional[datetime]
    created_at: datetime
    
    # 预览数据（前几条净值）
    nav_preview: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class PendingImportListResponse(BaseModel):
    """待导入数据列表响应"""
    items: List[PendingImportResponse]
    total: int


class ImportConfirmRequest(BaseModel):
    """确认导入请求"""
    product_id: int = Field(..., description="目标产品ID")
    conflict_action: str = Field(default="skip", description="冲突处理方式：skip | overwrite")


class ImportResultResponse(BaseModel):
    """导入结果响应"""
    success: bool
    message: str
    imported: int = 0
    skipped: int = 0
    updated: int = 0


# ========== 其他 ==========

class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    success: bool
    message: str


class ImapPresetResponse(BaseModel):
    """IMAP预设配置响应"""
    email_type: EmailTypeEnum
    server: str
    port: int
    ssl: bool
