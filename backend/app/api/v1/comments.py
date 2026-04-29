"""
批注与讨论 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.comment import Comment

router = APIRouter(prefix="/comments", tags=["批注讨论"])

VALID_RESOURCE_TYPES = {"manager", "product", "project", "portfolio"}


def _comment_to_dict(c: Comment) -> dict:
    return {
        "id": c.id,
        "resource_type": c.resource_type,
        "resource_id": c.resource_id,
        "content": c.content,
        "parent_id": c.parent_id,
        "user_id": c.user_id,
        "user_name": c.user.real_name or c.user.username if c.user else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("", summary="获取评论列表")
async def list_comments(
    resource_type: str = Query(..., description="资源类型: manager/product/project/portfolio"),
    resource_id: int = Query(..., description="资源ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资源的评论列表（仅顶层，子回复嵌套返回）"""
    if resource_type not in VALID_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"无效资源类型: {resource_type}")

    query = db.query(Comment).filter(
        Comment.resource_type == resource_type,
        Comment.resource_id == resource_id,
        Comment.parent_id.is_(None),
    )
    total = query.count()
    items = query.order_by(desc(Comment.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for c in items:
        d = _comment_to_dict(c)
        d["replies"] = [_comment_to_dict(r) for r in (c.replies or [])]
        result.append(d)

    return {"total": total, "items": result}


@router.post("", summary="添加评论")
async def create_comment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    添加评论。
    body: { resource_type, resource_id, content, parent_id? }
    """
    body = await request.json()
    resource_type = body.get("resource_type")
    if resource_type not in VALID_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"无效资源类型: {resource_type}")

    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="评论内容不能为空")

    comment = Comment(
        resource_type=resource_type,
        resource_id=body.get("resource_id"),
        content=content,
        parent_id=body.get("parent_id"),
        user_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"id": comment.id, "message": "评论已添加"}


@router.delete("/{comment_id}", summary="删除评论")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    # 只能删除自己的评论（管理员可删除任何评论）
    if comment.user_id != current_user.id and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权删除此评论")
    db.delete(comment)
    db.commit()
    return {"message": "评论已删除"}
