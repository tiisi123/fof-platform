<template>
  <div class="manager-view">
    <div class="page-header">
      <h2>管理人管理</h2>
      <div class="header-actions">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="table">列表</el-radio-button>
          <el-radio-button value="kanban">看板</el-radio-button>
        </el-radio-group>
        <el-button @click="handleDownloadTemplate"><el-icon><Download /></el-icon>下载模板</el-button>
        <el-upload :show-file-list="false" :before-upload="handleImport" accept=".xlsx,.xls">
          <el-button><el-icon><Upload /></el-icon>批量导入</el-button>
        </el-upload>
        <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>新增管理人</el-button>
      </div>
    </div>
    <div class="stats-cards">
      <el-card v-for="pool in POOL_CATEGORY_OPTIONS" :key="pool.value" class="stat-card" :class="{ active: filterForm.pool_categories?.includes(pool.value) }" @click="togglePoolFilter(pool.value)">
        <div class="stat-content">
          <div class="stat-value" :style="{ color: pool.color }">{{ getPoolCount(pool.value) }}</div>
          <div class="stat-label">{{ pool.label }}</div>
        </div>
      </el-card>
    </div>
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词"><el-input v-model="filterForm.keyword" placeholder="名称/编号" clearable @keyup.enter="handleSearch" style="width: 180px" /></el-form-item>
        <el-form-item label="一级策略"><el-select v-model="filterForm.primary_strategies" multiple placeholder="全部" clearable collapse-tags style="width: 180px"><el-option v-for="opt in PRIMARY_STRATEGY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item>
        <el-form-item label="评级"><el-select v-model="filterForm.rating" placeholder="全部" clearable style="width: 120px"><el-option v-for="opt in RATING_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item>
        <el-form-item label="标签"><el-select v-model="filterForm.tag_names" multiple placeholder="全部" clearable collapse-tags style="width: 200px"><el-option v-for="tag in allTags" :key="tag.tag_name" :label="`${tag.tag_name} (${tag.count})`" :value="tag.tag_name" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="handleSearch">搜索</el-button><el-button @click="handleReset">重置</el-button></el-form-item>
      </el-form>
    </el-card>
    <el-card v-if="viewMode === 'table'" class="table-card">
      <el-table :data="managerList" v-loading="loading" stripe @row-click="handleRowClick" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="manager_code" label="编号" width="100" />
        <el-table-column prop="manager_name" label="名称" min-width="180" />
        <el-table-column prop="pool_category" label="跟踪池" width="110"><template #default="{ row }"><el-tag :color="getPoolColor(row.pool_category)" effect="dark" size="small">{{ getPoolLabel(row.pool_category) }}</el-tag></template></el-table-column>
        <el-table-column prop="primary_strategy" label="策略" width="100"><template #default="{ row }">{{ getStrategyLabel(row.primary_strategy) }}</template></el-table-column>
        <el-table-column prop="aum_range" label="规模" width="100" />
        <el-table-column prop="rating" label="评级" width="80"><template #default="{ row }"><el-tag v-if="row.rating && row.rating !== 'unrated'" :type="getRatingType(row.rating)" size="small">{{ row.rating }}</el-tag><span v-else>-</span></template></el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="电话" width="130" />
        <el-table-column label="操作" width="240" fixed="right"><template #default="{ row }"><el-button link type="primary" @click.stop="router.push(`/managers/${row.id}`)">详情</el-button><el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button><el-button link type="primary" @click.stop="handleTransfer(row)">流转</el-button><el-button link type="danger" @click.stop="handleDelete(row)">删除</el-button></template></el-table-column>
      </el-table>
      <div v-if="selectedManagers.length > 0" class="batch-actions"><span>已选择 {{ selectedManagers.length }} 项</span><el-button size="small" @click="handleBatchTransfer">批量流转</el-button></div>
      <div class="pagination-wrapper"><el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSearch" @current-change="handleSearch" /></div>
    </el-card>
    <div v-else class="kanban-view">
      <div v-for="pool in POOL_CATEGORY_OPTIONS" :key="pool.value" class="kanban-column">
        <div class="kanban-header" :style="{ borderTopColor: pool.color }"><span>{{ pool.label }}</span><el-tag size="small">{{ getPoolCount(pool.value) }}</el-tag></div>
        <div class="kanban-body">
          <div v-for="manager in getManagersByPool(pool.value)" :key="manager.id" class="kanban-card" @click="handleRowClick(manager)">
            <div class="card-title">{{ manager.manager_name }}</div>
            <div class="card-info"><span>{{ getStrategyLabel(manager.primary_strategy) }}</span><el-tag v-if="manager.rating && manager.rating !== 'unrated'" :type="getRatingType(manager.rating)" size="small">{{ manager.rating }}</el-tag></div>
            <div class="card-contact">{{ manager.contact_person }} {{ manager.contact_phone }}</div>
          </div>
        </div>
      </div>
    </div>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20"><el-col :span="12"><el-form-item label="管理人编号" prop="manager_code"><el-input v-model="formData.manager_code" :disabled="isEdit" /></el-form-item></el-col><el-col :span="12"><el-form-item label="管理人名称" prop="manager_name"><el-input v-model="formData.manager_name" /></el-form-item></el-col></el-row>
        <el-row :gutter="20"><el-col :span="12"><el-form-item label="简称"><el-input v-model="formData.short_name" /></el-form-item></el-col><el-col :span="12"><el-form-item label="备案编号"><el-input v-model="formData.registration_no" /></el-form-item></el-col></el-row>
        <el-row :gutter="20"><el-col :span="12"><el-form-item label="一级策略"><el-select v-model="formData.primary_strategy" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in PRIMARY_STRATEGY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="二级策略"><el-select v-model="formData.secondary_strategy" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in secondaryOptions" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col></el-row>
        <el-row :gutter="20"><el-col :span="12"><el-form-item label="跟踪池"><el-select v-model="formData.pool_category" placeholder="请选择" style="width: 100%"><el-option v-for="opt in POOL_CATEGORY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="管理规模"><el-select v-model="formData.aum_range" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in AUM_RANGE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col></el-row>
        <el-row :gutter="20"><el-col :span="12"><el-form-item label="评级"><el-select v-model="formData.rating" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in RATING_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="成立日期"><el-date-picker v-model="formData.established_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col></el-row>
        <el-row :gutter="20"><el-col :span="8"><el-form-item label="联系人"><el-input v-model="formData.contact_person" /></el-form-item></el-col><el-col :span="8"><el-form-item label="联系电话"><el-input v-model="formData.contact_phone" /></el-form-item></el-col><el-col :span="8"><el-form-item label="联系邮箱"><el-input v-model="formData.contact_email" /></el-form-item></el-col></el-row>
        <el-form-item label="备注"><el-input v-model="formData.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button></template>
    </el-dialog>
    <el-dialog v-model="transferDialogVisible" title="跟踪池流转" width="500px">
      <el-form :model="transferForm" label-width="80px">
        <el-form-item label="当前分类"><el-tag :color="getPoolColor(currentManager?.pool_category)" effect="dark">{{ getPoolLabel(currentManager?.pool_category) }}</el-tag></el-form-item>
        <el-form-item label="目标分类" required><el-select v-model="transferForm.to_pool" placeholder="请选择" style="width: 100%"><el-option v-for="opt in POOL_CATEGORY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item>
        <el-form-item label="流转原因" required><el-input v-model="transferForm.reason" type="textarea" :rows="3" placeholder="请输入流转原因" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="transferDialogVisible = false">取消</el-button><el-button type="primary" @click="handleTransferSubmit" :loading="submitting">确定</el-button></template>
    </el-dialog>
    <el-drawer v-model="detailDrawerVisible" title="管理人详情" size="50%"><ManagerDetail v-if="currentManager" :manager="currentManager" @refresh="loadManagerDetail" /></el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { managerApi } from '@/api'
import type { Manager, ManagerCreate, ManagerStatistics, PoolCategory, PrimaryStrategy, PoolTransferCreate } from '@/types'
import { POOL_CATEGORY_OPTIONS, PRIMARY_STRATEGY_OPTIONS, SECONDARY_STRATEGY_OPTIONS, RATING_OPTIONS, AUM_RANGE_OPTIONS } from '@/types'
import ManagerDetail from '@/components/manager/ManagerDetail.vue'

const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const viewMode = ref<'table' | 'kanban'>('table')
const managerList = ref<Manager[]>([])
const stats = ref<ManagerStatistics>({ total: 0, by_pool: [], by_strategy: {} })
const dialogVisible = ref(false)
const transferDialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentManager = ref<Manager | null>(null)
const selectedManagers = ref<Manager[]>([])
const isEdit = ref(false)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filterForm = reactive({ keyword: '', pool_categories: [] as PoolCategory[], primary_strategies: [] as PrimaryStrategy[], rating: '', tag_names: [] as string[] })
const allTags = ref<{ tag_type: string; tag_name: string; tag_color: string; count: number }[]>([])
const formRef = ref()
const formData = reactive<ManagerCreate>({ manager_code: '', manager_name: '', short_name: '', registration_no: '', primary_strategy: undefined, secondary_strategy: '', pool_category: 'observation', aum_range: '', rating: 'unrated', established_date: '', contact_person: '', contact_phone: '', contact_email: '', remark: '' })
const formRules = { manager_code: [{ required: true, message: '请输入管理人编号', trigger: 'blur' }], manager_name: [{ required: true, message: '请输入管理人名称', trigger: 'blur' }] }
const transferForm = reactive<PoolTransferCreate>({ to_pool: 'observation', reason: '' })
const dialogTitle = computed(() => isEdit.value ? '编辑管理人' : '新增管理人')
const secondaryOptions = computed(() => formData.primary_strategy ? SECONDARY_STRATEGY_OPTIONS[formData.primary_strategy] || [] : [])
const getPoolLabel = (pool?: PoolCategory) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.label || pool || '-'
const getPoolColor = (pool?: PoolCategory) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.color || '#909399'
const getStrategyLabel = (strategy?: PrimaryStrategy) => PRIMARY_STRATEGY_OPTIONS.find(s => s.value === strategy)?.label || strategy || '-'
const getRatingType = (rating: string) => ({ S: 'success', A: 'success', B: 'warning', C: 'info', D: 'danger' }[rating] || 'info')
const getPoolCount = (pool: PoolCategory) => stats.value.by_pool?.find(p => p.category === pool)?.count || 0
const getManagersByPool = (pool: PoolCategory) => managerList.value.filter(m => m.pool_category === pool)

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize, keyword: filterForm.keyword || undefined, pool_categories: filterForm.pool_categories.length ? filterForm.pool_categories.join(',') : undefined, primary_strategies: filterForm.primary_strategies.length ? filterForm.primary_strategies.join(',') : undefined, rating: filterForm.rating || undefined, tag_names: filterForm.tag_names.length ? filterForm.tag_names.join(',') : undefined }
    const res = await managerApi.getList(params)
    managerList.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) { console.error('加载失败', error) } finally { loading.value = false }
}
const loadTags = async () => { try { allTags.value = await managerApi.getAllTags() } catch (error) { console.error('加载标签失败', error) } }
const loadStats = async () => { try { stats.value = await managerApi.getStatistics() } catch (error) { console.error('加载统计失败', error) } }
const loadManagerDetail = async () => { if (!currentManager.value) return; try { currentManager.value = await managerApi.getById(currentManager.value.id) } catch (error) { console.error('加载详情失败', error) } }
const handleSearch = () => { pagination.page = 1; loadData() }
const handleReset = () => { filterForm.keyword = ''; filterForm.pool_categories = []; filterForm.primary_strategies = []; filterForm.rating = ''; filterForm.tag_names = []; handleSearch() }
const togglePoolFilter = (pool: PoolCategory) => { const idx = filterForm.pool_categories.indexOf(pool); if (idx >= 0) filterForm.pool_categories.splice(idx, 1); else filterForm.pool_categories.push(pool); handleSearch() }
const handleAdd = () => { isEdit.value = false; Object.assign(formData, { manager_code: '', manager_name: '', short_name: '', registration_no: '', primary_strategy: undefined, secondary_strategy: '', pool_category: 'observation', aum_range: '', rating: 'unrated', established_date: '', contact_person: '', contact_phone: '', contact_email: '', remark: '' }); dialogVisible.value = true }
const handleEdit = (row: Manager) => { isEdit.value = true; currentManager.value = row; Object.assign(formData, row); dialogVisible.value = true }
const handleRowClick = (row: Manager) => { router.push(`/managers/${row.id}`) }
const handleSelectionChange = (selection: Manager[]) => { selectedManagers.value = selection }
const handleSubmit = async () => { if (!formRef.value) return; await formRef.value.validate(); submitting.value = true; try { if (isEdit.value && currentManager.value) { await managerApi.update(currentManager.value.id, formData); ElMessage.success('更新成功') } else { await managerApi.create(formData); ElMessage.success('创建成功') } dialogVisible.value = false; loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '操作失败') } finally { submitting.value = false } }
const handleDelete = async (row: Manager) => { await ElMessageBox.confirm('确定删除管理人"' + row.manager_name + '"吗？', '提示', { type: 'warning' }); try { await managerApi.delete(row.id); ElMessage.success('删除成功'); loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '删除失败') } }
const handleTransfer = (row: Manager) => { currentManager.value = row; transferForm.to_pool = row.pool_category || 'observation'; transferForm.reason = ''; transferDialogVisible.value = true }
const handleTransferSubmit = async () => { if (!currentManager.value || !transferForm.reason) { ElMessage.warning('请填写流转原因'); return } submitting.value = true; try { await managerApi.transferPool(currentManager.value.id, transferForm); ElMessage.success('流转成功'); transferDialogVisible.value = false; loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '流转失败') } finally { submitting.value = false } }
const handleBatchTransfer = () => { if (selectedManagers.value.length === 0) return; currentManager.value = selectedManagers.value[0]; transferForm.to_pool = 'observation'; transferForm.reason = ''; transferDialogVisible.value = true }
const handleDownloadTemplate = async () => { try { const blob = await managerApi.downloadTemplate(); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'manager_import_template.xlsx'; a.click(); window.URL.revokeObjectURL(url) } catch (error) { ElMessage.error('下载失败') } }
const handleImport = async (file: File) => { try { const res = await managerApi.import(file); ElMessage.success('导入成功' + res.success_count + '条，失败' + res.fail_count + '条'); loadData(); loadStats() } catch (error: any) { ElMessage.error(error.message || '导入失败') } return false }
onMounted(() => { loadData(); loadStats(); loadTags() })
</script>

<style scoped>
.manager-view { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; color: var(--text-primary); }
.header-actions { display: flex; gap: 10px; align-items: center; }
.stats-cards { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-card { flex: 1; min-width: 120px; cursor: pointer; transition: all 0.3s; background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
.stat-card.active { border: 2px solid var(--accent-color) !important; }
.stat-content { text-align: center; }
.stat-value { font-size: 28px; font-weight: bold; }
.stat-label { color: var(--text-muted); font-size: 14px; margin-top: 5px; }
.filter-card { margin-bottom: 20px; background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
.table-card { margin-bottom: 20px; background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
.batch-actions { display: flex; align-items: center; gap: 15px; margin-top: 15px; padding: 10px; background: var(--hover-bg); border-radius: 4px; color: var(--text-primary); }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 20px; }
.kanban-view { display: flex; gap: 15px; overflow-x: auto; padding-bottom: 10px; }
.kanban-column { flex: 0 0 280px; background: var(--hover-bg); border-radius: 8px; display: flex; flex-direction: column; max-height: calc(100vh - 350px); }
.kanban-header { padding: 12px 15px; background: var(--card-bg); border-radius: 8px 8px 0 0; border-top: 3px solid; display: flex; justify-content: space-between; align-items: center; font-weight: 600; color: var(--text-primary); }
.kanban-body { flex: 1; overflow-y: auto; padding: 10px; }
.kanban-card { background: var(--card-bg); border-radius: 6px; padding: 12px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); border: 1px solid var(--card-border); }
.kanban-card:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); border-color: var(--accent-color); }
.card-title { font-weight: 600; margin-bottom: 8px; color: var(--text-primary); }
.card-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; color: var(--text-secondary); }
.card-contact { font-size: 12px; color: var(--text-muted); }

/* Element Plus 组件样式覆盖 */
:deep(.el-card) {
  background: var(--card-bg) !important;
  border: 1px solid var(--card-border) !important;
}
:deep(.el-card__body) {
  color: var(--text-primary);
}
</style>
