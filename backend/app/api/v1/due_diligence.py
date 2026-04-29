"""
尽调工作流 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.due_diligence import DueDiligenceFlow, DDStatus

router = APIRouter(prefix="/due-diligence", tags=["尽调工作流"])


def _dd_to_dict(dd: DueDiligenceFlow) -> dict:
    return {
        "id": dd.id,
        "title": dd.title,
        "manager_id": dd.manager_id,
        "manager_name": dd.manager.manager_name if dd.manager else None,
        "project_id": dd.project_id,
        "project_name": dd.project.project_name if dd.project else None,
        "status": dd.status,
        "dd_type": dd.dd_type,
        "start_date": str(dd.start_date) if dd.start_date else None,
        "end_date": str(dd.end_date) if dd.end_date else None,
        "actual_end_date": str(dd.actual_end_date) if dd.actual_end_date else None,
        "checklist": dd.checklist or [],
        "conclusion": dd.conclusion,
        "risk_points": dd.risk_points,
        "lead_user_id": dd.lead_user_id,
        "lead_user_name": dd.lead_user.username if dd.lead_user else None,
        "reviewer_id": dd.reviewer_id,
        "reviewer_name": dd.reviewer.username if dd.reviewer else None,
        "created_at": dd.created_at.isoformat() if dd.created_at else None,
        "updated_at": dd.updated_at.isoformat() if dd.updated_at else None,
    }


@router.get("", summary="获取尽调列表")
async def list_dd(
    manager_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DueDiligenceFlow)
    if manager_id:
        query = query.filter(DueDiligenceFlow.manager_id == manager_id)
    if project_id:
        query = query.filter(DueDiligenceFlow.project_id == project_id)
    if status:
        query = query.filter(DueDiligenceFlow.status == status)

    total = query.count()
    items = query.order_by(desc(DueDiligenceFlow.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {"total": total, "items": [_dd_to_dict(dd) for dd in items]}


@router.post("", summary="创建尽调")
async def create_dd(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json()
    dd = DueDiligenceFlow(
        title=body.get("title", ""),
        manager_id=body.get("manager_id"),
        project_id=body.get("project_id"),
        dd_type=body.get("dd_type"),
        start_date=body.get("start_date"),
        end_date=body.get("end_date"),
        checklist=body.get("checklist", []),
        lead_user_id=body.get("lead_user_id") or current_user.id,
        reviewer_id=body.get("reviewer_id"),
    )
    db.add(dd)
    db.commit()
    db.refresh(dd)
    return {"id": dd.id, "message": "尽调已创建"}


@router.get("/{dd_id}", summary="获取尽调详情")
async def get_dd(dd_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dd = db.query(DueDiligenceFlow).filter(DueDiligenceFlow.id == dd_id).first()
    if not dd:
        raise HTTPException(status_code=404, detail="尽调不存在")
    return _dd_to_dict(dd)


@router.put("/{dd_id}", summary="更新尽调")
async def update_dd(
    dd_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dd = db.query(DueDiligenceFlow).filter(DueDiligenceFlow.id == dd_id).first()
    if not dd:
        raise HTTPException(status_code=404, detail="尽调不存在")
    body = await request.json()
    for field in ["title", "status", "dd_type", "start_date", "end_date", "actual_end_date",
                   "checklist", "conclusion", "risk_points", "lead_user_id", "reviewer_id"]:
        if field in body:
            setattr(dd, field, body[field])
    db.commit()
    return {"message": "尽调已更新"}


@router.delete("/{dd_id}", summary="删除尽调")
async def delete_dd(dd_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dd = db.query(DueDiligenceFlow).filter(DueDiligenceFlow.id == dd_id).first()
    if not dd:
        raise HTTPException(status_code=404, detail="尽调不存在")
    db.delete(dd)
    db.commit()
    return {"message": "尽调已删除"}
