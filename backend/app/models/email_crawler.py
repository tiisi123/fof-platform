"""
邮箱爬虫数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class EmailType(str, enum.Enum):
    """邮箱类型"""
    QQ = "qq"
    NETEASE_163 = "163"
    NETEASE_126 = "126"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    EXCHANGE = "exchange"
    OTHER = "other"


class ScanStatus(str, enum.Enum):
    """扫描状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportStatus(str, enum.Enum):
    """导入状态"""
    PENDING = "pending"
    IMPORTED = "imported"
    SKIPPED = "skipped"
    FAILED = "failed"


class EmailAccount(Base):
    """邮箱账号配置"""
    __tablename__ = "email_accounts"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    
    # 邮箱基本信息
    email_address = Column(String(255), unique=True, nullable=False, comment="邮箱地址")
    email_type = Column(Enum(EmailType), nullable=False, default=EmailType.OTHER, comment="邮箱类型")
    description = Column(String(255), comment="备注说明")
    
    # IMAP配置
    imap_server = Column(String(255), nullable=False, comment="IMAP服务器")
    imap_port = Column(Integer, nullable=False, default=993, comment="IMAP端口")
    use_ssl = Column(Boolean, nullable=False, default=True, comment="是否使用SSL")
    
    # 认证信息
    username = Column(String(255), nullable=False, comment="登录用户名")
    password_encrypted = Column(String(512), nullable=False, comment="加密后的密码/授权码")
    
    # 扫描配置
    scan_folder = Column(String(100), nullable=False, default="INBOX", comment="扫描文件夹")
    filter_sender = Column(String(500), comment="发件人过滤（多个用逗号分隔）")
    filter_subject = Column(String(500), comment="主题关键词过滤（多个用逗号分隔）")
    scan_days = Column(Integer, nullable=False, default=7, comment="扫描最近N天的邮件")
    
    # 状态
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    last_scan_at = Column(DateTime, comment="最后扫描时间")
    last_scan_status = Column(Enum(ScanStatus), comment="最后扫描状态")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联
    scan_logs = relationship("ScanLog", back_populates="email_account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmailAccount(id={self.id}, email='{self.email_address}')>"


class ScanLog(Base):
    """扫描日志"""
    __tablename__ = "email_scan_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    email_account_id = Column(Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, comment="邮箱账号ID")
    
    # 扫描时间
    scan_start = Column(DateTime, nullable=False, server_default=func.now(), comment="扫描开始时间")
    scan_end = Column(DateTime, comment="扫描结束时间")
    
    # 扫描结果统计
    emails_found = Column(Integer, default=0, comment="发现邮件数")
    attachments_found = Column(Integer, default=0, comment="发现附件数")
    parsed_success = Column(Integer, default=0, comment="解析成功数")
    parsed_failed = Column(Integer, default=0, comment="解析失败数")
    
    # 状态
    status = Column(Enum(ScanStatus), nullable=False, default=ScanStatus.RUNNING, comment="扫描状态")
    error_message = Column(Text, comment="错误信息")
    
    # 关联
    email_account = relationship("EmailAccount", back_populates="scan_logs")
    pending_imports = relationship("PendingImport", back_populates="scan_log", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScanLog(id={self.id}, status='{self.status}')>"


class PendingImport(Base):
    """待确认导入的数据"""
    __tablename__ = "email_pending_imports"
    
    id = Column(Integer, primary_key=True, index=True, comment="ID")
    scan_log_id = Column(Integer, ForeignKey("email_scan_logs.id", ondelete="CASCADE"), nullable=False, comment="扫描日志ID")
    
    # 邮件信息
    email_subject = Column(String(500), comment="邮件主题")
    email_from = Column(String(255), comment="发件人")
    email_date = Column(DateTime, comment="邮件日期")
    email_uid = Column(String(100), comment="邮件UID（用于去重）")
    
    # 附件信息
    attachment_name = Column(String(255), nullable=False, comment="附件文件名")
    attachment_size = Column(Integer, comment="附件大小(字节)")
    
    # 解析结果
    product_code = Column(String(50), comment="解析出的产品代码")
    product_name = Column(String(255), comment="解析出的产品名称")
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), comment="匹配到的产品ID")
    nav_records_count = Column(Integer, default=0, comment="净值记录数")
    nav_data_json = Column(JSON, comment="解析的净值数据JSON")
    parse_warnings = Column(Text, comment="解析警告信息")
    
    # 状态
    status = Column(Enum(ImportStatus), nullable=False, default=ImportStatus.PENDING, comment="导入状态")
    import_result = Column(Text, comment="导入结果说明")
    imported_at = Column(DateTime, comment="导入时间")
    imported_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), comment="导入操作人")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联
    scan_log = relationship("ScanLog", back_populates="pending_imports")
    
    def __repr__(self):
        return f"<PendingImport(id={self.id}, attachment='{self.attachment_name}', status='{self.status}')>"
