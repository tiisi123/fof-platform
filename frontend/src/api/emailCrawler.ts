/**
 * 邮箱爬虫 API
 */
import request from "./request";

// ========== 类型定义 ==========

export type EmailType = 'qq' | '163' | '126' | 'gmail' | 'outlook' | 'exchange' | 'other'
export type ScanStatus = 'running' | 'completed' | 'failed'
export type ImportStatus = 'pending' | 'imported' | 'skipped' | 'failed'

export interface EmailAccount {
  id: number
  email_address: string
  email_type: EmailType
  description?: string
  imap_server: string
  imap_port: number
  use_ssl: boolean
  username: string
  scan_folder: string
  filter_sender?: string
  filter_subject?: string
  scan_days: number
  is_active: boolean
  last_scan_at?: string
  last_scan_status?: ScanStatus
  created_at: string
  updated_at: string
}

export interface EmailAccountCreate {
  email_address: string
  email_type: EmailType
  description?: string
  imap_server?: string
  imap_port?: number
  use_ssl?: boolean
  username: string
  password: string
  scan_folder?: string
  filter_sender?: string
  filter_subject?: string
  scan_days?: number
}

export interface EmailAccountUpdate {
  email_address?: string
  email_type?: EmailType
  description?: string
  imap_server?: string
  imap_port?: number
  use_ssl?: boolean
  username?: string
  password?: string
  scan_folder?: string
  filter_sender?: string
  filter_subject?: string
  scan_days?: number
  is_active?: boolean
}

export interface ScanLog {
  id: number
  email_account_id: number
  scan_start: string
  scan_end?: string
  emails_found: number
  attachments_found: number
  parsed_success: number
  parsed_failed: number
  status: ScanStatus
  error_message?: string
  email_address?: string
}

export interface NavPreview {
  nav_date: string
  unit_nav?: number
  cumulative_nav?: number
}

export interface PendingImport {
  id: number
  scan_log_id: number
  email_subject?: string
  email_from?: string
  email_date?: string
  attachment_name: string
  attachment_size?: number
  product_code?: string
  product_name?: string
  product_id?: number
  nav_records_count: number
  parse_warnings?: string
  status: ImportStatus
  import_result?: string
  imported_at?: string
  created_at: string
  nav_preview?: NavPreview[]
}

export interface ImapPreset {
  email_type: EmailType
  server: string
  port: number
  ssl: boolean
}

export interface ImportResult {
  success: boolean
  message: string
  imported: number
  skipped: number
  updated: number
}

// ========== API ==========

/**
 * 获取 IMAP 预设配置
 */
export function getImapPresets() {
  return request.get<ImapPreset[]>('/email-crawler/presets')
}

/**
 * 获取邮箱账号列表
 */
export function getEmailAccounts(params?: { is_active?: boolean }) {
  return request.get<{ items: EmailAccount[], total: number }>('/email-crawler/accounts', { params })
}

/**
 * 获取邮箱账号详情
 */
export function getEmailAccount(id: number) {
  return request.get<EmailAccount>(`/email-crawler/accounts/${id}`)
}

/**
 * 创建邮箱账号
 */
export function createEmailAccount(data: EmailAccountCreate) {
  return request.post<EmailAccount>('/email-crawler/accounts', data)
}

/**
 * 更新邮箱账号
 */
export function updateEmailAccount(id: number, data: EmailAccountUpdate) {
  return request.put<EmailAccount>(`/email-crawler/accounts/${id}`, data)
}

/**
 * 删除邮箱账号
 */
export function deleteEmailAccount(id: number) {
  return request.delete(`/email-crawler/accounts/${id}`)
}

/**
 * 测试邮箱连接
 */
export function testEmailConnection(id: number) {
  return request.post<{ success: boolean, message: string }>(`/email-crawler/accounts/${id}/test`)
}

/**
 * 扫描邮箱
 */
export function scanMailbox(id: number) {
  return request.post<ScanLog>(`/email-crawler/accounts/${id}/scan`)
}

/**
 * 获取扫描日志列表
 */
export function getScanLogs(params?: { account_id?: number, skip?: number, limit?: number }) {
  return request.get<{ items: ScanLog[], total: number }>('/email-crawler/logs', { params })
}

/**
 * 获取扫描日志详情
 */
export function getScanLog(id: number) {
  return request.get<ScanLog>(`/email-crawler/logs/${id}`)
}

/**
 * 获取待导入数据列表
 */
export function getPendingImports(params?: { status?: ImportStatus, scan_log_id?: number, skip?: number, limit?: number }) {
  return request.get<{ items: PendingImport[], total: number }>('/email-crawler/pending', { params })
}

/**
 * 获取待导入数据详情
 */
export function getPendingImport(id: number) {
  return request.get<PendingImport>(`/email-crawler/pending/${id}`)
}

/**
 * 确认导入
 */
export function confirmImport(id: number, data: { product_id: number, conflict_action: 'skip' | 'overwrite' }) {
  return request.post<ImportResult>(`/email-crawler/pending/${id}/import`, data)
}

/**
 * 跳过导入
 */
export function skipImport(id: number) {
  return request.post(`/email-crawler/pending/${id}/skip`)
}

// 邮箱类型显示名称
export const EMAIL_TYPE_LABELS: Record<EmailType, string> = {
  qq: 'QQ邮箱',
  '163': '网易163邮箱',
  '126': '网易126邮箱',
  gmail: 'Gmail (谷歌邮箱)',
  outlook: 'Outlook/Hotmail',
  exchange: 'Exchange/企业邮箱',
  other: '其他'
}

// 扫描状态显示
export const SCAN_STATUS_LABELS: Record<ScanStatus, string> = {
  running: '扫描中',
  completed: '已完成',
  failed: '失败'
}

// 导入状态显示
export const IMPORT_STATUS_LABELS: Record<ImportStatus, string> = {
  pending: '待处理',
  imported: '已导入',
  skipped: '已跳过',
  failed: '失败'
}
