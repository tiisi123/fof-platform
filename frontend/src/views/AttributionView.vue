<template>
  <div class="attribution-view">
    <div class="page-header">
      <h1>因子归因分析</h1>
      <p class="subtitle">基于Barra多因子模型的业绩归因分析</p>
    </div>

    <!-- 产品选择 -->
    <div class="control-panel">
      <div class="control-item">
        <label>选择产品</label>
        <el-select 
          v-model="selectedProductId" 
          placeholder="请选择产品"
          filterable
          style="width: 300px"
          @change="loadAttribution"
        >
          <el-option 
            v-for="p in products" 
            :key="p.id" 
            :label="p.product_name" 
            :value="p.id"
          />
        </el-select>
      </div>
      <div class="control-item">
        <label>分析周期</label>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="loadAttribution"
        />
      </div>
      <el-button type="primary" @click="loadAttribution" :loading="loading">
        <el-icon><Refresh /></el-icon>
        分析
      </el-button>
    </div>

    <!-- 分析结果 -->
    <div v-if="attribution" v-loading="loading" class="result-container">
      <!-- 摘要卡片 -->
      <div class="summary-section">
        <div class="summary-card">
          <div class="summary-title">分析周期</div>
          <div class="summary-value">
            {{ attribution.analysis_period?.start_date }} 至 {{ attribution.analysis_period?.end_date }}
          </div>
          <div class="summary-sub">共 {{ attribution.analysis_period?.trading_days }} 个交易日</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">R²</div>
          <div class="summary-value">{{ formatPercent(attribution.regression_stats?.r_squared) }}</div>
          <div class="summary-sub">模型解释力</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">年化Alpha</div>
          <div class="summary-value" :class="getReturnClass(attribution.regression_stats?.alpha_annualized)">
            {{ formatPercent(attribution.regression_stats?.alpha_annualized) }}
          </div>
          <div class="summary-sub">超额收益能力</div>
        </div>
        <div class="summary-card">
          <div class="summary-title">跟踪误差</div>
          <div class="summary-value">{{ formatPercent(attribution.regression_stats?.tracking_error) }}</div>
          <div class="summary-sub">残差波动</div>
        </div>
      </div>

      <!-- 风格标签 -->
      <div class="style-tags" v-if="attribution.summary?.style_tags?.length">
        <span class="tag-label">风格特征：</span>
        <el-tag v-for="tag in attribution.summary.style_tags" :key="tag" type="info" class="style-tag">
          {{ tag }}
        </el-tag>
      </div>

      <div class="charts-row">
        <!-- 因子暴露雷达图 -->
        <div class="chart-card">
          <h3>因子暴露</h3>
          <div ref="radarChart" class="chart-container"></div>
        </div>

        <!-- 归因饼图 -->
        <div class="chart-card">
          <h3>业绩归因</h3>
          <div ref="pieChart" class="chart-container"></div>
        </div>
      </div>

      <!-- 归因走势图 -->
      <div class="chart-card full-width">
        <h3>累计归因走势</h3>
        <div ref="lineChart" class="chart-container-large"></div>
      </div>

      <!-- 因子明细表 -->
      <div class="detail-section">
        <h3>因子贡献明细</h3>
        <div class="factor-table">
          <table>
            <thead>
              <tr>
                <th>因子</th>
                <th>因子暴露</th>
                <th>因子收益</th>
                <th>收益贡献</th>
                <th>贡献占比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(data, factor) in attribution.attribution?.by_factor" :key="factor">
                <td>
                  <span class="factor-name">{{ data.name }}</span>
                </td>
                <td>
                  <div class="exposure-bar-container">
                    <div 
                      class="exposure-bar" 
                      :class="{ positive: data.exposure > 0, negative: data.exposure < 0 }"
                      :style="{ width: Math.abs(data.exposure) * 50 + '%' }"
                    ></div>
                    <span class="exposure-value">{{ data.exposure?.toFixed(3) }}</span>
                  </div>
                </td>
                <td :class="getReturnClass(data.factor_return)">
                  {{ formatPercent(data.factor_return) }}
                </td>
                <td :class="getReturnClass(data.contribution)">
                  {{ formatPercent(data.contribution) }}
                </td>
                <td>{{ data.contribution_pct?.toFixed(1) }}%</td>
              </tr>
              <!-- Alpha 行 -->
              <tr class="alpha-row">
                <td><span class="factor-name">Alpha (超额收益)</span></td>
                <td>-</td>
                <td>-</td>
                <td :class="getReturnClass(attribution.attribution?.summary?.alpha_contribution)">
                  {{ formatPercent(attribution.attribution?.summary?.alpha_contribution) }}
                </td>
                <td>{{ attribution.attribution?.summary?.alpha_contribution_pct?.toFixed(1) }}%</td>
              </tr>
              <!-- 合计行 -->
              <tr class="total-row">
                <td><strong>合计</strong></td>
                <td>-</td>
                <td>-</td>
                <td :class="getReturnClass(attribution.attribution?.summary?.total_return)">
                  <strong>{{ formatPercent(attribution.attribution?.summary?.total_return) }}</strong>
                </td>
                <td><strong>100%</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 分析描述 -->
      <div class="description-section" v-if="attribution.summary?.description">
        <h3>分析结论</h3>
        <p>{{ attribution.summary.description }}</p>
      </div>
    </div>

    <!-- Barra 因子数据来源说明 -->
    <div class="data-source-section glass-card" style="margin-top: 24px">
      <div class="section-header">
        <h3>因子数据来源</h3>
        <el-button type="primary" @click="factorImportDialogVisible = true">导入因子数据</el-button>
      </div>
      <div class="source-desc">
        <p>本系统采用 <strong>Barra CNE6 多因子模型</strong> 进行业绩归因分析，包含以下核心因子：</p>
        <ul class="factor-list">
          <li><span class="factor-code">CNE6_BETA</span> 市场因子 - 泡露于市场系统性风险</li>
          <li><span class="factor-code">CNE6_SIZE</span> 市值因子 - 大/小盘风格偏好</li>
          <li><span class="factor-code">CNE6_MOMENTUM</span> 动量因子 - 趋势跟随/反转特征</li>
          <li><span class="factor-code">CNE6_VALUE</span> 价值因子 - 估值偏好 (PB/PE)</li>
          <li><span class="factor-code">CNE6_GROWTH</span> 成长因子 - 盈利成长预期</li>
          <li><span class="factor-code">CNE6_VOLATILITY</span> 波动因子 - 收益率波动波露</li>
          <li><span class="factor-code">CNE6_QUALITY</span> 质量因子 - 盈利质量、ROE稳定性</li>
          <li><span class="factor-code">CNE6_LIQUIDITY</span> 流动性因子 - 换手率/成交量</li>
        </ul>
        <el-alert type="info" :closable="false" style="margin-top: 12px">
          <template #title>
            <strong>数据对接方式</strong>
          </template>
          因子收益率数据可通过以下方式获取：<br/>
          1. <strong>Wind/万得</strong>：订阅 Barra CNE6 因子数据库，导出 CSV 格式<br/>
          2. <strong>API 对接</strong>：配置第三方数据提供商 API 自动拉取（联系管理员配置）<br/>
          3. <strong>手工导入</strong>：上传 Excel 文件，格式要求：日期 | 因子代码 | 因子收益率
        </el-alert>
      </div>
    </div>

    <!-- 因子数据导入对话框 -->
    <el-dialog v-model="factorImportDialogVisible" title="导入因子数据" width="550px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        请上传包含 Barra 因子收益率的 Excel 文件，样例格式：<br/>
        <code>日期 | 因子代码 | 因子收益率</code>
      </el-alert>
      <el-upload
        class="upload-area"
        drag
        action=""
        :auto-upload="false"
        :show-file-list="true"
        :on-change="handleFactorFileChange"
        :limit="1"
        accept=".xls,.xlsx,.csv"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 .xls / .xlsx / .csv 格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="factorImportDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!factorFile" @click="handleFactorImport" :loading="factorImporting">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!attribution && !loading">
      <el-icon :size="64"><TrendCharts /></el-icon>
      <p>选择产品后进行因子归因分析</p>
    </div>

    <!-- 数据不足提示 -->
    <div class="error-state" v-if="attribution?.error">
      <el-icon :size="48"><Warning /></el-icon>
      <p>{{ attribution.message || attribution.error }}</p>
      <p class="sub-text" v-if="attribution.data_points">当前数据点：{{ attribution.data_points }} 个</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, TrendCharts, Warning, Upload } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '@/api/request'

const loading = ref(false)
const selectedProductId = ref<number | null>(null)
const dateRange = ref<[string, string] | null>(null)
const products = ref<any[]>([])
const attribution = ref<any>(null)

// 主题颜色解析
const getThemeColors = () => {
  const s = getComputedStyle(document.documentElement)
  return {
    textPrimary: s.getPropertyValue('--text-primary').trim() || '#f1f5f9',
    textSecondary: s.getPropertyValue('--text-secondary').trim() || '#cbd5e1',
    textMuted: s.getPropertyValue('--text-muted').trim() || '#94a3b8',
    border: s.getPropertyValue('--card-border').trim() || 'rgba(71, 85, 105, 0.4)',
    cardBg: s.getPropertyValue('--card-bg').trim() || 'rgba(30, 41, 59, 0.8)',
  }
}

// 图表实例
let radarChartInstance: echarts.ECharts | null = null
let pieChartInstance: echarts.ECharts | null = null
let lineChartInstance: echarts.ECharts | null = null

const radarChart = ref<HTMLElement | null>(null)
const pieChart = ref<HTMLElement | null>(null)
const lineChart = ref<HTMLElement | null>(null)

// Barra 因子导入
const factorImportDialogVisible = ref(false)
const factorFile = ref<File | null>(null)
const factorImporting = ref(false)

const handleFactorFileChange = (file: any) => {
  factorFile.value = file.raw
}

const handleFactorImport = async () => {
  if (!factorFile.value) return
  factorImporting.value = true
  try {
    const formData = new FormData()
    formData.append('file', factorFile.value)
    await request.post('/attribution/import-factors', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('因子数据导入成功')
    factorImportDialogVisible.value = false
    factorFile.value = null
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    factorImporting.value = false
  }
}

// 加载产品列表
const loadProducts = async () => {
  try {
    const res = await request.get('/products', { params: { page_size: 500 } })
    products.value = res.data?.items || res.items || []
  } catch (e) {
    console.error('加载产品失败', e)
  }
}

// 销毁图表实例
const disposeCharts = () => {
  if (radarChartInstance) {
    radarChartInstance.dispose()
    radarChartInstance = null
  }
  if (pieChartInstance) {
    pieChartInstance.dispose()
    pieChartInstance = null
  }
  if (lineChartInstance) {
    lineChartInstance.dispose()
    lineChartInstance = null
  }
}

// 加载归因分析
const loadAttribution = async () => {
  if (!selectedProductId.value) {
    ElMessage.warning('请选择产品')
    return
  }
  
  loading.value = true
  disposeCharts()
  attribution.value = null
  
  try {
    const params: any = {}
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    console.log('正在加载归因分析，产品ID:', selectedProductId.value, '参数:', params)
    const res = await request.get(`/attribution/product/${selectedProductId.value}`, { params })
    console.log('API响应:', res)
    
    // request拦截器已经提取了response.data，所以res就是数据本身
    attribution.value = res
    
    console.log('归因数据已设置:', attribution.value)
    
    if (!attribution.value.error) {
      await nextTick()
      console.log('开始渲染图表')
      renderCharts()
    } else {
      console.warn('归因分析返回错误:', attribution.value.error, attribution.value.message)
    }
  } catch (e: any) {
    console.error('加载归因分析失败:', e)
    ElMessage.error(e.message || '分析失败')
  } finally {
    loading.value = false
  }
}

// 渲染图表
const renderCharts = () => {
  renderRadarChart()
  renderPieChart()
  renderLineChart()
}

// 雷达图 - 因子暴露
const renderRadarChart = () => {
  if (!radarChart.value || !attribution.value?.factor_exposures) return
  
  if (!radarChartInstance) {
    radarChartInstance = echarts.init(radarChart.value)
  }
  
  const factors = Object.entries(attribution.value.factor_exposures)
  const indicators = factors.map(([_, data]: any) => ({
    name: data.name,
    max: 1,
    min: -1,
  }))
  const values = factors.map(([_, data]: any) => data.normalized_exposure || 0)
  
  const tc = getThemeColors()
  const option = {
    tooltip: {
      backgroundColor: 'rgba(30, 41, 59, 0.9)',
      borderColor: 'rgba(71, 85, 105, 0.5)',
      textStyle: { color: '#f1f5f9' }
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: tc.textSecondary,
        fontSize: 12,
      },
      splitLine: {
        lineStyle: { color: tc.border }
      },
      splitArea: {
        areaStyle: { color: ['transparent'] }
      },
      axisLine: {
        lineStyle: { color: tc.border }
      },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '因子暴露',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        },
        lineStyle: {
          color: '#409eff',
          width: 2,
        },
        itemStyle: {
          color: '#409eff',
        }
      }]
    }]
  }
  
  radarChartInstance.setOption(option, { notMerge: true })
}

// 饼图 - 业绩归因
const renderPieChart = () => {
  if (!pieChart.value || !attribution.value?.attribution?.summary?.by_category) return
  
  if (!pieChartInstance) {
    pieChartInstance = echarts.init(pieChart.value)
  }
  
  const category = attribution.value.attribution.summary.by_category
  const data = [
    { name: '市场因子', value: Math.abs(category.market || 0), realValue: category.market },
    { name: '风格因子', value: Math.abs(category.style || 0), realValue: category.style },
    { name: '其他因子', value: Math.abs(category.other || 0), realValue: category.other },
    { name: 'Alpha', value: Math.abs(category.alpha || 0), realValue: category.alpha },
  ].filter(d => d.value > 0.0001)
  
  const tc = getThemeColors()
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 41, 59, 0.9)',
      borderColor: 'rgba(71, 85, 105, 0.5)',
      textStyle: { color: '#f1f5f9' },
      formatter: (params: any) => {
        const realVal = params.data.realValue
        return `${params.name}<br/>贡献: ${(realVal * 100).toFixed(2)}%`
      }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: tc.textSecondary }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: tc.cardBg,
        borderWidth: 2
      },
      label: {
        show: false,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data: data,
      // 中国A股习惯：红涨绿跌（这里是图表配色，保持原样）
      color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c']
    }]
  }
  
  pieChartInstance.setOption(option, { notMerge: true })
}

// 折线图 - 累计归因走势
const renderLineChart = () => {
  if (!lineChart.value || !attribution.value?.cumulative_attribution) return
  
  if (!lineChartInstance) {
    lineChartInstance = echarts.init(lineChart.value)
  }
  
  const data = attribution.value.cumulative_attribution
  const xData = data.map((d: any) => d.index)
  
  const tc = getThemeColors()
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.9)',
      borderColor: 'rgba(71, 85, 105, 0.5)',
      textStyle: { color: '#f1f5f9' },
      formatter: (params: any) => {
        let result = `第 ${params[0].axisValue} 日<br/>`
        params.forEach((p: any) => {
          result += `${p.marker} ${p.seriesName}: ${(p.value * 100).toFixed(2)}%<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['总收益', '因子贡献', 'Alpha贡献'],
      textStyle: { color: tc.textSecondary }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: tc.border } },
      axisLabel: { color: tc.textSecondary },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: tc.textSecondary,
        formatter: (val: number) => (val * 100).toFixed(0) + '%'
      },
      axisLine: { lineStyle: { color: tc.border } },
      splitLine: { lineStyle: { color: tc.border } },
    },
    series: [
      {
        name: '总收益',
        type: 'line',
        data: data.map((d: any) => d.total_return),
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#409eff' },
      },
      {
        name: '因子贡献',
        type: 'line',
        data: data.map((d: any) => d.factor_contribution),
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#f56c6c' },  // 中国A股习惯：红涨绿跌
      },
      {
        name: 'Alpha贡献',
        type: 'line',
        data: data.map((d: any) => d.alpha_contribution),
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: '#67c23a' },  // 中国A股习惯：红涨绿跌
      }
    ]
  }
  
  lineChartInstance.setOption(option, { notMerge: true })
}

// 格式化方法
const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(2)}%`
}

const getReturnClass = (value: number | null | undefined) => {
  if (value === null || value === undefined) return ''
  return value >= 0 ? 'positive' : 'negative'
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  radarChartInstance?.resize()
  pieChartInstance?.resize()
  lineChartInstance?.resize()
}

onMounted(() => {
  loadProducts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  disposeCharts()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.attribution-view {
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

.control-panel {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 24px;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-item label {
  font-size: 14px;
  color: var(--text-secondary);
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.summary-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.summary-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.summary-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.style-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-label {
  color: var(--text-secondary);
  font-size: 14px;
}

.style-tag {
  margin: 0;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.chart-container {
  height: 300px;
}

.chart-container-large {
  height: 350px;
}

.detail-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.factor-table table {
  width: 100%;
  border-collapse: collapse;
}

.factor-table th,
.factor-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--card-border);
}

.factor-table th {
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 13px;
}

.factor-name {
  font-weight: 500;
}

.exposure-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.exposure-bar {
  height: 8px;
  border-radius: 4px;
  min-width: 4px;
}

.exposure-bar.positive {
  background: #10b981;
}

.exposure-bar.negative {
  background: #ef4444;
}

.exposure-value {
  font-size: 13px;
  color: var(--text-secondary);
}

.alpha-row td:first-child,
.total-row td:first-child {
  font-weight: 500;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}

.description-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
}

.description-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.description-section p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.empty-state,
.error-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
}

.empty-state .el-icon,
.error-state .el-icon {
  color: var(--el-color-primary-light-5);
  margin-bottom: 16px;
}

.error-state .el-icon {
  color: var(--el-color-warning);
}

.sub-text {
  font-size: 13px;
  margin-top: 8px;
}

@media (max-width: 1200px) {
  .summary-section {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .control-panel {
    flex-direction: column;
    align-items: stretch;
  }
  
  .summary-section {
    grid-template-columns: 1fr;
  }
}

/* 因子数据来源说明 */
.data-source-section {
  padding: 20px;
  border-radius: 12px;
}

.data-source-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.data-source-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.source-desc p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.factor-list {
  list-style: none;
  padding: 0;
  margin: 0 0 12px 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.factor-list li {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 6px 10px;
  background: var(--input-bg);
  border-radius: 6px;
}

.factor-code {
  font-family: monospace;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-right: 8px;
}

.upload-area {
  width: 100%;
}

@media (max-width: 768px) {
  .factor-list {
    grid-template-columns: 1fr;
  }
}
</style>
