<template>
  <div class="ai-reports-view">
    <div class="page-header">
      <h1>AI智能报告</h1>
      <p class="subtitle">基于数据分析自动生成投资分析报告</p>
    </div>

    <!-- Tab切换 -->
    <el-tabs v-model="activeTab" class="report-tabs">
      <el-tab-pane label="生成报告" name="generate" />
      <el-tab-pane :label="`已保存报告 (${savedTotal})`" name="saved" />
    </el-tabs>

    <!-- ===== 生成报告 Tab ===== -->
    <template v-if="activeTab === 'generate'">
    <div class="report-types">
      <div 
        v-for="type in reportTypes" 
        :key="type.key"
        class="type-card"
        :class="{ active: selectedType === type.key }"
        @click="selectType(type.key)"
      >
        <div class="type-icon">
          <el-icon :size="24">
            <component :is="getTypeIcon(type.key)" />
          </el-icon>
        </div>
        <div class="type-info">
          <div class="type-name">{{ type.name }}</div>
          <div class="type-desc">{{ type.description }}</div>
        </div>
      </div>
    </div>

    <!-- 参数选择 -->
    <div class="params-section" v-if="selectedType">
      <div class="params-row">
        <!-- 产品选择 -->
        <div v-if="selectedType === 'product'" class="param-item">
          <label>选择产品 <span class="param-count">({{ products.length }} 个)</span></label>
          <el-select 
            v-model="selectedProductId" 
            placeholder="请选择产品"
            filterable
            no-data-text="暂无产品数据，请先在产品管理中添加"
            style="width: 300px"
          >
            <el-option 
              v-for="p in products" 
              :key="p.id" 
              :label="`${p.product_name} (${p.product_code || ''})`" 
              :value="p.id"
            />
          </el-select>
        </div>

        <!-- 管理人选择 -->
        <div v-if="selectedType === 'manager'" class="param-item">
          <label>选择管理人 <span class="param-count">({{ managers.length }} 个)</span></label>
          <el-select 
            v-model="selectedManagerId" 
            placeholder="请选择管理人"
            filterable
            no-data-text="暂无管理人数据，请先在管理人模块添加"
            style="width: 300px"
          >
            <el-option 
              v-for="m in managers" 
              :key="m.id" 
              :label="`${m.manager_name} (${m.short_name || m.manager_code || ''})`" 
              :value="m.id"
            />
          </el-select>
        </div>

        <!-- 组合选择 -->
        <div v-if="selectedType === 'portfolio'" class="param-item">
          <label>选择组合 <span class="param-count">({{ portfolios.length }} 个)</span></label>
          <el-select 
            v-model="selectedPortfolioId" 
            placeholder="请选择组合"
            filterable
            no-data-text="暂无投资组合，请先在组合管理中创建"
            style="width: 300px"
          >
            <el-option 
              v-for="pf in portfolios" 
              :key="pf.id" 
              :label="pf.name" 
              :value="pf.id"
            />
          </el-select>
        </div>

        <el-button 
          v-if="selectedType !== 'market'"
          type="primary" 
          :loading="generating"
          :disabled="!canGenerate"
          @click="generateReport"
        >
          <el-icon><MagicStick /></el-icon>
          生成报告
        </el-button>
        <el-button 
          v-else
          type="primary" 
          :loading="generating"
          @click="generateReport"
        >
          <el-icon><MagicStick /></el-icon>
          生成市场概览报告
        </el-button>
      </div>
      <!-- 提示信息 -->
      <div v-if="selectedType === 'product' && products.length === 0" class="param-hint">
        <el-icon><Warning /></el-icon>
        当前没有产品数据，请先在“产品管理”模块中添加产品并导入净值数据
      </div>
      <div v-if="selectedType === 'manager' && managers.length === 0" class="param-hint">
        <el-icon><Warning /></el-icon>
        当前没有管理人数据，请先在“管理人”模块中添加管理人
      </div>
      <div v-if="selectedType === 'portfolio' && portfolios.length === 0" class="param-hint">
        <el-icon><Warning /></el-icon>
        当前没有投资组合，请先在“组合管理”模块中创建组合
      </div>
      <div v-if="selectedType === 'market'" class="param-hint info">
        <el-icon><InfoFilled /></el-icon>
        市场概览报告将分析全市场各策略表现、跟踪池分布、预警汇总，无需选择具体对象
      </div>
    </div>

    <!-- 报告展示 -->
    <div class="report-content" v-if="report" v-loading="generating">
      <div class="report-header">
        <h2>{{ report.title }}</h2>
      <div class="report-meta">
          <span>生成时间：{{ formatTime(report.generated_at) }}</span>
          <el-button type="success" size="small" @click="saveCurrentReport" :loading="saving">
            <el-icon><FolderChecked /></el-icon>
            保存报告
          </el-button>
          <el-dropdown trigger="click">
            <el-button text type="primary">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="exportWord(report)">导出 Word</el-dropdown-item>
                <el-dropdown-item @click="exportPdf">导出 PDF（打印）</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 摘要 -->
      <div class="report-summary">
        <el-icon><InfoFilled /></el-icon>
        <span>{{ report.summary }}</span>
      </div>

      <!-- 基本信息 -->
      <div class="report-section" v-if="report.basic_info">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div v-for="(value, key) in formatBasicInfo(report.basic_info)" :key="key" class="info-item">
            <span class="info-label">{{ key }}</span>
            <span class="info-value">{{ value || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 业绩指标 -->
      <div class="report-section" v-if="report.performance && Object.keys(report.performance).length">
        <h3>业绩指标</h3>
        <div class="metrics-table">
          <table>
            <thead>
              <tr>
                <th>周期</th>
                <th>总收益</th>
                <th>年化收益</th>
                <th>年化波动</th>
                <th>最大回撤</th>
                <th>夏普比率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(metrics, period) in report.performance" :key="period">
                <td>{{ formatPeriod(period) }}</td>
                <td :class="getReturnClass(metrics.total_return)">
                  {{ formatPercent(metrics.total_return) }}
                </td>
                <td :class="getReturnClass(metrics.annualized_return)">
                  {{ formatPercent(metrics.annualized_return) }}
                </td>
                <td>{{ formatPercent(metrics.annualized_volatility) }}</td>
                <td class="negative">{{ formatPercent(metrics.max_drawdown) }}</td>
                <td>{{ formatNumber(metrics.sharpe_ratio) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 预警信息 -->
      <div class="report-section" v-if="report.alerts && report.alerts.total > 0">
        <h3>
          风险预警
          <el-tag size="small" :type="report.alerts.critical > 0 ? 'danger' : 'warning'">
            {{ report.alerts.total }} 条
          </el-tag>
        </h3>
        <div class="alerts-list">
          <div v-for="(alert, idx) in report.alerts.items" :key="idx" class="alert-item" :class="alert.level">
            <el-icon v-if="alert.level === 'critical'"><WarningFilled /></el-icon>
            <el-icon v-else><Warning /></el-icon>
            <span class="alert-text">{{ alert.title }}：{{ alert.message }}</span>
          </div>
        </div>
      </div>

      <!-- AI分析 -->
      <div class="report-section" v-if="report.analysis && report.analysis.length">
        <h3>AI分析</h3>
        <div class="analysis-sections">
          <div v-for="(section, idx) in report.analysis" :key="idx" class="analysis-item">
            <h4>{{ section.title }}</h4>
            <p>{{ section.content }}</p>
          </div>
        </div>
      </div>

      <!-- 成分明细（组合报告） -->
      <div class="report-section" v-if="report.components && report.components.length">
        <h3>成分明细</h3>
        <div class="components-table">
          <table>
            <thead>
              <tr>
                <th>产品名称</th>
                <th>管理人</th>
                <th>策略</th>
                <th>权重</th>
                <th>近1年收益</th>
                <th>预警</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="comp in report.components" :key="comp.product_id">
                <td>{{ comp.product_name }}</td>
                <td>{{ comp.manager_name }}</td>
                <td>{{ comp.strategy_type }}</td>
                <td>{{ formatPercent(comp.weight) }}</td>
                <td :class="getReturnClass(comp.metrics?.total_return)">
                  {{ formatPercent(comp.metrics?.total_return) }}
                </td>
                <td>
                  <el-tag v-if="comp.alerts_count > 0" size="small" type="warning">
                    {{ comp.alerts_count }}
                  </el-tag>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 策略统计（市场报告） -->
      <div class="report-section" v-if="report.strategy_stats && Object.keys(report.strategy_stats).length">
        <h3>策略表现对比</h3>
        <div class="strategy-table">
          <table>
            <thead>
              <tr>
                <th>策略</th>
                <th>产品数</th>
                <th>平均收益</th>
                <th>中位数收益</th>
                <th>最佳收益</th>
                <th>最差收益</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(stats, name) in report.strategy_stats" :key="name">
                <td>{{ name }}</td>
                <td>{{ stats.count }}</td>
                <td :class="getReturnClass(stats.avg_return)">{{ formatPercent(stats.avg_return) }}</td>
                <td :class="getReturnClass(stats.median_return)">{{ formatPercent(stats.median_return) }}</td>
                <td class="positive">{{ formatPercent(stats.best_return) }}</td>
                <td class="negative">{{ formatPercent(stats.worst_return) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 建议 -->
      <div class="report-section" v-if="report.recommendations && report.recommendations.length">
        <h3>投资建议</h3>
        <div class="recommendations">
          <div v-for="(rec, idx) in report.recommendations" :key="idx" class="rec-item">
            <el-icon><CircleCheck /></el-icon>
            <span>{{ rec }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!report && !generating">
      <el-icon :size="64"><Document /></el-icon>
      <p v-if="!selectedType">请先选择报告类型，然后点击“生成报告”</p>
      <p v-else-if="generating">报告生成中，请稍候...</p>
      <p v-else>选择对应的{{ selectedType === 'product' ? '产品' : selectedType === 'manager' ? '管理人' : selectedType === 'portfolio' ? '组合' : '' }}并点击“生成报告”按钮</p>
      <div class="empty-tips" v-if="!selectedType">
        <div class="tip-item">
          <span class="tip-num">1</span>
          <span>选择报告类型（产品/管理人/组合/市场）</span>
        </div>
        <div class="tip-item">
          <span class="tip-num">2</span>
          <span>选择分析对象（市场报告无需选择）</span>
        </div>
        <div class="tip-item">
          <span class="tip-num">3</span>
          <span>点击生成，AI将自动分析并输出报告</span>
        </div>
      </div>
    </div>
    </template>

    <!-- ===== 已保存报告 Tab ===== -->
    <template v-if="activeTab === 'saved'">
    <div class="saved-reports">
      <!-- 筛选栏 -->
      <div class="saved-filters">
        <el-select v-model="savedFilter.report_type" placeholder="报告类型" clearable style="width: 150px">
          <el-option label="产品报告" value="product" />
          <el-option label="管理人报告" value="manager" />
          <el-option label="组合报告" value="portfolio" />
          <el-option label="市场报告" value="market" />
        </el-select>
        <el-select v-model="savedFilter.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-input v-model="savedFilter.keyword" placeholder="搜索报告..." clearable style="width: 200px" @keyup.enter="loadSavedReports" />
        <el-button type="primary" @click="loadSavedReports">搜索</el-button>
      </div>

      <!-- 报告列表 -->
      <div class="saved-list" v-loading="loadingSaved">
        <div v-if="savedReports.length === 0 && !loadingSaved" class="empty-state">
          <el-icon :size="48"><Document /></el-icon>
          <p>暂无已保存的报告</p>
        </div>
        <div v-for="item in savedReports" :key="item.id" class="saved-card">
          <div class="saved-card-header">
            <div class="saved-title-row">
              <h3>{{ item.title }}</h3>
              <el-tag size="small" :type="getStatusType(item.status)">{{ getStatusLabel(item.status) }}</el-tag>
              <el-tag size="small" type="info">{{ getTypeLabel(item.report_type) }}</el-tag>
            </div>
            <div class="saved-actions">
              <el-button text type="primary" size="small" @click="viewSavedReport(item.id)">查看</el-button>
              <el-button text type="warning" size="small" @click="editSavedReport(item.id)">编辑</el-button>
              <el-button v-if="item.status === 'draft'" text type="success" size="small" @click="publishReport(item.id)">发布</el-button>
              <el-button text size="small" @click="openShareDialog(item)"><el-icon><Share /></el-icon>分享</el-button>
              <el-button text type="danger" size="small" @click="deleteSavedReport(item.id)">删除</el-button>
            </div>
          </div>
          <div class="saved-card-body">
            <p class="saved-summary">{{ item.summary || '无摘要' }}</p>
            <div class="saved-meta">
              <span v-if="item.product_name">产品: {{ item.product_name }}</span>
              <span v-if="item.manager_name">管理人: {{ item.manager_name }}</span>
              <span v-if="item.portfolio_name">组合: {{ item.portfolio_name }}</span>
              <span>创建人: {{ item.created_by_name || '-' }}</span>
              <span>时间: {{ formatTime(item.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="saved-pagination" v-if="savedTotal > savedFilter.page_size">
        <el-pagination
          v-model:current-page="savedFilter.page"
          :page-size="savedFilter.page_size"
          :total="savedTotal"
          layout="prev, pager, next"
          @current-change="loadSavedReports"
        />
      </div>
    </div>

    <!-- 查看报告弹窗 -->
    <el-dialog v-model="viewDialogVisible" :title="viewingReport?.title || '报告详情'" width="80%" top="5vh">
      <div v-if="viewingReport" class="report-content">
        <div class="report-summary" v-if="viewingReport.summary">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ viewingReport.summary }}</span>
        </div>
        <div v-if="viewingReport.content">
          <!-- AI分析 -->
          <div class="report-section" v-if="viewingReport.content.analysis?.length">
            <h3>AI分析</h3>
            <div class="analysis-sections">
              <div v-for="(section, idx) in viewingReport.content.analysis" :key="idx" class="analysis-item">
                <h4>{{ section.title }}</h4>
                <p>{{ section.content }}</p>
              </div>
            </div>
          </div>
          <!-- 建议 -->
          <div class="report-section" v-if="viewingReport.content.recommendations?.length">
            <h3>投资建议</h3>
            <div class="recommendations">
              <div v-for="(rec, idx) in viewingReport.content.recommendations" :key="idx" class="rec-item">
                <el-icon><CircleCheck /></el-icon>
                <span>{{ rec }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="dialog-meta">
          <span>状态: {{ getStatusLabel(viewingReport.status) }}</span>
          <span>创建: {{ viewingReport.created_by_name || '-' }}</span>
          <span>时间: {{ formatTime(viewingReport.created_at) }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="exportWord(viewingReport)">导出 Word</el-button>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 编辑报告弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑报告" width="80%" top="5vh" :close-on-click-modal="false">
      <div v-if="editFormData" class="edit-report-form">
        <el-form label-width="80px">
          <el-form-item label="标题">
            <el-input v-model="editFormData.title" />
          </el-form-item>
          <el-form-item label="摘要">
            <el-input v-model="editFormData.summary" type="textarea" :rows="2" />
          </el-form-item>
          <el-divider content-position="left">AI分析内容</el-divider>
          <div v-for="(section, idx) in editFormData.analysis" :key="idx" class="edit-analysis-section">
            <div class="flex items-center gap-2 mb-2">
              <el-input v-model="section.title" placeholder="段落标题" style="width: 300px" />
              <el-button text type="danger" size="small" @click="editFormData.analysis.splice(idx, 1)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-input v-model="section.content" type="textarea" :rows="4" placeholder="分析内容" />
          </div>
          <el-button size="small" class="mt-2" @click="editFormData.analysis.push({ title: '', content: '' })">
            <el-icon class="mr-1"><Plus /></el-icon>添加分析段落
          </el-button>
          <el-divider content-position="left">投资建议</el-divider>
          <div v-for="(rec, idx) in editFormData.recommendations" :key="idx" class="flex items-center gap-2 mb-2">
            <el-input v-model="editFormData.recommendations[idx]" placeholder="建议内容" />
            <el-button text type="danger" size="small" @click="editFormData.recommendations.splice(idx, 1)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button size="small" @click="editFormData.recommendations.push('')">
            <el-icon class="mr-1"><Plus /></el-icon>添加建议
          </el-button>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit" :loading="savingEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分享对话框 -->
    <el-dialog v-model="shareDialogVisible" title="分享报告" width="500px">
      <div v-if="sharingReport">
        <template v-if="!shareResult">
          <el-form label-width="100px">
            <el-form-item label="设置密码">
              <el-input v-model="shareForm.password" placeholder="留空则无需密码" show-password />
            </el-form-item>
            <el-form-item label="有效期">
              <el-select v-model="shareForm.expires_days" style="width: 100%">
                <el-option :value="0" label="永不过期" />
                <el-option :value="7" label="7天" />
                <el-option :value="30" label="30天" />
                <el-option :value="90" label="90天" />
              </el-select>
            </el-form-item>
          </el-form>
        </template>
        <template v-else>
          <div class="share-result">
            <p class="text-sm card-desc mb-3">分享链接已生成：</p>
            <el-input :model-value="fullShareUrl" readonly>
              <template #append>
                <el-button @click="copyShareLink">复制</el-button>
              </template>
            </el-input>
            <div class="mt-3 text-sm card-desc">
              <span v-if="shareResult.has_password">🔒 需要密码访问</span>
              <span v-else>🔓 无密码</span>
              <span class="ml-4" v-if="shareResult.expires_at">⛳ 过期时间: {{ formatTime(shareResult.expires_at) }}</span>
              <span class="ml-4" v-else>∞ 永不过期</span>
            </div>
          </div>
        </template>
      </div>
      <template #footer>
        <template v-if="!shareResult">
          <el-button @click="shareDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateShare" :loading="creatingShare">生成分享链接</el-button>
        </template>
        <template v-else>
          <el-button @click="shareDialogVisible = false">关闭</el-button>
        </template>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  MagicStick, 
  Download, 
  InfoFilled,
  WarningFilled,
  Warning,
  CircleCheck,
  Document,
  Goods,
  User,
  Coin,
  TrendCharts,
  FolderChecked,
  Share,
  Edit,
  Delete,
  Plus
} from '@element-plus/icons-vue'
import request from '@/api/request'

const activeTab = ref('generate')
const generating = ref(false)
const saving = ref(false)
const selectedType = ref<string>('')
const selectedProductId = ref<number | null>(null)
const selectedManagerId = ref<number | null>(null)
const selectedPortfolioId = ref<number | null>(null)

const products = ref<any[]>([])
const managers = ref<any[]>([])
const portfolios = ref<any[]>([])

const report = ref<any>(null)

// 已保存报告相关
const savedReports = ref<any[]>([])
const savedTotal = ref(0)
const loadingSaved = ref(false)
const savedFilter = reactive({
  report_type: '',
  status: '',
  keyword: '',
  page: 1,
  page_size: 10,
})
const viewDialogVisible = ref(false)
const viewingReport = ref<any>(null)

const reportTypes = [
  { key: 'product', name: '产品分析报告', description: '针对单个产品的业绩、风险分析' },
  { key: 'manager', name: '管理人分析报告', description: '管理人及旗下产品综合分析' },
  { key: 'portfolio', name: '组合分析报告', description: '投资组合的配置、业绩分析' },
  { key: 'market', name: '市场概览报告', description: '全市场策略表现、预警汇总' },
]

const getTypeIcon = (type: string) => {
  const icons: Record<string, any> = {
    product: Goods,
    manager: User,
    portfolio: Coin,
    market: TrendCharts,
  }
  return icons[type] || Document
}

const canGenerate = computed(() => {
  if (selectedType.value === 'product') return !!selectedProductId.value
  if (selectedType.value === 'manager') return !!selectedManagerId.value
  if (selectedType.value === 'portfolio') return !!selectedPortfolioId.value
  if (selectedType.value === 'market') return true
  return false
})

const selectType = (type: string) => {
  selectedType.value = type
  report.value = null
}

const loadData = async () => {
  try {
    const [prodRes, mgrRes, pfRes] = await Promise.allSettled([
      request.get('/products', { params: { page_size: 500 } }),
      request.get('/managers', { params: { page_size: 500 } }),
      request.get('/portfolios', { params: { limit: 100 } }),
    ])
    if (prodRes.status === 'fulfilled') {
      const d = prodRes.value
      products.value = d.data?.items || d.items || []
    }
    if (mgrRes.status === 'fulfilled') {
      const d = mgrRes.value
      managers.value = d.data?.items || d.items || []
    }
    if (pfRes.status === 'fulfilled') {
      const d = pfRes.value
      portfolios.value = d.data?.items || d.items || []
    }
  } catch (e) {
    console.error('加载数据失败', e)
  }
}

const generateReport = async () => {
  generating.value = true
  report.value = null
  
  try {
    let url = ''
    if (selectedType.value === 'product') {
      url = `/ai-reports/product/${selectedProductId.value}`
    } else if (selectedType.value === 'manager') {
      url = `/ai-reports/manager/${selectedManagerId.value}`
    } else if (selectedType.value === 'portfolio') {
      url = `/ai-reports/portfolio/${selectedPortfolioId.value}`
    } else if (selectedType.value === 'market') {
      url = '/ai-reports/market'
    }
    
    const res = await request.get(url)
    report.value = res.data || res
    ElMessage.success('报告生成成功')
  } catch (e: any) {
    ElMessage.error(e.message || '生成报告失败')
  } finally {
    generating.value = false
  }
}

// ============ 导出 Word ============
const buildReportHtml = (rpt: any): string => {
  let html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head><meta charset="utf-8"><style>
  body { font-family: 'Microsoft YaHei', sans-serif; color: #333; line-height: 1.8; }
  h1 { font-size: 22px; border-bottom: 2px solid #409eff; padding-bottom: 8px; }
  h2 { font-size: 16px; color: #409eff; margin-top: 20px; }
  h3 { font-size: 14px; color: #606266; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
  th { background: #f5f7fa; font-weight: 600; }
  .summary { background: #ecf5ff; padding: 12px; border-radius: 4px; color: #409eff; margin: 12px 0; }
  /* 中国A股习惯：红涨绿跌 */
  .positive { color: #f56c6c; } .negative { color: #67c23a; }
  .rec { padding: 4px 0; }
  .meta { color: #999; font-size: 12px; margin-top: 20px; }
</style></head><body>`

  html += `<h1>${rpt.title || 'AI智能报告'}</h1>`
  if (rpt.summary) html += `<div class="summary">${rpt.summary}</div>`

  // 基本信息
  if (rpt.basic_info) {
    html += '<h2>基本信息</h2><table>'
    const labels = formatBasicInfo(rpt.basic_info)
    for (const [k, v] of Object.entries(labels)) {
      html += `<tr><td style="width:120px;font-weight:600">${k}</td><td>${v || '-'}</td></tr>`
    }
    html += '</table>'
  }

  // 业绩指标
  if (rpt.performance && Object.keys(rpt.performance).length) {
    html += '<h2>业绩指标</h2><table><tr><th>周期</th><th>总收益</th><th>年化收益</th><th>年化波动</th><th>最大回撤</th><th>夏普比率</th></tr>'
    for (const [period, m] of Object.entries(rpt.performance) as [string, any][]) {
      html += `<tr><td>${formatPeriod(period)}</td><td>${formatPercent(m.total_return)}</td><td>${formatPercent(m.annualized_return)}</td><td>${formatPercent(m.annualized_volatility)}</td><td>${formatPercent(m.max_drawdown)}</td><td>${formatNumber(m.sharpe_ratio)}</td></tr>`
    }
    html += '</table>'
  }

  // AI分析
  if (rpt.analysis?.length) {
    html += '<h2>AI分析</h2>'
    for (const s of rpt.analysis) {
      html += `<h3>${s.title}</h3><p>${s.content}</p>`
    }
  }

  // 建议
  if (rpt.recommendations?.length) {
    html += '<h2>投资建议</h2>'
    for (const r of rpt.recommendations) {
      html += `<div class="rec">✓ ${r}</div>`
    }
  }

  html += `<div class="meta">报告生成时间：${formatTime(rpt.generated_at || rpt.created_at || new Date().toISOString())}</div>`
  html += '</body></html>'
  return html
}

const exportWord = (rpt: any) => {
  if (!rpt) return
  const html = buildReportHtml(rpt.content || rpt)
  const blob = new Blob(['\ufeff' + html], { type: 'application/msword' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${rpt.title || 'AI报告'}.doc`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('Word报告已导出')
}

const exportPdf = () => {
  // 使用浏览器打印功能导出PDF
  if (!report.value) return
  const html = buildReportHtml(report.value)
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(html)
    printWindow.document.close()
    printWindow.onload = () => { printWindow.print() }
  }
}

// 格式化方法
const formatTime = (iso: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const formatNumber = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2)
}

const formatPeriod = (period: string) => {
  const map: Record<string, string> = {
    '1m': '近1月',
    '3m': '近3月',
    '6m': '近6月',
    '1y': '近1年',
    'ytd': '今年以来',
  }
  return map[period] || period
}

const formatBasicInfo = (info: Record<string, any>) => {
  const labelMap: Record<string, string> = {
    product_name: '产品名称',
    product_code: '产品代码',
    manager_name: '管理人',
    strategy_type: '策略类型',
    inception_date: '成立日期',
    short_name: '简称',
    manager_code: '管理人代码',
    primary_strategy: '主策略',
    pool_category: '跟踪池分类',
    aum_range: '管理规模',
    registration_no: '备案号',
    established_date: '成立日期',
    product_count: '产品数量',
    name: '组合名称',
    description: '描述',
    component_count: '成分数量',
    created_at: '创建时间',
  }
  
  const result: Record<string, any> = {}
  for (const [key, value] of Object.entries(info)) {
    const label = labelMap[key] || key
    result[label] = value
  }
  return result
}

const getReturnClass = (value: number | null | undefined) => {
  if (value === null || value === undefined) return ''
  return value >= 0 ? 'positive' : 'negative'
}

// ===== 已保存报告方法 =====
const saveCurrentReport = async () => {
  if (!report.value) return
  saving.value = true
  try {
    const payload: any = {
      title: report.value.title,
      report_type: report.value.type,
      content: report.value,
      summary: report.value.summary,
    }
    if (report.value.type === 'product' && selectedProductId.value) payload.product_id = selectedProductId.value
    if (report.value.type === 'manager' && selectedManagerId.value) payload.manager_id = selectedManagerId.value
    if (report.value.type === 'portfolio' && selectedPortfolioId.value) payload.portfolio_id = selectedPortfolioId.value
    
    await request.post('/ai-reports/save', payload)
    ElMessage.success('报告已保存')
    loadSavedReports()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const loadSavedReports = async () => {
  loadingSaved.value = true
  try {
    const params: any = { page: savedFilter.page, page_size: savedFilter.page_size }
    if (savedFilter.report_type) params.report_type = savedFilter.report_type
    if (savedFilter.status) params.status = savedFilter.status
    if (savedFilter.keyword) params.keyword = savedFilter.keyword
    
    const res = await request.get('/ai-reports/saved', { params })
    const data = res.data || res
    savedReports.value = data.items || []
    savedTotal.value = data.total || 0
  } catch (e) {
    console.error('加载已保存报告失败', e)
  } finally {
    loadingSaved.value = false
  }
}

const viewSavedReport = async (id: number) => {
  try {
    const res = await request.get(`/ai-reports/saved/${id}`)
    viewingReport.value = res.data || res
    viewDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '加载报告失败')
  }
}

const publishReport = async (id: number) => {
  try {
    await request.put(`/ai-reports/saved/${id}/publish`)
    ElMessage.success('报告已发布')
    loadSavedReports()
  } catch (e: any) {
    ElMessage.error(e.message || '发布失败')
  }
}

const deleteSavedReport = async (id: number) => {
  try {
    await request.delete(`/ai-reports/saved/${id}`)
    ElMessage.success('报告已删除')
    loadSavedReports()
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = { draft: 'info', published: 'success', archived: 'warning' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[status] || status
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = { product: '产品', manager: '管理人', portfolio: '组合', market: '市场' }
  return map[type] || type
}

// ============ 草稿编辑 ============
const editDialogVisible = ref(false)
const savingEdit = ref(false)
const editingReportId = ref<number | null>(null)
const editFormData = ref<{ title: string; summary: string; analysis: { title: string; content: string }[]; recommendations: string[] } | null>(null)

const editSavedReport = async (id: number) => {
  try {
    const res = await request.get(`/ai-reports/saved/${id}`)
    const data = res.data || res
    editingReportId.value = id
    const content = data.content || {}
    editFormData.value = {
      title: data.title || '',
      summary: data.summary || content.summary || '',
      analysis: content.analysis?.map((s: any) => ({ title: s.title || '', content: s.content || '' })) || [],
      recommendations: content.recommendations?.slice() || [],
    }
    editDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error(e.message || '加载报告失败')
  }
}

const handleSaveEdit = async () => {
  if (!editingReportId.value || !editFormData.value) return
  savingEdit.value = true
  try {
    const payload: any = {
      title: editFormData.value.title,
      summary: editFormData.value.summary,
      content: {
        analysis: editFormData.value.analysis.filter(a => a.title || a.content),
        recommendations: editFormData.value.recommendations.filter(Boolean),
      },
    }
    await request.put(`/ai-reports/saved/${editingReportId.value}`, payload)
    ElMessage.success('报告已更新')
    editDialogVisible.value = false
    loadSavedReports()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally { savingEdit.value = false }
}

// ============ 报告分享 ============
const shareDialogVisible = ref(false)
const creatingShare = ref(false)
const sharingReport = ref<any>(null)
const shareForm = ref({ password: '', expires_days: 0 })
const shareResult = ref<any>(null)

const openShareDialog = (item: any) => {
  sharingReport.value = item
  shareForm.value = { password: '', expires_days: 0 }
  shareResult.value = null
  shareDialogVisible.value = true
}

const handleCreateShare = async () => {
  if (!sharingReport.value) return
  creatingShare.value = true
  try {
    const res = await request.post(`/ai-reports/saved/${sharingReport.value.id}/share`, {
      password: shareForm.value.password || undefined,
      expires_days: shareForm.value.expires_days || undefined,
    })
    shareResult.value = res.data || res
    ElMessage.success('分享链接已生成')
  } catch (e: any) {
    ElMessage.error(e.message || '创建分享失败')
  } finally { creatingShare.value = false }
}

const fullShareUrl = computed(() => {
  if (!shareResult.value?.share_url) return ''
  return `${window.location.origin}${shareResult.value.share_url}`
})

const copyShareLink = async () => {
  try {
    await navigator.clipboard.writeText(fullShareUrl.value)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

onMounted(() => {
  loadData()
  loadSavedReports()
})
</script>

<style scoped>
.ai-reports-view {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
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

.report-types {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.type-card {
  background: var(--card-bg);
  border: 2px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.type-card:hover {
  border-color: rgba(var(--accent-primary), 0.4);
}

.type-card.active {
  border-color: var(--accent-color);
  background: rgba(var(--accent-primary), 0.12);
}

.type-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(var(--accent-primary), 0.15);
  color: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-card.active .type-icon {
  background: var(--accent-color);
  color: white;
}

.type-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.type-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.params-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.params-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item label {
  font-size: 14px;
  color: var(--text-secondary);
}

.param-count {
  color: var(--text-muted);
  font-size: 12px;
}

.param-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.08);
}

.param-hint.info {
  color: var(--accent-color);
  background: rgba(var(--accent-primary), 0.08);
}

.report-content {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 24px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--card-border);
}

.report-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #606266;
  font-size: 13px;
  background: var(--hover-bg, #f5f7fa);
  padding: 8px 16px;
  border-radius: 8px;
}

.report-summary {
  background: rgba(var(--accent-primary), 0.1);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
  color: var(--accent-color);
}

.report-summary .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.metrics-table table,
.components-table table,
.strategy-table table {
  width: 100%;
  border-collapse: collapse;
}

.metrics-table th,
.metrics-table td,
.components-table th,
.components-table td,
.strategy-table th,
.strategy-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--card-border);
}

.metrics-table th,
.components-table th,
.strategy-table th {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
}

.positive {
  color: #67c23a;
}

.negative {
  color: #f56c6c;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: var(--hover-bg);
}

.alert-item.critical {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.alert-item.warning {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.alert-text {
  font-size: 14px;
}

.analysis-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-item h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.analysis-item p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.recommendations {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rec-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--text-primary);
}

.rec-item .el-icon {
  color: #67c23a;
  flex-shrink: 0;
  margin-top: 3px;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
}

.empty-state .el-icon {
  color: rgba(var(--accent-primary), 0.4);
  margin-bottom: 16px;
}

.empty-tips {
  display: flex;
  gap: 32px;
  margin-top: 24px;
  justify-content: center;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-secondary);
}

.tip-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--accent-primary), 0.15);
  color: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.report-tabs {
  margin-bottom: 20px;
}

.saved-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.saved-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100px;
}

.saved-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.2s;
}

.saved-card:hover {
  border-color: var(--el-color-primary-light-3);
}

.saved-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.saved-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.saved-title-row h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.saved-actions {
  display: flex;
  gap: 4px;
}

.saved-summary {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 8px 0;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.saved-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
  background: var(--hover-bg, #f5f7fa);
  padding: 8px 12px;
  border-radius: 6px;
}

.saved-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-meta {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--card-border);
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--text-secondary);
}

@media (max-width: 1200px) {
  .report-types {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.edit-analysis-section {
  background: var(--hover-bg);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.share-result {
  padding: 8px 0;
}

@media (max-width: 768px) {
  .report-types {
    grid-template-columns: 1fr;
  }
  
  .params-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .param-item {
    width: 100%;
  }
}
</style>
