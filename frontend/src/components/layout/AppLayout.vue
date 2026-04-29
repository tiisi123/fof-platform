<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="app-sidebar glass-card" :class="{ collapsed: isCollapsed }">
      <AppSidebar :is-collapsed="isCollapsed" @toggle="toggleSidebar" />
    </aside>

    <!-- 主内容区 -->
    <main class="app-main" :class="{ 'sidebar-collapsed': isCollapsed }">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <AiCopilot />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AiCopilot from '@/components/ai/AiCopilot.vue'

// 侧边栏折叠状态
const isCollapsed = ref(false)

// 切换侧边栏
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 响应式处理
const handleResize = () => {
  const width = window.innerWidth
  if (width < 768) {
    isCollapsed.value = true
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
}

.app-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 240px;
  z-index: 100;
  transition: width 0.3s ease;
  border-radius: 0 !important;
  border-left: none !important;
  border-top: none !important;
  border-bottom: none !important;
}

.app-sidebar.collapsed {
  width: 72px;
}

.app-main {
  flex: 1;
  margin-left: 240px;
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.app-main.sidebar-collapsed {
  margin-left: 72px;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .app-sidebar {
    width: 72px;
  }
  
  .app-main {
    margin-left: 72px;
  }
}
</style>
