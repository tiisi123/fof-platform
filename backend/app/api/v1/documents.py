"""
尽调资料 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
import mimetypes

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.document import DocumentCategory, DocumentRelationType
from app.services.document_service import DocumentService, UPLOAD_DIR

router = APIRouter(prefix="/documents", tags=["尽调资料"])


# ========== Pydantic Schemas ==========

class CategoryEnum(str, Enum):
    dd_report = "dd_report"
    legal = "legal"
    financial = "financial"
    contract = "contract"
    presentation = "presentation"
    meeting = "meeting"
    other = "other"


class RelationTypeEnum(str, Enum):
    manager = "manager"
    product = "product"
    project = "project"


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    file_type: Optional[str]
    mime_type: Optional[str]
    category: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[str]
    relation_type: Optional[str]
    relation_id: Optional[int]
    uploaded_by: Optional[int]
    uploaded_at: Optional[str]
    uploader_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CategoryEnum] = None
    tags: Optional[str] = None
    relation_type: Optional[RelationTypeEnum] = None
    relation_id: Optional[int] = None


# ========== API Endpoints ==========

@router.post("/upload", response_model=DocumentResponse, summary="上传文件")
async def upload_document(
    file: UploadFile = File(...),
    category: CategoryEnum = Form(CategoryEnum.other),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    relation_type: Optional[RelationTypeEnum] = Form(None),
    relation_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传尽调资料文件
    
    支持的文件类型：PDF、Word、Excel、PPT、图片、压缩包
    """
    service = DocumentService(db)
    
    try:
        content = await file.read()
        
        # 检查文件大小 (限制50MB)
        max_size = 50 * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
        
        doc = service.upload_file(
            file_content=content,
            filename=file.filename,
            user_id=current_user.id,
            category=DocumentCategory(category.value),
            title=title,
            description=description,
            tags=tags,
            relation_type=DocumentRelationType(relation_type.value) if relation_type else None,
            relation_id=relation_id
        )
        
        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            mime_type=doc.mime_type,
            category=doc.category.value if doc.category else "other",
            title=doc.title,
            description=doc.description,
            tags=doc.tags,
            relation_type=doc.relation_type.value if doc.relation_type else None,
            relation_id=doc.relation_id,
            uploaded_by=doc.uploaded_by,
            uploaded_at=str(doc.uploaded_at) if doc.uploaded_at else None,
            uploader_name=current_user.real_name or current_user.username
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DocumentListResponse, summary="获取文件列表")
async def list_documents(
    category: Optional[CategoryEnum] = Query(None, description="资料分类"),
    relation_type: Optional[RelationTypeEnum] = Query(None, description="关联类型"),
    relation_id: Optional[int] = Query(None, description="关联ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取尽调资料列表"""
    service = DocumentService(db)
    
    items, total = service.list_documents(
        category=DocumentCategory(category.value) if category else None,
        relation_type=DocumentRelationType(relation_type.value) if relation_type else None,
        relation_id=relation_id,
        keyword=keyword,
        skip=skip,
        limit=limit
    )
    
    response_items = []
    for doc in items:
        uploader_name = None
        if doc.uploader:
            uploader_name = doc.uploader.real_name or doc.uploader.username
        
        response_items.append(DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            mime_type=doc.mime_type,
            category=doc.category.value if doc.category else "other",
            title=doc.title,
            description=doc.description,
            tags=doc.tags,
            relation_type=doc.relation_type.value if doc.relation_type else None,
            relation_id=doc.relation_id,
            uploaded_by=doc.uploaded_by,
            uploaded_at=str(doc.uploaded_at) if doc.uploaded_at else None,
            uploader_name=uploader_name
        ))
    
    return DocumentListResponse(items=response_items, total=total)


@router.get("/statistics", summary="获取统计信息")
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资料统计信息"""
    service = DocumentService(db)
    return service.get_statistics()


@router.get("/categories", summary="获取分类列表")
async def get_categories():
    """获取资料分类列表"""
    return [
        {"key": "dd_report", "name": "尽调报告"},
        {"key": "legal", "name": "法律文件"},
        {"key": "financial", "name": "财务资料"},
        {"key": "contract", "name": "合同协议"},
        {"key": "presentation", "name": "路演材料"},
        {"key": "meeting", "name": "会议纪要"},
        {"key": "other", "name": "其他"}
    ]


@router.get("/{doc_id}", response_model=DocumentResponse, summary="获取文件详情")
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文件详情"""
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    uploader_name = None
    if doc.uploader:
        uploader_name = doc.uploader.real_name or doc.uploader.username
    
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        file_type=doc.file_type,
        mime_type=doc.mime_type,
        category=doc.category.value if doc.category else "other",
        title=doc.title,
        description=doc.description,
        tags=doc.tags,
        relation_type=doc.relation_type.value if doc.relation_type else None,
        relation_id=doc.relation_id,
        uploaded_by=doc.uploaded_by,
        uploaded_at=str(doc.uploaded_at) if doc.uploaded_at else None,
        uploader_name=uploader_name
    )


@router.put("/{doc_id}", response_model=DocumentResponse, summary="更新文件信息")
async def update_document(
    doc_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文件信息"""
    service = DocumentService(db)
    
    doc = service.update_document(
        doc_id=doc_id,
        title=data.title,
        description=data.description,
        category=DocumentCategory(data.category.value) if data.category else None,
        tags=data.tags,
        relation_type=DocumentRelationType(data.relation_type.value) if data.relation_type else None,
        relation_id=data.relation_id
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        file_type=doc.file_type,
        mime_type=doc.mime_type,
        category=doc.category.value if doc.category else "other",
        title=doc.title,
        description=doc.description,
        tags=doc.tags,
        relation_type=doc.relation_type.value if doc.relation_type else None,
        relation_id=doc.relation_id,
        uploaded_by=doc.uploaded_by,
        uploaded_at=str(doc.uploaded_at) if doc.uploaded_at else None
    )


@router.delete("/{doc_id}", summary="删除文件")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文件"""
    service = DocumentService(db)
    
    if not service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"message": "删除成功"}


@router.get("/{doc_id}/download", summary="下载文件")
async def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载文件"""
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = UPLOAD_DIR / doc.storage_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    return FileResponse(
        path=str(file_path),
        filename=doc.filename,
        media_type=doc.mime_type or 'application/octet-stream'
    )


@router.get("/{doc_id}/preview", summary="预览文件")
async def preview_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览文件（适用于PDF和图片）
    
    返回文件内容，浏览器可直接预览
    """
    service = DocumentService(db)
    doc = service.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path = UPLOAD_DIR / doc.storage_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已被删除")
    
    # 只允许预览PDF和图片
    previewable_types = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    if doc.file_type not in previewable_types:
        raise HTTPException(status_code=400, detail="该文件类型不支持预览")
    
    return FileResponse(
        path=str(file_path),
        media_type=doc.mime_type or 'application/octet-stream',
        headers={
            "Content-Disposition": "inline"  # inline表示在浏览器中预览
        }
    )
