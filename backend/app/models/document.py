"""
尽调资料模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class DocumentCategory(str, enum.Enum):
    """资料分类"""
    DD_REPORT = "dd_report"           # 尽调报告
    LEGAL = "legal"                   # 法律文件
    FINANCIAL = "financial"           # 财务资料
    CONTRACT = "contract"             # 合同协议
    PRESENTATION = "presentation"     # 路演材料
    MEETING = "meeting"               # 会议纪要
    OTHER = "other"                   # 其他


class DocumentRelationType(str, enum.Enum):
    """关联类型"""
    MANAGER = "manager"       # 关联管理人
    PRODUCT = "product"       # 关联产品
    PROJECT = "project"       # 关联一级项目


class Document(Base):
    """尽调资料"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 文件信息
    filename = Column(String(255), nullable=False, comment="原始文件名")
    storage_path = Column(String(500), nullable=False, comment="存储路径")
    file_size = Column(BigInteger, default=0, comment="文件大小(字节)")
    file_type = Column(String(50), comment="文件类型(扩展名)")
    mime_type = Column(String(100), comment="MIME类型")
    
    # 分类和描述
    category = Column(Enum(DocumentCategory), default=DocumentCategory.OTHER, comment="资料分类")
    title = Column(String(255), comment="资料标题")
    description = Column(Text, comment="资料描述")
    tags = Column(String(500), comment="标签,逗号分隔")
    
    # 关联信息
    relation_type = Column(Enum(DocumentRelationType), comment="关联类型")
    relation_id = Column(Integer, comment="关联ID")
    
    # 上传信息
    uploaded_by = Column(Integer, ForeignKey("users.id"), comment="上传人ID")
    uploaded_at = Column(DateTime, server_default=func.now(), comment="上传时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    uploader = relationship("User", backref="uploaded_documents")
    
    def __repr__(self):
        return f"<Document {self.filename}>"
