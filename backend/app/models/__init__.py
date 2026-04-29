"""
数据模型 V2
"""
from app.models.user import User, UserRole, UserStatus
from app.models.manager import (
    Manager, ManagerStatus, ManagerContact, ManagerTeam, 
    PoolTransfer, PoolCategory, PrimaryStrategy
)
from app.models.product import Product, ProductStatus
from app.models.nav import NavData
from app.models.project import (
    Project, ProjectFollowUp, ProjectStageChange,
    ProjectStage, ProjectIndustry
)
from app.models.portfolio import (
    Portfolio, PortfolioStatus, PortfolioType, PortfolioComponent,
    PortfolioHolding, PortfolioNav, PortfolioAdjustment
)
from app.models.email_crawler import (
    EmailAccount, EmailType, ScanLog, ScanStatus, PendingImport, ImportStatus
)
from app.models.document import Document, DocumentCategory, DocumentRelationType
from app.models.audit_log import AuditLog
from app.models.ai_report import AIReport, ReportStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.news_article import NewsArticle, SentimentType
from app.models.project_cashflow import ProjectCashflow, CashflowType
from app.models.comment import Comment
from app.models.due_diligence import DueDiligenceFlow, DDStatus
from app.models.holdings_detail import HoldingsDetail
from app.models.calendar_event import CalendarEvent
from app.models.manager_edit_history import ManagerEditHistory
from app.models.project_review import ProjectReview, ReviewResult

__all__ = [
    "User",
    "UserRole",
    "UserStatus",
    "Manager",
    "ManagerStatus",
    "ManagerContact",
    "ManagerTeam",
    "PoolTransfer",
    "PoolCategory",
    "PrimaryStrategy",
    "Product",
    "ProductStatus",
    "NavData",
    "Project",
    "ProjectFollowUp",
    "ProjectStageChange",
    "ProjectStage",
    "ProjectIndustry",
    "Portfolio",
    "PortfolioStatus",
    "PortfolioType",
    "PortfolioComponent",
    "PortfolioHolding",
    "PortfolioNav",
    "PortfolioAdjustment",
    "EmailAccount",
    "EmailType",
    "ScanLog",
    "ScanStatus",
    "PendingImport",
    "ImportStatus",
    "Document",
    "DocumentCategory",
    "DocumentRelationType",
    "AuditLog",
    "AIReport",
    "ReportStatus",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "NewsArticle",
    "SentimentType",
    "ProjectCashflow",
    "CashflowType",
    "Comment",
    "DueDiligenceFlow",
    "DDStatus",
    "HoldingsDetail",
    "CalendarEvent",
    "ManagerEditHistory",
    "ProjectReview",
    "ReviewResult",
]
