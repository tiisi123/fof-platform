<template>
  <div class="min-h-screen p-6">
    <!-- 页面头部 -->
    <div class="flex items-center justify-between mb-6 animate-fade-in">
      <div>
        <h2 class="text-2xl font-bold gradient-text">待办任务</h2>
        <p class="text-sm text-dark-400 mt-2">管理您的工作任务和待办事项</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon class="mr-1"><Plus /></el-icon>新建任务
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:0ms">
        <p class="text-2xl font-bold stat-number">{{ stats.total }}</p>
        <p class="text-sm text-dark-400 mt-1">全部任务</p>
      </div>
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:50ms">
        <p class="text-2xl font-bold text-amber-400 stat-number">{{ stats.pending }}</p>
        <p class="text-sm text-dark-400 mt-1">待处理</p>
      </div>
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:100ms">
        <p class="text-2xl font-bold text-primary-400 stat-number">{{ stats.in_progress }}</p>
        <p class="text-sm text-dark-400 mt-1">进行中</p>
      </div>
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:150ms">
        <p class="text-2xl font-bold text-emerald-400 stat-number">{{ stats.completed }}</p>
        <p class="text-sm text-dark-400 mt-1">已完成</p>
      </div>
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:200ms">
        <p class="text-2xl font-bold text-blue-400 stat-number">{{ stats.my_pending }}</p>
        <p class="text-sm text-dark-400 mt-1">我的待办</p>
      </div>
      <div class="glass-card p-4 text-center animate-slide-up" style="animation-delay:250ms">
        <p class="text-2xl font-bold text-red-400 stat-number">{{ stats.overdue }}</p>
        <p class="text-sm text-dark-400 mt-1">已逾期</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="glass-card p-4 mb-6 animate-slide-up" style="animation-delay:300ms">
      <div class="flex flex-wrap gap-3 items-center">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索任务标题..."
          clearable
          style="width: 220px"
          @keyup.enter="fetchTasks"
          @clear="fetchTasks"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="fetchTasks">
          <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-select v-model="filters.priority" placeholder="优先级" clearable style="width: 130px" @change="fetchTasks">
          <el-option v-for="p in PRIORITY_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
        <el-checkbox v-model="filters.my_tasks" @change="fetchTasks">只看我的</el-checkbox>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="glass-card animate-slide-up" style="animation-delay:350ms">
      <el-table :data="tasks" v-loading="loading" style="width: 100%" row-class-name="task-row">
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small" effect="dark" round>
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-checkbox
                :model-value="row.status === 'completed'"
                @change="(val: boolean) => toggleComplete(row, val)"
              />
              <span :class="{ 'line-through text-dark-500': row.status === 'completed' }">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联" width="150">
          <template #default="{ row }">
            <span v-if="row.product_name" class="text-xs text-primary-400">产品: {{ row.product_name }}</span>
            <span v-else-if="row.manager_name" class="text-xs text-primary-400">管理人: {{ row.manager_name }}</span>
            <span v-else-if="row.portfolio_name" class="text-xs text-primary-400">组合: {{ row.portfolio_name }}</span>
            <span v-else class="text-xs text-dark-500">-</span>
          </template>
        </el-table-column>
        <el-table-column label="指派给" width="100">
          <template #default="{ row }">
            <span>{{ row.assignee_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="120">
          <template #default="{ row }">
            <span :class="{ 'text-red-400': isOverdue(row) }">{{ row.due_date || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="120">
          <template #default="{ row }">
            <span class="text-xs text-dark-400">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteTask(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end p-4">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchTasks"
        />
      </div>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTask ? '编辑任务' : '新建任务'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="请输入任务标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="任务描述（可选）" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option v-for="p in PRIORITY_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="editingTask">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" placeholder="选择截止日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="指派给">
          <el-select v-model="form.assigned_to" placeholder="选择指派人" clearable style="width: 100%">
            <el-option v-for="u in users" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTask" :loading="submitting">{{ editingTask ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { taskApi } from '@/api/task'
import type { TaskItem, TaskStats } from '@/api/task'
import request from '@/api/request'

const STATUS_OPTIONS = [
  { value: 'pending', label: '待处理' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'cancelled', label: '已取消' },
]
const PRIORITY_OPTIONS = [
  { value: 'urgent', label: '紧急' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
]

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editingTask = ref<TaskItem | null>(null)
const tasks = ref<TaskItem[]>([])
const stats = ref<TaskStats>({ total: 0, pending: 0, in_progress: 0, completed: 0, my_pending: 0, overdue: 0 })
const users = ref<any[]>([])
const filters = reactive({ keyword: '', status: '', priority: '', my_tasks: false })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  title: '',
  description: '',
  priority: 'medium',
  status: 'pending',
  due_date: '',
  assigned_to: null as number | null,
})

const getPriorityType = (p: string) => ({ urgent: 'danger', high: 'warning', medium: '', low: 'info' }[p] || '')
const getPriorityLabel = (p: string) => ({ urgent: '紧急', high: '高', medium: '中', low: '低' }[p] || p)
const getStatusType = (s: string) => ({ pending: 'warning', in_progress: '', completed: 'success', cancelled: 'info' }[s] || '')
const getStatusLabel = (s: string) => ({ pending: '待处理', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }[s] || s)

const isOverdue = (row: TaskItem) => {
  if (!row.due_date || row.status === 'completed' || row.status === 'cancelled') return false
  return new Date(row.due_date) < new Date(new Date().toISOString().slice(0, 10))
}

const formatDate = (dt: string) => dt ? dt.slice(0, 10) : '-'

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await taskApi.getList({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      my_tasks: filters.my_tasks || undefined,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tasks.value = res.items
    pagination.total = res.total
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    stats.value = await taskApi.getStats()
  } catch { /* silent */ }
}

const fetchUsers = async () => {
  try {
    const res: any = await request.get('/users', { params: { skip: 0, limit: 100 } })
    users.value = res.items || res || []
  } catch { /* silent */ }
}

const openCreateDialog = () => {
  editingTask.value = null
  Object.assign(form, { title: '', description: '', priority: 'medium', status: 'pending', due_date: '', assigned_to: null })
  dialogVisible.value = true
}

const openEditDialog = (task: TaskItem) => {
  editingTask.value = task
  Object.assign(form, {
    title: task.title,
    description: task.description || '',
    priority: task.priority,
    status: task.status,
    due_date: task.due_date || '',
    assigned_to: task.assigned_to,
  })
  dialogVisible.value = true
}

const submitTask = async () => {
  if (!form.title.trim()) {
    ElMessage.warning('请输入任务标题')
    return
  }
  submitting.value = true
  try {
    const data: any = {
      title: form.title,
      description: form.description || undefined,
      priority: form.priority,
      due_date: form.due_date || undefined,
      assigned_to: form.assigned_to || undefined,
    }
    if (editingTask.value) {
      data.status = form.status
      await taskApi.update(editingTask.value.id, data)
      ElMessage.success('任务已更新')
    } else {
      await taskApi.create(data)
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    fetchTasks()
    fetchStats()
  } catch { /* handled */ } finally {
    submitting.value = false
  }
}

const toggleComplete = async (task: TaskItem, checked: boolean) => {
  try {
    if (checked) {
      await taskApi.complete(task.id)
      ElMessage.success('任务已完成')
    } else {
      await taskApi.update(task.id, { status: 'pending' })
    }
    fetchTasks()
    fetchStats()
  } catch { /* handled */ }
}

const deleteTask = async (id: number) => {
  try {
    await taskApi.delete(id)
    ElMessage.success('任务已删除')
    fetchTasks()
    fetchStats()
  } catch { /* handled */ }
}

onMounted(() => {
  fetchTasks()
  fetchStats()
  fetchUsers()
})
</script>

<style scoped>
.task-row {
  transition: background-color 0.2s;
}
</style>
