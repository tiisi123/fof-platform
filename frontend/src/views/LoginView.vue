<template>
  <div class="login-container">
    <!-- 主题设置 -->
    <div class="theme-settings">
      <button class="settings-trigger" @click="showSettings = !showSettings" title="外观设置">
        <el-icon :size="18"><Setting /></el-icon>
      </button>
      <transition name="fade-scale">
        <div v-if="showSettings" class="settings-panel">
          <div class="settings-section">
            <span class="settings-label">主题</span>
            <div class="theme-switch">
              <button 
                class="theme-btn" 
                :class="{ active: currentTheme === 'light' }"
                @click="setTheme('light')"
              >
                <el-icon :size="14"><Sunny /></el-icon>
              </button>
              <button 
                class="theme-btn" 
                :class="{ active: currentTheme === 'dark' }"
                @click="setTheme('dark')"
              >
                <el-icon :size="14"><Moon /></el-icon>
              </button>
            </div>
          </div>
          <div class="settings-section">
            <span class="settings-label">颜色</span>
            <div class="color-options">
              <button 
                v-for="color in accentColors" 
                :key="color.value"
                class="color-dot"
                :class="{ active: currentAccent === color.value }"
                :style="{ background: color.hex }"
                @click="setAccentColor(color.value)"
              ></button>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-wrapper">
      <div class="login-card glass-card animate-slide-up">
        <!-- Logo -->
        <div class="login-header">
          <div class="logo-icon shadow-glow-lg">
            <el-icon :size="32" color="#fff">
              <TrendCharts />
            </el-icon>
          </div>
          <h1 class="gradient-text">FOF管理平台</h1>
          <p class="subtitle">基金管理人一体化工作台</p>
        </div>

        <!-- 登录表单 -->
        <form class="login-form" @submit.prevent="handleLogin">
          <!-- 错误提示 -->
          <div v-if="errorMsg" class="error-alert animate-fade-in">
            <el-icon><WarningFilled /></el-icon>
            {{ errorMsg }}
          </div>

          <!-- 用户名 -->
          <div class="form-group">
            <label>用户名</label>
            <div class="input-wrapper">
              <el-icon class="input-icon"><User /></el-icon>
              <input
                v-model="loginForm.username"
                type="text"
                class="input-field"
                placeholder="请输入用户名"
                autocomplete="username"
                required
              />
            </div>
          </div>

          <!-- 密码 -->
          <div class="form-group">
            <label>密码</label>
            <div class="input-wrapper">
              <el-icon class="input-icon"><Lock /></el-icon>
              <input
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                class="input-field"
                placeholder="请输入密码"
                autocomplete="current-password"
                required
              />
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                <el-icon>
                  <View v-if="!showPassword" />
                  <Hide v-else />
                </el-icon>
              </button>
            </div>
          </div>

          <!-- 记住我 -->
          <div class="form-options">
            <label class="remember-me">
              <input type="checkbox" v-model="rememberMe" />
              <span>记住我</span>
            </label>
          </div>

          <!-- 登录按钮 -->
          <button type="submit" class="login-btn" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? '登录中...' : '登 录' }}
          </button>
        </form>

      </div>

      <!-- 底部信息 -->
      <p class="footer-text">© 2026 FOF管理平台 · 专业版</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, TrendCharts, View, Hide, WarningFilled, Sunny, Moon, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 主题设置
const currentTheme = ref('light')
const currentAccent = ref('blue')
const showSettings = ref(false)

const accentColors = [
  { value: 'blue', label: '蓝色', hex: '#3b82f6' },
  { value: 'green', label: '绿色', hex: '#22c55e' },
  { value: 'purple', label: '紫色', hex: '#8b5cf6' },
  { value: 'orange', label: '橙色', hex: '#f59e0b' },
  { value: 'pink', label: '粉色', hex: '#ec4899' },
]

const currentAccentHex = computed(() => {
  return accentColors.find(c => c.value === currentAccent.value)?.hex || '#3b82f6'
})

// 初始化主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme') || 'light'
  const savedAccent = localStorage.getItem('accent-color') || 'blue'
  currentTheme.value = savedTheme
  currentAccent.value = savedAccent
  applyTheme(savedTheme)
  document.documentElement.setAttribute('data-accent', savedAccent)
})

// 设置主题
const setTheme = (theme: string) => {
  currentTheme.value = theme
  localStorage.setItem('theme', theme)
  applyTheme(theme)
}

const applyTheme = (theme: string) => {
  document.documentElement.setAttribute('data-theme', theme)
  if (theme === 'light') {
    document.documentElement.classList.add('light-theme')
    document.documentElement.classList.remove('dark-theme')
  } else {
    document.documentElement.classList.add('dark-theme')
    document.documentElement.classList.remove('light-theme')
  }
}

// 设置强调色
const setAccentColor = (color: string) => {
  currentAccent.value = color
  localStorage.setItem('accent-color', color)
  document.documentElement.setAttribute('data-accent', color)
}

// 表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 状态
const loading = ref(false)
const showPassword = ref(false)
const rememberMe = ref(false)
const errorMsg = ref('')

/**
 * 处理登录
 */
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    errorMsg.value = '请输入用户名和密码'
    return
  }

  if (loginForm.password.length < 6) {
    errorMsg.value = '密码至少6位'
    return
  }

  errorMsg.value = ''
  loading.value = true

  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    console.error('登录失败:', error)
    errorMsg.value = error?.response?.data?.detail || error?.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 主题设置 */
.theme-settings {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 100;
}

.settings-trigger {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(10px);
}

.settings-trigger:hover {
  border-color: var(--accent-color);
  color: var(--accent-color);
}

.settings-panel {
  position: absolute;
  top: 44px;
  right: 0;
  width: 180px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
}

.settings-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.settings-section:first-child {
  padding-top: 0;
}

.settings-section:last-child {
  padding-bottom: 0;
}

.settings-section:not(:last-child) {
  border-bottom: 1px solid var(--card-border);
}

.settings-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.theme-switch {
  display: flex;
  gap: 4px;
  padding: 3px;
  border-radius: 8px;
  background: var(--input-bg);
}

.theme-btn {
  width: 28px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.theme-btn:hover {
  color: var(--text-primary);
}

.theme-btn.active {
  background: var(--accent-color);
  color: #fff;
}

.color-options {
  display: flex;
  gap: 6px;
}

.color-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.color-dot:hover {
  transform: scale(1.2);
}

.color-dot.active {
  border-color: var(--text-primary);
  box-shadow: 0 0 0 1px var(--card-bg);
}

/* 动画 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.2s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-5px);
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
}

.bg-circle-1 {
  width: 320px;
  height: 320px;
  background: rgba(var(--accent-primary), 0.1);
  top: -80px;
  right: -80px;
}

.bg-circle-2 {
  width: 320px;
  height: 320px;
  background: rgba(var(--accent-primary-hover), 0.1);
  bottom: -80px;
  left: -80px;
}

.bg-circle-3 {
  width: 600px;
  height: 600px;
  background: rgba(var(--accent-primary), 0.05);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.bg-grid {
  position: absolute;
  inset: 0;
  opacity: 0.02;
  background-image: 
    linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* 登录卡片 */
.login-wrapper {
  position: relative;
  width: 100%;
  max-width: 420px;
}

.login-card {
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--accent-color) 0%, rgba(var(--accent-primary-hover), 1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.login-header .subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f87171;
  font-size: 0.875rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  color: var(--text-muted);
  z-index: 1;
}

.input-field {
  padding-left: 48px !important;
  padding-right: 48px !important;
  height: 48px;
}

.password-toggle {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  z-index: 1;
}

.password-toggle:hover {
  color: var(--text-secondary);
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.875rem;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-secondary);
}

.remember-me input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent-color);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, var(--accent-color) 0%, rgba(var(--accent-primary-hover), 1) 100%);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(var(--accent-primary), 0.25);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(var(--accent-primary), 0.35);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 底部信息 */
.footer-text {
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 24px 0 0 0;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }
}
</style>
