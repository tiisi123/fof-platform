"""
尽调资料服务
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.document import Document, DocumentCategory, DocumentRelationType
from app.core.config import settings

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    # 文档
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv',
    # 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    # 压缩包
    '.zip', '.rar', '.7z'
}

# MIME类型映射
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp',
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed',
    '.7z': 'application/x-7z-compressed'
}

# 上传目录
UPLOAD_DIR = Path(settings.UPLOAD_DIR if hasattr(settings, 'UPLOAD_DIR') else './uploads/documents')


class DocumentService:
    """尽调资料服务"""
    
    def __init__(self, db: Session):
        self.db = db
        # 确保上传目录存在
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    def _generate_storage_path(self, filename: str) -> str:
        """生成存储路径"""
        ext = Path(filename).suffix.lower()
        # 按年月组织目录
        date_dir = datetime.now().strftime('%Y/%m')
        # 生成唯一文件名
        unique_name = f"{uuid.uuid4().hex}{ext}"
        
        # 创建目录
        full_dir = UPLOAD_DIR / date_dir
        full_dir.mkdir(parents=True, exist_ok=True)
        
        return f"{date_dir}/{unique_name}"
    
    def _get_file_type(self, filename: str) -> str:
        """获取文件类型"""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        ext = Path(filename).suffix.lower()
        return MIME_TYPES.get(ext, 'application/octet-stream')
    
    def _is_allowed_file(self, filename: str) -> bool:
        """检查文件是否允许上传"""
        ext = Path(filename).suffix.lower()
        return ext in ALLOWED_EXTENSIONS
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: int,
        category: DocumentCategory = DocumentCategory.OTHER,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        relation_type: Optional[DocumentRelationType] = None,
        relation_id: Optional[int] = None
    ) -> Document:
        """
        上传文件
        
        Args:
            file_content: 文件内容
            filename: 原始文件名
            user_id: 上传人ID
            category: 资料分类
            title: 资料标题
            description: 资料描述
            tags: 标签
            relation_type: 关联类型
            relation_id: 关联ID
        
        Returns:
            创建的文档对象
        """
        # 检查文件类型
        if not self._is_allowed_file(filename):
            raise ValueError(f"不支持的文件类型: {Path(filename).suffix}")
        
        # 生成存储路径
        storage_path = self._generate_storage_path(filename)
        full_path = UPLOAD_DIR / storage_path
        
        # 保存文件
        with open(full_path, 'wb') as f:
            f.write(file_content)
        
        # 创建数据库记录
        document = Document(
            filename=filename,
            storage_path=storage_path,
            file_size=len(file_content),
            file_type=self._get_file_type(filename),
            mime_type=self._get_mime_type(filename),
            category=category,
            title=title or filename,
            description=description,
            tags=tags,
            relation_type=relation_type,
            relation_id=relation_id,
            uploaded_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """获取文档"""
        return self.db.query(Document).filter(Document.id == doc_id).first()
    
    def get_document_path(self, doc_id: int) -> Optional[Path]:
        """获取文档的完整路径"""
        doc = self.get_document(doc_id)
        if doc:
            return UPLOAD_DIR / doc.storage_path
        return None
    
    def list_documents(
        self,
        category: Optional[DocumentCategory] = None,
        relation_type: Optional[DocumentRelationType] = None,
        relation_id: Optional[int] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Document], int]:
        """
        获取文档列表
        
        Args:
            category: 资料分类
            relation_type: 关联类型
            relation_id: 关联ID
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量
        
        Returns:
            (文档列表, 总数)
        """
        query = self.db.query(Document)
        
        if category:
            query = query.filter(Document.category == category)
        
        if relation_type:
            query = query.filter(Document.relation_type == relation_type)
        
        if relation_id:
            query = query.filter(Document.relation_id == relation_id)
        
        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                or_(
                    Document.filename.ilike(keyword_filter),
                    Document.title.ilike(keyword_filter),
                    Document.description.ilike(keyword_filter),
                    Document.tags.ilike(keyword_filter)
                )
            )
        
        total = query.count()
        items = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    def update_document(
        self,
        doc_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[DocumentCategory] = None,
        tags: Optional[str] = None,
        relation_type: Optional[DocumentRelationType] = None,
        relation_id: Optional[int] = None
    ) -> Optional[Document]:
        """更新文档信息"""
        doc = self.get_document(doc_id)
        if not doc:
            return None
        
        if title is not None:
            doc.title = title
        if description is not None:
            doc.description = description
        if category is not None:
            doc.category = category
        if tags is not None:
            doc.tags = tags
        if relation_type is not None:
            doc.relation_type = relation_type
        if relation_id is not None:
            doc.relation_id = relation_id
        
        self.db.commit()
        self.db.refresh(doc)
        
        return doc
    
    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        
        # 删除文件
        file_path = UPLOAD_DIR / doc.storage_path
        if file_path.exists():
            file_path.unlink()
        
        # 删除数据库记录
        self.db.delete(doc)
        self.db.commit()
        
        return True
    
    def get_relation_documents(
        self,
        relation_type: DocumentRelationType,
        relation_id: int
    ) -> List[Document]:
        """获取关联的所有文档"""
        return self.db.query(Document).filter(
            and_(
                Document.relation_type == relation_type,
                Document.relation_id == relation_id
            )
        ).order_by(Document.uploaded_at.desc()).all()
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        from sqlalchemy import func
        
        total_count = self.db.query(func.count(Document.id)).scalar()
        total_size = self.db.query(func.sum(Document.file_size)).scalar() or 0
        
        # 按分类统计
        category_stats = self.db.query(
            Document.category,
            func.count(Document.id)
        ).group_by(Document.category).all()
        
        # 按文件类型统计
        type_stats = self.db.query(
            Document.file_type,
            func.count(Document.id)
        ).group_by(Document.file_type).all()
        
        return {
            "total_count": total_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_category": {str(cat): count for cat, count in category_stats},
            "by_type": {t: count for t, count in type_stats if t}
        }
