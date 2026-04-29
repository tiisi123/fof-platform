"""
日历 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.calendar_event import CalendarEvent

router = APIRouter(prefix="/calendar", tags=["日历"])


def _event_to_dict(e: CalendarEvent) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_type": e.event_type,
        "event_date": str(e.event_date) if e.event_date else None,
        "start_time": e.start_time,
        "end_time": e.end_time,
        "is_all_day": e.is_all_day,
        "color": e.color,
        "manager_id": e.manager_id,
        "project_id": e.project_id,
        "user_id": e.user_id,
        "user_name": e.user.real_name or e.user.username if e.user else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("", summary="获取日历事件")
async def list_events(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CalendarEvent)
    if start_date:
        query = query.filter(CalendarEvent.event_date >= start_date)
    if end_date:
        query = query.filter(CalendarEvent.event_date <= end_date)
    if event_type:
        query = query.filter(CalendarEvent.event_type == event_type)
    items = query.order_by(CalendarEvent.event_date).all()
    return {"items": [_event_to_dict(e) for e in items]}


@router.post("", summary="创建日历事件")
async def create_event(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json()
    event = CalendarEvent(
        title=body.get("title", ""),
        description=body.get("description"),
        event_type=body.get("event_type"),
        event_date=body.get("event_date"),
        start_time=body.get("start_time"),
        end_time=body.get("end_time"),
        is_all_day=body.get("is_all_day", True),
        color=body.get("color", "#409EFF"),
        manager_id=body.get("manager_id"),
        project_id=body.get("project_id"),
        user_id=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "message": "事件已创建"}


@router.put("/{event_id}", summary="更新日历事件")
async def update_event(event_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    body = await request.json()
    for field in ["title", "description", "event_type", "event_date", "start_time", "end_time", "is_all_day", "color"]:
        if field in body:
            setattr(event, field, body[field])
    db.commit()
    return {"message": "事件已更新"}


@router.delete("/{event_id}", summary="删除日历事件")
async def delete_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    db.delete(event)
    db.commit()
    return {"message": "事件已删除"}
