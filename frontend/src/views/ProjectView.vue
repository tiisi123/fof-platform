<template>
  <div class="project-view">
    <!-- 页面头部 -->
    <div class="page-header animate-fade-in">
      <div class="header-left">
        <h2 class="gradient-text">一级项目管理</h2>
        <p class="subtitle">共 {{ pagination.total }} 个项目</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>
          <span>下载模板</span>
        </el-button>
        <el-upload :show-file-list="false" :before-upload="handleImport" accept=".xlsx,.xls">
          <el-button>
            <el-icon><Upload /></el-icon>
            <span>批量导入</span>
          </el-button>
        </el-upload>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          <span>新建项目</span>
        </el-button>
      </div>
    </div>

    <!-- 阶段统计卡片 -->
    <div class="stage-cards animate-slide-up">
      <div 
        v-for="(stage, index) in PROJECT_STAGE_OPTIONS" 
        :key="stage.value" 
        class="stage-card glass-card"
        :style="{ animationDelay: `${index * 50}ms` }"
      >
        <div class="stage-dot" :style="{ backgroundColor: stage.color }"></div>
        <div class="stage-info">
          <span class="stage-count stat-number">{{ stats.by_stage[stage.value] || 0 }}</span>
          <span class="stage-label">{{ stage.label }}</span>
        </div>
      </div>
    </div>

    <!-- 投资漏斗图 + 行业分布 -->
    <div class="charts-row animate-slide-up" style="animation-delay: 200ms">
      <div class="glass-card chart-card">
        <h4 class="chart-title">项目漏斗</h4>
        <div ref="funnelChartRef" style="height: 240px; width: 100%"></div>
      </div>
      <div class="glass-card chart-card">
        <h4 class="chart-title">行业分布</h4>
        <div ref="industryChartRef" style="height: 240px; width: 100%"></div>
      </div>
      <div class="glass-card chart-card">
        <h4 class="chart-title">投资汇总</h4>
        <div class="invest-summary">
          <div class="invest-item">
            <span class="invest-value">{{ stats.total_investment?.toLocaleString() || 0 }}</span>
            <span class="invest-label">总投资金额(万)</span>
          </div>
          <div class="invest-item">
            <span class="invest-value">{{ stats.total || 0 }}</span>
            <span class="invest-label">项目总数</span>
          </div>
          <div class="invest-item">
            <span class="invest-value">{{ (stats.by_stage['post_investment'] || 0) + (stats.by_stage['exit'] || 0) }}</span>
            <span class="invest-label">已投/已退</span>
          </div>
          <div class="invest-item">
            <span class="invest-value">{{ conversionRate }}%</span>
            <span class="invest-label">整体转化率</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 视图切换 -->
    <div class="view-toggle animate-slide-up" style="animation-delay: 280ms">
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button value="table">列表视图</el-radio-button>
        <el-radio-button value="pipeline">管线跟踪</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 管线跟踪视图 -->
    <div v-if="viewMode === 'pipeline'" class="pipeline-view animate-slide-up" style="animation-delay: 320ms">
      <div class="pipeline-board">
        <div v-for="stage in pipelineStages" :key="stage.value" class="pipeline-column glass-card">
          <div class="pipeline-col-header" :style="{ borderTopColor: stage.color }">
            <span class="pipeline-col-title">{{ stage.label }}</span>
            <span class="pipeline-col-count">{{ pipelineProjects[stage.value]?.length || 0 }}</span>
          </div>
          <div class="pipeline-col-body">
            <div
              v-for="proj in (pipelineProjects[stage.value] || [])" :key="proj.id"
              class="pipeline-card" @click="handleRowClick(proj)"
            >
              <div class="pipeline-card-title">{{ proj.project_name }}</div>
              <div class="pipeline-card-meta">
                <span>{{ proj.project_code }}</span>
                <span v-if="proj.industry">{{ getIndustryLabel(proj.industry) }}</span>
              </div>
              <div class="pipeline-card-footer">
                <span v-if="proj.investment_amount" class="stat-number">{{ proj.investment_amount.toLocaleString() }}万</span>
                <span v-if="proj.assigned_user_name" class="pipeline-user">{{ proj.assigned_user_name }}</span>
              </div>
            </div>
            <div v-if="!pipelineProjects[stage.value]?.length" class="pipeline-empty">暂无项目</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div v-show="viewMode === 'table'" class="filter-bar glass-card animate-slide-up" style="animation-delay: 300ms">
      <div class="filter-row">
        <el-input v-model="filterForm.keyword" placeholder="搜索项目名称..." :prefix-icon="Search" clearable style="flex: 1; min-width: 200px" @keyup.enter="handleSearch" />
        <div class="filter-select">
          <el-select v-model="filterForm.stages" multiple placeholder="全部阶段" clearable collapse-tags>
            <el-option v-for="opt in PROJECT_STAGE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </div>
        <div class="filter-select">
          <el-select v-model="filterForm.industries" multiple placeholder="全部行业" clearable collapse-tags>
            <el-option v-for="opt in PROJECT_INDUSTRY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </div>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>
    </div>

    <!-- 项目列表 -->
    <div v-show="viewMode === 'table'" class="table-container glass-card animate-slide-up" style="animation-delay: 400ms">
      <el-table :data="projectList" v-loading="loading" @row-click="handleRowClick">
        <el-table-column prop="project_code" label="编号" width="120" />
        <el-table-column prop="project_name" label="项目名称" min-width="180">
          <template #default="{ row }">
            <div class="project-cell">
              <div class="project-avatar">{{ row.project_name?.charAt(0) }}</div>
              <div class="project-info">
                <span class="project-name">{{ row.project_name }}</span>
                <span class="project-code">{{ row.project_code }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" width="100">
          <template #default="{ row }">{{ getIndustryLabel(row.industry) }}</template>
        </el-table-column>
        <el-table-column prop="stage" label="阶段" width="100">
          <template #default="{ row }">
            <span class="tag" :class="'tag-' + getStageType(row.stage)">{{ getStageLabel(row.stage) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="investment_amount" label="投资金额(万)" width="120">
          <template #default="{ row }">
            <span class="stat-number">{{ row.investment_amount ? row.investment_amount.toLocaleString() : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_user_name" label="负责人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" link @click.stop="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click.stop="handleTransfer(row)">流转</el-button>
              <el-button type="danger" link @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next" @size-change="handleSearch" @current-change="handleSearch" />
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="项目编号" prop="project_code"><el-input v-model="formData.project_code" :disabled="isEdit" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目名称" prop="project_name"><el-input v-model="formData.project_name" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="行业"><el-select v-model="formData.industry" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in PROJECT_INDUSTRY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="细分领域"><el-input v-model="formData.sub_industry" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="项目来源"><el-input v-model="formData.source" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="来源渠道"><el-input v-model="formData.source_channel" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="联系人"><el-input v-model="formData.contact_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系电话"><el-input v-model="formData.contact_phone" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="初步介绍"><el-input v-model="formData.initial_intro" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="formData.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 阶段流转对话框 -->
    <el-dialog v-model="transferDialogVisible" title="阶段流转" width="500px">
      <el-form :model="transferForm" label-width="80px">
        <el-form-item label="当前阶段">
          <span class="tag" :class="'tag-' + getStageType(currentProject?.stage)">{{ getStageLabel(currentProject?.stage) }}</span>
        </el-form-item>
        <el-form-item label="目标阶段" required>
          <el-select v-model="transferForm.to_stage" placeholder="请选择" style="width: 100%">
            <el-option v-for="opt in PROJECT_STAGE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="流转原因">
          <el-input v-model="transferForm.reason" type="textarea" :rows="3" placeholder="请输入流转原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleTransferSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 项目详情抽屉 -->
    <el-drawer v-model="detailDrawerVisible" title="项目详情" size="50%">
      <ProjectDetail v-if="currentProject" :project="currentProject" @refresh="loadProjectDetail" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Download, Search } from '@element-plus/icons-vue'
import { projectApi } from '@/api'
import * as echarts from 'echarts'
import type { Project, ProjectCreate, ProjectStats, StageTransfer, ProjectStage, ProjectIndustry } from '@/types'
import { PROJECT_STAGE_OPTIONS, PROJECT_INDUSTRY_OPTIONS } from '@/types'
import ProjectDetail from '@/components/project/ProjectDetail.vue'

const viewMode = ref('table')
const loading = ref(false)
const submitting = ref(false)
const projectList = ref<Project[]>([])
const stats = ref<ProjectStats>({ total: 0, by_stage: {}, by_industry: {}, total_investment: 0 })
const dialogVisible = ref(false)
const transferDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentProject = ref<Project | null>(null)
const isEdit = ref(false)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filterForm = reactive({ keyword: '', stages: [] as string[], industries: [] as string[] })
const formRef = ref()
const formData = reactive<ProjectCreate>({ project_code: '', project_name: '', industry: undefined, sub_industry: '', source: '', source_channel: '', contact_name: '', contact_phone: '', initial_intro: '', remark: '' })
const formRules = { project_code: [{ required: true, message: '请输入项目编号', trigger: 'blur' }], project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] }
const transferForm = reactive<StageTransfer>({ to_stage: 'sourcing' as ProjectStage, reason: '' })
const dialogTitle = computed(() => isEdit.value ? '编辑项目' : '新建项目')

const getStageLabel = (stage?: ProjectStage) => PROJECT_STAGE_OPTIONS.find(s => s.value === stage)?.label || stage
const getStageType = (stage?: ProjectStage) => {
  const typeMap: Record<string, string> = { sourcing: 'info', screening: 'info', due_diligence: 'warning', ic: 'warning', post_investment: 'success', exit: 'success' }
  return typeMap[stage || ''] || 'info'
}
const getIndustryLabel = (industry?: ProjectIndustry) => PROJECT_INDUSTRY_OPTIONS.find(i => i.value === industry)?.label || industry
const formatDate = (dateStr: string) => dateStr ? dateStr.split('T')[0] : ''

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize, keyword: filterForm.keyword || undefined, stages: filterForm.stages.length ? filterForm.stages.join(',') : undefined, industries: filterForm.industries.length ? filterForm.industries.join(',') : undefined }
    const res = await projectApi.getList(params)
    projectList.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) { console.error('加载项目列表失败', error) } finally { loading.value = false }
}
const loadStats = async () => { try { stats.value = await projectApi.getStatistics() } catch (error) { console.error('加载统计失败', error) } }
const loadProjectDetail = async () => { if (!currentProject.value) return; try { currentProject.value = await projectApi.getById(currentProject.value.id) } catch (error) { console.error('加载项目详情失败', error) } }
const handleSearch = () => { pagination.page = 1; loadData() }
const handleReset = () => { filterForm.keyword = ''; filterForm.stages = []; filterForm.industries = []; handleSearch() }
const handleCreate = () => { isEdit.value = false; Object.assign(formData, { project_code: '', project_name: '', industry: undefined, sub_industry: '', source: '', source_channel: '', contact_name: '', contact_phone: '', initial_intro: '', remark: '' }); dialogVisible.value = true }
const handleEdit = (row: Project) => { isEdit.value = true; Object.assign(formData, row); dialogVisible.value = true }
const handleRowClick = (row: Project) => { currentProject.value = row; detailDrawerVisible.value = true; loadProjectDetail() }

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value && currentProject.value) { await projectApi.update(currentProject.value.id, formData); ElMessage.success('更新成功') }
    else { await projectApi.create(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false; loadData(); loadStats()
  } catch (error: any) { ElMessage.error(error.message || '操作失败') } finally { submitting.value = false }
}
const handleDelete = async (row: Project) => {
  await ElMessageBox.confirm(`确定删除项目"${row.project_name}"吗？`, '提示', { type: 'warning' })
  try { await projectApi.delete(row.id); ElMessage.success('删除成功'); loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '删除失败') }
}
const handleTransfer = (row: Project) => { currentProject.value = row; transferForm.to_stage = row.stage; transferForm.reason = ''; transferDialogVisible.value = true }
const handleTransferSubmit = async () => {
  if (!currentProject.value) return
  submitting.value = true
  try { await projectApi.transferStage(currentProject.value.id, transferForm); ElMessage.success('流转成功'); transferDialogVisible.value = false; loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '流转失败') } finally { submitting.value = false }
}
const handleDownloadTemplate = async () => { try { const blob = await projectApi.downloadTemplate(); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'project_import_template.xlsx'; a.click(); window.URL.revokeObjectURL(url) } catch (error) { ElMessage.error('下载失败') } }
const handleImport = async (file: File) => { try { const res = await projectApi.import(file); ElMessage.success(`导入成功${res.success_count}条，失败${res.fail_count}条`); loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '导入失败') } return false }
// 图表
const funnelChartRef = ref<HTMLElement>()
const industryChartRef = ref<HTMLElement>()
let funnelChart: echarts.ECharts | null = null
let industryChart: echarts.ECharts | null = null

const conversionRate = computed(() => {
  if (!stats.value.total) return '0'
  const invested = (stats.value.by_stage['post_investment'] || 0) + (stats.value.by_stage['exit'] || 0)
  return ((invested / stats.value.total) * 100).toFixed(1)
})

const renderCharts = () => {
  // 漏斗图
  if (funnelChartRef.value) {
    if (funnelChart) funnelChart.dispose()
    funnelChart = echarts.init(funnelChartRef.value)
    const funnelData = PROJECT_STAGE_OPTIONS
      .filter(s => s.value !== 'rejected')
      .map(s => ({ name: s.label, value: stats.value.by_stage[s.value] || 0 }))
    funnelChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 个' },
      series: [{
        type: 'funnel',
        left: '10%', right: '10%', top: 10, bottom: 10,
        width: '80%',
        sort: 'none',
        gap: 2,
        label: { show: true, position: 'inside', formatter: '{b}\n{c}' },
        itemStyle: { borderWidth: 1, borderColor: '#fff' },
        data: funnelData,
        color: PROJECT_STAGE_OPTIONS.filter(s => s.value !== 'rejected').map(s => s.color),
      }]
    })
  }
  // 行业饼图
  if (industryChartRef.value) {
    if (industryChart) industryChart.dispose()
    industryChart = echarts.init(industryChartRef.value)
    const indData = PROJECT_INDUSTRY_OPTIONS
      .map(i => ({ name: i.label, value: stats.value.by_industry[i.value] || 0 }))
      .filter(d => d.value > 0)
    industryChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie',
        radius: ['35%', '70%'],
        center: ['50%', '55%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, fontSize: 11 },
        data: indData,
      }]
    })
  }
}

// ============ 管线跟踪 ============
const pipelineStages = PROJECT_STAGE_OPTIONS.filter(s => s.value !== 'rejected')
const pipelineProjects = ref<Record<string, any[]>>({})

const loadPipelineData = async () => {
  // Fetch all projects without pagination
  try {
    const res = await projectApi.getList({ page: 1, page_size: 1000 })
    const all = res.items || []
    const grouped: Record<string, any[]> = {}
    for (const s of pipelineStages) grouped[s.value] = []
    for (const p of all) {
      const stg = p.stage || 'sourcing'
      if (grouped[stg]) grouped[stg].push(p)
    }
    pipelineProjects.value = grouped
  } catch { /* silent */ }
}

watch(viewMode, (mode) => {
  if (mode === 'pipeline') loadPipelineData()
})

const handleResize = () => { funnelChart?.resize(); industryChart?.resize() }

watch(() => stats.value, () => { nextTick(renderCharts) }, { deep: true })

onMounted(() => {
  loadData()
  loadStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  funnelChart?.dispose()
  industryChart?.dispose()
})
</script>

<style scoped>
.project-view { padding: 24px; min-height: 100vh; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }
.header-left h2 { font-size: 1.75rem; font-weight: 700; margin: 0 0 4px 0; }
.header-left .subtitle { font-size: 0.875rem; color: var(--text-secondary); margin: 0; }
.header-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* 阶段统计卡片 */
.stage-cards { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.stage-card { display: flex; align-items: center; gap: 12px; padding: 16px 20px; min-width: 130px; }
.stage-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.stage-info { display: flex; flex-direction: column; }
.stage-count { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
.stage-label { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }

/* 筛选栏 */
.filter-bar { padding: 16px 20px; margin-bottom: 24px; }
.filter-row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.filter-select { min-width: 160px; }

/* 表格容器 */
.table-container { padding: 0; overflow: hidden; }
.project-cell { display: flex; align-items: center; gap: 12px; }
.project-avatar { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.3) 100%); display: flex; align-items: center; justify-content: center; color: #f59e0b; font-weight: 600; font-size: 0.875rem; flex-shrink: 0; }
.project-info { display: flex; flex-direction: column; }
.project-name { font-weight: 500; color: var(--text-primary); }
.project-code { font-size: 0.75rem; color: var(--text-muted); }

.action-btns { display: flex; gap: 4px; }

.pagination-wrapper { display: flex; justify-content: flex-end; padding: 16px 20px; border-top: 1px solid var(--card-border); }

.charts-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.chart-card { padding: 16px; }
.chart-title { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); margin: 0 0 8px 0; }
.invest-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 12px 0; }
.invest-item { display: flex; flex-direction: column; align-items: center; }
.invest-value { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
.invest-label { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }

@media (max-width: 1200px) { .charts-row { grid-template-columns: 1fr 1fr; } }
/* 视图切换 */
.view-toggle { margin-bottom: 16px; }

/* 管线视图 */
.pipeline-view { margin-bottom: 24px; }
.pipeline-board { display: flex; gap: 12px; overflow-x: auto; min-height: 400px; }
.pipeline-column { flex: 1; min-width: 200px; display: flex; flex-direction: column; padding: 0; overflow: hidden; }
.pipeline-col-header { padding: 12px 14px; border-top: 3px solid #409eff; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); }
.pipeline-col-title { font-weight: 600; font-size: 0.875rem; color: var(--text-primary); }
.pipeline-col-count { background: var(--input-bg); padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
.pipeline-col-body { padding: 10px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.pipeline-card { padding: 10px 12px; border-radius: 8px; background: var(--input-bg); border: 1px solid var(--card-border); cursor: pointer; transition: all 0.2s; }
.pipeline-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.pipeline-card-title { font-weight: 500; font-size: 0.875rem; color: var(--text-primary); margin-bottom: 4px; }
.pipeline-card-meta { display: flex; gap: 8px; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 6px; }
.pipeline-card-footer { display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; }
.pipeline-user { color: var(--text-secondary); }
.pipeline-empty { text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 20px 0; }

@media (max-width: 768px) {
  .project-view { padding: 16px; }
  .stage-cards { flex-wrap: nowrap; overflow-x: auto; }
  .stage-card { min-width: 110px; flex-shrink: 0; }
  .charts-row { grid-template-columns: 1fr; }
  .pipeline-board { flex-direction: column; }
  .pipeline-column { min-width: unset; }
}
</style>
