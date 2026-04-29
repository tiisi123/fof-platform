"""
邮箱爬虫服务 - 扫描邮箱净值报告并解析导入
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from cryptography.fernet import Fernet
import base64
import os

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.email_crawler import (
    EmailAccount, EmailType, ScanLog, ScanStatus, PendingImport, ImportStatus
)
from app.models.product import Product
from app.models.nav import NavData
from app.services.nav_parser import NavDataParser

logger = logging.getLogger(__name__)

# 加密密钥 - 生产环境应该从环境变量或配置文件读取
ENCRYPTION_KEY = os.environ.get("EMAIL_ENCRYPTION_KEY", "your-32-byte-key-here-for-fernet")


def get_fernet_key() -> bytes:
    """获取Fernet加密密钥"""
    key = ENCRYPTION_KEY
    if len(key) < 32:
        key = key.ljust(32, '0')
    return base64.urlsafe_b64encode(key[:32].encode())


def encrypt_password(password: str) -> str:
    """加密密码"""
    fernet = Fernet(get_fernet_key())
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    fernet = Fernet(get_fernet_key())
    return fernet.decrypt(encrypted.encode()).decode()


# 预设的IMAP服务器配置
IMAP_PRESETS = {
    EmailType.QQ: {
        "server": "imap.qq.com",
        "port": 993,
        "ssl": True
    },
    EmailType.NETEASE_163: {
        "server": "imap.163.com",
        "port": 993,
        "ssl": True
    },
    EmailType.NETEASE_126: {
        "server": "imap.126.com",
        "port": 993,
        "ssl": True
    },
    EmailType.GMAIL: {
        "server": "imap.gmail.com",
        "port": 993,
        "ssl": True
    },
    EmailType.OUTLOOK: {
        "server": "outlook.office365.com",
        "port": 993,
        "ssl": True
    },
    EmailType.EXCHANGE: {
        "server": "",  # 需要用户配置
        "port": 993,
        "ssl": True
    }
}


def get_imap_preset(email_type: EmailType) -> Dict[str, Any]:
    """获取邮箱类型的预设配置"""
    return IMAP_PRESETS.get(email_type, IMAP_PRESETS[EmailType.EXCHANGE])


class EmailCrawlerService:
    """邮箱爬虫服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None
    
    # ========== 邮箱账号管理 ==========
    
    def create_account(
        self,
        email_address: str,
        email_type: EmailType,
        username: str,
        password: str,
        imap_server: Optional[str] = None,
        imap_port: Optional[int] = None,
        use_ssl: bool = True,
        description: Optional[str] = None,
        scan_folder: str = "INBOX",
        filter_sender: Optional[str] = None,
        filter_subject: Optional[str] = None,
        scan_days: int = 7
    ) -> EmailAccount:
        """创建邮箱账号"""
        # 使用预设或自定义配置
        preset = get_imap_preset(email_type)
        
        account = EmailAccount(
            email_address=email_address,
            email_type=email_type,
            description=description,
            imap_server=imap_server or preset["server"],
            imap_port=imap_port or preset["port"],
            use_ssl=use_ssl,
            username=username,
            password_encrypted=encrypt_password(password),
            scan_folder=scan_folder,
            filter_sender=filter_sender,
            filter_subject=filter_subject,
            scan_days=scan_days,
            is_active=True
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def update_account(
        self,
        account_id: int,
        **kwargs
    ) -> Optional[EmailAccount]:
        """更新邮箱账号"""
        account = self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            return None
        
        # 如果更新密码，需要加密
        if "password" in kwargs:
            kwargs["password_encrypted"] = encrypt_password(kwargs.pop("password"))
        
        for key, value in kwargs.items():
            if hasattr(account, key) and value is not None:
                setattr(account, key, value)
        
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def delete_account(self, account_id: int) -> bool:
        """删除邮箱账号"""
        account = self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            return False
        
        self.db.delete(account)
        self.db.commit()
        return True
    
    def get_account(self, account_id: int) -> Optional[EmailAccount]:
        """获取邮箱账号"""
        return self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
    
    def list_accounts(self, is_active: Optional[bool] = None) -> List[EmailAccount]:
        """获取邮箱账号列表"""
        query = self.db.query(EmailAccount)
        if is_active is not None:
            query = query.filter(EmailAccount.is_active == is_active)
        return query.order_by(desc(EmailAccount.created_at)).all()
    
    # ========== 邮箱连接 ==========
    
    def test_connection(self, account_id: int) -> Tuple[bool, str]:
        """测试邮箱连接"""
        account = self.get_account(account_id)
        if not account:
            return False, "邮箱账号不存在"
        
        try:
            password = decrypt_password(account.password_encrypted)
            
            if account.use_ssl:
                conn = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            else:
                conn = imaplib.IMAP4(account.imap_server, account.imap_port)
            
            conn.login(account.username, password)
            
            # 尝试选择文件夹
            status, _ = conn.select(account.scan_folder, readonly=True)
            if status != "OK":
                conn.logout()
                return False, f"无法访问文件夹: {account.scan_folder}"
            
            conn.logout()
            return True, "连接成功"
            
        except imaplib.IMAP4.error as e:
            return False, f"IMAP错误: {str(e)}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def _connect(self, account: EmailAccount) -> imaplib.IMAP4_SSL:
        """建立IMAP连接"""
        password = decrypt_password(account.password_encrypted)
        
        if account.use_ssl:
            conn = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
        else:
            conn = imaplib.IMAP4(account.imap_server, account.imap_port)
        
        conn.login(account.username, password)
        return conn
    
    def _disconnect(self):
        """断开IMAP连接"""
        if self.imap_conn:
            try:
                self.imap_conn.logout()
            except:
                pass
            self.imap_conn = None
    
    # ========== 邮件扫描 ==========
    
    def scan_mailbox(self, account_id: int) -> ScanLog:
        """扫描邮箱"""
        account = self.get_account(account_id)
        if not account:
            raise ValueError("邮箱账号不存在")
        
        # 创建扫描日志
        scan_log = ScanLog(
            email_account_id=account_id,
            status=ScanStatus.RUNNING
        )
        self.db.add(scan_log)
        self.db.commit()
        self.db.refresh(scan_log)
        
        try:
            # 连接邮箱
            self.imap_conn = self._connect(account)
            self.imap_conn.select(account.scan_folder, readonly=True)
            
            # 构建搜索条件
            search_criteria = self._build_search_criteria(account)
            
            # 搜索邮件
            status, messages = self.imap_conn.search(None, search_criteria)
            if status != "OK":
                raise Exception("搜索邮件失败")
            
            email_ids = messages[0].split()
            scan_log.emails_found = len(email_ids)
            
            attachments_found = 0
            parsed_success = 0
            parsed_failed = 0
            
            # 处理每封邮件
            for email_id in email_ids:
                try:
                    attachment_count, success_count, failed_count = self._process_email(
                        email_id, scan_log, account
                    )
                    attachments_found += attachment_count
                    parsed_success += success_count
                    parsed_failed += failed_count
                except Exception as e:
                    logger.error(f"处理邮件 {email_id} 失败: {e}")
                    parsed_failed += 1
            
            # 更新扫描日志
            scan_log.attachments_found = attachments_found
            scan_log.parsed_success = parsed_success
            scan_log.parsed_failed = parsed_failed
            scan_log.status = ScanStatus.COMPLETED
            scan_log.scan_end = datetime.now()
            
            # 更新账号最后扫描时间
            account.last_scan_at = datetime.now()
            account.last_scan_status = ScanStatus.COMPLETED
            
        except Exception as e:
            scan_log.status = ScanStatus.FAILED
            scan_log.error_message = str(e)
            scan_log.scan_end = datetime.now()
            
            account.last_scan_status = ScanStatus.FAILED
            logger.error(f"扫描邮箱失败: {e}")
            
        finally:
            self._disconnect()
            self.db.commit()
            self.db.refresh(scan_log)
        
        return scan_log
    
    def _build_search_criteria(self, account: EmailAccount) -> str:
        """构建IMAP搜索条件"""
        criteria = []
        
        # 日期过滤 - 最近N天
        since_date = (datetime.now() - timedelta(days=account.scan_days)).strftime("%d-%b-%Y")
        criteria.append(f'SINCE {since_date}')
        
        # 发件人过滤
        if account.filter_sender:
            senders = [s.strip() for s in account.filter_sender.split(",") if s.strip()]
            if len(senders) == 1:
                criteria.append(f'FROM "{senders[0]}"')
            elif len(senders) > 1:
                # 多个发件人用OR连接
                or_criteria = " ".join([f'FROM "{s}"' for s in senders])
                criteria.append(f'(OR {or_criteria})')
        
        # 主题过滤
        if account.filter_subject:
            subjects = [s.strip() for s in account.filter_subject.split(",") if s.strip()]
            if len(subjects) == 1:
                criteria.append(f'SUBJECT "{subjects[0]}"')
            elif len(subjects) > 1:
                or_criteria = " ".join([f'SUBJECT "{s}"' for s in subjects])
                criteria.append(f'(OR {or_criteria})')
        
        # 只搜索有附件的邮件（不是所有服务器都支持）
        # criteria.append('HAS attachment')  # 部分服务器不支持
        
        return " ".join(criteria) if criteria else "ALL"
    
    def _decode_header_value(self, value: str) -> str:
        """解码邮件头"""
        if not value:
            return ""
        
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                charset = charset or "utf-8"
                try:
                    result.append(part.decode(charset))
                except:
                    result.append(part.decode("utf-8", errors="ignore"))
            else:
                result.append(part)
        return "".join(result)
    
    def _process_email(
        self,
        email_id: bytes,
        scan_log: ScanLog,
        account: EmailAccount
    ) -> Tuple[int, int, int]:
        """处理单封邮件，返回 (附件数, 成功数, 失败数)"""
        status, data = self.imap_conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            return 0, 0, 0
        
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # 解析邮件信息
        subject = self._decode_header_value(msg.get("Subject", ""))
        from_addr = self._decode_header_value(msg.get("From", ""))
        date_str = msg.get("Date", "")
        email_date = None
        try:
            email_date = parsedate_to_datetime(date_str)
        except:
            pass
        
        email_uid = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
        
        # 检查是否已处理过
        existing = self.db.query(PendingImport).filter(
            PendingImport.email_uid == email_uid
        ).first()
        if existing:
            return 0, 0, 0
        
        attachment_count = 0
        success_count = 0
        failed_count = 0
        
        # 遍历邮件部分，查找附件
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            filename = self._decode_header_value(filename)
            
            # 只处理Excel文件
            if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
                continue
            
            attachment_count += 1
            
            try:
                # 获取附件内容
                content = part.get_payload(decode=True)
                if not content:
                    failed_count += 1
                    continue
                
                # 解析净值数据
                parser = NavDataParser(content, filename)
                parse_success, df, parse_info = parser.parse()
                
                if parse_success and not df.empty:
                    # 尝试匹配产品
                    product_code = None
                    product_name = None
                    product_id = None
                    
                    if "product_code" in df.columns:
                        product_code = df["product_code"].iloc[0]
                    if "product_name" in df.columns:
                        product_name = df["product_name"].iloc[0]
                    
                    # 在数据库中查找匹配的产品
                    if product_code:
                        product = self.db.query(Product).filter(
                            Product.product_code == product_code
                        ).first()
                        if product:
                            product_id = product.id
                    
                    # 转换净值数据为JSON
                    nav_data = []
                    for _, row in df.iterrows():
                        nav_record = {
                            "nav_date": row.get("nav_date").strftime("%Y-%m-%d") if hasattr(row.get("nav_date"), "strftime") else str(row.get("nav_date")),
                            "unit_nav": float(row.get("unit_nav", 0)) if row.get("unit_nav") else None,
                            "cumulative_nav": float(row.get("cumulative_nav", 0)) if row.get("cumulative_nav") else None,
                        }
                        nav_data.append(nav_record)
                    
                    # 创建待导入记录
                    pending = PendingImport(
                        scan_log_id=scan_log.id,
                        email_subject=subject[:500] if subject else None,
                        email_from=from_addr[:255] if from_addr else None,
                        email_date=email_date,
                        email_uid=email_uid,
                        attachment_name=filename[:255],
                        attachment_size=len(content),
                        product_code=product_code,
                        product_name=product_name,
                        product_id=product_id,
                        nav_records_count=len(nav_data),
                        nav_data_json=nav_data,
                        parse_warnings="\n".join(parse_info.get("warnings", [])),
                        status=ImportStatus.PENDING
                    )
                    self.db.add(pending)
                    success_count += 1
                else:
                    # 解析失败，也创建记录但标记失败
                    pending = PendingImport(
                        scan_log_id=scan_log.id,
                        email_subject=subject[:500] if subject else None,
                        email_from=from_addr[:255] if from_addr else None,
                        email_date=email_date,
                        email_uid=email_uid,
                        attachment_name=filename[:255],
                        attachment_size=len(content),
                        status=ImportStatus.FAILED,
                        import_result="\n".join(parse_info.get("errors", ["解析失败"]))
                    )
                    self.db.add(pending)
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"处理附件 {filename} 失败: {e}")
                failed_count += 1
        
        self.db.commit()
        return attachment_count, success_count, failed_count
    
    # ========== 待导入数据管理 ==========
    
    def list_pending_imports(
        self,
        status: Optional[ImportStatus] = None,
        scan_log_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[PendingImport], int]:
        """获取待导入数据列表"""
        query = self.db.query(PendingImport)
        
        if status:
            query = query.filter(PendingImport.status == status)
        if scan_log_id:
            query = query.filter(PendingImport.scan_log_id == scan_log_id)
        
        total = query.count()
        items = query.order_by(desc(PendingImport.created_at)).offset(skip).limit(limit).all()
        
        return items, total
    
    def confirm_import(
        self,
        pending_id: int,
        product_id: int,
        user_id: int,
        conflict_action: str = "skip"  # skip | overwrite
    ) -> Tuple[bool, str, Dict[str, int]]:
        """确认导入净值数据"""
        pending = self.db.query(PendingImport).filter(PendingImport.id == pending_id).first()
        if not pending:
            return False, "记录不存在", {}
        
        if pending.status != ImportStatus.PENDING:
            return False, f"记录状态为 {pending.status}，无法导入", {}
        
        if not pending.nav_data_json:
            return False, "无净值数据", {}
        
        # 验证产品存在
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False, "产品不存在", {}
        
        try:
            imported = 0
            skipped = 0
            updated = 0
            
            for nav_record in pending.nav_data_json:
                nav_date = datetime.strptime(nav_record["nav_date"], "%Y-%m-%d").date()
                
                # 检查是否已存在
                existing = self.db.query(NavData).filter(
                    NavData.product_id == product_id,
                    NavData.nav_date == nav_date
                ).first()
                
                if existing:
                    if conflict_action == "skip":
                        skipped += 1
                        continue
                    elif conflict_action == "overwrite":
                        existing.unit_nav = nav_record.get("unit_nav")
                        existing.cumulative_nav = nav_record.get("cumulative_nav")
                        updated += 1
                else:
                    nav_data = NavData(
                        product_id=product_id,
                        nav_date=nav_date,
                        unit_nav=nav_record.get("unit_nav"),
                        cumulative_nav=nav_record.get("cumulative_nav")
                    )
                    self.db.add(nav_data)
                    imported += 1
            
            # 更新待导入记录状态
            pending.status = ImportStatus.IMPORTED
            pending.product_id = product_id
            pending.imported_at = datetime.now()
            pending.imported_by = user_id
            pending.import_result = f"导入: {imported}, 跳过: {skipped}, 更新: {updated}"
            
            self.db.commit()
            
            return True, "导入成功", {
                "imported": imported,
                "skipped": skipped,
                "updated": updated
            }
            
        except Exception as e:
            self.db.rollback()
            pending.status = ImportStatus.FAILED
            pending.import_result = str(e)
            self.db.commit()
            return False, f"导入失败: {str(e)}", {}
    
    def skip_import(self, pending_id: int) -> bool:
        """跳过导入"""
        pending = self.db.query(PendingImport).filter(PendingImport.id == pending_id).first()
        if not pending:
            return False
        
        pending.status = ImportStatus.SKIPPED
        pending.import_result = "用户手动跳过"
        self.db.commit()
        return True
    
    # ========== 扫描日志 ==========
    
    def list_scan_logs(
        self,
        account_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ScanLog], int]:
        """获取扫描日志列表"""
        query = self.db.query(ScanLog)
        
        if account_id:
            query = query.filter(ScanLog.email_account_id == account_id)
        
        total = query.count()
        items = query.order_by(desc(ScanLog.scan_start)).offset(skip).limit(limit).all()
        
        return items, total
    
    def get_scan_log(self, log_id: int) -> Optional[ScanLog]:
        """获取扫描日志详情"""
        return self.db.query(ScanLog).filter(ScanLog.id == log_id).first()
