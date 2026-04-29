"""
待办任务 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from typing import Optional
from datetime import datetime, date

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskPriority

router = APIRouter(prefix="/tasks", tags=["待办任务"])


def _task_to_dict(t: Task) -> dict:
    """Task转字典"""
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "product_id": t.product_id,
        "manager_id": t.manager_id,
        "portfolio_id": t.portfolio_id,
        "product_name": t.product.product_name if t.product else None,
        "manager_name": t.manager.manager_name if t.manager else None,
        "portfolio_name": t.portfolio.name if t.portfolio else None,
        "assigned_to": t.assigned_to,
        "assignee_name": t.assignee.username if t.assignee else None,
        "created_by": t.created_by,
        "creator_name": t.creator.username if t.creator else None,
        "due_date": str(t.due_date) if t.due_date else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("", summary="获取任务列表")
async def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[int] = Query(None, description="指派人ID"),
    my_tasks: bool = Query(False, description="只看我的任务"),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务列表，支持筛选和分页"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if my_tasks:
        query = query.filter(
            or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id)
        )
    if keyword:
        query = query.filter(
            or_(Task.title.contains(keyword), Task.description.contains(keyword))
        )
    
    total = query.count()
    
    # 排序: 未完成优先, 优先级高优先, 截止日期近优先
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    tasks = query.order_by(
        Task.status != TaskStatus.COMPLETED,  # 未完成优先
        desc(Task.created_at),
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_task_to_dict(t) for t in tasks],
    }


@router.post("", summary="创建任务")
async def create_task(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建新任务。
    请求体: { title, description?, priority?, due_date?, assigned_to?, product_id?, manager_id?, portfolio_id? }
    """
    body = await request.json()
    
    title = body.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    
    task = Task(
        title=title,
        description=body.get("description"),
        priority=body.get("priority", TaskPriority.MEDIUM),
        due_date=body.get("due_date"),
        assigned_to=body.get("assigned_to"),
        product_id=body.get("product_id"),
        manager_id=body.get("manager_id"),
        portfolio_id=body.get("portfolio_id"),
        created_by=current_user.id,
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {"id": task.id, "message": "任务已创建"}


@router.get("/stats", summary="获取任务统计")
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务统计信息"""
    total = db.query(Task).count()
    pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    
    # 我的待办
    my_pending = db.query(Task).filter(
        or_(Task.assigned_to == current_user.id, Task.created_by == current_user.id),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
    ).count()
    
    # 逾期任务
    overdue = db.query(Task).filter(
        Task.due_date < date.today(),
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
    ).count()
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "my_pending": my_pending,
        "overdue": overdue,
    }


@router.get("/{task_id}", summary="获取任务详情")
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _task_to_dict(task)


@router.put("/{task_id}", summary="更新任务")
async def update_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新任务信息"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    body = await request.json()
    
    for field in ["title", "description", "priority", "due_date", "assigned_to", "product_id", "manager_id", "portfolio_id"]:
        if field in body:
            setattr(task, field, body[field])
    
    if "status" in body:
        task.status = body["status"]
        if body["status"] == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
        elif task.completed_at:
            task.completed_at = None
    
    db.commit()
    return {"message": "任务已更新"}


@router.put("/{task_id}/complete", summary="完成任务")
async def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记任务为已完成"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    db.commit()
    return {"message": "任务已完成"}


@router.delete("/{task_id}", summary="删除任务")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}
