<template>
  <div class="product-table">
    <el-table
      :data="products"
      :loading="loading"
      stripe
      border
      style="width: 100%"
      @sort-change="handleSortChange"
    >
      <el-table-column prop="product_code" label="产品代码" width="140" sortable="custom" />
      <el-table-column prop="product_name" label="产品名称" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewDetail(row)">
            {{ row.product_name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="manager_name" label="管理人" width="150" show-overflow-tooltip />
      <el-table-column prop="strategy_type" label="策略类型" width="120" />
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="established_date" label="成立日期" width="120">
        <template #default="{ row }">
          {{ formatDate(row.established_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            link
            @click="handleViewDetail(row)"
          >
            详情
          </el-button>
          <el-button
            type="primary"
            size="small"
            link
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            type="danger"
            size="small"
            link
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Product } from '@/types'
import { PRODUCT_STATUS_COLOR } from '@/types/product'

interface Props {
  products: Product[]
  total: number
  loading?: boolean
}

interface Emits {
  (e: 'edit', product: Product): void
  (e: 'delete', product: Product): void
  (e: 'view-detail', product: Product): void
  (e: 'page-change', page: number, size: number): void
  (e: 'sort-change', prop: string, order: string): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)

// 状态类型映射
const getStatusType = (status: string) => {
  return PRODUCT_STATUS_COLOR[status as keyof typeof PRODUCT_STATUS_COLOR] || ''
}

// 格式化日期（仅日期）
const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理查看详情
const handleViewDetail = (product: Product) => {
  emit('view-detail', product)
}

// 处理编辑
const handleEdit = (product: Product) => {
  emit('edit', product)
}

// 处理删除
const handleDelete = (product: Product) => {
  emit('delete', product)
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  emit('page-change', currentPage.value, pageSize.value)
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  emit('page-change', currentPage.value, pageSize.value)
}

// 处理排序变化
const handleSortChange = ({ prop, order }: any) => {
  emit('sort-change', prop, order)
}

// 监听total变化，重置页码
watch(() => props.total, () => {
  if (currentPage.value > 1 && props.products.length === 0) {
    currentPage.value = 1
  }
})
</script>

<style scoped>
.product-table {
  width: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 768px) {
  .pagination-container {
    justify-content: center;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
  }
}
</style>
