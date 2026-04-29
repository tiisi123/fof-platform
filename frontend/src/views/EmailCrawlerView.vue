<template>
  <div class="email-crawler-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>邮箱爬虫</h2>
        <p class="subtitle">自动从邮箱扫描净值报告并导入系统</p>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon accounts-icon">
          <el-icon :size="22"><Message /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ accounts.length }}</span>
          <span class="stat-label">邮箱账号</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon active-icon">
          <el-icon :size="22"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ accounts.filter(a => a.is_active).length }}</span>
          <span class="stat-label">已启用</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon logs-icon">
          <el-icon :size="22"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ logTotal }}</span>
          <span class="stat-label">扫描记录</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon pending-icon">
          <el-icon :size="22"><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ pendingTotal }}</span>
          <span class="stat-label">待导入</span>
        </div>
      </div>
    </div>

    <!-- Tab 标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="handleTabChange">
      <!-- 邮箱配置 -->
      <el-tab-pane label="邮箱配置" name="accounts">
        <el-card class="glass-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>邮箱账号列表</span>
              <el-button type="primary" :icon="Plus" @click="handleAddAccount">
                添加邮箱
              </el-button>
            </div>
          </template>

          <!-- 空状态 -->
          <el-empty v-if="!loadingAccounts && accounts.length === 0" description="暂无邮箱账号，点击上方按钮添加">
            <el-button type="primary" @click="handleAddAccount">添加邮箱</el-button>
          </el-empty>

          <el-table v-else :data="accounts" v-loading="loadingAccounts" stripe>
            <el-table-column prop="email_address" label="邮箱地址" min-width="200" />
            <el-table-column prop="email_type" label="类型" width="120">
              <template #default="{ row }">
                {{ EMAIL_TYPE_LABELS[row.email_type] }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="备注" min-width="120" />
            <el-table-column prop="scan_days" label="扫描天数" width="100" align="center" />
            <el-table-column prop="is_active" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_scan_at" label="最后扫描" width="160">
              <template #default="{ row }">
                {{ row.last_scan_at ? formatDateTime(row.last_scan_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleTestConnection(row)">
                  测试
                </el-button>
                <el-button link type="success" @click="handleScan(row)" :loading="scanningId === row.id">
                  扫描
                </el-button>
                <el-button link type="primary" @click="handleEditAccount(row)">
                  编辑
                </el-button>
                <el-button link type="danger" @click="handleDeleteAccount(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 扫描日志 -->
      <el-tab-pane label="扫描日志" name="logs" lazy>
        <el-card class="glass-card" shadow="never">
          <el-empty v-if="!loadingLogs && scanLogs.length === 0" description="暂无扫描记录" />
          <el-table v-else :data="scanLogs" v-loading="loadingLogs" stripe>
            <el-table-column prop="email_address" label="邮箱" min-width="200" />
            <el-table-column prop="scan_start" label="扫描时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.scan_start) }}
              </template>
            </el-table-column>
            <el-table-column prop="emails_found" label="邮件数" width="80" align="center" />
            <el-table-column prop="attachments_found" label="附件数" width="80" align="center" />
            <el-table-column prop="parsed_success" label="解析成功" width="90" align="center">
              <template #default="{ row }">
                <span class="text-success">{{ row.parsed_success }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="parsed_failed" label="解析失败" width="90" align="center">
              <template #default="{ row }">
                <span :class="row.parsed_failed > 0 ? 'text-danger' : ''">{{ row.parsed_failed }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ SCAN_STATUS_LABELS[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="logPage"
              v-model:page-size="logPageSize"
              :total="logTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchScanLogs"
              @current-change="fetchScanLogs"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 待导入数据 -->
      <el-tab-pane label="待导入" name="pending" lazy>
        <el-card class="glass-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>待处理数据</span>
              <el-select v-model="pendingStatus" placeholder="状态筛选" clearable style="width: 120px" @change="fetchPendingImports">
                <el-option label="待处理" value="pending" />
                <el-option label="已导入" value="imported" />
                <el-option label="已跳过" value="skipped" />
                <el-option label="失败" value="failed" />
              </el-select>
            </div>
          </template>

          <el-empty v-if="!loadingPending && pendingImports.length === 0" description="暂无待处理数据" />
          <el-table v-else :data="pendingImports" v-loading="loadingPending" stripe>
            <el-table-column prop="attachment_name" label="附件名称" min-width="200" />
            <el-table-column prop="email_from" label="发件人" min-width="150" />
            <el-table-column prop="email_date" label="邮件日期" width="160">
              <template #default="{ row }">
                {{ row.email_date ? formatDateTime(row.email_date) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="product_code" label="产品代码" width="120" />
            <el-table-column prop="nav_records_count" label="记录数" width="80" align="center" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getImportStatusType(row.status)" size="small">
                  {{ IMPORT_STATUS_LABELS[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button link type="primary" @click="handleImport(row)">
                    导入
                  </el-button>
                  <el-button link type="info" @click="handleSkip(row)">
                    跳过
                  </el-button>
                </template>
                <span v-else class="text-muted">{{ row.import_result }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pendingPage"
              v-model:page-size="pendingPageSize"
              :total="pendingTotal"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchPendingImports"
              @current-change="fetchPendingImports"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑邮箱对话框 -->
    <el-dialog
      v-model="accountDialogVisible"
      :title="editingAccount ? '编辑邮箱' : '添加邮箱'"
      width="600px"
      destroy-on-close
    >
      <el-form ref="accountFormRef" :model="accountForm" :rules="accountRules" label-width="100px">
        <el-form-item label="邮箱类型" prop="email_type">
          <el-select v-model="accountForm.email_type" placeholder="选择邮箱类型" @change="onEmailTypeChange">
            <el-option label="QQ邮箱" value="qq" />
            <el-option label="网易163邮箱" value="163" />
            <el-option label="网易126邮箱" value="126" />
            <el-option label="Exchange/企业邮箱" value="exchange" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱地址" prop="email_address">
          <el-input v-model="accountForm.email_address" placeholder="example@qq.com" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="accountForm.username" placeholder="通常与邮箱地址相同" />
        </el-form-item>
        <el-form-item label="密码/授权码" prop="password">
          <el-input v-model="accountForm.password" type="password" placeholder="QQ邮箱请使用授权码" show-password />
        </el-form-item>
        <el-form-item label="IMAP服务器" prop="imap_server">
          <el-input v-model="accountForm.imap_server" placeholder="imap.qq.com" />
        </el-form-item>
        <el-form-item label="端口" prop="imap_port">
          <el-input-number v-model="accountForm.imap_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="使用SSL">
          <el-switch v-model="accountForm.use_ssl" />
        </el-form-item>
        <el-form-item label="扫描天数">
          <el-input-number v-model="accountForm.scan_days" :min="1" :max="365" />
          <span class="form-hint">扫描最近N天的邮件</span>
        </el-form-item>
        <el-form-item label="发件人过滤">
          <el-input v-model="accountForm.filter_sender" placeholder="多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="主题关键词">
          <el-input v-model="accountForm.filter_subject" placeholder="多个用逗号分隔，如：净值,周报" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="accountForm.description" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="accountDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAccountForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入确认对话框 -->
    <el-dialog v-model="importDialogVisible" title="确认导入" width="500px">
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="附件名称">
          <span>{{ importingItem?.attachment_name }}</span>
        </el-form-item>
        <el-form-item label="净值记录数">
          <span>{{ importingItem?.nav_records_count }} 条</span>
        </el-form-item>
        <el-form-item label="目标产品" required>
          <el-select v-model="importForm.product_id" filterable placeholder="选择产品" style="width: 100%">
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="`${p.product_code} - ${p.product_name}`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="冲突处理">
          <el-radio-group v-model="importForm.conflict_action">
            <el-radio value="skip">跳过已存在的日期</el-radio>
            <el-radio value="overwrite">覆盖已存在的数据</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importing">
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Message, CircleCheck, Document, Clock } from '@element-plus/icons-vue'
import {
  getEmailAccounts, createEmailAccount, updateEmailAccount, deleteEmailAccount,
  testEmailConnection, scanMailbox, getScanLogs, getPendingImports,
  confirmImport, skipImport, getImapPresets,
  EMAIL_TYPE_LABELS, SCAN_STATUS_LABELS, IMPORT_STATUS_LABELS,
  type EmailAccount, type ScanLog, type PendingImport, type EmailType, type ImapPreset
} from '@/api/emailCrawler'
import { productApi } from '@/api/product'

// Tab
const activeTab = ref('accounts')

// 邮箱账号
const accounts = ref<EmailAccount[]>([])
const loadingAccounts = ref(false)
const scanningId = ref<number | null>(null)

// 扫描日志
const scanLogs = ref<ScanLog[]>([])
const loadingLogs = ref(false)
const logPage = ref(1)
const logPageSize = ref(20)
const logTotal = ref(0)

// 待导入
const pendingImports = ref<PendingImport[]>([])
const loadingPending = ref(false)
const pendingPage = ref(1)
const pendingPageSize = ref(50)
const pendingTotal = ref(0)
const pendingStatus = ref<string>('')

// 产品列表（用于导入时选择）
const products = ref<any[]>([])

// IMAP 预设
const imapPresets = ref<ImapPreset[]>([])

// 添加/编辑邮箱
const accountDialogVisible = ref(false)
const editingAccount = ref<EmailAccount | null>(null)
const accountFormRef = ref<FormInstance>()
const submitting = ref(false)
const accountForm = ref({
  email_address: '',
  email_type: 'qq' as EmailType,
  username: '',
  password: '',
  imap_server: '',
  imap_port: 993,
  use_ssl: true,
  scan_days: 7,
  filter_sender: '',
  filter_subject: '',
  description: ''
})

const accountRules: FormRules = {
  email_address: [{ required: true, message: '请输入邮箱地址', trigger: 'blur' }],
  email_type: [{ required: true, message: '请选择邮箱类型', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码/授权码', trigger: 'blur' }],
  imap_server: [{ required: true, message: '请输入IMAP服务器', trigger: 'blur' }]
}

// 导入对话框
const importDialogVisible = ref(false)
const importingItem = ref<PendingImport | null>(null)
const importing = ref(false)
const importForm = ref({
  product_id: null as number | null,
  conflict_action: 'skip' as 'skip' | 'overwrite'
})

// 加载数据
const fetchAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await getEmailAccounts()
    accounts.value = res.items
  } catch (e) {
    console.error(e)
  } finally {
    loadingAccounts.value = false
  }
}

const fetchScanLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await getScanLogs({
      skip: (logPage.value - 1) * logPageSize.value,
      limit: logPageSize.value
    })
    scanLogs.value = res.items
    logTotal.value = res.total
  } catch (e) {
    console.error(e)
  } finally {
    loadingLogs.value = false
  }
}

const fetchPendingImports = async () => {
  loadingPending.value = true
  try {
    const res = await getPendingImports({
      status: pendingStatus.value || undefined,
      skip: (pendingPage.value - 1) * pendingPageSize.value,
      limit: pendingPageSize.value
    })
    pendingImports.value = res.items
    pendingTotal.value = res.total
  } catch (e) {
    console.error(e)
  } finally {
    loadingPending.value = false
  }
}

const fetchProducts = async () => {
  try {
    const res = await productApi.getList({ limit: 1000 })
    products.value = res.items
  } catch (e) {
    console.error(e)
  }
}

const fetchImapPresets = async () => {
  try {
    imapPresets.value = await getImapPresets()
  } catch (e) {
    console.error(e)
  }
}

// 邮箱类型变化时自动填充服务器配置
const onEmailTypeChange = (type: EmailType) => {
  const preset = imapPresets.value.find(p => p.email_type === type)
  if (preset) {
    accountForm.value.imap_server = preset.server
    accountForm.value.imap_port = preset.port
    accountForm.value.use_ssl = preset.ssl
  }
}

// 添加邮箱
const handleAddAccount = () => {
  editingAccount.value = null
  accountForm.value = {
    email_address: '',
    email_type: 'qq',
    username: '',
    password: '',
    imap_server: 'imap.qq.com',
    imap_port: 993,
    use_ssl: true,
    scan_days: 7,
    filter_sender: '',
    filter_subject: '',
    description: ''
  }
  accountDialogVisible.value = true
}

// 编辑邮箱
const handleEditAccount = (row: EmailAccount) => {
  editingAccount.value = row
  accountForm.value = {
    email_address: row.email_address,
    email_type: row.email_type,
    username: row.username,
    password: '',  // 编辑时不显示密码
    imap_server: row.imap_server,
    imap_port: row.imap_port,
    use_ssl: row.use_ssl,
    scan_days: row.scan_days,
    filter_sender: row.filter_sender || '',
    filter_subject: row.filter_subject || '',
    description: row.description || ''
  }
  accountDialogVisible.value = true
}

// 提交邮箱表单
const submitAccountForm = async () => {
  const valid = await accountFormRef.value?.validate()
  if (!valid) return

  submitting.value = true
  try {
    if (editingAccount.value) {
      // 编辑
      const updateData: any = { ...accountForm.value }
      if (!updateData.password) delete updateData.password  // 不更新密码
      await updateEmailAccount(editingAccount.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 新增
      await createEmailAccount(accountForm.value)
      ElMessage.success('添加成功')
    }
    accountDialogVisible.value = false
    fetchAccounts()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 删除邮箱
const handleDeleteAccount = async (row: EmailAccount) => {
  await ElMessageBox.confirm(`确定删除邮箱 ${row.email_address} 吗？`, '提示', { type: 'warning' })
  try {
    await deleteEmailAccount(row.id)
    ElMessage.success('删除成功')
    fetchAccounts()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

// 测试连接
const handleTestConnection = async (row: EmailAccount) => {
  try {
    const res = await testEmailConnection(row.id)
    if (res.success) {
      ElMessage.success(res.message)
    } else {
      ElMessage.error(res.message)
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '测试失败')
  }
}

// 扫描邮箱
const handleScan = async (row: EmailAccount) => {
  scanningId.value = row.id
  try {
    const res = await scanMailbox(row.id)
    ElMessage.success(`扫描完成：发现 ${res.emails_found} 封邮件，${res.attachments_found} 个附件，成功解析 ${res.parsed_success} 个`)
    fetchAccounts()
    fetchScanLogs()
    fetchPendingImports()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '扫描失败')
  } finally {
    scanningId.value = null
  }
}

// 导入
const handleImport = (row: PendingImport) => {
  importingItem.value = row
  importForm.value = {
    product_id: row.product_id,
    conflict_action: 'skip'
  }
  importDialogVisible.value = true
}

// 提交导入
const submitImport = async () => {
  if (!importForm.value.product_id) {
    ElMessage.warning('请选择目标产品')
    return
  }
  if (!importingItem.value) return

  importing.value = true
  try {
    const res = await confirmImport(importingItem.value.id, {
      product_id: importForm.value.product_id,
      conflict_action: importForm.value.conflict_action
    })
    if (res.success) {
      ElMessage.success(`导入成功：新增 ${res.imported} 条，跳过 ${res.skipped} 条，更新 ${res.updated} 条`)
      importDialogVisible.value = false
      fetchPendingImports()
    } else {
      ElMessage.error(res.message)
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

// 跳过
const handleSkip = async (row: PendingImport) => {
  await ElMessageBox.confirm('确定跳过该条数据吗？', '提示')
  try {
    await skipImport(row.id)
    ElMessage.success('已跳过')
    fetchPendingImports()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

// 工具函数
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getImportStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    imported: 'success',
    skipped: 'info',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// Tab 切换时刷新对应数据
const handleTabChange = (tab: string) => {
  if (tab === 'accounts') fetchAccounts()
  else if (tab === 'logs') fetchScanLogs()
  else if (tab === 'pending') fetchPendingImports()
}

// 初始化
onMounted(() => {
  fetchImapPresets()
  fetchAccounts()
  fetchScanLogs()
  fetchPendingImports()
  fetchProducts()
})
</script>

<style scoped>
.email-crawler-view {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.subtitle {
  color: var(--text-secondary);
  margin: 0;
  font-size: 14px;
}

/* 统计概览 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-icon.accounts-icon {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.stat-icon.active-icon {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}

.stat-icon.logs-icon {
  background: linear-gradient(135deg, #e6a23c, #cf8e2e);
}

.stat-icon.pending-icon {
  background: linear-gradient(135deg, #909399, #73767a);
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 卡片 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.text-muted {
  color: var(--text-muted);
  font-size: 12px;
}

.form-hint {
  margin-left: 10px;
  color: var(--text-muted);
  font-size: 12px;
}

.main-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

/* glass-card override for dark theme */
:deep(.glass-card) {
  background: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
}

:deep(.glass-card .el-card__header) {
  border-bottom: 1px solid var(--card-border);
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
