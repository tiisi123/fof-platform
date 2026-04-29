<template>
  <div class="reports-view">
    <div class="page-header">
      <h1>报表中心</h1>
      <p class="subtitle">导出各类业务报表</p>
    </div>

    <div class="reports-grid">
      <div 
        v-for="report in reportTypes" 
        :key="report.key"
        class="report-card"
      >
        <div class="report-icon">
          <el-icon :size="32">
            <component :is="getIcon(report.key)" />
          </el-icon>
        </div>
        <div class="report-info">
          <h3>{{ report.name }}</h3>
          <p>{{ report.description }}</p>
        </div>
        
        <!-- 筛选条件 -->
        <div class="report-filters" v-if="report.filters.length > 0">
          <template v-for="filter in report.filters" :key="filter">
            <!-- 跟踪池分类 -->
            <el-select
              v-if="filter === 'pool_category'"
              v-model="filters[report.key].pool_category"
              placeholder="跟踪池分类"
              clearable
              size="small"
            >
              <el-option label="在投池" value="invested" />
              <el-option label="重点跟踪池" value="key_tracking" />
              <el-option label="观察池" value="observation" />
              <el-option label="淘汰池" value="eliminated" />
              <el-option label="已看过" value="contacted" />
            </el-select>
            
            <!-- 策略类型 -->
            <el-select
              v-if="filter === 'primary_strategy' || filter === 'strategy_type'"
              v-model="filters[report.key][filter]"
              placeholder="策略类型"
              clearable
              size="small"
            >
              <el-option label="股票多头" value="equity_long" />
              <el-option label="量化中性" value="quant_neutral" />
              <el-option label="CTA" value="cta" />
              <el-option label="套利" value="arbitrage" />
              <el-option label="多策略" value="multi_strategy" />
              <el-option label="债券" value="bond" />
              <el-option label="其他" value="other" />
            </el-select>
            
            <!-- 业绩周期 -->
            <el-select
              v-if="filter === 'period'"
              v-model="filters[report.key].period"
              placeholder="业绩周期"
              size="small"
            >
              <el-option label="近1月" value="1m" />
              <el-option label="近3月" value="3m" />
              <el-option label="近6月" value="6m" />
              <el-option label="近1年" value="1y" />
              <el-option label="今年以来" value="ytd" />
            </el-select>
            
            <!-- 组合选择 -->
            <el-select
              v-if="filter === 'portfolio_id'"
              v-model="filters[report.key].portfolio_id"
              placeholder="选择组合（可选）"
              clearable
              size="small"
            >
              <el-option
                v-for="p in portfolios"
                :key="p.id"
                :label="p.name"
                :value="p.id"
              />
            </el-select>
            
            <!-- 项目阶段 -->
            <el-select
              v-if="filter === 'stage'"
              v-model="filters[report.key].stage"
              placeholder="项目阶段"
              clearable
              size="small"
            >
              <el-option label="Sourcing" value="sourcing" />
              <el-option label="初筛" value="initial_screening" />
              <el-option label="尽调" value="due_diligence" />
              <el-option label="投决" value="investment_decision" />
              <el-option label="投后" value="post_investment" />
              <el-option label="退出" value="exit" />
            </el-select>
          </template>
        </div>
        
        <div class="report-action">
          <el-button 
            @click="previewReport(report.key)"
            :loading="previewing[report.key]"
          >
            <el-icon><View /></el-icon>
            预览
          </el-button>
          <el-button 
            type="primary" 
            @click="exportReport(report.key)"
            :loading="exporting[report.key]"
          >
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 单产品净值导出 -->
    <div class="nav-export-section">
      <h2>净值数据导出</h2>
      <div class="nav-export-form">
        <el-select
          v-model="navExport.productId"
          placeholder="选择产品"
          filterable
          clearable
          style="width: 300px"
        >
          <el-option
            v-for="p in products"
            :key="p.id"
            :label="`${p.product_code || ''} - ${p.product_name}`"
            :value="p.id"
          />
        </el-select>
        
        <el-date-picker
          v-model="navExport.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
        />
        
        <el-button 
          type="primary" 
          @click="exportNavData"
          :loading="navExport.loading"
          :disabled="!navExport.productId"
        >
          <el-icon><Download /></el-icon>
          导出净值
        </el-button>
      </div>
    </div>
    <!-- 预览对话框 -->
    <el-dialog v-model="previewDialogVisible" :title="previewTitle" width="80%" top="5vh" destroy-on-close>
      <div v-loading="previewLoading">
        <div class="preview-summary" v-if="previewData">
          <el-tag type="info" size="small">共 {{ previewData.total }} 条记录，预览前 {{ previewData.rows?.length || 0 }} 条</el-tag>
        </div>
        <el-table :data="previewData?.rows || []" stripe border max-height="500" style="margin-top: 12px">
          <el-table-column
            v-for="col in previewData?.columns || []"
            :key="col"
            :prop="col"
            :label="col"
            min-width="120"
            show-overflow-tooltip
          />
        </el-table>
        <el-empty v-if="previewData && (!previewData.rows || previewData.rows.length === 0)" description="暂无数据" />
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="exportFromPreview">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { Download, User, Collection, DataBoard, Folder, TrendCharts, View } from '@element-plus/icons-vue'
import request from '@/api/request'

// 报表类型
const reportTypes = ref([
  {
    key: 'manager',
    name: '管理人汇总报表',
    description: '管理人基本信息、产品数量、代表产品业绩',
    filters: ['pool_category', 'primary_strategy']
  },
  {
    key: 'pool',
    name: '跟踪池报表',
    description: '各分类管理人及代表产品多周期业绩',
    filters: ['pool_category']
  },
  {
    key: 'product',
    name: '产品业绩报表',
    description: '产品信息、最新净值、多周期收益、风险指标',
    filters: ['strategy_type', 'period']
  },
  {
    key: 'portfolio',
    name: '组合报表',
    description: '组合概览、成分明细',
    filters: ['portfolio_id']
  },
  {
    key: 'project',
    name: '一级项目报表',
    description: '项目基本信息、阶段、投资金额等',
    filters: ['stage']
  }
])

// 筛选条件
const filters = reactive<Record<string, any>>({
  manager: { pool_category: '', primary_strategy: '' },
  pool: { pool_category: '' },
  product: { strategy_type: '', period: '1y' },
  portfolio: { portfolio_id: null },
  project: { stage: '' }
})

// 导出状态
const exporting = reactive<Record<string, boolean>>({
  manager: false,
  pool: false,
  product: false,
  portfolio: false,
  project: false
})

// 预览状态
const previewing = reactive<Record<string, boolean>>({
  manager: false, pool: false, product: false, portfolio: false, project: false
})
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewTitle = ref('')
const previewData = ref<any>(null)
const previewCurrentKey = ref('')

// 组合列表
const portfolios = ref<any[]>([])

// 产品列表
const products = ref<any[]>([])

// 净值导出
const navExport = reactive({
  productId: null as number | null,
  dateRange: null as [string, string] | null,
  loading: false
})

// 获取图标
const getIcon = (key: string) => {
  const icons: Record<string, any> = {
    manager: User,
    pool: Collection,
    product: TrendCharts,
    portfolio: DataBoard,
    project: Folder
  }
  return icons[key] || DataBoard
}

// 加载组合列表
const loadPortfolios = async () => {
  try {
    const res = await request.get('/portfolios')
    portfolios.value = res.data?.items || res.items || []
  } catch (e) {
    console.error('加载组合失败', e)
  }
}

// 加载产品列表
const loadProducts = async () => {
  try {
    const res = await request.get('/products', { params: { limit: 1000 } })
    products.value = res.data?.items || res.items || []
  } catch (e) {
    console.error('加载产品失败', e)
  }
}

// 报表预览
const previewReport = async (key: string) => {
  const nameMap: Record<string, string> = {
    manager: '管理人汇总报表', pool: '跟踪池报表',
    product: '产品业绩报表', portfolio: '组合报表', project: '一级项目报表'
  }
  previewTitle.value = `${nameMap[key] || '报表'}预览`
  previewCurrentKey.value = key
  previewDialogVisible.value = true
  previewLoading.value = true
  previewing[key] = true

  try {
    const params = new URLSearchParams()
    const filterData = filters[key]
    for (const [k, v] of Object.entries(filterData)) {
      if (v !== null && v !== '' && v !== undefined) {
        params.append(k, String(v))
      }
    }
    const url = `/reports/preview/${key}${params.toString() ? '?' + params.toString() : ''}`
    const res = await request.get(url)
    previewData.value = res.data || res
  } catch (e: any) {
    previewData.value = { columns: [], rows: [], total: 0 }
    ElMessage.error(e.message || '加载预览失败')
  } finally {
    previewLoading.value = false
    previewing[key] = false
  }
}

const exportFromPreview = () => {
  previewDialogVisible.value = false
  exportReport(previewCurrentKey.value)
}

// 导出报表
const exportReport = async (key: string) => {
  exporting[key] = true
  
  const nameMap: Record<string, string> = {
    manager: '管理人汇总报表',
    pool: '跟踪池报表',
    product: '产品业绩报表',
    portfolio: '组合报表',
    project: '一级项目报表'
  }
  
  // 显示导出进度通知
  const notifyInstance = ElNotification({
    title: '正在导出',
    message: `${nameMap[key]} 正在生成中，请稍候...`,
    duration: 0,
    type: 'info',
    showClose: false
  })
  
  try {
    const params = new URLSearchParams()
    const filterData = filters[key]
    
    for (const [k, v] of Object.entries(filterData)) {
      if (v !== null && v !== '' && v !== undefined) {
        params.append(k, String(v))
      }
    }
    
    const url = `/reports/${key}${params.toString() ? '?' + params.toString() : ''}`
    
    const response = await request.get(url, {
      responseType: 'blob'
    })
    
    // 关闭进度通知
    notifyInstance.close()
    
    // 下载文件
    const blob = new Blob([response as any], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    link.download = `${nameMap[key]}_${today}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
    
    // 显示成功通知
    ElNotification({
      title: '导出成功',
      message: `${nameMap[key]} 已下载`,
      type: 'success',
      duration: 3000
    })
  } catch (e: any) {
    notifyInstance.close()
    console.error('导出失败', e)
    ElNotification({
      title: '导出失败',
      message: e.message || '报表生成失败，请稍后重试',
      type: 'error',
      duration: 5000
    })
  } finally {
    exporting[key] = false
  }
}

// 导出净值数据
const exportNavData = async () => {
  if (!navExport.productId) {
    ElMessage.warning('请选择产品')
    return
  }
  
  navExport.loading = true
  
  // 显示导出进度通知
  const notifyInstance = ElNotification({
    title: '正在导出',
    message: '净值数据正在生成中，请稍候...',
    duration: 0,
    type: 'info',
    showClose: false
  })
  
  try {
    const params = new URLSearchParams()
    if (navExport.dateRange) {
      params.append('start_date', navExport.dateRange[0])
      params.append('end_date', navExport.dateRange[1])
    }
    
    const url = `/reports/nav/${navExport.productId}${params.toString() ? '?' + params.toString() : ''}`
    
    const response = await request.get(url, {
      responseType: 'blob'
    })
    
    notifyInstance.close()
    
    const blob = new Blob([response as any], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const productName = products.value.find(p => p.id === navExport.productId)?.product_name || navExport.productId
    link.download = `净值数据_${productName}_${today}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
    
    ElNotification({
      title: '导出成功',
      message: '净值数据已下载',
      type: 'success',
      duration: 3000
    })
  } catch (e: any) {
    notifyInstance.close()
    console.error('导出失败', e)
    ElNotification({
      title: '导出失败',
      message: e.message || '净值数据导出失败',
      type: 'error',
      duration: 5000
    })
  } finally {
    navExport.loading = false
  }
}

onMounted(() => {
  loadPortfolios()
  loadProducts()
})
</script>

<style scoped>
.reports-view {
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

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.report-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s ease;
}

.report-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.report-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.report-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.report-info p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.report-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.report-filters .el-select {
  width: 150px;
}

.report-action {
  margin-top: auto;
  padding-top: 8px;
  display: flex;
  gap: 8px;
}

.preview-summary {
  margin-bottom: 8px;
}

.nav-export-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 24px;
}

.nav-export-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

.nav-export-form {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
</style>
