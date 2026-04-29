"""
AI智能报告 API - 生成 + CRUD持久化
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional, List
from datetime import datetime, timedelta
import secrets

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.ai_report import AIReport, ReportStatus
from app.services.ai_report_service import AIReportService, ReportType

router = APIRouter(prefix="/ai-reports", tags=["AI智能报告"])


@router.get("/product/{product_id}", summary="生成产品分析报告")
async def generate_product_report(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成指定产品的AI分析报告
    
    包含：
    - 基本信息
    - 净值摘要
    - 多周期业绩指标
    - 风险预警
    - AI分析文本
    - 投资建议
    """
    service = AIReportService(db)
    report = service.generate_product_report(product_id)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return report


@router.get("/manager/{manager_id}", summary="生成管理人分析报告")
async def generate_manager_report(
    manager_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成指定管理人的AI分析报告
    
    包含：
    - 管理人基本信息
    - 旗下产品概览
    - 代表产品分析
    - AI分析文本
    - 跟踪建议
    """
    service = AIReportService(db)
    report = service.generate_manager_report(manager_id)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return report


@router.get("/portfolio/{portfolio_id}", summary="生成组合分析报告")
async def generate_portfolio_report(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成指定组合的AI分析报告
    
    包含：
    - 组合基本信息
    - 成分明细
    - 策略分布
    - 加权业绩
    - AI分析文本
    - 配置建议
    """
    service = AIReportService(db)
    report = service.generate_portfolio_report(portfolio_id)
    
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    
    return report


@router.get("/market", summary="生成市场概览报告")
async def generate_market_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成市场概览AI分析报告
    
    包含：
    - 各策略产品统计
    - 业绩排行对比
    - 跟踪池分布
    - 预警汇总
    - AI分析文本
    - 市场建议
    """
    service = AIReportService(db)
    report = service.generate_market_overview()
    
    return report


@router.get("/types", summary="获取报告类型列表")
async def get_report_types(
    current_user: User = Depends(get_current_user)
):
    """获取可用的AI报告类型"""
    return [
        {"key": ReportType.PRODUCT, "name": "产品分析报告", "description": "针对单个产品的业绩、风险、预警分析", "required_param": "product_id"},
        {"key": ReportType.MANAGER, "name": "管理人分析报告", "description": "针对管理人及其旗下产品的综合分析", "required_param": "manager_id"},
        {"key": ReportType.PORTFOLIO, "name": "组合分析报告", "description": "针对投资组合的成分、配置、业绩分析", "required_param": "portfolio_id"},
        {"key": ReportType.MARKET, "name": "市场概览报告", "description": "全市场策略表现、跟踪池分布、预警汇总", "required_param": None},
    ]


# ========== 报告持久化 CRUD ==========

@router.get("/saved", summary="获取已保存报告列表")
async def list_saved_reports(
    report_type: Optional[str] = Query(None, description="报告类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取已保存的AI报告列表，支持筛选和分页"""
    query = db.query(AIReport).filter(AIReport.parent_id == None)  # 只显示最新版本
    
    if report_type:
        query = query.filter(AIReport.report_type == report_type)
    if status:
        query = query.filter(AIReport.status == status)
    if keyword:
        query = query.filter(
            or_(AIReport.title.contains(keyword), AIReport.analysis_text.contains(keyword))
        )
    
    total = query.count()
    reports = query.order_by(desc(AIReport.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "report_type": r.report_type,
                "summary": r.summary,
                "status": r.status,
                "version": r.version,
                "created_by_name": r.creator.username if r.creator else None,
                "product_name": r.product.product_name if r.product else None,
                "manager_name": r.manager.manager_name if r.manager else None,
                "portfolio_name": r.portfolio.name if r.portfolio else None,
                "report_date": r.report_date.isoformat() if r.report_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in reports
        ],
    }


@router.post("/save", summary="保存报告")
async def save_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    保存AI报告到数据库。
    请求体: { title, report_type, content, summary?, product_id?, manager_id?, portfolio_id? }
    """
    body = await request.json()
    
    title = body.get("title")
    report_type = body.get("report_type")
    content = body.get("content")
    
    if not title or not report_type or not content:
        raise HTTPException(status_code=400, detail="title, report_type, content 为必填")
    
    # 提取分析文本用于搜索
    analysis_text = ""
    analysis_sections = content.get("analysis", []) if isinstance(content, dict) else []
    for section in analysis_sections:
        if isinstance(section, dict):
            analysis_text += section.get("title", "") + " " + section.get("content", "") + "\n"
    
    report = AIReport(
        title=title,
        report_type=report_type,
        content=content,
        summary=body.get("summary", content.get("summary", "") if isinstance(content, dict) else ""),
        analysis_text=analysis_text.strip() or None,
        product_id=body.get("product_id"),
        manager_id=body.get("manager_id"),
        portfolio_id=body.get("portfolio_id"),
        status=ReportStatus.DRAFT,
        created_by=current_user.id,
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return {"id": report.id, "message": "报告已保存"}


@router.get("/saved/{report_id}", summary="获取已保存报告详情")
async def get_saved_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取已保存报告的完整内容"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "summary": report.summary,
        "content": report.content,
        "status": report.status,
        "version": report.version,
        "product_id": report.product_id,
        "manager_id": report.manager_id,
        "portfolio_id": report.portfolio_id,
        "product_name": report.product.product_name if report.product else None,
        "manager_name": report.manager.manager_name if report.manager else None,
        "portfolio_name": report.portfolio.name if report.portfolio else None,
        "created_by_name": report.creator.username if report.creator else None,
        "report_date": report.report_date.isoformat() if report.report_date else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }


@router.put("/saved/{report_id}", summary="更新已保存报告")
async def update_saved_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新报告内容（创建新版本）"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    body = await request.json()
    
    if body.get("title"):
        report.title = body["title"]
    if body.get("summary"):
        report.summary = body["summary"]
    if body.get("status"):
        report.status = body["status"]
    if body.get("content"):
        report.content = body["content"]
        # 更新搜索文本
        analysis_sections = body["content"].get("analysis", []) if isinstance(body["content"], dict) else []
        text = ""
        for section in analysis_sections:
            if isinstance(section, dict):
                text += section.get("title", "") + " " + section.get("content", "") + "\n"
        report.analysis_text = text.strip() or None
    
    report.updated_by = current_user.id
    
    db.commit()
    return {"message": "报告已更新"}


@router.delete("/saved/{report_id}", summary="删除已保存报告")
async def delete_saved_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除已保存报告"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    db.delete(report)
    db.commit()
    return {"message": "报告已删除"}


@router.put("/saved/{report_id}/publish", summary="发布报告")
async def publish_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将报告状态改为已发布"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report.status = ReportStatus.PUBLISHED
    report.updated_by = current_user.id
    db.commit()
    return {"message": "报告已发布"}


@router.get("/saved/{report_id}/versions", summary="获取报告历史版本")
async def get_report_versions(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取报告的历史版本列表"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    versions = db.query(AIReport).filter(
        AIReport.parent_id == report_id
    ).order_by(desc(AIReport.version)).all()
    
    return [
        {
            "id": v.id,
            "version": v.version,
            "title": v.title,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "created_by_name": v.creator.username if v.creator else None,
        }
        for v in versions
    ]


@router.post("/saved/{report_id}/share", summary="创建分享链接")
async def create_share_link(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建报告分享链接，可设置密码和有效期"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    body = await request.json()
    
    # 生成唯一share token
    report.share_token = secrets.token_urlsafe(32)
    report.is_shared = True
    report.share_password = body.get("password") or None
    
    expires_days = body.get("expires_days")
    if expires_days and isinstance(expires_days, int):
        report.share_expires_at = datetime.utcnow() + timedelta(days=expires_days)
    else:
        report.share_expires_at = None  # 永不过期
    
    report.updated_by = current_user.id
    db.commit()
    
    return {
        "share_token": report.share_token,
        "share_url": f"/shared/report/{report.share_token}",
        "has_password": bool(report.share_password),
        "expires_at": report.share_expires_at.isoformat() if report.share_expires_at else None,
    }


@router.delete("/saved/{report_id}/share", summary="取消分享")
async def revoke_share(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消报告分享"""
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report.share_token = None
    report.is_shared = False
    report.share_password = None
    report.share_expires_at = None
    report.updated_by = current_user.id
    db.commit()
    
    return {"message": "分享已取消"}


@router.post("/shared/{share_token}", summary="通过分享链接查看报告")
async def view_shared_report(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """公开接口，无需登录，通过share_token查看报告"""
    report = db.query(AIReport).filter(
        AIReport.share_token == share_token,
        AIReport.is_shared == True,
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="分享链接无效或已取消")
    
    # 检查过期
    if report.share_expires_at and datetime.utcnow() > report.share_expires_at:
        raise HTTPException(status_code=410, detail="分享链接已过期")
    
    # 检查密码
    if report.share_password:
        body = await request.json()
        if body.get("password") != report.share_password:
            raise HTTPException(status_code=403, detail="分享密码错误")
    
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "summary": report.summary,
        "content": report.content,
        "report_date": report.report_date.isoformat() if report.report_date else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }
