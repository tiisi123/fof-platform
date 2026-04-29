"""
一级项目API
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
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectFollowUpCreate, ProjectFollowUpResponse,
    ProjectStageChangeResponse, StageTransfer, ProjectStats,
    ProjectStage, ProjectIndustry
)
from app.services import project_service

router = APIRouter()


@router.get("", summary="获取项目列表")
async def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stages: Optional[str] = Query(None, description="阶段,逗号分隔"),
    industries: Optional[str] = Query(None, description="行业,逗号分隔"),
    assigned_user_ids: Optional[str] = Query(None, description="负责人ID,逗号分隔"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    stage_list = stages.split(",") if stages else None
    industry_list = industries.split(",") if industries else None
    user_list = [int(u) for u in assigned_user_ids.split(",")] if assigned_user_ids else None
    
    projects, total = project_service.get_projects(
        db, page, page_size, keyword, stage_list, industry_list, user_list, sort_by, sort_order
    )
    
    # 序列化项目列表
    items = [ProjectListResponse.model_validate(p).model_dump() for p in projects]
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/statistics", response_model=ProjectStats, summary="获取项目统计")
async def get_project_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目统计信息"""
    return project_service.get_project_statistics(db)


@router.get("/{project_id}", response_model=ProjectResponse, summary="获取项目详情")
async def get_project(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情（包含跟进记录和阶段变更历史）"""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("", response_model=ProjectResponse, status_code=201, summary="创建项目")
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目"""
    return project_service.create_project(db, project)


@router.put("/{project_id}", response_model=ProjectResponse, summary="更新项目")
async def update_project(
    project_id: int = Path(...),
    project_update: ProjectUpdate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目信息"""
    return project_service.update_project(db, project_id, project_update)


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目（软删除）"""
    project_service.delete_project(db, project_id)
    return {"message": "删除成功"}


# ========== 阶段流转 ==========
@router.post("/{project_id}/transfer", response_model=ProjectStageChangeResponse, summary="阶段流转")
async def transfer_stage(
    project_id: int = Path(...),
    transfer: StageTransfer = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """项目阶段流转"""
    return project_service.transfer_stage(db, project_id, transfer, current_user.id)


@router.get("/{project_id}/stage-changes", response_model=List[ProjectStageChangeResponse], summary="获取阶段变更历史")
async def get_stage_changes(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目阶段变更历史"""
    return project_service.get_stage_changes(db, project_id)


# ========== 跟进记录 ==========
@router.post("/{project_id}/follow-ups", response_model=ProjectFollowUpResponse, summary="添加跟进记录")
async def add_follow_up(
    project_id: int = Path(...),
    follow_up: ProjectFollowUpCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加项目跟进记录"""
    return project_service.add_follow_up(db, project_id, follow_up, current_user.id)


@router.get("/{project_id}/follow-ups", response_model=List[ProjectFollowUpResponse], summary="获取跟进记录")
async def get_follow_ups(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目跟进记录"""
    return project_service.get_follow_ups(db, project_id)


@router.delete("/follow-ups/{follow_up_id}", summary="删除跟进记录")
async def delete_follow_up(
    follow_up_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除跟进记录"""
    project_service.delete_follow_up(db, follow_up_id)
    return {"message": "删除成功"}


# ========== 现金流与IRR/MOIC ==========
from fastapi import Request as FastAPIRequest
from app.models.project_cashflow import ProjectCashflow, CashflowType
from app.services.project_calc_service import calculate_irr_moic


@router.get("/{project_id}/cashflows", summary="获取项目现金流")
async def get_cashflows(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目现金流列表"""
    items = db.query(ProjectCashflow).filter(
        ProjectCashflow.project_id == project_id
    ).order_by(ProjectCashflow.cashflow_date).all()
    return {
        "items": [
            {
                "id": c.id,
                "project_id": c.project_id,
                "cashflow_date": str(c.cashflow_date),
                "cashflow_type": c.cashflow_type,
                "amount": float(c.amount),
                "description": c.description,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ],
        "total": len(items),
    }


@router.post("/{project_id}/cashflows", summary="添加现金流")
async def add_cashflow(
    project_id: int = Path(...),
    request: FastAPIRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加现金流记录"""
    body = await request.json()
    cf = ProjectCashflow(
        project_id=project_id,
        cashflow_date=body.get("cashflow_date"),
        cashflow_type=body.get("cashflow_type", CashflowType.INVESTMENT),
        amount=body.get("amount", 0),
        description=body.get("description"),
    )
    db.add(cf)
    db.commit()
    db.refresh(cf)
    return {"id": cf.id, "message": "现金流已添加"}


@router.delete("/{project_id}/cashflows/{cf_id}", summary="删除现金流")
async def delete_cashflow(
    project_id: int = Path(...),
    cf_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cf = db.query(ProjectCashflow).filter(
        ProjectCashflow.id == cf_id, ProjectCashflow.project_id == project_id
    ).first()
    if not cf:
        raise HTTPException(status_code=404, detail="现金流记录不存在")
    db.delete(cf)
    db.commit()
    return {"message": "已删除"}


@router.post("/{project_id}/calculate-irr", summary="计算IRR/MOIC")
async def calc_irr(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据现金流计算项目IRR和MOIC"""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    result = calculate_irr_moic(project_id, db)
    return result


# ========== 退出情景模拟 ==========
@router.post("/{project_id}/exit-simulation", summary="退出情景模拟")
async def exit_simulation(
    project_id: int = Path(...),
    request: FastAPIRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    多情景退出模拟：在现有现金流基础上，模拟不同退出方案的IRR/MOIC。
    body: { scenarios: [{ name, exit_date, exit_amount, exit_method? }] }
    """
    from app.services.project_calc_service import _xirr

    body = await request.json()
    scenarios = body.get("scenarios", [])
    if not scenarios:
        raise HTTPException(status_code=400, detail="请提供至少一个退出场景")

    # 获取历史现金流
    cashflows = db.query(ProjectCashflow).filter(
        ProjectCashflow.project_id == project_id
    ).order_by(ProjectCashflow.cashflow_date).all()

    total_invested = sum(float(abs(cf.amount)) for cf in cashflows if cf.cashflow_type == CashflowType.INVESTMENT)
    total_distributed = sum(float(cf.amount) for cf in cashflows if cf.cashflow_type == CashflowType.DISTRIBUTION)

    # 构建基础现金流对
    base_pairs = []
    for cf in cashflows:
        amount = float(cf.amount)
        if cf.cashflow_type == CashflowType.INVESTMENT:
            amount = -abs(amount)
        elif cf.cashflow_type == CashflowType.DISTRIBUTION:
            amount = abs(amount)
        base_pairs.append((cf.cashflow_date, amount))

    results = []
    for sc in scenarios:
        from datetime import datetime as dt
        exit_date_str = sc.get("exit_date")
        exit_amount = float(sc.get("exit_amount", 0))
        exit_name = sc.get("name", f"场景{len(results)+1}")

        if not exit_date_str or exit_amount <= 0:
            results.append({"name": exit_name, "irr": None, "moic": None, "error": "参数不完整"})
            continue

        try:
            exit_date = dt.strptime(exit_date_str, "%Y-%m-%d").date()
        except Exception:
            results.append({"name": exit_name, "irr": None, "moic": None, "error": "日期格式错误"})
            continue

        # 在基础现金流上加上退出现金流
        sim_pairs = base_pairs + [(exit_date, exit_amount)]
        sim_pairs.sort(key=lambda x: x[0])

        irr = _xirr(sim_pairs)
        irr = round(irr, 6) if irr is not None else None
        sim_total_dist = total_distributed + exit_amount
        moic = round(sim_total_dist / total_invested, 4) if total_invested > 0 else None

        results.append({
            "name": exit_name,
            "exit_date": exit_date_str,
            "exit_amount": exit_amount,
            "exit_method": sc.get("exit_method", ""),
            "irr": irr,
            "moic": moic,
            "total_invested": round(total_invested, 2),
            "total_distributed": round(sim_total_dist, 2),
        })

    return {"project_id": project_id, "scenarios": results}


# ========== 现金流预测 ==========
@router.post("/{project_id}/cashflow-forecast", summary="现金流预测")
async def cashflow_forecast(
    project_id: int = Path(...),
    request: FastAPIRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    生成现金流预测序列：历史+将来。
    body: {
        forecast_items?: [{ date, amount, type, label }],
        exit_date?: str, exit_amount?: float
    }
    """
    from datetime import datetime as dt, timedelta

    body = await request.json()

    # 历史现金流
    cashflows = db.query(ProjectCashflow).filter(
        ProjectCashflow.project_id == project_id
    ).order_by(ProjectCashflow.cashflow_date).all()

    history = []
    cumulative = 0.0
    for cf in cashflows:
        amt = float(cf.amount)
        signed = -abs(amt) if cf.cashflow_type == CashflowType.INVESTMENT else abs(amt)
        cumulative += signed
        history.append({
            "date": str(cf.cashflow_date),
            "amount": signed,
            "cumulative": round(cumulative, 2),
            "type": cf.cashflow_type,
            "label": cf.description or ("投入" if cf.cashflow_type == CashflowType.INVESTMENT else "回收"),
            "is_forecast": False,
        })

    # 用户自定义预测项
    forecast_items = body.get("forecast_items", [])
    forecast = []
    for fi in forecast_items:
        amt = float(fi.get("amount", 0))
        signed = -abs(amt) if fi.get("type") == "investment" else abs(amt)
        cumulative += signed
        forecast.append({
            "date": fi.get("date"),
            "amount": signed,
            "cumulative": round(cumulative, 2),
            "type": fi.get("type", "distribution"),
            "label": fi.get("label", "预测"),
            "is_forecast": True,
        })

    # 自动添加退出项
    exit_date = body.get("exit_date")
    exit_amount = body.get("exit_amount")
    if exit_date and exit_amount:
        cumulative += float(exit_amount)
        forecast.append({
            "date": exit_date,
            "amount": float(exit_amount),
            "cumulative": round(cumulative, 2),
            "type": "distribution",
            "label": "预期退出",
            "is_forecast": True,
        })

    all_items = history + sorted(forecast, key=lambda x: x["date"])
    return {"project_id": project_id, "items": all_items}


# ========== 评审意见 ==========
from app.models.project_review import ProjectReview


@router.get("/{project_id}/reviews", summary="获取评审意见")
async def get_reviews(
    project_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目评审意见列表"""
    items = db.query(ProjectReview).filter(
        ProjectReview.project_id == project_id
    ).order_by(ProjectReview.meeting_date.desc(), ProjectReview.created_at.desc()).all()
    return {
        "items": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "review_type": r.review_type,
                "meeting_date": str(r.meeting_date) if r.meeting_date else None,
                "reviewer_name": r.reviewer_name,
                "reviewer_role": r.reviewer_role,
                "result": r.result,
                "opinion": r.opinion,
                "conditions": r.conditions,
                "risk_notes": r.risk_notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ],
        "total": len(items),
        "summary": {
            "approve": sum(1 for r in items if r.result == "approve"),
            "reject": sum(1 for r in items if r.result == "reject"),
            "conditional": sum(1 for r in items if r.result == "conditional"),
            "abstain": sum(1 for r in items if r.result == "abstain"),
        },
    }


@router.post("/{project_id}/reviews", summary="添加评审意见")
async def add_review(
    project_id: int = Path(...),
    req: FastAPIRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加项目评审意见"""
    body = await req.json()
    review = ProjectReview(
        project_id=project_id,
        review_type=body.get("review_type", "ic"),
        meeting_date=body.get("meeting_date"),
        reviewer_name=body["reviewer_name"],
        reviewer_role=body.get("reviewer_role"),
        result=body["result"],
        opinion=body.get("opinion"),
        conditions=body.get("conditions"),
        risk_notes=body.get("risk_notes"),
        created_by=current_user.id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {"id": review.id, "message": "评审意见已添加"}


@router.delete("/{project_id}/reviews/{review_id}", summary="删除评审意见")
async def delete_review(
    project_id: int = Path(...),
    review_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = db.query(ProjectReview).filter(
        ProjectReview.id == review_id, ProjectReview.project_id == project_id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="评审记录不存在")
    db.delete(r)
    db.commit()
    return {"message": "已删除"}


# ========== 批量导入导出 ==========
@router.post("/import", summary="批量导入项目")
async def import_projects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量导入项目（Excel格式）"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传Excel文件")
    
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        column_map = {
            "项目编号": "project_code",
            "项目名称": "project_name",
            "项目简称": "short_name",
            "行业": "industry",
            "细分领域": "sub_industry",
            "项目来源": "source",
            "来源渠道": "source_channel",
            "项目阶段": "stage",
            "联系人": "contact_name",
            "联系电话": "contact_phone",
            "联系邮箱": "contact_email",
            "初步介绍": "initial_intro",
            "备注": "remark"
        }
        
        industry_map = {
            "TMT": "tmt", "医疗健康": "healthcare", "消费": "consumer",
            "先进制造": "manufacturing", "新能源": "energy", 
            "金融": "finance", "房地产": "real_estate", "其他": "other"
        }
        
        stage_map = {
            "Sourcing": "sourcing", "初筛": "screening", "尽调": "due_diligence",
            "投决": "ic", "投后": "post_investment", "退出": "exit", "已否决": "rejected"
        }
        
        projects = []
        for _, row in df.iterrows():
            project_data = {}
            for cn_name, en_name in column_map.items():
                if cn_name in df.columns:
                    value = row[cn_name]
                    if pd.notna(value):
                        if en_name == "industry":
                            value = industry_map.get(str(value), "other")
                        elif en_name == "stage":
                            value = stage_map.get(str(value), "sourcing")
                        project_data[en_name] = value
            
            if project_data.get("project_code") and project_data.get("project_name"):
                projects.append(ProjectCreate(**project_data))
        
        result = project_service.batch_import_projects(db, projects)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.get("/export/template", summary="下载导入模板")
async def download_template():
    """下载项目导入模板"""
    columns = [
        "项目编号", "项目名称", "项目简称", "行业", "细分领域",
        "项目来源", "来源渠道", "项目阶段", "联系人", "联系电话",
        "联系邮箱", "初步介绍", "备注"
    ]
    
    df = pd.DataFrame(columns=columns)
    df.loc[0] = ["PRJ001", "示例项目", "示例", "TMT", "人工智能",
                 "FA推荐", "华兴资本", "Sourcing", "李四", "13900139000",
                 "test@example.com", "这是一个示例项目", ""]
    
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=project_import_template.xlsx"}
    )
