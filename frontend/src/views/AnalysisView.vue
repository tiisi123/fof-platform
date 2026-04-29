<template>
  <div class="analysis-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>产品分析</h2>
    </div>

    <!-- 选择器 -->
    <el-card class="selector-card" shadow="never">
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="选择产品">
          <el-select
            v-model="queryForm.product_id"
            placeholder="请选择产品"
            filterable
            clearable
            style="width: 300px"
            :loading="productsLoading"
            @change="handleProductChange"
          >
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="`${product.code} - ${product.name}`"
              :value="product.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 300px"
            @change="handleDateChange"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" :loading="loading" @click="handleAnalyze">
            分析
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 分析结果 -->
    <template v-if="hasData">
      <!-- 指标卡片 -->
      <el-row :gutter="20" class="indicators-row">
        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="indicator-card" shadow="hover">
            <div class="indicator-content">
              <!-- 中国A股习惯：红涨绿跌 -->
              <div class="indicator-icon" style="background-color: #F56C6C">
                <el-icon :size="32"><TrendCharts /></el-icon>
              </div>
              <div class="indicator-data">
                <div class="indicator-label">累计收益率</div>
                <div class="indicator-value">{{ formatPercent(indicators?.return_analysis.cumulative_return) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="indicator-card" shadow="hover">
            <div class="indicator-content">
              <div class="indicator-icon" style="background-color: #409EFF">
                <el-icon :size="32"><DataLine /></el-icon>
              </div>
              <div class="indicator-data">
                <div class="indicator-label">年化收益率</div>
                <div class="indicator-value">{{ formatPercent(indicators?.return_analysis.annualized_return) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="indicator-card" shadow="hover">
            <div class="indicator-content">
              <div class="indicator-icon" style="background-color: #E6A23C">
                <el-icon :size="32"><Warning /></el-icon>
              </div>
              <div class="indicator-data">
                <div class="indicator-label">波动率</div>
                <div class="indicator-value">{{ formatPercent(indicators?.volatility_analysis.annualized_volatility) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :lg="6">
          <el-card class="indicator-card" shadow="hover">
            <div class="indicator-content">
              <!-- 中国A股习惯：红涨绿跌 -->
              <div class="indicator-icon" style="background-color: #67C23A">
                <el-icon :size="32"><Bottom /></el-icon>
              </div>
              <div class="indicator-data">
                <div class="indicator-label">最大回撤</div>
                <div class="indicator-value">{{ formatPercent(indicators?.max_drawdown_analysis.max_drawdown) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 详细指标 -->
      <el-row :gutter="20" class="details-row">
        <el-col :xs="24" :lg="12">
          <el-card class="detail-card" shadow="never">
            <template #header>
              <span>收益指标</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="累计收益率">
                {{ formatPercent(indicators?.return_analysis.cumulative_return) }}
              </el-descriptions-item>
              <el-descriptions-item label="年化收益率">
                {{ formatPercent(indicators?.return_analysis.annualized_return) }}
              </el-descriptions-item>
              <el-descriptions-item label="分析天数">
                {{ indicators?.return_analysis.period_days }} 天
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card class="detail-card" shadow="never">
            <template #header>
              <span>风险指标</span>
            </template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="波动率">
                {{ formatPercent(indicators?.volatility_analysis.volatility) }}
              </el-descriptions-item>
              <el-descriptions-item label="年化波动率">
                {{ formatPercent(indicators?.volatility_analysis.annualized_volatility) }}
              </el-descriptions-item>
              <el-descriptions-item label="夏普比率">
                {{ formatNumber(indicators?.sharpe_ratio_analysis.sharpe_ratio) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="details-row">
        <el-col :span="24">
          <el-card class="detail-card" shadow="never">
            <template #header>
              <span>回撤分析</span>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="最大回撤">
                {{ formatPercent(indicators?.max_drawdown_analysis.max_drawdown) }}
              </el-descriptions-item>
              <el-descriptions-item label="回撤天数">
                {{ indicators?.max_drawdown_analysis.max_drawdown_days }} 天
              </el-descriptions-item>
              <el-descriptions-item label="回撤开始日期">
                {{ indicators?.max_drawdown_analysis.max_drawdown_start_date }}
              </el-descriptions-item>
              <el-descriptions-item label="回撤结束日期">
                {{ indicators?.max_drawdown_analysis.max_drawdown_end_date }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 多周期业绩表格 -->
      <el-card class="detail-card" shadow="never" v-if="multiPeriod && multiPeriod.periods">
        <template #header>
          <div class="section-header">
            <span>多周期业绩指标</span>
            <el-tag size="small" type="info" v-if="multiPeriod.latest_nav">
              最新净值 {{ multiPeriod.latest_nav?.toFixed(4) }}
              <template v-if="multiPeriod.latest_nav_date"> · {{ multiPeriod.latest_nav_date }}</template>
            </el-tag>
          </div>
        </template>
        <div class="multi-period-table">
          <table>
            <thead>
              <tr>
                <th>周期</th>
                <th>累计收益</th>
                <th>年化收益</th>
                <th>年化波动</th>
                <th>最大回撤</th>
                <th>夏普比率</th>
                <th>卡玛比率</th>
                <th>胜率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pKey in periodOrder" :key="pKey" v-if="multiPeriod.periods[pKey]?.has_data">
                <td class="period-name">{{ multiPeriod.periods[pKey]?.period_name }}</td>
                <td :class="getReturnClass(multiPeriod.periods[pKey]?.total_return)">
                  {{ formatPct(multiPeriod.periods[pKey]?.total_return) }}
                </td>
                <td :class="getReturnClass(multiPeriod.periods[pKey]?.annualized_return)">
                  {{ formatPct(multiPeriod.periods[pKey]?.annualized_return) }}
                </td>
                <td>{{ formatPct(multiPeriod.periods[pKey]?.annualized_volatility) }}</td>
                <td class="negative">{{ formatPct(multiPeriod.periods[pKey]?.max_drawdown) }}</td>
                <td>{{ formatNum(multiPeriod.periods[pKey]?.sharpe_ratio) }}</td>
                <td>{{ formatNum(multiPeriod.periods[pKey]?.calmar_ratio) }}</td>
                <td>{{ formatPct(multiPeriod.periods[pKey]?.win_rate) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-card>

      <!-- 市场排名卡片 -->
      <el-card class="ranking-card" shadow="never" v-if="ranking && ranking.indicators">
        <template #header>
          <div class="ranking-header">
            <span>市场排名（{{ ranking.period_name }}）</span>
            <div class="ranking-actions">
              <el-radio-group v-model="rankingPeriod" size="small" @change="handleRankingPeriodChange">
                <el-radio-button label="3m">近3月</el-radio-button>
                <el-radio-button label="6m">近6月</el-radio-button>
                <el-radio-button label="1y">近1年</el-radio-button>
                <el-radio-button label="inception">成立以来</el-radio-button>
              </el-radio-group>
              <el-tag size="small" type="info" style="margin-left: 8px">同策略{{ ranking.peer_count }}只产品</el-tag>
            </div>
          </div>
        </template>
        <div class="ranking-grid">
          <div class="ranking-item" v-if="ranking.indicators.annualized_return">
            <div class="ranking-label">年化收益</div>
            <div class="ranking-value">
              <span class="rank">第{{ ranking.indicators.annualized_return.rank }}名</span>
              <span class="percentile" :class="getPercentileClass(ranking.indicators.annualized_return.percentile)">
                前{{ (100 - ranking.indicators.annualized_return.percentile).toFixed(0) }}%
              </span>
            </div>
            <div class="ranking-bar">
              <div class="ranking-bar-fill" :style="{ width: ranking.indicators.annualized_return.percentile + '%' }"></div>
            </div>
          </div>
          <div class="ranking-item" v-if="ranking.indicators.sharpe_ratio">
            <div class="ranking-label">夏普比率</div>
            <div class="ranking-value">
              <span class="rank">第{{ ranking.indicators.sharpe_ratio.rank }}名</span>
              <span class="percentile" :class="getPercentileClass(ranking.indicators.sharpe_ratio.percentile)">
                前{{ (100 - ranking.indicators.sharpe_ratio.percentile).toFixed(0) }}%
              </span>
            </div>
            <div class="ranking-bar">
              <div class="ranking-bar-fill" :style="{ width: ranking.indicators.sharpe_ratio.percentile + '%' }"></div>
            </div>
          </div>
          <div class="ranking-item" v-if="ranking.indicators.max_drawdown">
            <div class="ranking-label">最大回撤</div>
            <div class="ranking-value">
              <span class="rank">第{{ ranking.indicators.max_drawdown.rank }}名</span>
              <span class="percentile" :class="getPercentileClass(ranking.indicators.max_drawdown.percentile)">
                前{{ (100 - ranking.indicators.max_drawdown.percentile).toFixed(0) }}%
              </span>
            </div>
            <div class="ranking-bar">
              <div class="ranking-bar-fill drawdown" :style="{ width: ranking.indicators.max_drawdown.percentile + '%' }"></div>
            </div>
          </div>
          <div class="ranking-item" v-if="ranking.indicators.annualized_volatility">
            <div class="ranking-label">波动率</div>
            <div class="ranking-value">
              <span class="rank">第{{ ranking.indicators.annualized_volatility.rank }}名</span>
              <span class="percentile" :class="getPercentileClass(ranking.indicators.annualized_volatility.percentile)">
                前{{ (100 - ranking.indicators.annualized_volatility.percentile).toFixed(0) }}%
              </span>
            </div>
            <div class="ranking-bar">
              <div class="ranking-bar-fill volatility" :style="{ width: ranking.indicators.annualized_volatility.percentile + '%' }"></div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 净值曲线图 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <span>净值走势图</span>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </template>

    <!-- 空状态 -->
    <el-empty v-else description="请选择产品并点击分析按钮" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, TrendCharts, DataLine, Warning, Bottom } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { productApi } from '@/api/product'
import { analysisApi } from '@/api/analysis'
import type { Product } from '@/types'
import type { AllIndicators, ChartData, ProductRanking, MultiPeriodPerformance } from '@/api/analysis'

// 产品列表
const products = ref<Product[]>([])
const productsLoading = ref(false)

// 多周期业绩
const multiPeriod = ref<MultiPeriodPerformance | null>(null)
const periodOrder = ['1w', '1m', '3m', '6m', '1y', 'ytd', 'inception']

// 排名周期
const rankingPeriod = ref('1y')

// 查询表单
const queryForm = reactive({
  product_id: undefined as number | undefined
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 分析数据
const loading = ref(false)
const hasData = ref(false)
const indicators = ref<AllIndicators | null>(null)
const chartData = ref<ChartData | null>(null)
const ranking = ref<ProductRanking | null>(null)

// 图表
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

// 获取产品列表
const fetchProducts = async () => {
  productsLoading.value = true
  try {
    const response = await productApi.getList({ skip: 0, limit: 1000, status: '运行中' })
    products.value = response.items
  } catch (error) {
    console.error('获取产品列表失败:', error)
  } finally {
    productsLoading.value = false
  }
}

// 处理产品变化
const handleProductChange = () => {
  // 产品变化时清空数据
  hasData.value = false
  indicators.value = null
  chartData.value = null
}

// 处理日期变化
const handleDateChange = () => {
  // 日期变化时不自动分析，等待用户点击分析按钮
}

// 处理分析
const handleAnalyze = async () => {
  if (!queryForm.product_id) {
    ElMessage.warning('请选择产品')
    return
  }

  loading.value = true
  hasData.value = false

  try {
    const params = {
      product_id: queryForm.product_id,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }

    // 并行获取所有数据
    const [indicatorsData, chartDataResult, rankingData, multiPeriodData] = await Promise.all([
      analysisApi.getAllIndicators(params),
      analysisApi.getChartData(params),
      analysisApi.getProductRanking(queryForm.product_id, rankingPeriod.value).catch(() => null),
      analysisApi.getMultiPeriodPerformance(queryForm.product_id).catch(() => null)
    ])

    indicators.value = indicatorsData
    chartData.value = chartDataResult
    ranking.value = rankingData
    multiPeriod.value = multiPeriodData
    hasData.value = true

    // 渲染图表
    await nextTick()
    renderChart()

    ElMessage.success('分析完成')
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败')
  } finally {
    loading.value = false
  }
}

// 处理重置
const handleReset = () => {
  queryForm.product_id = undefined
  dateRange.value = null
  hasData.value = false
  indicators.value = null
  chartData.value = null
  ranking.value = null
  multiPeriod.value = null
  
  if (chartInstance) {
    chartInstance.clear()
  }
}

// 切换排名周期
const handleRankingPeriodChange = async (period: string) => {
  if (!queryForm.product_id) return
  try {
    ranking.value = await analysisApi.getProductRanking(queryForm.product_id, period)
  } catch {
    // 静默
  }
}

// 格式化百分比（简短）
const formatPct = (v: number | null | undefined) => {
  if (v === undefined || v === null) return '-'
  return `${(v * 100).toFixed(2)}%`
}

const formatNum = (v: number | null | undefined) => {
  if (v === undefined || v === null) return '-'
  return v.toFixed(2)
}

const getReturnClass = (v: number | null | undefined) => {
  if (v === undefined || v === null) return ''
  return v >= 0 ? 'positive' : 'negative'
}

// 获取分位数样式类
const getPercentileClass = (percentile: number) => {
  if (percentile >= 80) return 'excellent'
  if (percentile >= 60) return 'good'
  if (percentile >= 40) return 'average'
  return 'poor'
}

// 格式化百分比
const formatPercent = (value: number | undefined) => {
  if (value === undefined || value === null) return '-'
  return `${(value * 100).toFixed(2)}%`
}

// 格式化数字
const formatNumber = (value: number | undefined) => {
  if (value === undefined || value === null) return '-'
  return value.toFixed(4)
}

// 获取当前主题文字颜色
const getThemeTextColor = () => {
  const style = getComputedStyle(document.documentElement)
  return {
    primary: style.getPropertyValue('--text-primary').trim() || '#f1f5f9',
    secondary: style.getPropertyValue('--text-secondary').trim() || '#cbd5e1',
    muted: style.getPropertyValue('--text-muted').trim() || '#94a3b8',
    border: style.getPropertyValue('--card-border').trim() || 'rgba(71, 85, 105, 0.4)'
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || !chartData.value) return

  // 初始化图表
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const tc = getThemeTextColor()

  const option: EChartsOption = {
    title: {
      text: '净值走势',
      left: 'center',
      textStyle: { color: tc.primary, fontSize: 16 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(30, 41, 59, 0.9)',
      borderColor: 'rgba(71, 85, 105, 0.5)',
      textStyle: { color: '#f1f5f9' }
    },
    legend: {
      data: ['单位净值', '累计净值'],
      top: 30,
      textStyle: { color: tc.secondary }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.value.dates,
      axisLabel: { color: tc.muted },
      axisLine: { lineStyle: { color: tc.border } },
      splitLine: { lineStyle: { color: tc.border } }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: tc.muted },
      axisLine: { lineStyle: { color: tc.border } },
      splitLine: { lineStyle: { color: tc.border } }
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      {
        start: 0, end: 100,
        textStyle: { color: tc.muted },
        borderColor: tc.border,
        fillerColor: 'rgba(59, 130, 246, 0.15)'
      }
    ],
    series: [
      {
        name: '单位净值',
        type: 'line',
        data: chartData.value.unit_navs,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '累计净值',
        type: 'line',
        data: chartData.value.cumulative_navs,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#F56C6C' }  // 中国A股习惯：红涨绿跌
      }
    ]
  }

  chartInstance.setOption(option)
}

// 窗口大小变化时重新渲染图表
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 初始化
onMounted(() => {
  fetchProducts()
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.analysis-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.selector-card {
  margin-bottom: 20px;
}

.indicators-row {
  margin-bottom: 20px;
}

.indicators-row .el-col {
  margin-bottom: 20px;
}

.indicator-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.indicator-card:hover {
  transform: translateY(-4px);
}

.indicator-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.indicator-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.indicator-data {
  flex: 1;
  min-width: 0;
}

.indicator-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.indicator-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.details-row {
  margin-bottom: 20px;
}

.details-row .el-col {
  margin-bottom: 20px;
}

.detail-card {
  height: 100%;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 500px;
}

/* 排名卡片样式 */
.ranking-card {
  margin-bottom: 20px;
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ranking-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 992px) {
  .ranking-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 576px) {
  .ranking-grid {
    grid-template-columns: 1fr;
  }
}

.ranking-item {
  padding: 16px;
  background: var(--input-bg);
  border-radius: 8px;
}

.ranking-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.ranking-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ranking-value .rank {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.ranking-value .percentile {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.ranking-value .percentile.excellent {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.ranking-value .percentile.good {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.ranking-value .percentile.average {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.ranking-value .percentile.poor {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.ranking-bar {
  height: 6px;
  background: var(--input-border);
  border-radius: 3px;
  overflow: hidden;
}

.ranking-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #95d475);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.ranking-bar-fill.drawdown {
  background: linear-gradient(90deg, #f56c6c, #fab6b6);
}

.ranking-bar-fill.volatility {
  background: linear-gradient(90deg, #e6a23c, #f3d19e);
}

/* 多周期业绩表格 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.multi-period-table {
  overflow-x: auto;
}

.multi-period-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.multi-period-table th {
  padding: 10px 12px;
  text-align: right;
  font-weight: 500;
  color: var(--text-secondary);
  border-bottom: 2px solid var(--card-border);
  white-space: nowrap;
}

.multi-period-table th:first-child {
  text-align: left;
}

.multi-period-table td {
  padding: 10px 12px;
  text-align: right;
  color: var(--text-primary);
  border-bottom: 1px solid var(--card-border);
  white-space: nowrap;
}

.multi-period-table td:first-child {
  text-align: left;
}

.multi-period-table td.period-name {
  font-weight: 500;
  color: var(--text-secondary);
}

.multi-period-table td.positive {
  color: #10b981;
}

.multi-period-table td.negative {
  color: #ef4444;
}

/* 排名卡片头部 */
.ranking-actions {
  display: flex;
  align-items: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .analysis-view {
    padding: 15px;
  }

  .indicator-icon {
    width: 48px;
    height: 48px;
  }

  .indicator-icon .el-icon {
    font-size: 24px !important;
  }

  .indicator-value {
    font-size: 20px;
  }

  .chart-container {
    height: 400px;
  }

  .ranking-header {
    flex-direction: column;
    gap: 8px;
  }

  .ranking-actions {
    flex-wrap: wrap;
  }
}
</style>
