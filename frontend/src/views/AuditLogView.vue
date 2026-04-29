<template>
  <div class="p-6">
    <div class="mb-5">
      <h2 class="text-2xl font-bold gradient-text">操作审计日志</h2>
      <p class="text-sm text-dark-400 mt-1">记录所有用户关键操作，便于审计与回溯</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
      <div class="glass-card p-4 text-center">
        <p class="text-2xl font-bold text-primary-400">{{ stats.total || 0 }}</p>
        <p class="text-xs text-dark-400 mt-1">总记录数</p>
      </div>
      <div class="glass-card p-4 text-center">
        <p class="text-2xl font-bold text-emerald-400">{{ stats.today || 0 }}</p>
        <p class="text-xs text-dark-400 mt-1">今日操作</p>
      </div>
      <div class="glass-card p-4 text-center">
        <p class="text-2xl font-bold text-amber-400">{{ stats.by_action?.create || 0 }}</p>
        <p class="text-xs text-dark-400 mt-1">新增操作</p>
      </div>
      <div class="glass-card p-4 text-center">
        <p class="text-2xl font-bold text-red-400">{{ stats.by_action?.delete || 0 }}</p>
        <p class="text-xs text-dark-400 mt-1">删除操作</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="glass-card p-4 mb-5">
      <div class="flex flex-wrap gap-3 items-center">
        <el-select v-model="filters.action" placeholder="操作类型" clearable style="width: 130px" size="default">
          <el-option v-for="a in actionTypes" :key="a.key" :label="a.label" :value="a.key" />
        </el-select>
        <el-select v-model="filters.resource_type" placeholder="资源类型" clearable style="width: 130px" size="default">
          <el-option v-for="r in resourceTypes" :key="r.key" :label="r.label" :value="r.key" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          size="default"
        />
        <el-input
          v-model="filters.keyword"
          placeholder="搜索用户名/资源名"
          clearable
          style="width: 180px"
          size="default"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch" size="default">搜索</el-button>
        <el-button @click="resetFilters" size="default">重置</el-button>
      </div>
    </div>

    <!-- 日志表格 -->
    <div class="glass-card">
      <el-table :data="logs" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">
              {{ row.action_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源类型" width="90">
          <template #default="{ row }">
            {{ row.resource_type_label }}
          </template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源ID" width="80" />
        <el-table-column prop="request_method" label="方法" width="70">
          <template #default="{ row }">
            <el-tag :type="getMethodTagType(row.request_method)" size="small" effect="plain">
              {{ row.request_method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="request_path" label="请求路径" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <span :class="row.status_code < 400 ? 'text-emerald-400' : 'text-red-400'">
              {{ row.status_code }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="130" />
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end p-4">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchLogs"
          @current-change="fetchLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const logs = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const stats = ref<any>({})
const actionTypes = ref<any[]>([])
const resourceTypes = ref<any[]>([])
const dateRange = ref<string[] | null>(null)

const filters = reactive({
  action: '',
  resource_type: '',
  keyword: '',
})

const formatTime = (iso: string) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { hour12: false })
}

const getActionTagType = (action: string) => {
  const map: Record<string, string> = {
    create: 'success', update: 'warning', delete: 'danger',
    login: '', logout: 'info', import: 'success', export: 'info',
  }
  return map[action] || 'info'
}

const getMethodTagType = (method: string) => {
  const map: Record<string, string> = {
    POST: 'success', PUT: 'warning', PATCH: 'warning', DELETE: 'danger',
  }
  return map[method] || 'info'
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filters.action) params.action = filters.action
    if (filters.resource_type) params.resource_type = filters.resource_type
    if (filters.keyword) params.keyword = filters.keyword
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await request.get('/audit', { params })
    const data = res.data || res
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    console.error('获取审计日志失败:', e)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await request.get('/audit/statistics')
    stats.value = res.data || res
  } catch { /* silent */ }
}

const fetchMeta = async () => {
  try {
    const [actRes, resRes] = await Promise.all([
      request.get('/audit/actions'),
      request.get('/audit/resource-types'),
    ])
    actionTypes.value = actRes.data || actRes || []
    resourceTypes.value = resRes.data || resRes || []
  } catch { /* silent */ }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchLogs()
}

const resetFilters = () => {
  filters.action = ''
  filters.resource_type = ''
  filters.keyword = ''
  dateRange.value = null
  currentPage.value = 1
  fetchLogs()
}

onMounted(() => {
  fetchLogs()
  fetchStats()
  fetchMeta()
})
</script>
