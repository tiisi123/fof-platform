"""
管理人相关API V2
"""
from fastapi import APIRouter, Depends, Query, Path, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import pandas as pd
import io

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.manager import (
    ManagerCreate, ManagerUpdate, ManagerResponse, ManagerListResponse,
    ManagerContactCreate, ManagerContactResponse,
    ManagerTeamCreate, ManagerTeamResponse,
    PoolTransferCreate, PoolTransferResponse,
    PoolCategory, PrimaryStrategy, ManagerListParams, ManagerStats,
    ManagerProductInfo, ManagerPerformanceSummary,
    ManagerTagCreate, ManagerTagResponse
)
from app.services import manager_service
from app.services.document_service import DocumentService
from app.models.document import DocumentCategory, DocumentRelationType

router = APIRouter()


# ========== 管理人CRUD ==========
@router.get("", response_model=dict, summary="获取管理人列表")
async def get_managers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    pool_categories: Optional[str] = Query(None, description="跟踪池分类,逗号分隔"),
    primary_strategies: Optional[str] = Query(None, description="一级策略,逗号分隔"),
    assigned_user_ids: Optional[str] = Query(None, description="负责人ID,逗号分隔"),
    tag_names: Optional[str] = Query(None, description="标签名称筛选,逗号分隔"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人列表（支持多条件筛选，包含标签筛选）"""
    # 解析逗号分隔的参数
    pool_list = [PoolCategory(p) for p in pool_categories.split(",")] if pool_categories else None
    strategy_list = [PrimaryStrategy(s) for s in primary_strategies.split(",")] if primary_strategies else None
    user_list = [int(u) for u in assigned_user_ids.split(",")] if assigned_user_ids else None
    tag_list = [t.strip() for t in tag_names.split(",")] if tag_names else None
    
    params = ManagerListParams(
        page=page,
        page_size=page_size,
        keyword=keyword,
        pool_categories=pool_list,
        primary_strategies=strategy_list,
        assigned_user_ids=user_list,
        tag_names=tag_list,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    managers, total = manager_service.get_managers(db, params)
    
    # 将SQLAlchemy对象转换为Pydantic模型
    items = [ManagerListResponse.model_validate(m) for m in managers]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/simple", response_model=dict, summary="获取管理人列表(兼容V1)")
async def get_managers_simple(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    strategy_type: Optional[str] = Query(None),
    rating: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """兼容V1的管理人列表接口"""
    managers, total = manager_service.get_managers_simple(
        db, skip, limit, search, strategy_type, rating, status
    )
    # 将SQLAlchemy对象转换为Pydantic模型
    items = [ManagerListResponse.model_validate(m) for m in managers]
    return {"total": total, "items": items}


@router.get("/statistics/summary", response_model=ManagerStats, summary="获取管理人统计")
async def get_manager_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人统计信息（按跟踪池、策略分类）"""
    return manager_service.get_manager_statistics(db)


@router.get("/{manager_id}", response_model=ManagerResponse, summary="获取管理人详情")
async def get_manager(
    manager_id: int = Path(..., description="管理人ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人详情（包含联系人、团队、产品数量）"""
    manager = manager_service.get_manager_by_id(db, manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail=f"管理人ID {manager_id} 不存在")
    
    # 补充产品数量
    manager.product_count = len(manager.products) if manager.products else 0
    return manager


@router.post("", response_model=ManagerResponse, status_code=201, summary="创建管理人")
async def create_manager(
    manager: ManagerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建管理人（可同时创建联系人和团队）"""
    return manager_service.create_manager(db, manager)


@router.put("/{manager_id}", response_model=ManagerResponse, summary="更新管理人")
async def update_manager(
    manager_id: int = Path(...),
    manager_update: ManagerUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新管理人信息（自动记录编辑历史）"""
    return manager_service.update_manager(db, manager_id, manager_update, operator_id=current_user.id)


@router.delete("/{manager_id}", summary="删除管理人")
async def delete_manager(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除管理人（软删除）"""
    manager_service.delete_manager(db, manager_id)
    return {"message": "删除成功"}


# ========== 联系人管理 ==========
@router.post("/{manager_id}/contacts", response_model=ManagerContactResponse, summary="添加联系人")
async def add_contact(
    manager_id: int = Path(...),
    contact: ManagerContactCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为管理人添加联系人"""
    return manager_service.add_contact(db, manager_id, contact)


@router.put("/contacts/{contact_id}", response_model=ManagerContactResponse, summary="更新联系人")
async def update_contact(
    contact_id: int = Path(...),
    contact: ManagerContactCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新联系人信息"""
    return manager_service.update_contact(db, contact_id, contact)


@router.delete("/contacts/{contact_id}", summary="删除联系人")
async def delete_contact(
    contact_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除联系人"""
    manager_service.delete_contact(db, contact_id)
    return {"message": "删除成功"}


# ========== 核心团队管理 ==========
@router.post("/{manager_id}/team", response_model=ManagerTeamResponse, summary="添加团队成员")
async def add_team_member(
    manager_id: int = Path(...),
    member: ManagerTeamCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为管理人添加核心团队成员"""
    return manager_service.add_team_member(db, manager_id, member)


@router.delete("/team/{member_id}", summary="删除团队成员")
async def delete_team_member(
    member_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除核心团队成员"""
    manager_service.delete_team_member(db, member_id)
    return {"message": "删除成功"}


# ========== 跟踪池流转 ==========
@router.post("/{manager_id}/transfer", response_model=PoolTransferResponse, summary="跟踪池流转")
async def transfer_pool(
    manager_id: int = Path(...),
    transfer: PoolTransferCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将管理人流转到其他跟踪池"""
    return manager_service.transfer_pool(db, manager_id, transfer, current_user.id)


@router.get("/{manager_id}/transfers", response_model=List[PoolTransferResponse], summary="获取流转历史")
async def get_pool_transfers(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人的跟踪池流转历史"""
    return manager_service.get_pool_transfers(db, manager_id)


@router.post("/batch-transfer", summary="批量流转")
async def batch_transfer_pool(
    manager_ids: List[int],
    transfer: PoolTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量将管理人流转到其他跟踪池"""
    count = manager_service.batch_transfer_pool(db, manager_ids, transfer, current_user.id)
    return {"message": f"成功流转 {count} 个管理人"}


# ========== 编辑历史 ==========
@router.get("/{manager_id}/edit-history", summary="获取编辑历史")
async def get_edit_history(
    manager_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人的编辑历史记录"""
    items, total = manager_service.get_edit_history(db, manager_id, skip, limit)
    return {
        "total": total,
        "items": [
            {
                "id": h.id,
                "field_name": h.field_name,
                "field_label": h.field_label,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "operator_name": h.operator.real_name or h.operator.username if h.operator else None,
                "batch_id": h.batch_id,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in items
        ]
    }


# ========== 旗下产品 ==========
@router.get("/{manager_id}/products", response_model=List[ManagerProductInfo], summary="获取管理人旗下产品")
async def get_manager_products(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人旗下所有产品（含最新净值和绩效指标）"""
    return manager_service.get_manager_products(db, manager_id)


# ========== 业绩汇总 ==========
@router.get("/{manager_id}/performance-summary", response_model=ManagerPerformanceSummary, summary="获取管理人业绩汇总")
async def get_manager_performance_summary(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人旗下产品的业绩汇总分析"""
    return manager_service.get_manager_performance_summary(db, manager_id)


# ========== 尽调资料 ==========
@router.get("/{manager_id}/documents", summary="获取管理人尽调资料")
async def get_manager_documents(
    manager_id: int = Path(...),
    category: Optional[str] = Query(None, description="资料分类"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人关联的尽调资料列表"""
    doc_service = DocumentService(db)
    cat = DocumentCategory(category) if category else None
    docs, total = doc_service.list_documents(
        category=cat,
        relation_type=DocumentRelationType.MANAGER,
        relation_id=manager_id,
        keyword=keyword,
        skip=skip,
        limit=limit
    )
    return {"total": total, "items": docs}


@router.post("/{manager_id}/documents", summary="上传管理人尽调资料")
async def upload_manager_document(
    manager_id: int = Path(...),
    file: UploadFile = File(...),
    category: str = Query("other", description="资料分类"),
    title: Optional[str] = Query(None, description="资料标题"),
    description: Optional[str] = Query(None, description="描述"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为管理人上传尽调资料"""
    content = await file.read()
    doc_service = DocumentService(db)
    doc = doc_service.upload_file(
        file_content=content,
        filename=file.filename,
        user_id=current_user.id,
        category=DocumentCategory(category),
        title=title,
        relation_type=DocumentRelationType.MANAGER,
        relation_id=manager_id,
        description=description
    )
    return {"id": doc.id, "filename": doc.filename, "message": "上传成功"}


# ========== 标签管理 ==========
@router.get("/tags/all", summary="获取所有标签（去重）")
async def get_all_tags(
    tag_type: Optional[str] = Query(None, description="标签类型筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有管理人标签（去重，用于筛选下拉）"""
    return manager_service.get_all_unique_tags(db, tag_type)


@router.get("/{manager_id}/tags", response_model=List[ManagerTagResponse], summary="获取管理人标签")
async def get_manager_tags(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取管理人的所有标签"""
    return manager_service.get_manager_tags(db, manager_id)


@router.post("/{manager_id}/tags", response_model=ManagerTagResponse, status_code=201, summary="添加标签")
async def add_manager_tag(
    manager_id: int = Path(...),
    tag: ManagerTagCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为管理人添加标签"""
    return manager_service.add_manager_tag(db, manager_id, tag)


@router.delete("/tags/{tag_id}", summary="删除标签")
async def delete_manager_tag(
    tag_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除管理人标签"""
    manager_service.delete_manager_tag(db, tag_id)
    return {"message": "删除成功"}


# ========== 批量导入导出 ==========
@router.post("/import", summary="批量导入管理人")
async def import_managers(
    file: UploadFile = File(..., description="Excel文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量导入管理人（Excel格式）
    
    Excel列名要求：
    - 管理人编号（必填）
    - 管理人名称（必填）
    - 管理人简称
    - 协会备案编号
    - 成立日期
    - 注册资本(万元)
    - 管理规模
    - 一级策略
    - 二级策略
    - 跟踪池分类
    - 联系人
    - 联系电话
    - 联系邮箱
    - 备注
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件")
    
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # 列名映射
        column_map = {
            "管理人编号": "manager_code",
            "管理人名称": "manager_name",
            "管理人简称": "short_name",
            "协会备案编号": "registration_no",
            "成立日期": "established_date",
            "注册资本(万元)": "registered_capital",
            "管理规模": "aum_range",
            "一级策略": "primary_strategy",
            "二级策略": "secondary_strategy",
            "跟踪池分类": "pool_category",
            "联系人": "contact_person",
            "联系电话": "contact_phone",
            "联系邮箱": "contact_email",
            "备注": "remark"
        }
        
        # 策略映射
        strategy_map = {
            "股票多头": "equity_long",
            "量化中性": "quant_neutral",
            "CTA": "cta",
            "套利": "arbitrage",
            "多策略": "multi_strategy",
            "债券": "bond",
            "其他": "other"
        }
        
        # 跟踪池映射
        pool_map = {
            "在投池": "invested",
            "重点跟踪池": "key_tracking",
            "观察池": "observation",
            "淘汰池": "eliminated",
            "已看过": "contacted"
        }
        
        managers = []
        for _, row in df.iterrows():
            manager_data = {}
            for cn_name, en_name in column_map.items():
                if cn_name in df.columns:
                    value = row[cn_name]
                    if pd.notna(value):
                        # 特殊处理
                        if en_name == "primary_strategy":
                            value = strategy_map.get(str(value), "other")
                        elif en_name == "pool_category":
                            value = pool_map.get(str(value), "observation")
                        elif en_name == "established_date":
                            value = pd.to_datetime(value).date()
                        manager_data[en_name] = value
            
            if manager_data.get("manager_code") and manager_data.get("manager_name"):
                managers.append(ManagerCreate(**manager_data))
        
        result = manager_service.batch_import_managers(db, managers)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.get("/export/excel", summary="导出管理人Excel")
async def export_managers(
    manager_ids: Optional[str] = Query(None, description="管理人ID,逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出管理人数据为Excel"""
    ids = [int(i) for i in manager_ids.split(",")] if manager_ids else None
    data = manager_service.export_managers(db, ids)
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=managers_export.xlsx"}
    )


@router.get("/export/template", summary="下载导入模板")
async def download_template():
    """下载管理人导入模板"""
    columns = [
        "管理人编号", "管理人名称", "管理人简称", "协会备案编号",
        "成立日期", "注册资本(万元)", "管理规模", "一级策略",
        "二级策略", "跟踪池分类", "联系人", "联系电话", "联系邮箱", "备注"
    ]
    
    df = pd.DataFrame(columns=columns)
    # 添加示例数据
    df.loc[0] = ["MGR001", "示例管理人", "示例", "P1234567", 
                 "2020-01-01", 1000, "10-20亿", "股票多头",
                 "价值型", "观察池", "张三", "13800138000", "test@example.com", ""]
    
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=manager_import_template.xlsx"}
    )
