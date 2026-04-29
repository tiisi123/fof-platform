<template>
  <div class="manager-table">
    <el-table
      :data="managers"
      :loading="loading"
      stripe
      border
      style="width: 100%"
      @sort-change="handleSortChange"
    >
      <el-table-column prop="manager_code" label="编号" width="120" sortable="custom" />
      <el-table-column prop="manager_name" label="名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="strategy_type" label="策略类型" width="120" />
      <el-table-column prop="rating" label="评级" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.rating" :type="getRatingType(row.rating)">
            {{ row.rating }}
          </el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '活跃' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right" align="center">
        <template #default="{ row }">
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
import type { Manager } from '@/types'

interface Props {
  managers: Manager[]
  total: number
  loading?: boolean
}

interface Emits {
  (e: 'edit', manager: Manager): void
  (e: 'delete', manager: Manager): void
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

// 评级类型映射
const getRatingType = (rating: string) => {
  const typeMap: Record<string, any> = {
    'A': 'success',
    'B': 'primary',
    'C': 'warning',
    'D': 'danger'
  }
  return typeMap[rating] || ''
}

// 格式化日期
const formatDate = (dateStr: string) => {
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

// 处理编辑
const handleEdit = (manager: Manager) => {
  emit('edit', manager)
}

// 处理删除
const handleDelete = (manager: Manager) => {
  emit('delete', manager)
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
  if (currentPage.value > 1 && props.managers.length === 0) {
    currentPage.value = 1
  }
})
</script>

<style scoped>
.manager-table {
  width: 100%;
}

.text-muted {
  color: #909399;
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
