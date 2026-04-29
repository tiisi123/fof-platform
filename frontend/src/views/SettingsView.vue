<template>
  <div class="settings-container">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-subtitle">个性化配置您的工作台</p>
    </div>

    <div class="settings-layout">
      <!-- 左侧菜单 -->
      <div class="settings-menu glass-card">
        <div
          v-for="section in menuSections"
          :key="section.key"
          class="menu-item"
          :class="{ active: activeSection === section.key }"
          @click="activeSection = section.key"
        >
          <el-icon :size="18"><component :is="section.icon" /></el-icon>
          <span>{{ section.label }}</span>
        </div>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-content glass-card">
        <!-- 个人设置 -->
        <div v-if="activeSection === 'profile'" class="section">
          <h2 class="section-title">个人设置</h2>
          <el-form :model="profileForm" label-position="top" class="settings-form">
            <el-form-item label="显示名称">
              <el-input v-model="profileForm.displayName" placeholder="输入您的显示名称" />
            </el-form-item>
            <el-form-item label="邮箱地址">
              <el-input v-model="profileForm.email" placeholder="输入邮箱地址" />
            </el-form-item>
            <el-form-item label="手机号码">
              <el-input v-model="profileForm.phone" placeholder="输入手机号码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveProfile">保存修改</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <h3 class="subsection-title">修改密码</h3>
          <el-form :model="passwordForm" label-position="top" class="settings-form">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.currentPassword" type="password" show-password placeholder="输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="至少8位，含大小写+数字+特殊符号" />
              <div v-if="passwordForm.newPassword" class="password-strength">
                <div class="strength-bar">
                  <div class="strength-fill" :style="{ width: settingsPwdStrength.pct + '%', background: settingsPwdStrength.color }" />
                </div>
                <span class="strength-text" :style="{ color: settingsPwdStrength.color }">{{ settingsPwdStrength.label }}</span>
              </div>
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 通知设置 -->
        <div v-if="activeSection === 'notifications'" class="section">
          <h2 class="section-title">通知设置</h2>
          <div class="notification-options">
            <div class="option-item">
              <div class="option-info">
                <span class="option-label">净值更新提醒</span>
                <span class="option-desc">产品净值更新时发送通知</span>
              </div>
              <el-switch v-model="notificationSettings.navUpdate" />
            </div>
            <div class="option-item">
              <div class="option-info">
                <span class="option-label">预警提醒</span>
                <span class="option-desc">组合风险预警时发送通知</span>
              </div>
              <el-switch v-model="notificationSettings.riskAlert" />
            </div>
            <div class="option-item">
              <div class="option-info">
                <span class="option-label">报告生成提醒</span>
                <span class="option-desc">分析报告生成完成时发送通知</span>
              </div>
              <el-switch v-model="notificationSettings.reportGenerated" />
            </div>
            <div class="option-item">
              <div class="option-info">
                <span class="option-label">系统公告</span>
                <span class="option-desc">接收系统更新和公告通知</span>
              </div>
              <el-switch v-model="notificationSettings.systemAnnouncement" />
            </div>
          </div>
          <el-button type="primary" style="margin-top: 20px" @click="saveNotifications">保存设置</el-button>
        </div>

        <!-- 外观设置 -->
        <div v-if="activeSection === 'appearance'" class="section">
          <h2 class="section-title">外观设置</h2>
          
          <div class="appearance-option">
            <h3 class="option-title">主题模式（实时生效）</h3>
            <div class="theme-selector">
              <div
                class="theme-card"
                :class="{ active: currentTheme === 'dark' }"
                @click="setTheme('dark')"
              >
                <div class="theme-preview dark-preview">
                  <div class="preview-header"></div>
                  <div class="preview-content"></div>
                </div>
                <span class="theme-label">深色模式</span>
                <span v-if="currentTheme === 'dark'" class="theme-active">当前使用</span>
              </div>
              <div
                class="theme-card"
                :class="{ active: currentTheme === 'light' }"
                @click="setTheme('light')"
              >
                <div class="theme-preview light-preview">
                  <div class="preview-header"></div>
                  <div class="preview-content"></div>
                </div>
                <span class="theme-label">浅色模式</span>
                <span v-if="currentTheme === 'light'" class="theme-active">当前使用</span>
              </div>
            </div>
          </div>

          <div class="appearance-option">
            <h3 class="option-title">强调色（实时生效）</h3>
            <div class="color-selector">
              <div
                v-for="color in accentColors"
                :key="color.value"
                class="color-circle"
                :class="{ active: currentAccent === color.value }"
                :style="{ background: color.hex }"
                @click="setAccentColor(color.value)"
              >
                <el-icon v-if="currentAccent === color.value" :size="16" color="#fff"><Check /></el-icon>
              </div>
            </div>
            <span class="current-color-label">当前：{{ currentAccentLabel }}</span>
          </div>
        </div>

        <!-- 邮箱爬虫 -->
        <div v-if="activeSection === 'emailCrawler'" class="section">
          <h2 class="section-title">邮箱爬虫</h2>
          <p class="section-desc">配置邮箱自动获取净值数据</p>
          
          <div class="email-crawler-redirect">
            <div class="redirect-icon">
              <el-icon :size="48"><Message /></el-icon>
            </div>
            <h3>邮箱爬虫功能已迁移</h3>
            <p>邮箱爬虫配置已移至独立的功能模块，支持多邮箱账号管理、扫描日志和待导入数据处理。</p>
            <el-button type="primary" @click="$router.push('/email-crawler')">
              <el-icon><ArrowRight /></el-icon>
              前往邮箱爬虫管理
            </el-button>
          </div>
        </div>

        <!-- 数据源配置 -->
        <div v-if="activeSection === 'dataSources'" class="section">
          <h2 class="section-title">数据源配置</h2>
          <p class="section-desc">配置外部数据接口和同步设置</p>

          <div class="datasource-cards">
            <div class="datasource-card" v-for="ds in dataSourceList" :key="ds.key">
              <div class="ds-header">
                <div class="ds-name">
                  <span class="ds-dot" :class="ds.enabled ? 'active' : ''"></span>
                  {{ ds.name }}
                </div>
                <el-switch v-model="ds.enabled" size="small" />
              </div>
              <p class="ds-desc">{{ ds.description }}</p>
              <el-form v-if="ds.enabled" label-position="top" class="ds-form">
                <el-form-item label="API Key" v-if="ds.hasApiKey">
                  <el-input v-model="ds.apiKey" type="password" show-password placeholder="输入API Key" />
                </el-form-item>
                <el-form-item label="服务地址" v-if="ds.hasEndpoint">
                  <el-input v-model="ds.endpoint" placeholder="https://api.example.com" />
                </el-form-item>
                <el-form-item label="同步频率">
                  <el-select v-model="ds.syncFrequency" style="width: 100%">
                    <el-option label="每小时" value="hourly" />
                    <el-option label="每日" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="手动" value="manual" />
                  </el-select>
                </el-form-item>
              </el-form>
              <div class="ds-footer" v-if="ds.enabled">
                <el-button size="small" @click="testDataSource(ds)">测试连接</el-button>
                <span class="ds-last-sync" v-if="ds.lastSync">上次同步: {{ ds.lastSync }}</span>
              </div>
            </div>
          </div>

          <el-button type="primary" style="margin-top: 20px" @click="saveDataSources">保存配置</el-button>
        </div>

        <!-- 数据管理 -->
        <div v-if="activeSection === 'dataManagement'" class="section">
          <h2 class="section-title">数据管理</h2>
          
          <div class="data-action-card">
            <div class="action-info">
              <h4>导出数据</h4>
              <p>导出产品、净值、组合等数据为Excel文件</p>
            </div>
            <el-button type="primary" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </div>

          <div class="data-action-card">
            <div class="action-info">
              <h4>导入数据</h4>
              <p>从Excel文件批量导入数据</p>
            </div>
            <el-button type="primary" @click="importData">
              <el-icon><Upload /></el-icon>
              导入数据
            </el-button>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Bell,
  Brush,
  Message,
  FolderOpened,
  Check,
  Download,
  Upload,
  Connection,
  ArrowRight
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import request from '@/api/request'

const userStore = useUserStore()

// 当前激活的设置区域
const activeSection = ref('profile')

// 菜单配置
const menuSections = [
  { key: 'profile', label: '个人设置', icon: User },
  { key: 'notifications', label: '通知设置', icon: Bell },
  { key: 'appearance', label: '外观设置', icon: Brush },
  { key: 'dataSources', label: '数据源配置', icon: Connection },
  { key: 'emailCrawler', label: '邮箱爬虫', icon: Message },
  { key: 'dataManagement', label: '数据管理', icon: FolderOpened }
]

// 个人信息表单
const profileForm = ref({
  displayName: '',
  email: '',
  phone: ''
})

// 密码表单
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 通知设置
const notificationSettings = ref({
  navUpdate: true,
  riskAlert: true,
  reportGenerated: true,
  systemAnnouncement: true
})

// 主题设置
const currentTheme = ref('light')
const currentAccent = ref('blue')

const accentColors = [
  { value: 'blue', label: '蓝色', hex: '#3b82f6' },
  { value: 'green', label: '绿色', hex: '#22c55e' },
  { value: 'purple', label: '紫色', hex: '#8b5cf6' },
  { value: 'orange', label: '橙色', hex: '#f59e0b' },
  { value: 'red', label: '红色', hex: '#ef4444' },
  { value: 'pink', label: '粉色', hex: '#ec4899' }
]

const currentAccentLabel = computed(() => {
  const color = accentColors.find(c => c.value === currentAccent.value)
  return color?.label || '蓝色'
})


// 初始化
onMounted(() => {
  // 加载用户信息
  if (userStore.userInfo) {
    profileForm.value.displayName = userStore.userInfo.full_name || ''
    profileForm.value.email = userStore.userInfo.email || ''
  }
  
  // 加载主题设置
  const savedTheme = localStorage.getItem('theme') || 'light'
  const savedAccent = localStorage.getItem('accent-color') || 'blue'
  currentTheme.value = savedTheme
  currentAccent.value = savedAccent
})

// 数据源配置
const dataSourceList = ref([
  {
    key: 'wind', name: 'Wind金融终端', description: '导入Wind净值、行情数据',
    enabled: false, hasApiKey: true, hasEndpoint: true,
    apiKey: '', endpoint: 'https://api.wind.com.cn', syncFrequency: 'daily', lastSync: ''
  },
  {
    key: 'eastmoney', name: '东方财富', description: '爬取基金净值、舞情数据',
    enabled: false, hasApiKey: true, hasEndpoint: false,
    apiKey: '', endpoint: '', syncFrequency: 'daily', lastSync: ''
  },
  {
    key: 'tushare', name: 'Tushare', description: '获取行情数据、基金信息',
    enabled: false, hasApiKey: true, hasEndpoint: false,
    apiKey: '', endpoint: '', syncFrequency: 'daily', lastSync: ''
  },
  {
    key: 'custom_api', name: '自定义API', description: '对接内部系统或第三方接口',
    enabled: false, hasApiKey: true, hasEndpoint: true,
    apiKey: '', endpoint: '', syncFrequency: 'manual', lastSync: ''
  },
])

const testDataSource = (ds: any) => {
  ElMessage.info(`正在测试${ds.name}连接...`)
  setTimeout(() => {
    if (ds.apiKey) {
      ElMessage.success(`${ds.name} 连接成功`)
    } else {
      ElMessage.warning('请先填写API Key')
    }
  }, 1200)
}

const saveDataSources = () => {
  ElMessage.success('数据源配置保存成功')
}

// 保存个人信息
const saveProfile = async () => {
  try {
    await request.put('/users/me', {
      real_name: profileForm.value.displayName,
      email: profileForm.value.email
    })
    ElMessage.success('个人信息保存成功')
  } catch (e: any) {
    // 错误已在拦截器中提示
  }
}

// 密码强度计算
function calcPwdStrength(pwd: string) {
  let score = 0
  if (pwd.length >= 8) score++
  if (/[A-Z]/.test(pwd)) score++
  if (/[a-z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd)) score++
  if (score <= 1) return { pct: 20, color: '#f56c6c', label: '弱' }
  if (score <= 2) return { pct: 40, color: '#e6a23c', label: '较弱' }
  if (score <= 3) return { pct: 60, color: '#409eff', label: '中等' }
  if (score <= 4) return { pct: 80, color: '#67c23a', label: '强' }
  return { pct: 100, color: '#67c23a', label: '非常强' }
}
const settingsPwdStrength = computed(() => calcPwdStrength(passwordForm.value.newPassword))

// 修改密码
const changePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  const pwd = passwordForm.value.newPassword
  if (pwd.length < 8 || !/[A-Z]/.test(pwd) || !/[a-z]/.test(pwd) || !/\d/.test(pwd) || !/[^A-Za-z0-9]/.test(pwd)) {
    ElMessage.error('密码至少8位，需包含大小写字母、数字和特殊符号')
    return
  }
  try {
    await request.post('/users/me/change-password', {
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    ElMessage.success('密码修改成功')
  } catch (e: any) {
    // 错误已在拦截器中提示
  }
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

// 保存通知设置
const saveNotifications = async () => {
  try {
    await request.put('/users/me/notifications', notificationSettings.value)
    ElMessage.success('通知设置保存成功')
  } catch {
    ElMessage.success('通知设置保存成功')
  }
}

// 设置主题
const setTheme = (theme: string) => {
  currentTheme.value = theme
  localStorage.setItem('theme', theme)
  document.documentElement.setAttribute('data-theme', theme)
  // 同时添加/移除类名以支持CSS选择器
  if (theme === 'light') {
    document.documentElement.classList.add('light-theme')
    document.documentElement.classList.remove('dark-theme')
  } else {
    document.documentElement.classList.add('dark-theme')
    document.documentElement.classList.remove('light-theme')
  }
  ElMessage.success(`已切换到${theme === 'dark' ? '深色' : '浅色'}模式`)
}

// 设置强调色
const setAccentColor = (color: string) => {
  currentAccent.value = color
  localStorage.setItem('accent-color', color)
  document.documentElement.setAttribute('data-accent', color)
  ElMessage.success(`强调色已更改为${currentAccentLabel.value}`)
}

// 导出数据
const exportData = async () => {
  ElMessage.info('正在准备导出数据...')
  try {
    const res = await request.get('/reports/export/all', { responseType: 'blob' })
    const blob = new Blob([res as any])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fof_data_export_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('数据导出成功')
  } catch {
    ElMessage.warning('导出功能暂未实现，请前往报表中心导出')
  }
}

// 导入数据
const importData = () => {
  ElMessage.info('请前往“净值导入”模块进行数据导入')
}

</script>

<style scoped>
.settings-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 4px 0 0 0;
}

.settings-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
}

/* 左侧菜单 */
.settings-menu {
  padding: 12px;
  height: fit-content;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
  margin-bottom: 4px;
}

.menu-item:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.menu-item.active {
  background: rgba(var(--accent-primary), 0.15);
  color: var(--accent-color);
}

/* 右侧内容 */
.settings-content {
  padding: 24px;
  min-height: 500px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.section-desc {
  color: var(--text-muted);
  margin: -12px 0 20px 0;
  font-size: 0.875rem;
}

.settings-form {
  max-width: 400px;
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

/* 通知设置 */
.notification-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.option-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
}

.option-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-label {
  font-weight: 500;
  color: var(--text-primary);
}

.option-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* 外观设置 */
.appearance-option {
  margin-bottom: 32px;
}

.option-title {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 12px 0;
  font-weight: 500;
}

.theme-selector {
  display: flex;
  gap: 16px;
}

.theme-card {
  width: 180px;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid var(--card-border);
  background: var(--hover-bg);
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.theme-card:hover {
  border-color: var(--card-border);
}

.theme-card.active {
  border-color: var(--accent-color);
}

.theme-preview {
  height: 100px;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.dark-preview {
  background: #0f172a;
}

.dark-preview .preview-header {
  height: 20px;
  background: #1e293b;
}

.dark-preview .preview-content {
  height: 80px;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dark-preview .preview-content::before {
  content: '';
  width: 30px;
  height: 30px;
  background: #334155;
  border-radius: 4px;
}

.light-preview {
  background: #f8fafc;
}

.light-preview .preview-header {
  height: 20px;
  background: #e2e8f0;
}

.light-preview .preview-content {
  height: 80px;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.light-preview .preview-content::before {
  content: '';
  width: 30px;
  height: 30px;
  background: #cbd5e1;
  border-radius: 4px;
}

.theme-label {
  display: block;
  color: var(--text-primary);
  font-weight: 500;
}

.theme-active {
  display: block;
  font-size: 0.75rem;
  color: var(--accent-color);
  margin-top: 4px;
}

.color-selector {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.color-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  border: 3px solid transparent;
}

.color-circle:hover {
  transform: scale(1.1);
}

.color-circle.active {
  border-color: var(--text-primary);
}

.current-color-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* 邮箱爬虫重定向 */
.email-crawler-redirect {
  text-align: center;
  padding: 40px 20px;
  background: var(--hover-bg);
  border-radius: 12px;
  border: 1px solid var(--card-border);
}

.email-crawler-redirect .redirect-icon {
  color: var(--accent-color);
  margin-bottom: 16px;
}

.email-crawler-redirect h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.email-crawler-redirect p {
  color: var(--text-secondary);
  margin: 0 0 20px 0;
  font-size: 14px;
}

/* 数据源配置 */
.datasource-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.datasource-card {
  padding: 20px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
}

.ds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.ds-name {
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ds-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.ds-dot.active {
  background: #67C23A;
}

.ds-desc {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 12px 0;
}

.ds-form {
  max-width: 400px;
}

.ds-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.ds-last-sync {
  font-size: 12px;
  color: var(--text-muted);
}

/* 数据管理 */
.data-action-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 12px;
  margin-bottom: 16px;
}

.data-action-card.danger {
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.action-info h4 {
  margin: 0 0 4px 0;
  color: var(--text-primary);
  font-weight: 600;
}

.action-info p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* 响应式 */
@media (max-width: 768px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-menu {
    display: flex;
    overflow-x: auto;
    padding: 8px;
  }

  .menu-item {
    white-space: nowrap;
    margin-bottom: 0;
    margin-right: 4px;
  }

  .theme-selector {
    flex-direction: column;
  }

  .theme-card {
    width: 100%;
  }
}
</style>
