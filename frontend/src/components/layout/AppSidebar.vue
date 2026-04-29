<template>
  <div class="sidebar-container">
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <div class="logo-icon">
        <el-icon :size="24" color="#fff">
          <TrendCharts />
        </el-icon>
      </div>
      <transition name="fade">
        <div v-show="!isCollapsed" class="logo-text animate-fade-in">
          <h1 class="gradient-text">FOF管理</h1>
          <p>基金管理人工作台</p>
        </div>
      </transition>
      <button class="toggle-btn" @click="$emit('toggle')">
        <el-icon :size="18">
          <ArrowLeft v-if="!isCollapsed" />
          <ArrowRight v-else />
        </el-icon>
      </button>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in visibleMenuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <el-icon :size="20">
          <component :is="item.icon" />
        </el-icon>
        <transition name="fade">
          <span v-show="!isCollapsed" class="nav-label">{{ item.title }}</span>
        </transition>
        <div v-if="isActive(item.path) && !isCollapsed" class="nav-indicator"></div>
      </router-link>
    </nav>

    <!-- 底部用户信息 -->
    <div class="sidebar-footer">
      <transition name="fade">
        <div v-if="!isCollapsed" class="user-card" @click="showProfileDialog = true" title="点击修改个人信息">
          <div class="user-avatar">
            {{ userStore.userInfo?.real_name?.charAt(0) || userStore.username?.charAt(0) || 'U' }}
          </div>
          <div class="user-info">
            <p class="user-name">{{ userStore.userInfo?.real_name || userStore.username || '用户' }}</p>
            <p class="user-role">{{ getRoleLabel(userStore.userRole) }}</p>
          </div>
          <el-icon class="user-card-arrow"><ArrowRight /></el-icon>
        </div>
      </transition>
      <button class="logout-btn" @click="handleLogout" :title="isCollapsed ? '退出登录' : ''">
        <el-icon :size="18"><SwitchButton /></el-icon>
        <span v-show="!isCollapsed">退出登录</span>
      </button>
    </div>

    <!-- 个人信息编辑弹窗 -->
    <el-dialog 
      v-model="showProfileDialog" 
      title="个人信息" 
      width="480px" 
      destroy-on-close
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="profile-dialog">
        <!-- 头像区域 -->
        <div class="profile-avatar-section">
          <div class="profile-avatar-large">
            {{ userStore.userInfo?.real_name?.charAt(0) || userStore.username?.charAt(0) || 'U' }}
          </div>
          <div class="profile-avatar-info">
            <h3>{{ userStore.userInfo?.real_name || userStore.username || '用户' }}</h3>
            <el-tag size="small" type="primary">{{ getRoleLabel(userStore.userRole) }}</el-tag>
          </div>
        </div>

        <!-- 信息表单 -->
        <el-form :model="profileForm" label-width="80px" class="profile-form">
          <el-form-item label="用户名">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="profileForm.realName" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-divider content-position="left">修改密码</el-divider>
          <el-form-item label="当前密码">
            <el-input v-model="profileForm.currentPassword" type="password" placeholder="请输入当前密码" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="profileForm.newPassword" type="password" placeholder="请输入新密码" show-password />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="profileForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showProfileDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProfile" :loading="savingProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '@/api'
import {
  HomeFilled,
  User,
  Box,
  Upload,
  TrendCharts,
  DataAnalysis,
  Setting,
  Folder,
  ArrowLeft,
  ArrowRight,
  SwitchButton,
  Coin,
  Histogram,
  Message,
  Document,
  Warning,
  FolderOpened,
  MagicStick,
  PieChart,
  Notebook,
  Finished
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

defineProps<{
  isCollapsed: boolean
}>()

defineEmits<{
  (e: 'toggle'): void
}>()

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 判断菜单是否激活
const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

// 菜单项配置
interface MenuItem {
  path: string
  title: string
  icon: any
  roles?: string[]
}

const menuItems: MenuItem[] = [
  { path: '/', title: '总览', icon: HomeFilled },
  { path: '/managers', title: '管理人', icon: User },
  { path: '/products', title: '跟踪池', icon: Box },
  { path: '/portfolios', title: '组合管理', icon: Coin },
  { path: '/projects', title: '一级项目', icon: Folder },
  { path: '/ranking', title: '市场数据', icon: Histogram },
  { path: '/attribution', title: '因子归因', icon: PieChart },
  { path: '/alerts', title: '异常预警', icon: Warning },
  { path: '/ai-reports', title: 'AI报告', icon: MagicStick },
  { path: '/documents', title: '尽调资料', icon: FolderOpened },
  { path: '/email-crawler', title: '邮箱爬虫', icon: Message },
  { path: '/reports', title: '报表中心', icon: Document },
  { path: '/tasks', title: '待办任务', icon: Finished },
  { path: '/audit-log', title: '审计日志', icon: Notebook, roles: ['super_admin', 'director'] },
  { path: '/settings', title: '设置', icon: Setting }
]

// 根据用户角色过滤菜单
const visibleMenuItems = computed(() => {
  return menuItems.filter(item => {
    if (!item.roles) return true
    return userStore.hasAnyRole(item.roles)
  })
})

// 获取角色标签
const getRoleLabel = (role: string): string => {
  const roleMap: Record<string, string> = {
    readonly: '只读用户',
    manager: '经理',
    director: '总监',
    super_admin: '管理员'
  }
  return roleMap[role] || role
}

// 个人信息弹窗
const showProfileDialog = ref(false)
const savingProfile = ref(false)
const profileForm = reactive({
  username: '',
  realName: '',
  email: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 监听弹窗打开，初始化表单数据
watch(showProfileDialog, (val) => {
  if (val) {
    profileForm.username = userStore.username || ''
    profileForm.realName = userStore.userInfo?.real_name || ''
    profileForm.email = userStore.userInfo?.email || ''
    profileForm.currentPassword = ''
    profileForm.newPassword = ''
    profileForm.confirmPassword = ''
  }
})

// 保存个人信息
const saveProfile = async () => {
  // 验证密码
  if (profileForm.newPassword) {
    if (!profileForm.currentPassword) {
      ElMessage.warning('请输入当前密码')
      return
    }
    if (profileForm.newPassword.length < 6) {
      ElMessage.warning('新密码长度至少6位')
      return
    }
    if (profileForm.newPassword !== profileForm.confirmPassword) {
      ElMessage.warning('两次输入的密码不一致')
      return
    }
  }

  savingProfile.value = true
  try {
    // 更新基本信息
    await userApi.updateProfile({
      real_name: profileForm.realName,
      email: profileForm.email
    })

    // 如果填写了新密码，则修改密码
    if (profileForm.newPassword && profileForm.currentPassword) {
      await userApi.changePassword({
        current_password: profileForm.currentPassword,
        new_password: profileForm.newPassword
      })
      ElMessage.success('密码修改成功')
    }

    // 更新本地用户信息
    if (userStore.userInfo) {
      userStore.userInfo.real_name = profileForm.realName
      userStore.userInfo.email = profileForm.email
    }

    ElMessage.success('个人信息保存成功')
    showProfileDialog.value = false
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    savingProfile.value = false
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
}

/* Logo区域 */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--card-border);
  min-height: 64px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent-color) 0%, rgba(var(--accent-primary-hover), 1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text {
  flex: 1;
  min-width: 0;
}

.logo-text h1 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
}

.logo-text p {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 2px 0 0 0;
  white-space: nowrap;
}

.toggle-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.toggle-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.2s;
  position: relative;
}

.nav-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(var(--accent-primary), 0.15);
  color: var(--accent-color);
}

.nav-label {
  font-weight: 500;
  white-space: nowrap;
}

.nav-indicator {
  position: absolute;
  right: 12px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-color);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 底部用户信息 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--card-border);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-card:hover {
  background: var(--card-bg);
  border-color: var(--accent-color);
}

.user-card-arrow {
  color: var(--text-muted);
  transition: transform 0.2s;
}

.user-card:hover .user-card-arrow {
  color: var(--accent-color);
  transform: translateX(2px);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 2px 0 0 0;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  font-weight: 500;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 个人信息弹窗 */
.profile-dialog {
  padding: 0 10px;
}

.profile-avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--card-border);
}

.profile-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.profile-avatar-info h3 {
  margin: 0 0 8px 0;
  font-size: 1.125rem;
  color: var(--text-primary);
}

.profile-form {
  margin-top: 16px;
}

.profile-form :deep(.el-divider__text) {
  color: var(--text-muted);
  font-size: 0.875rem;
  background-color: var(--el-dialog-bg-color, var(--card-bg));
}

.profile-form :deep(.el-divider) {
  border-color: var(--card-border);
}

/* 深色主题下的输入框样式 */
.profile-form :deep(.el-input__wrapper) {
  background-color: var(--el-input-bg-color, var(--card-bg));
}

.profile-form :deep(.el-input__inner) {
  color: var(--text-primary);
}
</style>
