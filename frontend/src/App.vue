<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

// 初始化主题设置
const initTheme = () => {
  // 加载主题模式
  const savedTheme = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-theme', savedTheme)
  // 同时添加/移除类名以支持CSS选择器
  if (savedTheme === 'light') {
    document.documentElement.classList.add('light-theme')
    document.documentElement.classList.remove('dark-theme')
  } else {
    document.documentElement.classList.add('dark-theme')
    document.documentElement.classList.remove('light-theme')
  }

  // 加载强调色
  const savedAccent = localStorage.getItem('accent-color') || 'blue'
  document.documentElement.setAttribute('data-accent', savedAccent)
}

// 初始化用户信息和主题
onMounted(async () => {
  initTheme()
  await userStore.init()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
}

#app {
  color: var(--text-primary);
}
</style>
