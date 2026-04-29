/**
 * 路由相关类型定义
 */

import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    // 是否需要认证，默认true
    requiresAuth?: boolean
    // 页面标题
    title?: string
    // 允许访问的角色列表
    roles?: string[]
    // 图标
    icon?: string
    // 是否在菜单中隐藏
    hidden?: boolean
  }
}

export {}
