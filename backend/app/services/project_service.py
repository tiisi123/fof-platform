"""
一级项目Service
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional, List
from fastapi import HTTPException

from app.models.project import Project, ProjectFollowUp, ProjectStageChange, ProjectStage
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectFollowUpCreate, StageTransfer
)


def get_projects(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    stages: Optional[List[str]] = None,
    industries: Optional[List[str]] = None,
    assigned_user_ids: Optional[List[int]] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> tuple[List[Project], int]:
    """获取项目列表"""
    query = db.query(Project).filter(Project.is_deleted == False)
    
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            or_(
                Project.project_name.like(kw),
                Project.project_code.like(kw),
                Project.short_name.like(kw)
            )
        )
    
    if stages:
        query = query.filter(Project.stage.in_(stages))
    
    if industries:
        query = query.filter(Project.industry.in_(industries))
    
    if assigned_user_ids:
        query = query.filter(Project.assigned_user_id.in_(assigned_user_ids))
    
    total = query.count()
    
    sort_column = getattr(Project, sort_by, Project.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    skip = (page - 1) * page_size
    projects = query.offset(skip).limit(page_size).all()
    
    return projects, total


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """获取项目详情"""
    return db.query(Project).options(
        joinedload(Project.follow_ups),
        joinedload(Project.stage_changes)
    ).filter(
        Project.id == project_id,
        Project.is_deleted == False
    ).first()


def get_project_by_code(db: Session, project_code: str) -> Optional[Project]:
    """根据编号获取项目"""
    return db.query(Project).filter(
        Project.project_code == project_code,
        Project.is_deleted == False
    ).first()


def create_project(db: Session, project: ProjectCreate) -> Project:
    """创建项目"""
    existing = get_project_by_code(db, project.project_code)
    if existing:
        raise HTTPException(status_code=400, detail=f"项目编号 {project.project_code} 已存在")
    
    db_project = Project(**project.model_dump())
    db_project.is_deleted = False
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


def update_project(db: Session, project_id: int, project_update: ProjectUpdate) -> Project:
    """更新项目"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """删除项目（软删除）"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_project.is_deleted = True
    db.commit()
    
    return True


# ========== 阶段流转 ==========
def transfer_stage(
    db: Session,
    project_id: int,
    transfer: StageTransfer,
    operator_id: Optional[int] = None
) -> ProjectStageChange:
    """项目阶段流转"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 记录变更
    db_change = ProjectStageChange(
        project_id=project_id,
        from_stage=db_project.stage,
        to_stage=transfer.to_stage,
        reason=transfer.reason,
        operator_id=operator_id
    )
    db.add(db_change)
    
    # 更新项目阶段
    db_project.stage = transfer.to_stage
    
    db.commit()
    db.refresh(db_change)
    
    return db_change


def get_stage_changes(db: Session, project_id: int) -> List[ProjectStageChange]:
    """获取阶段变更历史"""
    return db.query(ProjectStageChange).filter(
        ProjectStageChange.project_id == project_id
    ).order_by(ProjectStageChange.created_at.desc()).all()


# ========== 跟进记录 ==========
def add_follow_up(
    db: Session,
    project_id: int,
    follow_up: ProjectFollowUpCreate,
    user_id: Optional[int] = None
) -> ProjectFollowUp:
    """添加跟进记录"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_follow = ProjectFollowUp(
        project_id=project_id,
        follow_user_id=user_id,
        **follow_up.model_dump()
    )
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    
    return db_follow


def get_follow_ups(db: Session, project_id: int) -> List[ProjectFollowUp]:
    """获取跟进记录"""
    return db.query(ProjectFollowUp).filter(
        ProjectFollowUp.project_id == project_id
    ).order_by(ProjectFollowUp.follow_date.desc()).all()


def delete_follow_up(db: Session, follow_up_id: int) -> bool:
    """删除跟进记录"""
    db_follow = db.query(ProjectFollowUp).filter(ProjectFollowUp.id == follow_up_id).first()
    if not db_follow:
        raise HTTPException(status_code=404, detail="跟进记录不存在")
    
    db.delete(db_follow)
    db.commit()
    
    return True


# ========== 统计 ==========
def get_project_statistics(db: Session) -> dict:
    """获取项目统计"""
    query = db.query(Project).filter(Project.is_deleted == False)
    
    total = query.count()
    
    # 按阶段统计
    stage_stats = db.query(
        Project.stage,
        func.count(Project.id)
    ).filter(Project.is_deleted == False).group_by(Project.stage).all()
    
    # 按行业统计
    industry_stats = db.query(
        Project.industry,
        func.count(Project.id)
    ).filter(Project.is_deleted == False).group_by(Project.industry).all()
    
    # 总投资金额
    total_investment = db.query(
        func.sum(Project.investment_amount)
    ).filter(
        Project.is_deleted == False,
        Project.investment_amount.isnot(None)
    ).scalar() or 0
    
    return {
        "total": total,
        "by_stage": {
            (s.value if s else "unknown"): count 
            for s, count in stage_stats
        },
        "by_industry": {
            (i.value if i else "unknown"): count 
            for i, count in industry_stats
        },
        "total_investment": float(total_investment)
    }


# ========== 批量导入 ==========
def batch_import_projects(db: Session, projects: List[ProjectCreate]) -> dict:
    """批量导入项目"""
    success_count = 0
    fail_count = 0
    errors = []
    
    for i, project in enumerate(projects):
        try:
            existing = get_project_by_code(db, project.project_code)
            if existing:
                # 更新
                update_data = project.model_dump()
                for field, value in update_data.items():
                    if value is not None:
                        setattr(existing, field, value)
                success_count += 1
            else:
                # 创建
                create_project(db, project)
                success_count += 1
        except Exception as e:
            fail_count += 1
            errors.append({"row": i + 1, "code": project.project_code, "error": str(e)})
    
    db.commit()
    
    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors
    }
