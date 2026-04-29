import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      requiresAuth: false,
      title: '登录'
    }
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          title: '首页'
        }
      },
      {
        path: 'managers',
        name: 'Managers',
        component: () => import('@/views/ManagerView.vue'),
        meta: {
          title: '管理人管理'
        }
      },
      {
        path: 'managers/:id',
        name: 'ManagerDetail',
        component: () => import('@/views/ManagerDetailView.vue'),
        meta: {
          title: '管理人详情'
        }
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/ProductView.vue'),
        meta: {
          title: '产品管理'
        }
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/ProductDetailView.vue'),
        meta: {
          title: '产品详情'
        }
      },
      {
        path: 'nav-import',
        name: 'NavImport',
        component: () => import('@/views/NavImportView.vue'),
        meta: {
          title: '净值导入'
        }
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('@/views/AnalysisView.vue'),
        meta: {
          title: '产品分析'
        }
      },
      {
        path: 'portfolios',
        name: 'Portfolios',
        component: () => import('@/views/PortfolioView.vue'),
        meta: {
          title: '组合管理'
        }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/ProjectView.vue'),
        meta: {
          title: '一级项目'
        }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/UserView.vue'),
        meta: {
          title: '用户管理',
          roles: ['super_admin', 'director']
        }
      },
      {
        path: 'ranking',
        name: 'Ranking',
        component: () => import('@/views/RankingView.vue'),
        meta: {
          title: '市场数据'
        }
      },
      {
        path: 'email-crawler',
        name: 'EmailCrawler',
        component: () => import('@/views/EmailCrawlerView.vue'),
        meta: {
          title: '邮箱爬虫'
        }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/ReportsView.vue'),
        meta: {
          title: '报表中心'
        }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/AlertsView.vue'),
        meta: {
          title: '异常预警'
        }
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/DocumentsView.vue'),
        meta: {
          title: '尽调资料'
        }
      },
      {
        path: 'ai-reports',
        name: 'AIReports',
        component: () => import('@/views/AIReportsView.vue'),
        meta: {
          title: 'AI智能报告'
        }
      },
      {
        path: 'attribution',
        name: 'Attribution',
        component: () => import('@/views/AttributionView.vue'),
        meta: {
          title: '因子归因'
        }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/TaskView.vue'),
        meta: {
          title: '待办任务'
        }
      },
      {
        path: 'audit-log',
        name: 'AuditLog',
        component: () => import('@/views/AuditLogView.vue'),
        meta: {
          title: '审计日志',
          roles: ['super_admin', 'director']
        }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: {
          title: '系统设置'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})


// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - FOF管理平台`
  } else {
    document.title = 'FOF管理平台'
  }

  // 检查是否需要认证
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }

    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch (error) {
        ElMessage.error('登录已过期，请重新登录')
        next('/login')
        return
      }
    }

    if (to.meta.roles) {
      const roles = to.meta.roles as string[]
      if (!userStore.hasAnyRole(roles)) {
        ElMessage.error('无权限访问此页面')
        next(false)
        return
      }
    }

    next()
  } else {
    if (to.path === '/login' && userStore.isLoggedIn) {
      next('/')
    } else {
      next()
    }
  }
})

router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('页面加载失败')
})

export default router
