<template>
  <div class="product-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>产品管理</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新增产品
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">产品总数</div>
          <div class="stat-value">{{ statistics.total }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">运行中</div>
          <div class="stat-value text-success">{{ statistics.by_status?.active || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">已清盘</div>
          <div class="stat-value text-danger">{{ statistics.by_status?.liquidated || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">暂停</div>
          <div class="stat-value text-warning">{{ statistics.by_status?.suspended || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 策略分布 -->
    <el-card shadow="never" class="strategy-card" v-if="strategyEntries.length > 0">
      <template #header>
        <span>策略分布</span>
      </template>
      <div class="strategy-grid">
        <div class="strategy-item" v-for="[name, count] in strategyEntries" :key="name">
          <div class="strategy-count">{{ count }}</div>
          <div class="strategy-name">{{ name || '未分类' }}</div>
          <div class="strategy-bar">
            <div class="strategy-bar-fill" :style="{ width: (count / statistics.total * 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索代码或名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="管理人">
          <el-select
            v-model="searchForm.manager_id"
            placeholder="全部"
            clearable
            filterable
            style="width: 180px"
            @change="handleSearch"
          >
            <el-option
              v-for="manager in managers"
              :key="manager.id"
              :label="manager.name"
              :value="manager.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="策略类型">
          <el-select
            v-model="searchForm.strategy_type"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option
              v-for="item in STRATEGY_TYPES"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option
              v-for="item in PRODUCT_STATUS_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <span>产品列表</span>
          <el-button size="small" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出Excel
          </el-button>
        </div>
      </template>
      <ProductTable
        :products="productStore.products"
        :total="productStore.total"
        :loading="productStore.loading"
        @edit="handleEdit"
        @delete="handleDeleteConfirm"
        @view-detail="handleViewDetail"
        @page-change="handlePageChange"
        @sort-change="handleSortChange"
      />
    </el-card>

    <!-- 表单对话框 -->
    <ProductForm
      v-model:visible="formVisible"
      :product="currentProduct"
      :loading="productStore.loading"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Download } from '@element-plus/icons-vue'
import { useProductStore } from '@/store/product'
import ProductTable from '@/components/product/ProductTable.vue'
import ProductForm from '@/components/product/ProductForm.vue'
import { STRATEGY_TYPES } from '@/types/manager'
import { PRODUCT_STATUS_OPTIONS } from '@/types/product'
import type { Product, ProductCreate, ProductUpdate, ProductListParams, Manager, ProductStatistics } from '@/types'
import { managerApi } from '@/api/manager'
import { productApi } from '@/api/product'

const router = useRouter()
const productStore = useProductStore()

// 管理人列表（用于筛选）
const managers = ref<Manager[]>([])

// 统计数据
const statistics = ref<ProductStatistics>({ total: 0, by_status: {}, by_strategy: {} })

// 策略分布计算
const strategyEntries = computed(() => {
  const obj = statistics.value.by_strategy || {}
  return Object.entries(obj).sort((a, b) => (b[1] as number) - (a[1] as number))
})

const fetchStatistics = async () => {
  try {
    statistics.value = await productApi.getStatistics()
  } catch {
    // 静默
  }
}

// 搜索表单
const searchForm = reactive<ProductListParams>({
  search: '',
  manager_id: undefined,
  strategy_type: undefined,
  status: undefined,
  skip: 0,
  limit: 20
})

// 表单对话框
const formVisible = ref(false)
const currentProduct = ref<Product | null>(null)

// 获取管理人列表（用于筛选）
const fetchManagers = async () => {
  try {
    const response = await managerApi.getList({ skip: 0, limit: 1000, status: 'active' })
    managers.value = response.items
  } catch (error) {
    console.error('获取管理人列表失败:', error)
  }
}

// 获取产品列表
const fetchProducts = async () => {
  await productStore.fetchProducts(searchForm)
}

// 处理搜索
const handleSearch = () => {
  searchForm.skip = 0
  fetchProducts()
}

// 处理重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.manager_id = undefined
  searchForm.strategy_type = undefined
  searchForm.status = undefined
  searchForm.skip = 0
  fetchProducts()
}

// 处理新增
const handleAdd = () => {
  currentProduct.value = null
  formVisible.value = true
}

// 处理编辑
const handleEdit = (product: Product) => {
  currentProduct.value = product
  formVisible.value = true
}

// 处理查看详情
const handleViewDetail = (product: Product) => {
  router.push(`/products/${product.id}`)
}

// 处理删除确认
const handleDeleteConfirm = (product: Product) => {
  ElMessageBox.confirm(
    `确定要删除产品"${product.name}"吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      handleDelete(product.id)
    })
    .catch(() => {
      // 取消删除
    })
}

// 处理删除
const handleDelete = async (id: number) => {
  try {
    await productStore.deleteProduct(id)
    await fetchProducts()
  } catch (error) {
    // 错误已在store中处理
  }
}

// 处理表单提交
const handleSubmit = async (data: ProductCreate | ProductUpdate) => {
  try {
    if (currentProduct.value) {
      // 编辑
      await productStore.updateProduct(currentProduct.value.id, data as ProductUpdate)
    } else {
      // 新增
      await productStore.createProduct(data as ProductCreate)
    }
    formVisible.value = false
    await fetchProducts()
  } catch (error) {
    // 错误已在store中处理
  }
}

// 处理分页变化
const handlePageChange = (page: number, size: number) => {
  searchForm.skip = (page - 1) * size
  searchForm.limit = size
  fetchProducts()
}

// 处理排序变化
const handleSortChange = (prop: string, order: string) => {
  console.log('排序:', prop, order)
}

// 导出Excel
const handleExport = () => {
  const items = productStore.products
  if (!items.length) {
    ElMessage.warning('没有数据可导出')
    return
  }
  // CSV导出
  const headers = ['产品代码', '产品名称', '管理人', '策略类型', '状态', '成立日期']
  const rows = items.map((p: any) => [
    p.product_code || '',
    p.product_name || '',
    p.manager_name || '',
    p.strategy_type || '',
    p.status || '',
    p.established_date || ''
  ])
  const csv = '\uFEFF' + [headers, ...rows].map(r => r.map((c: string) => `"${c}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `产品列表_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
  ElMessage.success('导出成功')
}

// 初始化
onMounted(() => {
  fetchManagers()
  fetchProducts()
  fetchStatistics()
})
</script>

<style scoped>
.product-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-card {
  margin-bottom: 20px;
}

.search-card :deep(.el-card__body) {
  padding: 20px;
}

.search-card :deep(.el-form-item) {
  margin-bottom: 0;
}

.table-card :deep(.el-card__body) {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 8px 0;
}

.stat-card :deep(.el-card__body) {
  padding: 16px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.stat-value {
  font-size: 26px;
  font-weight: 600;
}

.text-success { color: #10b981; }
.text-danger { color: #ef4444; }
.text-warning { color: #f59e0b; }

/* 策略分布 */
.strategy-card {
  margin-bottom: 20px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.strategy-item {
  text-align: center;
  padding: 12px;
  background: var(--input-bg);
  border-radius: 8px;
}

.strategy-count {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
}

.strategy-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 4px 0 8px;
}

.strategy-bar {
  height: 4px;
  background: var(--input-border);
  border-radius: 2px;
  overflow: hidden;
}

.strategy-bar-fill {
  height: 100%;
  background: var(--accent-color);
  border-radius: 2px;
  transition: width 0.3s;
}

/* 表格头部 */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .product-view {
    padding: 15px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .search-card :deep(.el-form) {
    display: flex;
    flex-direction: column;
  }

  .search-card :deep(.el-form-item) {
    margin-right: 0;
    margin-bottom: 15px;
  }

  .search-card :deep(.el-input),
  .search-card :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
