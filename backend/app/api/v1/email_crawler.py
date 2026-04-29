"""
邮箱爬虫 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.email_crawler import EmailType, ImportStatus
from app.services.email_crawler_service import EmailCrawlerService, get_imap_preset, IMAP_PRESETS
from app.schemas.email_crawler import (
    EmailAccountCreate, EmailAccountUpdate, EmailAccountResponse, EmailAccountListResponse,
    ScanLogResponse, ScanLogListResponse,
    PendingImportResponse, PendingImportListResponse,
    ImportConfirmRequest, ImportResultResponse,
    TestConnectionResponse, ImapPresetResponse,
    EmailTypeEnum
)

router = APIRouter(prefix="/email-crawler", tags=["邮箱爬虫"])


# ========== IMAP预设 ==========

@router.get("/presets", response_model=List[ImapPresetResponse], summary="获取IMAP预设配置")
async def get_presets():
    """获取各邮箱类型的IMAP预设配置"""
    presets = []
    for email_type, config in IMAP_PRESETS.items():
        presets.append(ImapPresetResponse(
            email_type=EmailTypeEnum(email_type.value),
            server=config["server"],
            port=config["port"],
            ssl=config["ssl"]
        ))
    return presets


# ========== 邮箱账号管理 ==========

@router.post("/accounts", response_model=EmailAccountResponse, summary="添加邮箱账号")
async def create_account(
    data: EmailAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加邮箱账号配置"""
    service = EmailCrawlerService(db)
    
    try:
        account = service.create_account(
            email_address=data.email_address,
            email_type=EmailType(data.email_type.value),
            username=data.username,
            password=data.password,
            imap_server=data.imap_server,
            imap_port=data.imap_port,
            use_ssl=data.use_ssl,
            description=data.description,
            scan_folder=data.scan_folder,
            filter_sender=data.filter_sender,
            filter_subject=data.filter_subject,
            scan_days=data.scan_days
        )
        return EmailAccountResponse.model_validate(account)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts", response_model=EmailAccountListResponse, summary="获取邮箱账号列表")
async def list_accounts(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取邮箱账号列表"""
    service = EmailCrawlerService(db)
    accounts = service.list_accounts(is_active=is_active)
    return EmailAccountListResponse(
        items=[EmailAccountResponse.model_validate(a) for a in accounts],
        total=len(accounts)
    )


@router.get("/accounts/{account_id}", response_model=EmailAccountResponse, summary="获取邮箱账号详情")
async def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取邮箱账号详情"""
    service = EmailCrawlerService(db)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="邮箱账号不存在")
    return EmailAccountResponse.model_validate(account)


@router.put("/accounts/{account_id}", response_model=EmailAccountResponse, summary="更新邮箱账号")
async def update_account(
    account_id: int,
    data: EmailAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新邮箱账号配置"""
    service = EmailCrawlerService(db)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 转换 email_type
    if "email_type" in update_data and update_data["email_type"]:
        update_data["email_type"] = EmailType(update_data["email_type"].value)
    
    account = service.update_account(account_id, **update_data)
    if not account:
        raise HTTPException(status_code=404, detail="邮箱账号不存在")
    return EmailAccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}", summary="删除邮箱账号")
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除邮箱账号"""
    service = EmailCrawlerService(db)
    if not service.delete_account(account_id):
        raise HTTPException(status_code=404, detail="邮箱账号不存在")
    return {"message": "删除成功"}


# ========== 连接测试与扫描 ==========

@router.post("/accounts/{account_id}/test", response_model=TestConnectionResponse, summary="测试邮箱连接")
async def test_connection(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试邮箱IMAP连接"""
    service = EmailCrawlerService(db)
    success, message = service.test_connection(account_id)
    return TestConnectionResponse(success=success, message=message)


@router.post("/accounts/{account_id}/scan", response_model=ScanLogResponse, summary="立即扫描邮箱")
async def scan_mailbox(
    account_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """立即扫描指定邮箱"""
    service = EmailCrawlerService(db)
    
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="邮箱账号不存在")
    
    try:
        # 同步执行扫描（如果需要异步可以用 background_tasks）
        scan_log = service.scan_mailbox(account_id)
        
        response = ScanLogResponse.model_validate(scan_log)
        response.email_address = account.email_address
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 扫描日志 ==========

@router.get("/logs", response_model=ScanLogListResponse, summary="获取扫描日志列表")
async def list_scan_logs(
    account_id: Optional[int] = Query(None, description="邮箱账号ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取扫描日志列表"""
    service = EmailCrawlerService(db)
    items, total = service.list_scan_logs(account_id=account_id, skip=skip, limit=limit)
    
    response_items = []
    for log in items:
        resp = ScanLogResponse.model_validate(log)
        if log.email_account:
            resp.email_address = log.email_account.email_address
        response_items.append(resp)
    
    return ScanLogListResponse(items=response_items, total=total)


@router.get("/logs/{log_id}", response_model=ScanLogResponse, summary="获取扫描日志详情")
async def get_scan_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取扫描日志详情"""
    service = EmailCrawlerService(db)
    log = service.get_scan_log(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="扫描日志不存在")
    
    resp = ScanLogResponse.model_validate(log)
    if log.email_account:
        resp.email_address = log.email_account.email_address
    return resp


# ========== 待导入数据 ==========

@router.get("/pending", response_model=PendingImportListResponse, summary="获取待导入数据列表")
async def list_pending_imports(
    status: Optional[str] = Query(None, description="状态过滤"),
    scan_log_id: Optional[int] = Query(None, description="扫描日志ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待导入数据列表"""
    service = EmailCrawlerService(db)
    
    import_status = None
    if status:
        try:
            import_status = ImportStatus(status)
        except ValueError:
            pass
    
    items, total = service.list_pending_imports(
        status=import_status,
        scan_log_id=scan_log_id,
        skip=skip,
        limit=limit
    )
    
    response_items = []
    for item in items:
        resp = PendingImportResponse.model_validate(item)
        # 添加净值预览（前5条）
        if item.nav_data_json:
            resp.nav_preview = item.nav_data_json[:5]
        response_items.append(resp)
    
    return PendingImportListResponse(items=response_items, total=total)


@router.get("/pending/{pending_id}", response_model=PendingImportResponse, summary="获取待导入数据详情")
async def get_pending_import(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待导入数据详情"""
    service = EmailCrawlerService(db)
    items, _ = service.list_pending_imports(skip=0, limit=1)
    
    # 查找指定ID
    from app.models.email_crawler import PendingImport
    item = db.query(PendingImport).filter(PendingImport.id == pending_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    resp = PendingImportResponse.model_validate(item)
    if item.nav_data_json:
        resp.nav_preview = item.nav_data_json[:10]
    return resp


@router.post("/pending/{pending_id}/import", response_model=ImportResultResponse, summary="确认导入")
async def confirm_import(
    pending_id: int,
    data: ImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认导入净值数据到指定产品"""
    service = EmailCrawlerService(db)
    
    success, message, stats = service.confirm_import(
        pending_id=pending_id,
        product_id=data.product_id,
        user_id=current_user.id,
        conflict_action=data.conflict_action
    )
    
    return ImportResultResponse(
        success=success,
        message=message,
        imported=stats.get("imported", 0),
        skipped=stats.get("skipped", 0),
        updated=stats.get("updated", 0)
    )


@router.post("/pending/{pending_id}/skip", summary="跳过导入")
async def skip_import(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """跳过该条待导入数据"""
    service = EmailCrawlerService(db)
    if not service.skip_import(pending_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "已跳过"}
