<template>
  <div class="alerts-view">
    <div class="page-header">
      <div class="page-header-row">
        <div>
          <h1>异常预警</h1>
          <p class="subtitle">监控产品净值异常、回撤预警、更新状态</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="openRulesDialog">
            <el-icon><Setting /></el-icon>
            规则配置
          </el-button>
          <el-button @click="testDingtalk" :loading="dingtalkTesting" size="small">测试钉钉</el-button>
          <el-button type="warning" @click="pushToDingtalk" :loading="dingtalkPushing" :disabled="!summary.total">
            <el-icon><Promotion /></el-icon>
            推送到钉钉
          </el-button>
          <el-tag :type="dingtalkConfig.enabled ? 'success' : 'info'" size="small">
            钉钉: {{ dingtalkConfig.enabled ? '已启用' : '未启用' }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card critical">
        <div class="stat-icon">
          <el-icon :size="24"><WarningFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ summary.by_level?.critical || 0 }}</div>
          <div class="stat-label">严重预警</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">
          <el-icon :size="24"><Warning /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ summary.by_level?.warning || 0 }}</div>
          <div class="stat-label">一般预警</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">
          <el-icon :size="24"><InfoFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ summary.by_level?.info || 0 }}</div>
          <div class="stat-label">提示信息</div>
        </div>
      </div>
      <div class="stat-card total">
        <div class="stat-icon">
          <el-icon :size="24"><Bell /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ summary.total || 0 }}</div>
          <div class="stat-label">预警总数</div>
        </div>
      </div>
    </div>

    <!-- 按类型统计 -->
    <div class="type-stats">
      <div 
        v-for="(count, type) in summary.by_type" 
        :key="type"
        class="type-badge"
        :class="{ active: filters.type === type }"
        @click="toggleTypeFilter(type)"
      >
        <span class="type-name">{{ getTypeName(type) }}</span>
        <span class="type-count">{{ count }}</span>
      </div>
    </div>

    <!-- 预警列表 -->
    <div class="alerts-list" v-loading="loading">
      <div v-if="pagedAlerts.length === 0" class="empty-state">
        <el-icon :size="48"><CircleCheck /></el-icon>
        <p>暂无预警信息</p>
      </div>
      
      <div 
        v-for="alert in pagedAlerts" 
        :key="`${alert.product_id}-${alert.type}-${alert.date}`"
        class="alert-item"
        :class="alert.level"
      >
        <div class="alert-level">
          <el-icon v-if="alert.level === 'critical'" class="critical"><WarningFilled /></el-icon>
          <el-icon v-else-if="alert.level === 'warning'" class="warning"><Warning /></el-icon>
          <el-icon v-else class="info"><InfoFilled /></el-icon>
        </div>
        
        <div class="alert-content">
          <div class="alert-header">
            <span class="alert-title">{{ alert.title }}</span>
            <el-tag size="small" :type="getTypeTagType(alert.type)">
              {{ getTypeName(alert.type) }}
            </el-tag>
          </div>
          
          <div class="alert-product">
            <router-link :to="`/products/${alert.product_id}`">
              {{ alert.product_name }}
            </router-link>
            <span class="manager-name" v-if="alert.manager_name">
              · {{ alert.manager_name }}
            </span>
          </div>
          
          <div class="alert-message">{{ alert.message }}</div>
        </div>
        
        <div class="alert-date">
          {{ alert.date }}
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="filteredAlerts.length > 0" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="filteredAlerts.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="pagination.page = 1"
          @current-change="() => {}"
        />
      </div>
    </div>

    <!-- 规则配置对话框 -->
    <el-dialog v-model="rulesDialogVisible" title="预警规则配置" width="640px" destroy-on-close>
      <el-alert
        title="调整各类预警的触发阈值，修改后立即生效"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      />
      <el-form v-if="rulesForm" label-position="top" class="rules-form" v-loading="rulesLoading">
        <div class="rules-group">
          <h4 class="rules-group-title">净值下跌预警</h4>
          <div class="rules-row">
            <el-form-item label="警告阈值（单日跌幅）">
              <el-input-number
                v-model="rulesForm.nav_drop_warning"
                :min="-50" :max="0" :step="0.5" :precision="1"
                style="width: 100%"
              />
              <span class="rule-unit">%</span>
            </el-form-item>
            <el-form-item label="严重阈值（单日跌幅）">
              <el-input-number
                v-model="rulesForm.nav_drop_critical"
                :min="-50" :max="0" :step="0.5" :precision="1"
                style="width: 100%"
              />
              <span class="rule-unit">%</span>
            </el-form-item>
          </div>
        </div>

        <div class="rules-group">
          <h4 class="rules-group-title">回撤预警</h4>
          <div class="rules-row">
            <el-form-item label="警告阈值（累计回撤）">
              <el-input-number
                v-model="rulesForm.drawdown_warning"
                :min="-80" :max="0" :step="1" :precision="0"
                style="width: 100%"
              />
              <span class="rule-unit">%</span>
            </el-form-item>
            <el-form-item label="严重阈值（累计回撤）">
              <el-input-number
                v-model="rulesForm.drawdown_critical"
                :min="-80" :max="0" :step="1" :precision="0"
                style="width: 100%"
              />
              <span class="rule-unit">%</span>
            </el-form-item>
          </div>
        </div>

        <div class="rules-group">
          <h4 class="rules-group-title">其他预警</h4>
          <div class="rules-row">
            <el-form-item label="未更新天数阈值">
              <el-input-number
                v-model="rulesForm.no_update_days"
                :min="1" :max="365" :step="1"
                style="width: 100%"
              />
              <span class="rule-unit">天</span>
            </el-form-item>
            <el-form-item label="波动率异常倍数">
              <el-input-number
                v-model="rulesForm.volatility_threshold"
                :min="1" :max="10" :step="0.1" :precision="1"
                style="width: 100%"
              />
              <span class="rule-unit">倍</span>
            </el-form-item>
          </div>
          <div class="rules-row">
            <el-form-item label="异常波动标准差倍数">
              <el-input-number
                v-model="rulesForm.anomaly_std_multiple"
                :min="1" :max="10" :step="0.1" :precision="1"
                style="width: 100%"
              />
              <span class="rule-unit">倍</span>
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="resetRules">恢复默认</el-button>
        <el-button @click="rulesDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRules" :loading="rulesSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  WarningFilled, 
  Warning, 
  InfoFilled, 
  Bell, 
  CircleCheck,
  Promotion,
  Setting
} from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const summary = ref<any>({})
const dingtalkPushing = ref(false)
const dingtalkTesting = ref(false)
const dingtalkConfig = ref<any>({ enabled: false, webhook_configured: false })

// 规则配置
const rulesDialogVisible = ref(false)
const rulesLoading = ref(false)
const rulesSaving = ref(false)
const rulesForm = ref<any>(null)

const defaultRules = {
  nav_drop_warning: -3,
  nav_drop_critical: -5,
  drawdown_warning: -10,
  drawdown_critical: -20,
  no_update_days: 14,
  volatility_threshold: 2.0,
  anomaly_std_multiple: 3.0
}

const openRulesDialog = async () => {
  rulesDialogVisible.value = true
  rulesLoading.value = true
  try {
    const res = await request.get('/alerts/rules')
    const data = res.data || res
    const rules = data.rules || {}
    // 后端存储的是小数(如-0.03)，前端显示为百分比(如-3)
    rulesForm.value = {
      nav_drop_warning: (rules.nav_drop_warning || -0.03) * 100,
      nav_drop_critical: (rules.nav_drop_critical || -0.05) * 100,
      drawdown_warning: (rules.drawdown_warning || -0.10) * 100,
      drawdown_critical: (rules.drawdown_critical || -0.20) * 100,
      no_update_days: rules.no_update_days || 14,
      volatility_threshold: rules.volatility_threshold || 2.0,
      anomaly_std_multiple: rules.anomaly_std_multiple || 3.0,
    }
  } catch (e) {
    rulesForm.value = { ...defaultRules }
  } finally {
    rulesLoading.value = false
  }
}

const saveRules = async () => {
  if (!rulesForm.value) return
  rulesSaving.value = true
  try {
    // 前端百分比转回小数
    const rules = {
      nav_drop_warning: rulesForm.value.nav_drop_warning / 100,
      nav_drop_critical: rulesForm.value.nav_drop_critical / 100,
      drawdown_warning: rulesForm.value.drawdown_warning / 100,
      drawdown_critical: rulesForm.value.drawdown_critical / 100,
      no_update_days: rulesForm.value.no_update_days,
      volatility_threshold: rulesForm.value.volatility_threshold,
      anomaly_std_multiple: rulesForm.value.anomaly_std_multiple,
    }
    await request.put('/alerts/rules', { rules })
    ElMessage.success('预警规则保存成功')
    rulesDialogVisible.value = false
    loadAlerts()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    rulesSaving.value = false
  }
}

const resetRules = () => {
  rulesForm.value = { ...defaultRules }
}

const filters = reactive({
  type: '' as string
})

const pagination = reactive({
  page: 1,
  pageSize: 20
})

// 类型名称映射
const typeNameMap: Record<string, string> = {
  nav_drop: '净值下跌',
  nav_anomaly: '异常波动',
  drawdown: '回撤预警',
  no_update: '未更新',
  volatility: '波动率异常'
}

const getTypeName = (type: string) => typeNameMap[type] || type

const getTypeTagType = (type: string) => {
  const types: Record<string, string> = {
    nav_drop: 'danger',
    drawdown: 'warning',
    nav_anomaly: 'warning',
    no_update: 'info',
    volatility: ''
  }
  return types[type] || 'info'
}

// 筛选后的预警
const filteredAlerts = computed(() => {
  const alerts = summary.value.alerts || []
  if (!filters.type) return alerts
  return alerts.filter((a: any) => a.type === filters.type)
})

// 分页后的预警
const pagedAlerts = computed(() => {
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredAlerts.value.slice(start, end)
})

const toggleTypeFilter = (type: string) => {
  filters.type = filters.type === type ? '' : type
  pagination.page = 1 // 切换筛选时重置页码
}

// 加载预警数据
const loadAlerts = async () => {
  loading.value = true
  try {
    const res = await request.get('/alerts')
    summary.value = res.data || res || {}
  } catch (e) {
    console.error('加载预警失败', e)
  } finally {
    loading.value = false
  }
}

const pushToDingtalk = async () => {
  dingtalkPushing.value = true
  try {
    const res = await request.post('/alerts/dingtalk/push')
    const data = res.data || res
    ElMessage.success(data.message || '推送成功')
  } catch (e: any) {
    ElMessage.error(e.message || '推送失败')
  } finally {
    dingtalkPushing.value = false
  }
}

const testDingtalk = async () => {
  dingtalkTesting.value = true
  try {
    const res = await request.post('/alerts/dingtalk/test')
    const data = res.data || res
    if (data.success) {
      ElMessage.success('测试消息发送成功')
    } else {
      ElMessage.warning('发送失败，请检查钉钉配置')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '测试失败')
  } finally {
    dingtalkTesting.value = false
  }
}

const loadDingtalkConfig = async () => {
  try {
    const res = await request.get('/alerts/dingtalk/config')
    dingtalkConfig.value = res.data || res || {}
  } catch (e) {
    // ignore
  }
}

onMounted(() => {
  loadAlerts()
  loadDingtalkConfig()
})
</script>

<style scoped>
.alerts-view {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-header .subtitle {
  color: var(--text-secondary);
  margin: 0;
}

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
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card.critical .stat-icon {
  background: linear-gradient(135deg, #f56c6c 0%, #c45656 100%);
}

.stat-card.warning .stat-icon {
  background: linear-gradient(135deg, #e6a23c 0%, #cf8e2e 100%);
}

.stat-card.info .stat-icon {
  background: linear-gradient(135deg, #909399 0%, #73767a 100%);
}

.stat-card.total .stat-icon {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.type-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.type-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-badge:hover {
  border-color: var(--el-color-primary);
}

.type-badge.active {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: white;
}

.type-badge.active .type-count {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.type-name {
  font-size: 14px;
}

.type-count {
  background: var(--hover-bg);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.alerts-list {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  overflow: hidden;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-state .el-icon {
  color: #67c23a;
  margin-bottom: 16px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--card-border);
  transition: background 0.2s;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-item:hover {
  background: var(--hover-bg);
}

.alert-item.critical {
  border-left: 3px solid #f56c6c;
}

.alert-item.warning {
  border-left: 3px solid #e6a23c;
}

.alert-item.info {
  border-left: 3px solid #909399;
}

.alert-level {
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-level .critical {
  color: #f56c6c;
}

.alert-level .warning {
  color: #e6a23c;
}

.alert-level .info {
  color: #909399;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.alert-title {
  font-weight: 500;
  color: var(--text-primary);
}

.alert-product {
  font-size: 13px;
  margin-bottom: 4px;
}

.alert-product a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.alert-product a:hover {
  text-decoration: underline;
}

.manager-name {
  color: var(--text-secondary);
}

.alert-message {
  font-size: 13px;
  color: var(--text-secondary);
}

.alert-date {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid var(--card-border);
}

/* 规则配置对话框 */
.rules-form {
  max-height: 500px;
  overflow-y: auto;
}

.rules-group {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.rules-group-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.rules-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.rule-unit {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  display: block;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .rules-row {
    grid-template-columns: 1fr;
  }
}
</style>
