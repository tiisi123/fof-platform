<template>
  <div 
    class="stat-card glass-card animate-slide-up"
    :class="[`border-${color}`]"
    :style="{ animationDelay: `${delay}ms` }"
  >
    <div class="stat-header">
      <div class="stat-icon" :class="[`icon-${color}`]">
        <el-icon :size="24">
          <component :is="icon" />
        </el-icon>
      </div>
      <div v-if="change !== undefined" class="stat-change" :class="isPositive ? 'change-up' : 'change-down'">
        <el-icon :size="14">
          <TrendingUp v-if="isPositive" />
          <TrendingDown v-else />
        </el-icon>
        <span class="stat-number">{{ isPositive ? '+' : '' }}{{ change.toFixed(2) }}%</span>
      </div>
    </div>

    <div class="stat-body">
      <p class="stat-title">{{ title }}</p>
      <p v-if="loading" class="stat-value">
        <el-icon class="is-loading"><Loading /></el-icon>
      </p>
      <p v-else class="stat-value stat-number">{{ formattedValue }}</p>
      <p v-if="changeLabel" class="stat-label">{{ changeLabel }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

// 自定义趋势图标
const TrendingUp = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>`
}

const TrendingDown = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>`
}

interface Props {
  title: string
  value: number | string
  icon: any
  color?: 'primary' | 'success' | 'warning' | 'danger'
  change?: number
  changeLabel?: string
  loading?: boolean
  delay?: number
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  loading: false,
  delay: 0
})

const isPositive = computed(() => props.change !== undefined && props.change >= 0)

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})
</script>

<style scoped>
.stat-card {
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

/* 边框颜色 */
.border-primary {
  border-color: rgba(10, 125, 245, 0.2) !important;
}

.border-success {
  border-color: rgba(16, 185, 129, 0.2) !important;
}

.border-warning {
  border-color: rgba(245, 158, 11, 0.2) !important;
}

.border-danger {
  border-color: rgba(239, 68, 68, 0.2) !important;
}

.stat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图标颜色 */
.icon-primary {
  background: rgba(10, 125, 245, 0.2);
  color: #0a7df5;
}

.icon-success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.icon-warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.icon-danger {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.stat-change {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
}

.change-up {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.change-down {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.stat-body {
  /* 内容区域 */
}

.stat-title {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.is-loading {
  font-size: 24px;
  color: var(--accent-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-value {
    font-size: 1.5rem;
  }
}
</style>
