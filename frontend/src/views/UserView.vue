<template>
  <div class="user-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">
          新增用户
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索用户名或邮箱"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-select
            v-model="searchForm.role"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option
              v-for="item in ROLE_OPTIONS"
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
            <el-option label="活跃" value="active" />
            <el-option label="停用" value="inactive" />
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
      <el-table
        :data="userStore.users"
        :loading="userStore.loading"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="real_name" label="真实姓名" width="120" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
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
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="warning" size="small" link @click="handleChangePassword(row)">
              改密
            </el-button>
            <el-button type="danger" size="small" link @click="handleDeleteConfirm(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="userStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="formVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
            maxlength="50"
          />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="至少8位，含大小写+数字+特殊符号"
            show-password
            maxlength="50"
          />
          <div v-if="formData.password" class="password-strength">
            <div class="strength-bar">
              <div class="strength-fill" :style="{ width: pwdStrengthPercent + '%', background: pwdStrengthColor }" />
            </div>
            <span class="strength-text" :style="{ color: pwdStrengthColor }">{{ pwdStrengthLabel }}</span>
          </div>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="formData.email"
            placeholder="请输入邮箱"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input
            v-model="formData.real_name"
            placeholder="请输入真实姓名"
            maxlength="50"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="item in ROLE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
              <span>{{ item.label }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ ROLE_DESCRIPTIONS[item.value] }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="active">活跃</el-radio>
            <el-radio label="inactive">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="userStore.loading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordVisible"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="至少8位，含大小写+数字+特殊符号"
            show-password
          />
          <div v-if="passwordForm.new_password" class="password-strength">
            <div class="strength-bar">
              <div class="strength-fill" :style="{ width: newPwdStrengthPercent + '%', background: newPwdStrengthColor }" />
            </div>
            <span class="strength-text" :style="{ color: newPwdStrengthColor }">{{ newPwdStrengthLabel }}</span>
          </div>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="passwordVisible = false">取消</el-button>
        <el-button type="primary" :loading="userStore.loading" @click="handlePasswordSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { useUserManagementStore } from '@/store/userManagement'
import { ROLE_OPTIONS, ROLE_DESCRIPTIONS } from '@/types/user'
import type { User, UserCreate, UserUpdate, UserListParams } from '@/types'

const userStore = useUserManagementStore()

// 搜索表单
const searchForm = reactive<UserListParams>({
  search: '',
  role: undefined,
  status: undefined,
  skip: 0,
  limit: 20
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 用户表单
const formVisible = ref(false)
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const currentUser = ref<User | null>(null)

const formData = reactive<UserCreate>({
  username: '',
  password: '',
  email: '',
  real_name: '',
  role: 'readonly',
  status: 'active'
})

// ---- 密码强度计算 ----
function calcStrength(pwd: string) {
  let score = 0
  if (pwd.length >= 8) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[a-z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  return score
}
function strengthMeta(score: number) {
  if (score <= 1) return { pct: 20, color: '#f56c6c', label: '弱' }
  if (score <= 2) return { pct: 40, color: '#e6a23c', label: '较弱' }
  if (score <= 3) return { pct: 60, color: '#409eff', label: '中等' }
  if (score <= 4) return { pct: 80, color: '#67c23a', label: '强' }
  return { pct: 100, color: '#67c23a', label: '非常强' }
}
const pwdScore = computed(() => calcStrength(formData.password))
const pwdMeta = computed(() => strengthMeta(pwdScore.value))
const pwdStrengthPercent = computed(() => pwdMeta.value.pct)
const pwdStrengthColor = computed(() => pwdMeta.value.color)
const pwdStrengthLabel = computed(() => pwdMeta.value.label)

const newPwdScore = computed(() => calcStrength(passwordForm.new_password))
const newPwdMeta = computed(() => strengthMeta(newPwdScore.value))
const newPwdStrengthPercent = computed(() => newPwdMeta.value.pct)
const newPwdStrengthColor = computed(() => newPwdMeta.value.color)
const newPwdStrengthLabel = computed(() => newPwdMeta.value.label)

const validatePasswordStrength = (_rule: any, value: string, callback: any) => {
  if (!value) return callback()
  if (value.length < 8) return callback(new Error('密码至少8位'))
  if (!/[A-Z]/.test(value)) return callback(new Error('需包含至少一个大写字母'))
  if (!/[a-z]/.test(value)) return callback(new Error('需包含至少一个小写字母'))
  if (!/\d/.test(value)) return callback(new Error('需包含至少一个数字'))
  if (!/[^A-Za-z0-9]/.test(value)) return callback(new Error('需包含至少一个特殊符号'))
  callback()
}

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { validator: validatePasswordStrength, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 修改密码表单
const passwordVisible = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  user_id: 0,
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { validator: validatePasswordStrength, trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 获取用户列表
const fetchUsers = async () => {
  searchForm.skip = (currentPage.value - 1) * pageSize.value
  searchForm.limit = pageSize.value
  await userStore.fetchUsers(searchForm)
}

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

// 处理重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.role = undefined
  searchForm.status = undefined
  currentPage.value = 1
  fetchUsers()
}

// 处理新增
const handleAdd = () => {
  isEdit.value = false
  currentUser.value = null
  Object.assign(formData, {
    username: '',
    password: '',
    email: '',
    real_name: '',
    role: 'readonly',
    status: 'active'
  })
  formVisible.value = true
}

// 处理编辑
const handleEdit = (user: User) => {
  isEdit.value = true
  currentUser.value = user
  Object.assign(formData, {
    username: user.username,
    email: user.email || '',
    real_name: user.real_name || '',
    role: user.role,
    status: user.status
  })
  formVisible.value = true
}

// 处理删除确认
const handleDeleteConfirm = (user: User) => {
  ElMessageBox.confirm(
    `确定要删除用户"${user.username}"吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(() => {
      handleDelete(user.id)
    })
    .catch(() => {})
}

// 处理删除
const handleDelete = async (id: number) => {
  try {
    await userStore.deleteUser(id)
    await fetchUsers()
  } catch (error) {
    // 错误已在store中处理
  }
}

// 处理表单提交
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (isEdit.value && currentUser.value) {
      // 编辑
      const updateData: UserUpdate = {
        email: formData.email || undefined,
        real_name: formData.real_name || undefined,
        role: formData.role,
        status: formData.status
      }
      await userStore.updateUser(currentUser.value.id, updateData)
    } else {
      // 新增
      await userStore.createUser(formData)
    }

    formVisible.value = false
    await fetchUsers()
  } catch (error) {
    // 错误已在store中处理
  }
}

// 处理修改密码
const handleChangePassword = (user: User) => {
  passwordForm.user_id = user.id
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordVisible.value = true
}

// 处理密码提交
const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    await userStore.changePassword(
      passwordForm.user_id,
      passwordForm.old_password,
      passwordForm.new_password
    )
    passwordVisible.value = false
  } catch (error) {
    // 错误已在store中处理
  }
}

// 处理分页变化
const handlePageChange = () => {
  fetchUsers()
}

// 获取角色标签
const getRoleLabel = (role: string) => {
  const option = ROLE_OPTIONS.find(item => item.value === role)
  return option?.label || role
}

// 获取角色类型
const getRoleType = (role: string) => {
  const typeMap: Record<string, any> = {
    'super_admin': 'danger',
    'director': 'warning',
    'manager': 'primary',
    'readonly': 'info'
  }
  return typeMap[role] || ''
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-view {
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 密码强度指示器 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  width: 100%;
}

.strength-bar {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: var(--el-fill-color-light, #e4e7ed);
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s, background 0.3s;
}

.strength-text {
  font-size: 12px;
  white-space: nowrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .user-view {
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

  .pagination-container {
    justify-content: center;
  }
}
</style>
