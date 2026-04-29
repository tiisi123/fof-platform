<template>
  <div class="product-detail-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="handleBack">返回</el-button>
      <h2>{{ product?.product_name || '产品详情' }}</h2>
      <el-tag v-if="product" :type="getStatusType(product.status)" size="large">
        {{ getStatusText(product.status) }}
      </el-tag>
      <el-tag v-if="product?.is_invested" type="success" size="large" style="margin-left: 8px">
        在投
      </el-tag>
    </div>

    <el-skeleton :loading="loading" animated>
      <template #template>
        <el-skeleton-item variant="h1" style="width: 40%" />
        <el-skeleton-item variant="text" style="margin-top: 16px" />
      </template>

      <template #default>
        <div v-if="product">
          <el-tabs v-model="activeTab" type="border-card">
            <!-- Tab 1: 基本信息 -->
            <el-tab-pane label="基本信息" name="basic">
              <el-card class="info-card" shadow="never">
                <el-descriptions :column="3" border>
                  <el-descriptions-item label="产品代码">
                    {{ product.product_code }}
                  </el-descriptions-item>
                  <el-descriptions-item label="产品名称">
                    {{ product.product_name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="管理人">
                    <el-link type="primary" @click="handleViewManager">
                      {{ product.manager_name }}
                    </el-link>
                  </el-descriptions-item>
                  <el-descriptions-item label="策略类型">
                    {{ product.strategy_type || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="成立日期">
                    {{ formatDate(product.established_date) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="清算日期">
                    {{ formatDate(product.liquidation_date) }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- 分析指标 -->
              <el-card v-if="indicators" class="section-card" shadow="never">
                <template #header>
                  <span>核心指标</span>
                </template>
                <el-row :gutter="16">
                  <el-col :xs="12" :sm="6" v-for="item in indicatorCards" :key="item.label">
                    <div class="indicator-item">
                      <div class="indicator-label">{{ item.label }}</div>
                      <div class="indicator-value" :class="item.colorClass">
                        {{ item.value }}
                      </div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>

              <!-- 市场分位数 -->
              <el-card v-if="ranking && ranking.indicators" class="section-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>市场分位数</span>
                    <div class="ranking-controls">
                      <el-select v-model="rankingPeriod" size="small" style="width: 100px" @change="fetchRanking">
                        <el-option label="近1月" value="1m" />
                        <el-option label="近3月" value="3m" />
                        <el-option label="近6月" value="6m" />
                        <el-option label="近1年" value="1y" />
                        <el-option label="成立以来" value="inception" />
                      </el-select>
                      <el-tag type="info" size="small" style="margin-left: 8px">
                        同策略 {{ ranking.peer_count }} 只
                      </el-tag>
                    </div>
                  </div>
                </template>
                <div class="ranking-grid">
                  <div v-for="(item, idx) in rankingItems" :key="idx" class="ranking-item">
                    <div class="ranking-label">{{ item.label }}</div>
                    <div class="ranking-value" :class="item.isDanger ? 'danger' : ''">
                      {{ item.display }}
                    </div>
                    <div class="ranking-bar-container">
                      <div class="ranking-bar" :style="{ width: item.percentile + '%' }"
                        :class="getPercentileClass(item.percentile)"></div>
                    </div>
                    <div class="ranking-detail">
                      <span>排名 {{ item.rank }}/{{ item.total }}</span>
                      <span class="percentile">超越 {{ item.percentile?.toFixed(1) }}%</span>
                    </div>
                  </div>
                </div>
              </el-card>
              <el-card v-else-if="rankingMessage" class="section-card" shadow="never">
                <template #header><span>市场分位数</span></template>
                <el-empty :description="rankingMessage" :image-size="60" />
              </el-card>
            </el-tab-pane>

            <!-- Tab 2: 净值数据 -->
            <el-tab-pane label="净值数据" name="nav">
              <!-- 净值走势图 -->
              <el-card class="section-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>净值走势</span>
                    <div class="chart-controls">
                      <el-radio-group v-model="chartPeriod" size="small" @change="fetchChartData">
                        <el-radio-button label="1m">近1月</el-radio-button>
                        <el-radio-button label="3m">近3月</el-radio-button>
                        <el-radio-button label="6m">近6月</el-radio-button>
                        <el-radio-button label="1y">近1年</el-radio-button>
                        <el-radio-button label="all">全部</el-radio-button>
                      </el-radio-group>
                    </div>
                  </div>
                </template>
                <div v-if="chartLoading" class="chart-loading">
                  <el-skeleton :rows="6" animated />
                </div>
                <div v-else-if="chartData" ref="navChartRef" class="nav-chart"></div>
                <el-empty v-else description="暂无净值数据" :image-size="80" />
              </el-card>

              <!-- 净值数据表格 -->
              <el-card class="section-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>净值明细</span>
                    <el-button type="primary" size="small" @click="fetchNavData">刷新</el-button>
                  </div>
                </template>
                <el-table :data="navList" :loading="navLoading" stripe border max-height="400">
                  <el-table-column prop="nav_date" label="净值日期" width="120" />
                  <el-table-column prop="unit_nav" label="单位净值" width="120" align="right">
                    <template #default="{ row }">
                      {{ row.unit_nav?.toFixed(4) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="cumulative_nav" label="累计净值" width="120" align="right">
                    <template #default="{ row }">
                      {{ row.cumulative_nav ? row.cumulative_nav.toFixed(4) : '-' }}
                    </template>
                  </el-table-column>
                  <el-table-column label="日涨幅" width="100" align="right">
                    <template #default="{ row }">
                      <span :class="getDailyReturnClass(row, navList)">
                        {{ calcDailyReturn(row, navList) }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="created_at" label="导入时间" min-width="160">
                    <template #default="{ row }">
                      {{ formatDateTime(row.created_at) }}
                    </template>
                  </el-table-column>
                </el-table>
                <div class="pagination-container">
                  <el-pagination v-model:current-page="navPage" v-model:page-size="navPageSize" :total="navTotal"
                    :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @size-change="fetchNavData"
                    @current-change="fetchNavData" />
                </div>
              </el-card>
            </el-tab-pane>

            <!-- Tab 3: 绩效分析 -->
            <el-tab-pane label="绩效分析" name="performance">
              <!-- 多周期业绩表格 -->
              <el-card class="section-card" shadow="never">
                <template #header><span>多周期业绩指标</span></template>
                <div v-if="perfLoading" style="padding: 20px">
                  <el-skeleton :rows="5" animated />
                </div>
                <div v-else-if="multiPeriodPerf">
                  <el-table :data="perfTableData" stripe border>
                    <el-table-column prop="metric" label="指标" width="140" fixed />
                    <el-table-column v-for="p in perfPeriods" :key="p.key" :label="p.label" min-width="110"
                      align="right">
                      <template #default="{ row }">
                        <span :class="getCellClass(row.values[p.key])">
                          {{ row.values[p.key] ?? '-' }}
                        </span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无绩效数据" :image-size="80" />
              </el-card>

              <!-- 回撤走势图 -->
              <el-card class="section-card" shadow="never">
                <template #header><span>回撤走势</span></template>
                <div v-if="chartLoading" class="chart-loading">
                  <el-skeleton :rows="4" animated />
                </div>
                <div v-else-if="chartData" ref="drawdownChartRef" class="drawdown-chart"></div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </el-card>
            </el-tab-pane>

            <!-- Tab 4: 持仓穿透 -->
            <el-tab-pane label="持仓穿透" name="holdings" lazy>
              <el-card class="section-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>持仓穿透分析（四级估值表）</span>
                    <div style="display: flex; gap: 12px; align-items: center">
                      <el-select v-model="holdingsDate" placeholder="报告日期" size="small" style="width: 160px" @change="fetchHoldingsAnalysis">
                        <el-option v-for="d in holdingsDates" :key="d" :label="d" :value="d" />
                      </el-select>
                      <el-upload :show-file-list="false" :before-upload="handleHoldingsImport" accept=".xls,.xlsx">
                        <el-button size="small" type="primary">导入估值表</el-button>
                      </el-upload>
                    </div>
                  </div>
                </template>

                <div v-if="holdingsAnalysis" v-loading="holdingsLoading">
                  <!-- 概览指标 -->
                  <el-row :gutter="16" class="mb-4">
                    <el-col :span="6">
                      <div class="indicator-item">
                        <div class="indicator-label">持仓数量</div>
                        <div class="indicator-value">{{ holdingsAnalysis.total_holdings }}</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="indicator-item">
                        <div class="indicator-label">总市值</div>
                        <div class="indicator-value">{{ holdingsAnalysis.total_market_value?.toLocaleString() }}</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="indicator-item">
                        <div class="indicator-label">前5大集中度</div>
                        <div class="indicator-value">{{ holdingsAnalysis.concentration?.top5_weight }}%</div>
                      </div>
                    </el-col>
                    <el-col :span="6">
                      <div class="indicator-item">
                        <div class="indicator-label">HHI指数</div>
                        <div class="indicator-value">{{ holdingsAnalysis.concentration?.hhi_index }}</div>
                      </div>
                    </el-col>
                  </el-row>

                  <!-- 行业分布 + 资产类型 -->
                  <el-row :gutter="16" class="mb-4">
                    <el-col :span="12">
                      <el-card shadow="never">
                        <template #header><span>行业分布</span></template>
                        <div ref="industryPieRef" style="height: 260px"></div>
                      </el-card>
                    </el-col>
                    <el-col :span="12">
                      <el-card shadow="never">
                        <template #header><span>资产类型分布</span></template>
                        <div ref="assetTypePieRef" style="height: 260px"></div>
                      </el-card>
                    </el-col>
                  </el-row>

                  <!-- 集中度指标 -->
                  <el-card shadow="never" class="mb-4">
                    <template #header><span>持仓集中度</span></template>
                    <el-descriptions :column="4" border size="small">
                      <el-descriptions-item label="前5大">{{ holdingsAnalysis.concentration?.top5_weight }}%</el-descriptions-item>
                      <el-descriptions-item label="前10大">{{ holdingsAnalysis.concentration?.top10_weight }}%</el-descriptions-item>
                      <el-descriptions-item label="前20大">{{ holdingsAnalysis.concentration?.top20_weight }}%</el-descriptions-item>
                      <el-descriptions-item label="HHI指数">{{ holdingsAnalysis.concentration?.hhi_index }}</el-descriptions-item>
                    </el-descriptions>
                  </el-card>

                  <!-- 前20大持仓 -->
                  <el-card shadow="never">
                    <template #header><span>前20大持仓</span></template>
                    <el-table :data="holdingsAnalysis.top_holdings" stripe border size="small">
                      <el-table-column prop="security_name" label="证券名称" min-width="160" />
                      <el-table-column prop="security_code" label="代码" width="100" />
                      <el-table-column prop="security_type" label="类型" width="80" />
                      <el-table-column prop="market_value" label="市值" width="120" align="right">
                        <template #default="{ row }">{{ row.market_value?.toLocaleString() }}</template>
                      </el-table-column>
                      <el-table-column prop="weight" label="占比(%)" width="100" align="right" />
                      <el-table-column prop="pnl_ratio" label="盈亏(%)" width="100" align="right">
                        <template #default="{ row }">
                          <span v-if="row.pnl_ratio != null" :style="{ color: row.pnl_ratio >= 0 ? '#67C23A' : '#F56C6C' }">{{ row.pnl_ratio }}</span>
                          <span v-else>-</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="industry_l1" label="行业" width="120" />
                    </el-table>
                  </el-card>
                </div>

                <el-empty v-else-if="!holdingsLoading" description="暂无持仓数据，请导入四级估值表" :image-size="80" />
              </el-card>
            </el-tab-pane>

            <!-- Tab 5: 费率信息 -->
            <el-tab-pane label="费率信息" name="fees">
              <el-card class="section-card" shadow="never">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="管理费率">
                    {{ product.management_fee != null ? product.management_fee + '%' : '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="业绩报酬">
                    {{ product.performance_fee != null ? product.performance_fee + '%' : '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="基准代码">
                    {{ product.benchmark_code || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="基准名称">
                    {{ product.benchmark_name || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="是否在投">
                    <el-tag :type="product.is_invested ? 'success' : 'info'" size="small">
                      {{ product.is_invested ? '是' : '否' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="产品状态">
                    <el-tag :type="getStatusType(product.status)">
                      {{ getStatusText(product.status) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="备注" :span="2">
                    {{ product.remark || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="创建时间">
                    {{ formatDateTime(product.created_at) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="更新时间">
                    {{ formatDateTime(product.updated_at) }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-tab-pane>
          </el-tabs>
        </div>
        <el-empty v-else description="产品不存在" />
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { productApi } from '@/api/product'
import { navApi } from '@/api/nav'
import { analysisApi } from '@/api/analysis'
import { getProductRanking } from '@/api/ranking'
import request from '@/api/request'
import type { Product, NavData } from '@/types'
import type { AllIndicators, ChartData, MultiPeriodPerformance, PeriodPerformance } from '@/api/analysis'
import { PRODUCT_STATUS_COLOR, PRODUCT_STATUS_TEXT } from '@/types/product'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const productId = ref<number>(Number(route.params.id))
const activeTab = ref('basic')

// --- 产品基本信息 ---
const loading = ref(false)
const product = ref<Product | null>(null)

// --- 分析指标 ---
const indicators = ref<AllIndicators | null>(null)

// --- 市场分位数 ---
const ranking = ref<any>(null)
const rankingPeriod = ref('1y')
const rankingMessage = ref('')

// --- 净值图表 ---
const chartPeriod = ref('all')
const chartLoading = ref(false)
const chartData = ref<ChartData | null>(null)
const navChartRef = ref<HTMLElement>()
const drawdownChartRef = ref<HTMLElement>()
let navChartInstance: echarts.ECharts | null = null
let drawdownChartInstance: echarts.ECharts | null = null

// --- 净值列表 ---
const navLoading = ref(false)
const navList = ref<NavData[]>([])
const navPage = ref(1)
const navPageSize = ref(20)
const navTotal = ref(0)

// --- 绩效分析 ---
const perfLoading = ref(false)
const multiPeriodPerf = ref<MultiPeriodPerformance | null>(null)

// --- 持仓穿透 ---
const holdingsLoading = ref(false)
const holdingsAnalysis = ref<any>(null)
const holdingsDates = ref<string[]>([])
const holdingsDate = ref('')
const industryPieRef = ref<HTMLElement>()
const assetTypePieRef = ref<HTMLElement>()
let industryPieChart: echarts.ECharts | null = null
let assetTypePieChart: echarts.ECharts | null = null

// ============ 计算属性 ============

const indicatorCards = computed(() => {
  if (!indicators.value) return []
  const i = indicators.value
  return [
    { label: '累计收益率', value: fmtPct(i.return_analysis.cumulative_return), colorClass: 'success' },
    { label: '年化收益率', value: fmtPct(i.return_analysis.annualized_return), colorClass: 'primary' },
    { label: '年化波动率', value: fmtPct(i.volatility_analysis.annualized_volatility), colorClass: 'warning' },
    { label: '最大回撤', value: fmtPct(i.max_drawdown_analysis.max_drawdown), colorClass: 'danger' }
  ]
})

const rankingItems = computed(() => {
  if (!ranking.value?.indicators) return []
  const ind = ranking.value.indicators
  const items: any[] = []
  const config: Record<string, { label: string; isDanger: boolean; isRatio: boolean }> = {
    annualized_return: { label: '年化收益率', isDanger: false, isRatio: false },
    max_drawdown: { label: '最大回撤', isDanger: true, isRatio: false },
    sharpe_ratio: { label: '夏普比率', isDanger: false, isRatio: true },
    calmar_ratio: { label: '卡玛比率', isDanger: false, isRatio: true }
  }
  for (const [key, cfg] of Object.entries(config)) {
    if (ind[key]) {
      items.push({
        label: cfg.label,
        isDanger: cfg.isDanger,
        display: cfg.isRatio ? ind[key].value?.toFixed(2) : fmtPct(ind[key].value),
        percentile: ind[key].percentile,
        rank: ind[key].rank,
        total: ind[key].total
      })
    }
  }
  return items
})

// 绩效分析表格
const perfPeriods = [
  { key: '1m', label: '近1月' },
  { key: '3m', label: '近3月' },
  { key: '6m', label: '近6月' },
  { key: '1y', label: '近1年' },
  { key: 'inception', label: '成立以来' }
]

const perfTableData = computed(() => {
  if (!multiPeriodPerf.value) return []
  const periods = multiPeriodPerf.value.periods
  const metrics = [
    { metric: '累计收益率', field: 'total_return', fmt: fmtPct },
    { metric: '年化收益率', field: 'annualized_return', fmt: fmtPct },
    { metric: '年化波动率', field: 'annualized_volatility', fmt: fmtPct },
    { metric: '下行波动率', field: 'downside_volatility', fmt: fmtPct },
    { metric: '最大回撤', field: 'max_drawdown', fmt: fmtPct },
    { metric: '夏普比率', field: 'sharpe_ratio', fmt: fmtNum },
    { metric: '卡玛比率', field: 'calmar_ratio', fmt: fmtNum },
    { metric: '索提诺比率', field: 'sortino_ratio', fmt: fmtNum },
    { metric: '胜率', field: 'win_rate', fmt: fmtPct }
  ]
  return metrics.map(m => {
    const values: Record<string, string | null> = {}
    for (const p of perfPeriods) {
      const pd = periods[p.key] as PeriodPerformance | undefined
      const v = pd ? (pd as any)[m.field] : null
      values[p.key] = v != null ? m.fmt(v) : null
    }
    return { metric: m.metric, values }
  })
})

// ============ 数据加载 ============

const fetchProduct = async () => {
  loading.value = true
  try {
    product.value = await productApi.getById(productId.value)
  } catch {
    ElMessage.error('获取产品信息失败')
  } finally {
    loading.value = false
  }
}

const fetchIndicators = async () => {
  try {
    indicators.value = await analysisApi.getAllIndicators({ product_id: productId.value })
  } catch {
    // 没有净值数据时不报错
  }
}

const fetchRanking = async () => {
  try {
    const result = await getProductRanking(productId.value, rankingPeriod.value)
    if (result.error || result.message) {
      rankingMessage.value = result.error || result.message
      ranking.value = null
    } else {
      ranking.value = result
      rankingMessage.value = ''
    }
  } catch {
    rankingMessage.value = '获取分位数数据失败'
  }
}

const getChartDateRange = () => {
  if (chartPeriod.value === 'all') return {}
  const end = new Date()
  const start = new Date()
  const monthMap: Record<string, number> = { '1m': 1, '3m': 3, '6m': 6, '1y': 12 }
  start.setMonth(start.getMonth() - (monthMap[chartPeriod.value] || 12))
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10)
  }
}

const fetchChartData = async () => {
  chartLoading.value = true
  try {
    const range = getChartDateRange()
    chartData.value = await analysisApi.getChartData({
      product_id: productId.value,
      ...range
    })
  } catch {
    chartData.value = null
  } finally {
    chartLoading.value = false
  }
  // 必须在 chartLoading=false 之后等待 DOM 更新，再渲染图表
  if (chartData.value) {
    await nextTick()
    renderNavChart()
    renderDrawdownChart()
  }
}

const fetchNavData = async () => {
  navLoading.value = true
  try {
    const response = await navApi.getList({
      product_id: productId.value,
      skip: (navPage.value - 1) * navPageSize.value,
      limit: navPageSize.value
    })
    navList.value = response.items
    navTotal.value = response.total
  } catch {
    ElMessage.error('获取净值数据失败')
  } finally {
    navLoading.value = false
  }
}

const fetchMultiPeriodPerf = async () => {
  perfLoading.value = true
  try {
    multiPeriodPerf.value = await analysisApi.getMultiPeriodPerformance(
      productId.value,
      ['1m', '3m', '6m', '1y', 'inception']
    )
  } catch {
    multiPeriodPerf.value = null
  } finally {
    perfLoading.value = false
  }
}

// ============ 持仓穿透 ============

const fetchHoldingsAnalysis = async () => {
  holdingsLoading.value = true
  try {
    const params: any = { product_id: productId.value }
    if (holdingsDate.value) params.report_date = holdingsDate.value
    const res = await request.get('/holdings/analysis', { params })
    const data = res.data ?? res
    if (data.data === null) {
      holdingsAnalysis.value = null
    } else {
      holdingsAnalysis.value = data
      holdingsDates.value = data.available_dates || []
      if (!holdingsDate.value && data.report_date) holdingsDate.value = data.report_date
    }
  } catch {
    holdingsAnalysis.value = null
  } finally {
    holdingsLoading.value = false
  }
  if (holdingsAnalysis.value) {
    await nextTick()
    renderIndustryPie()
    renderAssetTypePie()
  }
}

const renderIndustryPie = () => {
  if (!industryPieRef.value || !holdingsAnalysis.value?.by_industry) return
  if (industryPieChart) industryPieChart.dispose()
  industryPieChart = echarts.init(industryPieRef.value)
  const data = Object.entries(holdingsAnalysis.value.by_industry).map(([name, v]: [string, any]) => ({
    name, value: v.weight
  }))
  industryPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    legend: { type: 'scroll', bottom: 0 },
    series: [{ type: 'pie', radius: ['35%', '60%'], data, label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } } }]
  })
}

const renderAssetTypePie = () => {
  if (!assetTypePieRef.value || !holdingsAnalysis.value?.by_asset_type) return
  if (assetTypePieChart) assetTypePieChart.dispose()
  assetTypePieChart = echarts.init(assetTypePieRef.value)
  const data = Object.entries(holdingsAnalysis.value.by_asset_type).map(([name, v]: [string, any]) => ({
    name, value: v.weight
  }))
  assetTypePieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    legend: { type: 'scroll', bottom: 0 },
    series: [{ type: 'pie', radius: ['35%', '60%'], data, label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } } }]
  })
}

const handleHoldingsImport = async (rawFile: any) => {
  if (!productId.value) return false
  const reportDate = holdingsDate.value || new Date().toISOString().slice(0, 10)
  const formData = new FormData()
  formData.append('file', rawFile)
  try {
    await request.post(`/holdings/import?product_id=${productId.value}&report_date=${reportDate}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('估值表导入成功')
    await fetchHoldingsAnalysis()
  } catch {
    ElMessage.error('导入失败')
  }
  return false // 阻止 el-upload 默认上传
}

// ============ 图表渲染 ============

const renderNavChart = () => {
  if (!navChartRef.value || !chartData.value) return
  if (navChartInstance) navChartInstance.dispose()
  navChartInstance = echarts.init(navChartRef.value)
  const { dates, unit_navs, cumulative_navs } = chartData.value
  const hasCumulative = cumulative_navs && cumulative_navs.some(v => v != null)

  const series: any[] = [{
    name: '单位净值',
    type: 'line',
    data: unit_navs,
    smooth: true,
    symbol: 'none',
    lineStyle: { width: 2 },
    itemStyle: { color: '#409EFF' }
  }]
  const yAxis: any[] = [{
    type: 'value',
    name: '单位净值',
    position: 'left',
    axisLabel: { formatter: (v: number) => v.toFixed(4) }
  }]

  if (hasCumulative) {
    series.push({
      name: '累计净值',
      type: 'line',
      yAxisIndex: 1,
      data: cumulative_navs,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, type: 'dashed' },
      itemStyle: { color: '#67C23A' }
    })
    yAxis.push({
      type: 'value',
      name: '累计净值',
      position: 'right',
      axisLabel: { formatter: (v: number) => v.toFixed(4) }
    })
  }

  navChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: hasCumulative ? ['单位净值', '累计净值'] : ['单位净值'] },
    grid: { left: 80, right: hasCumulative ? 80 : 40, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis,
    series
  })
}

const renderDrawdownChart = () => {
  if (!drawdownChartRef.value || !chartData.value) return
  if (drawdownChartInstance) drawdownChartInstance.dispose()
  drawdownChartInstance = echarts.init(drawdownChartRef.value)

  const { dates, unit_navs } = chartData.value
  // 计算回撤序列
  const drawdowns: number[] = []
  let peak = unit_navs[0]
  for (const nav of unit_navs) {
    if (nav > peak) peak = nav
    drawdowns.push((nav - peak) / peak)
  }

  drawdownChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `${p.axisValue}<br/>回撤: ${(p.value * 100).toFixed(2)}%`
      }
    },
    grid: { left: 80, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => (v * 100).toFixed(1) + '%' }
    },
    series: [{
      type: 'line',
      data: drawdowns,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1, color: '#F56C6C' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,108,108,0.3)' },
          { offset: 1, color: 'rgba(245,108,108,0.05)' }
        ])
      }
    }]
  })
}

// ============ Tab 切换懒加载 ============

const navDataLoaded = ref(false)
const perfDataLoaded = ref(false)
const holdingsDataLoaded = ref(false)

watch(activeTab, async (tab) => {
  if (tab === 'nav' && !navDataLoaded.value) {
    navDataLoaded.value = true
    await fetchChartData()
    await fetchNavData()
  }
  if (tab === 'performance' && !perfDataLoaded.value) {
    perfDataLoaded.value = true
    await fetchMultiPeriodPerf()
    // 回撤图依赖 chartData
    if (!chartData.value) {
      await fetchChartData()
    } else {
      await nextTick()
      renderDrawdownChart()
    }
  }
  if (tab === 'holdings' && !holdingsDataLoaded.value) {
    holdingsDataLoaded.value = true
    await fetchHoldingsAnalysis()
  }
})

// ============ 工具函数 ============

const fmtPct = (v: number | undefined | null) => {
  if (v == null) return '-'
  return (v * 100).toFixed(2) + '%'
}

const fmtNum = (v: number | undefined | null) => {
  if (v == null) return '-'
  return v.toFixed(2)
}

const getStatusType = (status: string) => {
  return PRODUCT_STATUS_COLOR[status as keyof typeof PRODUCT_STATUS_COLOR] || ''
}

const getStatusText = (status: string) => {
  return PRODUCT_STATUS_TEXT[status as keyof typeof PRODUCT_STATUS_TEXT] || status
}

const getPercentileClass = (percentile: number) => {
  if (percentile >= 75) return 'excellent'
  if (percentile >= 50) return 'good'
  if (percentile >= 25) return 'average'
  return 'poor'
}

const getCellClass = (value: string | null) => {
  if (!value || value === '-') return ''
  const num = parseFloat(value)
  if (isNaN(num)) return ''
  return num > 0 ? 'text-success' : num < 0 ? 'text-danger' : ''
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const calcDailyReturn = (row: NavData, list: NavData[]) => {
  const idx = list.indexOf(row)
  if (idx < 0 || idx >= list.length - 1) return '-'
  const prev = list[idx + 1] // 列表按日期倒序
  if (!prev || !prev.unit_nav || !row.unit_nav) return '-'
  const ret = (row.unit_nav - prev.unit_nav) / prev.unit_nav
  return (ret >= 0 ? '+' : '') + (ret * 100).toFixed(2) + '%'
}

const getDailyReturnClass = (row: NavData, list: NavData[]) => {
  const str = calcDailyReturn(row, list)
  if (str === '-') return ''
  return str.startsWith('+') ? 'text-success' : 'text-danger'
}

// ============ 导航 ============

const handleBack = () => router.back()

const handleViewManager = () => {
  if (product.value?.manager_id) {
    router.push(`/managers/${product.value.manager_id}`)
  }
}

// ============ 生命周期 ============

const handleResize = () => {
  navChartInstance?.resize()
  drawdownChartInstance?.resize()
  industryPieChart?.resize()
  assetTypePieChart?.resize()
}

onMounted(async () => {
  await fetchProduct()
  await Promise.all([fetchIndicators(), fetchRanking()])
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  navChartInstance?.dispose()
  drawdownChartInstance?.dispose()
  industryPieChart?.dispose()
  assetTypePieChart?.dispose()
})
</script>

<style scoped>
.product-detail-view {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ranking-controls {
  display: flex;
  align-items: center;
}

/* 指标卡片 */
.indicator-item {
  padding: 16px;
  text-align: center;
  background-color: var(--input-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  margin-bottom: 12px;
}

.indicator-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.indicator-value {
  font-size: 22px;
  font-weight: 600;
}

.indicator-value.success { color: #67C23A; }
.indicator-value.primary { color: #409EFF; }
.indicator-value.warning { color: #E6A23C; }
.indicator-value.danger { color: #F56C6C; }

/* 分位数 */
.ranking-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.ranking-item {
  padding: 14px;
  background-color: var(--input-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  text-align: center;
}

.ranking-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.ranking-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.ranking-value.danger { color: #F56C6C; }

.ranking-bar-container {
  height: 6px;
  background-color: var(--card-border);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.ranking-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}

.ranking-bar.excellent { background: linear-gradient(90deg, #67C23A, #85ce61); }
.ranking-bar.good { background: linear-gradient(90deg, #409EFF, #66b1ff); }
.ranking-bar.average { background: linear-gradient(90deg, #E6A23C, #ebb563); }
.ranking-bar.poor { background: linear-gradient(90deg, #F56C6C, #f89898); }

.ranking-detail {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-secondary);
}

.ranking-detail .percentile {
  color: #409EFF;
  font-weight: 500;
}

/* 图表 */
.nav-chart {
  width: 100%;
  height: 360px;
}

.drawdown-chart {
  width: 100%;
  height: 260px;
}

.chart-loading {
  padding: 20px;
}

/* 表格 */
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 文字颜色 */
.text-success { color: #67C23A; }
.text-danger { color: #F56C6C; }

/* Utility */
.mb-4 { margin-bottom: 16px; }

/* 响应式 */
@media (max-width: 1200px) {
  .ranking-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .product-detail-view { padding: 15px; }
  .page-header { flex-wrap: wrap; }
  .ranking-grid { grid-template-columns: 1fr; }
  .nav-chart { height: 280px; }
  .drawdown-chart { height: 200px; }
}
</style>
