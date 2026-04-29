<template>
  <div class="ranking-view p-6">
    <!-- 页面头部 -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold gradient-text">市场排名</h2>
        <p class="text-sm text-dark-400 mt-1">同策略排名对比，分位数分析</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="glass-card p-5 mb-6">
      <div class="flex flex-wrap items-center gap-4">
        <div>
          <span class="text-sm text-dark-400 mr-2">策略类型</span>
          <el-select v-model="selectedStrategy" placeholder="选择策略" style="width: 160px" @change="fetchRanking">
            <el-option v-for="s in strategies" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </div>
        <div>
          <span class="text-sm text-dark-400 mr-2">分析周期</span>
          <el-select v-model="selectedPeriod" placeholder="选择周期" style="width: 120px" @change="fetchRanking">
            <el-option v-for="p in PERIOD_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </div>
        <div>
          <span class="text-sm text-dark-400 mr-2">排名指标</span>
          <el-select v-model="selectedIndicator" placeholder="选择指标" style="width: 140px" @change="fetchRanking">
            <el-option v-for="i in INDICATOR_OPTIONS" :key="i.value" :label="i.label" :value="i.value" />
          </el-select>
        </div>
        <el-button type="primary" @click="fetchRanking" :loading="loading">
          <el-icon class="mr-1"><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6" v-if="distribution">
      <div class="glass-card p-4">
        <span class="text-sm card-label">产品数量</span>
        <p class="text-2xl font-bold card-value mt-1">{{ distribution.count }}</p>
      </div>
      <div class="glass-card p-4">
        <span class="text-sm card-label">平均值</span>
        <p class="text-2xl font-bold mt-1" :class="distribution.statistics?.mean >= 0 ? 'positive-value' : 'negative-value'">
          {{ formatPercent(distribution.statistics?.mean) }}
        </p>
      </div>
      <div class="glass-card p-4">
        <span class="text-sm card-label">中位数</span>
        <p class="text-2xl font-bold mt-1" :class="distribution.statistics?.median >= 0 ? 'positive-value' : 'negative-value'">
          {{ formatPercent(distribution.statistics?.median) }}
        </p>
      </div>
      <div class="glass-card p-4">
        <span class="text-sm card-label">标准差</span>
        <p class="text-2xl font-bold primary-value mt-1">{{ formatPercent(distribution.statistics?.std) }}</p>
      </div>
    </div>

    <!-- 排行榜表格 -->
    <div class="glass-card p-5 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold section-title">
          {{ getStrategyLabel(selectedStrategy) }}排行榜
          <span class="text-sm card-label ml-2">（{{ getPeriodLabel(selectedPeriod) }}）</span>
        </h3>
        <span class="text-sm card-label">共 {{ rankingData.total || 0 }} 只产品</span>
      </div>

      <el-table :data="rankingData.items" stripe v-loading="loading" max-height="500">
        <el-table-column label="排名" width="80" align="center">
          <template #default="{ row }">
            <span class="rank-badge" :class="getRankClass(row.rank)">{{ row.rank }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" min-width="200">
          <template #default="{ row }">
            <div class="product-info">
              <span class="product-name">{{ row.product_name }}</span>
              <span class="product-code">{{ row.product_code }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="manager_name" label="管理人" min-width="120" />
        <el-table-column label="年化收益" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.annualized_return >= 0 ? 'positive-value' : 'negative-value'">
              {{ formatPercent(row.annualized_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="波动率" width="100" align="right">
          <template #default="{ row }">
            {{ formatPercent(row.annualized_volatility) }}
          </template>
        </el-table-column>
        <el-table-column label="最大回撤" width="100" align="right">
          <template #default="{ row }">
            <span class="negative-value">{{ formatPercent(row.max_drawdown) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="夏普" width="80" align="right">
          <template #default="{ row }">
            {{ row.sharpe_ratio?.toFixed(2) || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="分位数" width="140" align="center">
          <template #default="{ row }">
            <div class="percentile-container">
              <div class="percentile-bar">
                <div class="percentile-fill" :style="{ width: row.percentile + '%' }"></div>
              </div>
              <span class="percentile-label">前{{ (100 - row.percentile).toFixed(0) }}%</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分布图表 -->
    <div class="glass-card p-5">
      <h3 class="text-lg font-semibold section-title mb-4">指标分布</h3>
      <div ref="distributionChart" style="height: 350px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getStrategyRanking,
  getStrategyDistribution,
  getStrategyTypes,
  INDICATOR_OPTIONS,
  PERIOD_OPTIONS
} from '@/api/ranking'

// 状态
const loading = ref(false)
const strategies = ref<Array<{value: string, label: string}>>([])
const selectedStrategy = ref('')
const selectedPeriod = ref('1y')
const selectedIndicator = ref('annualized_return')
const rankingData = ref<any>({ items: [], total: 0 })
const distribution = ref<any>(null)

// 图表
const distributionChart = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 获取策略列表
const fetchStrategies = async () => {
  try {
    const res = await getStrategyTypes()
    strategies.value = res.strategies || []
    if (strategies.value.length > 0 && !selectedStrategy.value) {
      selectedStrategy.value = strategies.value[0].value
      fetchRanking()
    }
  } catch (error) {
    console.error('获取策略列表失败:', error)
  }
}

// 获取排名数据
const fetchRanking = async () => {
  if (!selectedStrategy.value) return
  
  loading.value = true
  try {
    const [rankingRes, distributionRes] = await Promise.all([
      getStrategyRanking(selectedStrategy.value, selectedPeriod.value, selectedIndicator.value, 50),
      getStrategyDistribution(selectedStrategy.value, selectedPeriod.value, selectedIndicator.value)
    ])
    
    rankingData.value = rankingRes
    distribution.value = distributionRes
    
    await nextTick()
    renderDistributionChart()
  } catch (error) {
    console.error('获取排名数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 渲染分布图
const renderDistributionChart = () => {
  if (!distributionChart.value || !distribution.value?.distribution) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(distributionChart.value)
  }
  
  const data = distribution.value.distribution
  const indicatorLabel = INDICATOR_OPTIONS.find(i => i.value === selectedIndicator.value)?.label || selectedIndicator.value
  
  // 根据指标类型决定是否需要转换为百分比
  const isPercentage = ['annualized_return', 'total_return', 'annualized_volatility', 'max_drawdown'].includes(selectedIndicator.value)
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const item = data[params[0].dataIndex]
        const value = isPercentage ? (item.value * 100).toFixed(2) + '%' : item.value.toFixed(2)
        return `${item.product_name}<br/>${indicatorLabel}: ${value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((_: any, i: number) => i + 1),
      axisLabel: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#94a3b8',
        interval: Math.floor(data.length / 10)
      },
      axisLine: { lineStyle: { color: getComputedStyle(document.documentElement).getPropertyValue('--card-border').trim() || '#334155' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#94a3b8',
        formatter: isPercentage ? (val: number) => (val * 100).toFixed(0) + '%' : undefined
      },
      splitLine: { lineStyle: { color: getComputedStyle(document.documentElement).getPropertyValue('--card-border').trim() || '#1e293b' } }
    },
    series: [{
      type: 'bar',
      data: data.map((item: any) => ({
        value: item.value,
        itemStyle: {
          color: item.value >= 0 ? '#10b981' : '#ef4444'
        }
      })),
      barWidth: '60%'
    }]
  }
  
  chartInstance.setOption(option)
}

// 格式化百分比
const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return (value * 100).toFixed(2) + '%'
}

// 获取排名样式
const getRankClass = (rank: number) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

// 获取策略标签
const getStrategyLabel = (value: string) => {
  return strategies.value.find(s => s.value === value)?.label || value
}

// 获取周期标签
const getPeriodLabel = (value: string) => {
  return PERIOD_OPTIONS.find(p => p.value === value)?.label || value
}

// 监听窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  fetchStrategies()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-weight: 600;
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.rank-gold {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #1e293b;
}

.rank-silver {
  background: linear-gradient(135deg, #e2e8f0, #94a3b8);
  color: #1e293b;
}

.rank-bronze {
  background: linear-gradient(135deg, #d97706, #b45309);
  color: white;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.product-name {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 14px;
  line-height: 1.4;
}

.product-code {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.3;
}

.percentile-container {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.percentile-bar {
  position: relative;
  flex: 1;
  height: 18px;
  background: rgba(100, 116, 139, 0.15);
  border-radius: 9px;
  overflow: hidden;
  min-width: 60px;
}

.percentile-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #0a7df5, #38bdf8);
  border-radius: 9px;
  transition: width 0.3s ease;
}

.percentile-label {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  min-width: 40px;
}

/* 移除旧的 percentile-text 样式 */

/* 浅色主题适配 */
.section-title {
  color: var(--text-primary);
}

.card-label {
  color: var(--text-secondary);
}

.card-value {
  color: var(--text-primary);
}

/* 中国A股习惯：红涨绿跌 */
.positive-value {
  color: #ef4444 !important;  /* 正收益用红色 */
}

.negative-value {
  color: #10b981 !important;  /* 负收益用绿色 */
}

.primary-value {
  color: #3b82f6 !important;
}

:global(.light-theme) .section-title {
  color: #1e293b;
}

:global(.light-theme) .card-label {
  color: #6b7280;
}

:global(.light-theme) .card-value {
  color: #1e293b;
}

/* 中国A股习惯：红涨绿跌 - 浅色主题 */
:global(.light-theme) .positive-value {
  color: #dc2626 !important;  /* 正收益用红色 */
}

:global(.light-theme) .negative-value {
  color: #059669 !important;  /* 负收益用绿色 */
}

:global(.light-theme) .primary-value {
  color: #2563eb !important;
}
</style>
