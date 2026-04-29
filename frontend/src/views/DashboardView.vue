<template>
  <div class="min-h-screen p-6">
    <!-- 页面头部 -->
    <div class="mb-6 animate-fade-in">
      <div>
        <h2 class="text-2xl font-bold gradient-text">总览</h2>
        <p class="text-sm text-dark-400 mt-2">{{ greeting }}</p>
      </div>
    </div>

    <!-- 核心统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5 mb-6">
      <StatCard 
        title="管理人总数" 
        :value="managerStats.total" 
        :icon="OfficeBuilding" 
        color="primary" 
        :loading="loading"
        :delay="0"
      />
      <StatCard 
        title="产品数量" 
        :value="productCount" 
        :icon="Briefcase" 
        color="success" 
        :loading="loading"
        :delay="100"
      />
      <StatCard 
        title="一级项目" 
        :value="projectStats.total" 
        :icon="FolderOpened" 
        color="warning" 
        :loading="loading"
        :delay="200"
      />
      <StatCard 
        title="在投池" 
        :value="getPoolCount('invested')" 
        :icon="Star" 
        color="success"
        :loading="loading"
        :delay="300"
      />
      <StatCard 
        title="重点跟踪" 
        :value="getPoolCount('key_tracking')" 
        :icon="View" 
        color="warning" 
        :loading="loading"
        :delay="400"
      />
      <StatCard 
        title="观察池" 
        :value="getPoolCount('observation')" 
        :icon="Clock" 
        color="primary" 
        :loading="loading"
        :delay="500"
      />
    </div>

    <!-- 组合总览 + 预警摘要 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- 组合总览 -->
      <div class="glass-card p-5 lg:col-span-2 animate-slide-up" style="animation-delay: 300ms">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold section-title">FOF组合总览</h3>
          <a href="/portfolios" class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
            管理组合
            <el-icon><ArrowRight /></el-icon>
          </a>
        </div>
        <div v-if="portfolios.length === 0" class="text-center" style="padding: 30px; color: var(--text-secondary)">
          暂无组合数据，请前往组合管理创建
        </div>
        <div v-else class="portfolio-cards">
          <div
            v-for="pf in portfolios"
            :key="pf.id"
            class="portfolio-card"
            @click="navigateTo('/portfolios')"
          >
            <div class="pf-header">
              <span class="pf-name">{{ pf.name }}</span>
              <el-tag size="small" :type="pf.portfolio_type === 'invested' ? 'success' : 'info'">
                {{ pf.portfolio_type === 'invested' ? '已投' : '模拟' }}
              </el-tag>
            </div>
            <div class="pf-metrics">
              <div class="pf-metric">
                <span class="pf-metric-label">最新净值</span>
                <span class="pf-metric-value">{{ pf.latest_nav?.toFixed(4) || '-' }}</span>
              </div>
              <div class="pf-metric">
                <span class="pf-metric-label">累计收益</span>
                <span class="pf-metric-value" :class="getReturnClass(pf.total_return)">
                  {{ pf.total_return != null ? (pf.total_return >= 0 ? '+' : '') + (pf.total_return * 100).toFixed(2) + '%' : '-' }}
                </span>
              </div>
              <div class="pf-metric">
                <span class="pf-metric-label">成分数</span>
                <span class="pf-metric-value">{{ pf.component_count || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 组合净值对比 -->
      <div class="glass-card p-5 lg:col-span-3 animate-slide-up" style="animation-delay: 320ms">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold section-title">组合净值对比</h3>
          <el-radio-group v-model="navPeriod" size="small" @change="fetchPortfolioNavs">
            <el-radio-button value="3m">近3月</el-radio-button>
            <el-radio-button value="6m">近6月</el-radio-button>
            <el-radio-button value="1y">近1年</el-radio-button>
            <el-radio-button value="inception">成立以来</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="navCompareChartRef" style="height: 300px" v-loading="loadingNavCompare"></div>
        <!-- 关键指标对比表 -->
        <div v-if="portfolioPerfs.length" style="margin-top: 16px; overflow-x: auto">
          <table class="perf-compare-table">
            <thead>
              <tr>
                <th>组合</th>
                <th>类型</th>
                <th>最新净值</th>
                <th>区间收益</th>
                <th>年化收益</th>
                <th>年化波动</th>
                <th>最大回撤</th>
                <th>夏普比率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pf in portfolioPerfs" :key="pf.id">
                <td class="font-medium">{{ pf.name }}</td>
                <td><el-tag size="small" :type="pf.type === 'invested' ? 'success' : 'info'">{{ pf.type === 'invested' ? '已投' : '模拟' }}</el-tag></td>
                <td>{{ pf.nav ?? '-' }}</td>
                <td :class="getPerfClass(pf.total_return)">{{ formatPct(pf.total_return) }}</td>
                <td :class="getPerfClass(pf.annualized_return)">{{ formatPct(pf.annualized_return) }}</td>
                <td>{{ formatPct(pf.volatility) }}</td>
                <td class="text-red-400">{{ formatPct(pf.max_drawdown) }}</td>
                <td>{{ pf.sharpe != null ? pf.sharpe.toFixed(2) : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 预警 + 跟踪池 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- 预警摘要 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 350ms">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold section-title">预警摘要</h3>
          <a href="/alerts" class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </a>
        </div>
        <!-- 预警统计 -->
        <div class="alert-stats">
          <div class="alert-stat critical">
            <span class="alert-stat-count">{{ alertSummary.by_level?.critical || 0 }}</span>
            <span class="alert-stat-label">严重</span>
          </div>
          <div class="alert-stat warning">
            <span class="alert-stat-count">{{ alertSummary.by_level?.warning || 0 }}</span>
            <span class="alert-stat-label">警告</span>
          </div>
          <div class="alert-stat info">
            <span class="alert-stat-count">{{ alertSummary.by_level?.info || 0 }}</span>
            <span class="alert-stat-label">提示</span>
          </div>
        </div>
        <!-- 最新预警 -->
        <div class="alert-list">
          <div
            v-for="(alert, idx) in recentAlerts"
            :key="idx"
            class="alert-item-mini"
            :class="alert.level"
          >
            <div class="alert-dot" :class="alert.level"></div>
            <div class="alert-mini-content">
              <span class="alert-mini-product">{{ alert.product_name }}</span>
              <span class="alert-mini-msg">{{ alert.title }}</span>
            </div>
            <span class="alert-mini-date">{{ alert.date }}</span>
          </div>
          <div v-if="recentAlerts.length === 0" class="text-center" style="padding: 20px; color: var(--text-secondary); font-size: 13px">
            暂无预警信息
          </div>
        </div>
      </div>

      <!-- 跟踪池分布 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 400ms">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold section-title">跟踪池分布</h3>
        </div>
        <div class="pool-stats">
          <div 
            v-for="pool in POOL_CATEGORY_OPTIONS" 
            :key="pool.value" 
            class="pool-item"
            @click="navigateTo('/managers?pool=' + pool.value)"
          >
            <div class="pool-bar" :style="{ width: getPoolPercent(pool.value) + '%', backgroundColor: pool.color }"></div>
            <div class="pool-info">
              <div class="pool-left">
                <div class="pool-dot" :style="{ backgroundColor: pool.color }"></div>
                <span class="pool-label">{{ pool.label }}</span>
              </div>
              <span class="pool-count stat-number">{{ getPoolCount(pool.value) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 项目阶段分布 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 500ms">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold section-title">项目阶段分布</h3>
        </div>
        <div class="pool-stats">
          <div 
            v-for="stage in PROJECT_STAGE_OPTIONS" 
            :key="stage.value" 
            class="pool-item"
            @click="navigateTo('/projects?stage=' + stage.value)"
          >
            <div class="pool-bar" :style="{ width: getStagePercent(stage.value) + '%', backgroundColor: stage.color }"></div>
            <div class="pool-info">
              <div class="pool-left">
                <div class="pool-dot" :style="{ backgroundColor: stage.color }"></div>
                <span class="pool-label">{{ stage.label }}</span>
              </div>
              <span class="pool-count stat-number">{{ projectStats.by_stage[stage.value] || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 策略分布 + 最近日程 + 舆情动态 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- 策略分布 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 510ms">
        <h3 class="text-lg font-semibold section-title mb-4">策略分布</h3>
        <div ref="strategyPieRef" style="height: 260px" v-show="hasStrategyData"></div>
        <div v-if="!hasStrategyData" class="text-center" style="padding: 40px 0; color: var(--text-secondary); font-size: 13px">暂无策略数据</div>
      </div>

      <!-- 最近日程 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 530ms">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold section-title">最近日程（14天）</h3>
          <el-button type="primary" size="small" @click="openEventDialog()">添加日程</el-button>
        </div>
        <div v-loading="calendarLoading">
          <div v-if="upcomingEvents.length === 0" class="text-center" style="padding: 40px 0; color: var(--text-secondary); font-size: 13px">近期无日程</div>
          <div v-else class="calendar-list">
            <div v-for="ev in upcomingEvents" :key="ev.id" class="calendar-item" @click="openEventDialog(ev)" style="cursor: pointer">
              <div class="calendar-date-box">
                <div class="cal-day">{{ getDayNum(ev.event_date) }}</div>
                <div class="cal-month">{{ getMonthLabel(ev.event_date) }}</div>
              </div>
              <div class="calendar-body">
                <div class="cal-title"><span class="cal-dot" :style="{ background: ev.color || '#409EFF' }"></span>{{ ev.title }}</div>
                <div class="cal-meta">
                  <el-tag size="small" :type="getEventTag(ev.event_type)">{{ getEventLabel(ev.event_type) }}</el-tag>
                  <span v-if="ev.start_time" class="cal-time">{{ ev.start_time }}{{ ev.end_time ? ' - ' + ev.end_time : '' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 舆情动态 -->
      <div class="glass-card p-5 animate-slide-up" style="animation-delay: 550ms">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold section-title">舆情动态</h3>
          <a href="/managers" class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">更多<el-icon><ArrowRight /></el-icon></a>
        </div>
        <div v-loading="sentimentLoading">
          <div v-if="recentNews.length === 0" class="text-center" style="padding: 40px 0; color: var(--text-secondary); font-size: 13px">暂无舆情</div>
          <div v-else class="news-list">
            <div v-for="a in recentNews" :key="a.id" class="news-item">
              <div class="news-header">
                <el-tag size="small" :type="sentimentTagType(a.sentiment)">{{ sentimentText(a.sentiment) }}</el-tag>
                <el-tag v-if="a.is_alert" type="danger" size="small" effect="dark">预警</el-tag>
              </div>
              <div class="news-title">{{ a.title }}</div>
              <div class="news-sub">
                <span v-if="a.manager_name" class="text-primary-400">{{ a.manager_name }}</span>
                <span>{{ a.source || '' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 一级项目快速统计 -->
    <div class="glass-card p-5 mb-6 animate-slide-up" style="animation-delay: 600ms">
      <div class="flex items-center justify-between mb-5">
        <h3 class="text-lg font-semibold section-title">一级项目概览</h3>
        <a href="/projects" class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </a>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="overview-stat-card rounded-xl p-5 text-center">
          <p class="text-2xl font-bold stat-value stat-number">{{ projectStats.total }}</p>
          <p class="text-sm stat-label mt-1">项目总数</p>
        </div>
        <div class="overview-stat-card rounded-xl p-5 text-center">
          <p class="text-2xl font-bold text-emerald-400 stat-number">{{ projectStats.by_stage['post_investment'] || 0 }}</p>
          <p class="text-sm stat-label mt-1">已投资</p>
        </div>
        <div class="overview-stat-card rounded-xl p-5 text-center">
          <p class="text-2xl font-bold text-amber-400 stat-number">{{ projectStats.by_stage['due_diligence'] || 0 }}</p>
          <p class="text-sm stat-label mt-1">尽调中</p>
        </div>
        <div class="overview-stat-card rounded-xl p-5 text-center">
          <p class="text-2xl font-bold text-primary-400 stat-number">{{ projectStats.by_stage['screening'] || 0 }}</p>
          <p class="text-sm stat-label mt-1">初筛中</p>
        </div>
      </div>
    </div>

    <!-- 我的待办 -->
    <div class="glass-card p-5 mb-6 animate-slide-up" style="animation-delay: 650ms">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold section-title">我的待办</h3>
        <a href="/tasks" class="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1">
          全部任务
          <el-icon><ArrowRight /></el-icon>
        </a>
      </div>
      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="overview-stat-card rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-amber-400 stat-number">{{ taskStats.my_pending }}</p>
          <p class="text-sm stat-label mt-1">我的待办</p>
        </div>
        <div class="overview-stat-card rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-red-400 stat-number">{{ taskStats.overdue }}</p>
          <p class="text-sm stat-label mt-1">已逾期</p>
        </div>
        <div class="overview-stat-card rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-emerald-400 stat-number">{{ taskStats.completed }}</p>
          <p class="text-sm stat-label mt-1">已完成</p>
        </div>
      </div>
      <div v-if="myTasks.length">
        <div v-for="t in myTasks" :key="t.id" class="flex items-center gap-3 py-2 border-b border-dark-700 last:border-0" style="cursor:pointer" @click="navigateTo('/tasks')">
          <el-tag :type="t.priority === 'urgent' ? 'danger' : t.priority === 'high' ? 'warning' : 'info'" size="small" effect="dark" round>
            {{ { urgent: '紧急', high: '高', medium: '中', low: '低' }[t.priority] || t.priority }}
          </el-tag>
          <span class="flex-1 text-sm truncate">{{ t.title }}</span>
          <span class="text-xs text-dark-400">{{ t.due_date || '' }}</span>
        </div>
      </div>
      <div v-else class="text-center" style="padding: 20px; color: var(--text-secondary); font-size: 13px">
        暂无待办任务
      </div>
    </div>

    <!-- 日历事件对话框 -->
    <el-dialog v-model="eventDialogVisible" :title="editingEvent ? '编辑日程' : '添加日程'" width="520px">
      <el-form :model="eventForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="eventForm.title" placeholder="事件标题" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="日期" required>
              <el-date-picker v-model="eventForm.event_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="eventForm.event_type" style="width: 100%">
                <el-option value="meeting" label="会议" />
                <el-option value="deadline" label="截止" />
                <el-option value="review" label="评审" />
                <el-option value="report" label="报告" />
                <el-option value="other" label="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-time-select v-model="eventForm.start_time" :start="'08:00'" :step="'00:30'" :end="'22:00'" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-time-select v-model="eventForm.end_time" :start="'08:00'" :step="'00:30'" :end="'22:00'" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="颜色">
          <el-color-picker v-model="eventForm.color" :predefine="['#409EFF','#67C23A','#E6A23C','#F56C6C','#909399']" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="eventForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="eventDialogVisible = false">取消</el-button>
        <el-button v-if="editingEvent" type="danger" @click="handleDeleteEvent">删除</el-button>
        <el-button type="primary" @click="handleSaveEvent" :loading="eventSaving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 快速入口 -->
    <div class="quick-links animate-slide-up" style="animation-delay: 700ms">
      <h3>快速入口</h3>
      <div class="quick-links-grid">
        <div class="quick-link-card glass-card" @click="navigateTo('/managers')">
          <div class="quick-link-icon primary">
            <el-icon :size="32"><OfficeBuilding /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>管理人管理</h4>
            <p>跟踪池管理与分析</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/portfolios')">
          <div class="quick-link-icon primary">
            <el-icon :size="32"><TrendCharts /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>组合管理</h4>
            <p>FOF组合分析与归因</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/products')">
          <div class="quick-link-icon success">
            <el-icon :size="32"><Briefcase /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>产品管理</h4>
            <p>基金产品信息管理</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/projects')">
          <div class="quick-link-icon warning">
            <el-icon :size="32"><FolderOpened /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>一级项目</h4>
            <p>股权投资项目管理</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/ai-reports')">
          <div class="quick-link-icon success">
            <el-icon :size="32"><MagicStick /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>AI智能报告</h4>
            <p>一键生成分析报告</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/alerts')">
          <div class="quick-link-icon danger">
            <el-icon :size="32"><Bell /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>异常预警</h4>
            <p>监控风险与异常</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/nav-import')">
          <div class="quick-link-icon warning">
            <el-icon :size="32"><Upload /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>净值导入</h4>
            <p>导入产品净值数据</p>
          </div>
        </div>
        <div class="quick-link-card glass-card" @click="navigateTo('/attribution')">
          <div class="quick-link-icon primary">
            <el-icon :size="32"><DataAnalysis /></el-icon>
          </div>
          <div class="quick-link-text">
            <h4>因子归因</h4>
            <p>Barra多因子分析</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import { managerApi } from '@/api/manager'
import { productApi } from '@/api/product'
import { projectApi } from '@/api/project'
import { portfolioApi } from '@/api/portfolio'
import request from '@/api/request'
import { taskApi } from '@/api/task'
import type { TaskItem, TaskStats as TStats } from '@/api/task'
import StatCard from '@/components/common/StatCard.vue'
import { OfficeBuilding, Briefcase, Upload, FolderOpened, Star, View, Clock, ArrowRight, TrendCharts, MagicStick, Bell, DataAnalysis } from '@element-plus/icons-vue'
import { POOL_CATEGORY_OPTIONS } from '@/types/manager'
import { PROJECT_STAGE_OPTIONS } from '@/types/project'
import type { ManagerStatistics, PoolCategory } from '@/types/manager'
import type { ProjectStats, ProjectStage } from '@/types/project'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const managerStats = ref<ManagerStatistics>({ total: 0, by_pool: [], by_strategy: {} })
const productCount = ref(0)
const projectStats = ref<ProjectStats>({ total: 0, by_stage: {}, by_industry: {}, total_investment: 0 })

// 组合总览
const portfolios = ref<any[]>([])

// 组合净值对比
const navPeriod = ref('6m')
const loadingNavCompare = ref(false)
const navCompareChartRef = ref<HTMLElement>()
let navCompareChart: echarts.ECharts | null = null
const portfolioPerfs = ref<any[]>([])
const PORTFOLIO_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

// 待办任务
const taskStats = ref<TStats>({ total: 0, pending: 0, in_progress: 0, completed: 0, my_pending: 0, overdue: 0 })
const myTasks = ref<TaskItem[]>([])

// 预警摘要
const alertSummary = ref<any>({})
const recentAlerts = computed(() => {
  const alerts = alertSummary.value.alerts || []
  return alerts.slice(0, 5)
})

// 中国A股习惯：红涨绿跌
const getReturnClass = (v: number | null | undefined) => {
  if (v == null) return ''
  return v >= 0 ? 'text-red-400' : 'text-emerald-400'
}

const greeting = computed(() => {
  const hour = new Date().getHours()
  let t = hour < 6 ? '凌晨好' : hour < 9 ? '早上好' : hour < 12 ? '上午好' : hour < 14 ? '中午好' : hour < 18 ? '下午好' : hour < 22 ? '晚上好' : '夜深了'
  return `${t}，${userStore.userInfo?.real_name || userStore.username}！一站式查看管理人与项目整体表现`
})

const getPoolCount = (pool: PoolCategory) => managerStats.value.by_pool?.find(p => p.category === pool)?.count || 0
const getPoolPercent = (pool: PoolCategory) => managerStats.value.total ? Math.round(getPoolCount(pool) / managerStats.value.total * 100) : 0
const getStagePercent = (stage: ProjectStage) => projectStats.value.total ? Math.round((projectStats.value.by_stage[stage] || 0) / projectStats.value.total * 100) : 0

const fetchStatistics = async () => {
  loading.value = true
  try {
    // 使用Dashboard聚合API，一次请求获取所有数据
    const data = await request.get('/dashboard/summary')
    
    // 更新各个状态
    managerStats.value = data.manager_stats
    productCount.value = data.product_stats.total
    projectStats.value = data.project_stats
    portfolios.value = data.portfolios
    taskStats.value = data.task_stats
    alertSummary.value = data.alert_summary
    
    await nextTick()
    renderStrategyPie()
    
    // 如果有组合数据，自动加载净值对比
    if (portfolios.value.length > 0) {
      fetchPortfolioNavs()
    }
  } catch (error) { 
    console.error('获取统计数据失败:', error) 
  } finally { 
    loading.value = false 
  }
}

const fetchPortfolios = async () => {
  // 组合数据已在 fetchStatistics 中获取，无需单独请求
  if (portfolios.value.length > 0) {
    await nextTick()
    fetchPortfolioNavs()
  }
}

const getPeriodStart = (period: string): string | undefined => {
  if (period === 'inception') return undefined
  const d = new Date()
  if (period === '3m') d.setMonth(d.getMonth() - 3)
  else if (period === '6m') d.setMonth(d.getMonth() - 6)
  else if (period === '1y') d.setFullYear(d.getFullYear() - 1)
  return d.toISOString().slice(0, 10)
}

const fetchPortfolioNavs = async () => {
  if (!portfolios.value.length) return
  loadingNavCompare.value = true
  try {
    console.log('正在获取组合净值对比，周期:', navPeriod.value)
    
    // 使用优化的组合净值对比API
    const data = await request.get('/dashboard/portfolio-nav-compare', {
      params: { period: navPeriod.value }
    })
    
    console.log('组合净值对比数据:', data)
    
    // 更新绩效对比数据
    portfolioPerfs.value = Object.values(data.performance || {})
    
    // 渲染净值对比图
    renderNavCompareChart(data.nav_series)
  } catch (e) {
    console.error('获取组合净值对比失败:', e)
  } finally {
    loadingNavCompare.value = false
  }
}

const renderNavCompareChart = (navSeries: any) => {
  if (!navCompareChartRef.value) return
  if (navCompareChart) navCompareChart.dispose()
  navCompareChart = echarts.init(navCompareChartRef.value)

  const series: any[] = []
  let allDates: string[] = []

  Object.values(navSeries || {}).forEach((data: any, i: number) => {
    if (!data || !data.dates?.length) return
    
    const dates = data.dates
    const values = data.values
    
    if (dates.length > allDates.length) allDates = dates
    
    series.push({
      name: data.name,
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: PORTFOLIO_COLORS[i % PORTFOLIO_COLORS.length] },
      itemStyle: { color: PORTFOLIO_COLORS[i % PORTFOLIO_COLORS.length] }
    })
  })

  if (!series.length) {
    // 如果没有数据，显示空状态
    navCompareChart.setOption({
      title: {
        text: '暂无组合净值数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#94a3b8',
          fontSize: 14
        }
      }
    })
    return
  }

  navCompareChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.9)',
      borderColor: 'rgba(59,130,246,0.3)',
      textStyle: { color: '#fff', fontSize: 12 },
    },
    legend: {
      data: series.map(s => s.name),
      textStyle: { color: '#94a3b8', fontSize: 12 },
      top: 0,
    },
    grid: { left: '3%', right: '3%', bottom: '3%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: allDates,
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#1e293b' } },
      min: (value: any) => (value.min * 0.995).toFixed(4),
    },
    series,
  })
  
  // 确保图表正确渲染
  setTimeout(() => {
    if (navCompareChart) {
      navCompareChart.resize()
    }
  }, 100)
}

const formatPct = (v: number | null | undefined) => {
  if (v == null) return '-'
  return (Number(v) * 100).toFixed(2) + '%'
}

// 中国A股习惯：红涨绿跌
const getPerfClass = (v: number | null | undefined) => {
  if (v == null) return ''
  return Number(v) >= 0 ? 'text-red-400' : 'text-emerald-400'
}

const fetchAlerts = async () => {
  // 预警数据已在 fetchStatistics 中获取，无需单独请求
}

const fetchTaskData = async () => {
  // 任务数据已在 fetchStatistics 中获取，只需获取任务列表
  try {
    const list = await taskApi.getList({ my_tasks: true, page: 1, page_size: 5 })
    myTasks.value = list.items || []
  } catch { /* 静默 */ }
}

const navigateTo = (path: string) => router.push(path)

// ---- 策略分布饼图 ----
const strategyPieRef = ref<HTMLElement>()
let strategyPieChart: echarts.ECharts | null = null
const hasStrategyData = computed(() => {
  const obj = managerStats.value?.by_strategy || {}
  return Object.keys(obj).length > 0 && Object.values(obj).some((v: any) => Number(v) > 0)
})
const renderStrategyPie = () => {
  if (!strategyPieRef.value || !hasStrategyData.value) return
  if (strategyPieChart) strategyPieChart.dispose()
  strategyPieChart = echarts.init(strategyPieRef.value)
  const data = Object.entries(managerStats.value.by_strategy || {})
    .filter(([, v]) => Number(v) > 0)
    .map(([k, v]) => ({ name: k, value: Number(v) }))
  strategyPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '42%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: { label: { show: true, fontWeight: 'bold', color: '#e2e8f0' } },
      data,
    }]
  })
}

// ---- 日历事件 ----
const calendarLoading = ref(false)
const upcomingEvents = ref<any[]>([])
const getDayNum = (d: string) => { try { return String(new Date(d).getDate()).padStart(2, '0') } catch { return '' } }
const getMonthLabel = (d: string) => { try { return (new Date(d).getMonth() + 1) + '月' } catch { return '' } }
const getEventLabel = (t?: string) => ({ meeting: '会议', deadline: '截止', review: '评审', report: '报告', other: '其他' } as Record<string, string>)[t || 'other'] || '其他'
const getEventTag = (t?: string) => ({ meeting: 'success', deadline: 'danger', review: 'warning', report: '', other: 'info' } as Record<string, string>)[t || 'other'] || 'info'
const fetchCalendar = async () => {
  calendarLoading.value = true
  try {
    const now = new Date()
    const start = now.toISOString().slice(0, 10)
    const end = new Date(now.getTime() + 14 * 86400000).toISOString().slice(0, 10)
    const res = await request.get('/calendar', { params: { start_date: start, end_date: end } })
    upcomingEvents.value = (res.data?.items || res.items || []).slice(0, 6)
  } catch { /* 静默 */ }
  finally { calendarLoading.value = false }
}

// ---- 日历事件管理 ----
const eventDialogVisible = ref(false)
const editingEvent = ref<any>(null)
const eventSaving = ref(false)
const eventForm = reactive({
  title: '',
  event_date: '',
  event_type: 'meeting',
  start_time: '',
  end_time: '',
  color: '#409EFF',
  description: '',
})

const openEventDialog = (ev?: any) => {
  editingEvent.value = ev || null
  if (ev) {
    Object.assign(eventForm, { title: ev.title, event_date: ev.event_date, event_type: ev.event_type || 'meeting', start_time: ev.start_time || '', end_time: ev.end_time || '', color: ev.color || '#409EFF', description: ev.description || '' })
  } else {
    Object.assign(eventForm, { title: '', event_date: new Date().toISOString().slice(0, 10), event_type: 'meeting', start_time: '', end_time: '', color: '#409EFF', description: '' })
  }
  eventDialogVisible.value = true
}

const handleSaveEvent = async () => {
  if (!eventForm.title || !eventForm.event_date) { ElMessage.warning('请填写标题和日期'); return }
  eventSaving.value = true
  try {
    if (editingEvent.value) {
      await request.put(`/calendar/${editingEvent.value.id}`, eventForm)
      ElMessage.success('日程已更新')
    } else {
      await request.post('/calendar', eventForm)
      ElMessage.success('日程已添加')
    }
    eventDialogVisible.value = false
    fetchCalendar()
  } catch (e: any) { ElMessage.error(e.message || '保存失败') } finally { eventSaving.value = false }
}

const handleDeleteEvent = async () => {
  if (!editingEvent.value) return
  await ElMessageBox.confirm('确定删除该日程？', '提示', { type: 'warning' })
  try {
    await request.delete(`/calendar/${editingEvent.value.id}`)
    ElMessage.success('已删除')
    eventDialogVisible.value = false
    fetchCalendar()
  } catch { /* handled */ }
}

// ---- 舞情动态 ----
const sentimentLoading = ref(false)
const recentNews = ref<any[]>([])
const sentimentText = (s?: string) => ({ positive: '正面', neutral: '中性', negative: '负面' } as Record<string, string>)[s || 'neutral'] || '中性'
const sentimentTagType = (s?: string) => ({ positive: 'success', neutral: 'info', negative: 'danger' } as Record<string, string>)[s || 'neutral'] || 'info'
const fetchSentiments = async () => {
  sentimentLoading.value = true
  try {
    const res = await request.get('/sentiment/articles', { params: { page: 1, page_size: 5 } })
    recentNews.value = res.data?.items || res.items || []
  } catch { /* 静默 */ }
  finally { sentimentLoading.value = false }
}

onMounted(() => {
  // 优化：只调用一次聚合API获取所有数据
  fetchStatistics()
  fetchTaskData()  // 获取任务列表
  fetchCalendar()  // 日历可以延迟加载
  fetchSentiments()  // 舆情可以延迟加载
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.page-header .subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 主要内容区 */
.main-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.view-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.875rem;
  color: var(--accent-color);
  text-decoration: none;
  transition: color 0.2s;
}

.view-all:hover {
  color: rgba(var(--accent-primary-light), 1);
}

/* 跟踪池统计 */
.pool-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pool-item {
  position: relative;
  padding: 14px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.pool-item:hover {
  background: rgba(var(--accent-primary), 0.1);
}

.pool-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  opacity: 0.2;
  transition: width 0.5s ease;
}

.pool-info {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pool-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pool-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.pool-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.pool-count {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* 组合总览 */
.portfolio-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.portfolio-card {
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.portfolio-card:hover {
  background: rgba(var(--accent-primary), 0.1);
  transform: translateY(-2px);
}

.pf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.pf-name {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.pf-metrics {
  display: flex;
  gap: 16px;
}

.pf-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pf-metric-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.pf-metric-value {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* 预警摘要 */
.alert-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.alert-stat {
  flex: 1;
  text-align: center;
  padding: 10px 8px;
  border-radius: 8px;
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
}

.alert-stat-count {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
}

.alert-stat.critical .alert-stat-count { color: #f56c6c; }
.alert-stat.warning .alert-stat-count { color: #e6a23c; }
.alert-stat.info .alert-stat-count { color: #909399; }

.alert-stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alert-item-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--hover-bg);
  font-size: 0.8125rem;
}

.alert-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.alert-dot.critical { background: #f56c6c; }
.alert-dot.warning { background: #e6a23c; }
.alert-dot.info { background: #909399; }

.alert-mini-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-mini-product {
  color: var(--text-primary);
  font-weight: 500;
  margin-right: 6px;
}

.alert-mini-msg {
  color: var(--text-secondary);
}

.alert-mini-date {
  font-size: 0.75rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* 项目概览 */
.project-overview {
  padding: 20px;
  margin-bottom: 24px;
}

.project-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .project-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.project-stat-item {
  background: var(--hover-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.project-stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.project-stat-item.success .project-stat-value {
  color: var(--color-success);
}

.project-stat-item.warning .project-stat-value {
  color: var(--color-warning);
}

.project-stat-item.primary .project-stat-value {
  color: var(--accent-color);
}

.project-stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 快速入口 */
.quick-links {
  margin-top: 24px;
}

.quick-links h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

.quick-links-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 1024px) {
  .quick-links-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 576px) {
  .quick-links-grid {
    grid-template-columns: 1fr;
  }
}

.quick-link-card {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-link-card:hover {
  transform: translateY(-4px);
}

.quick-link-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-link-icon.primary {
  background: rgba(10, 125, 245, 0.2);
  color: #0a7df5;
}

.quick-link-icon.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.quick-link-icon.warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.quick-link-icon.danger {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.quick-link-text h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.quick-link-text p {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* 组合绩效对比表 */
.perf-compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.perf-compare-table th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  color: var(--text-secondary, #94a3b8);
  border-bottom: 1px solid var(--card-border, rgba(71, 85, 105, 0.3));
  white-space: nowrap;
}

.perf-compare-table td {
  padding: 8px 12px;
  color: var(--text-primary, #fff);
  border-bottom: 1px solid var(--card-border, rgba(71, 85, 105, 0.15));
  white-space: nowrap;
}

.perf-compare-table tbody tr:hover {
  background: rgba(59, 130, 246, 0.05);
}

/* 浅色主题适配 */
.section-title {
  color: var(--text-primary);
}

.stat-value {
  color: var(--text-primary);
}

.stat-label {
  color: var(--text-secondary);
}

.overview-stat-card {
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
}

.overview-stat-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

:global(.light-theme) .overview-stat-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
}

:global(.light-theme) .section-title {
  color: #1e293b;
}

:global(.light-theme) .stat-value {
  color: #1e293b;
}

:global(.light-theme) .stat-label {
  color: #6b7280;
}

/* 日历事件列表 */
.calendar-list { display: flex; flex-direction: column; gap: 10px; }
.calendar-item {
  display: flex; gap: 12px; padding: 10px 12px;
  border: 1px solid var(--card-border); border-radius: 10px; background: var(--hover-bg);
  transition: background 0.2s;
}
.calendar-item:hover { background: rgba(var(--accent-primary), 0.08); }
.calendar-date-box { width: 48px; text-align: center; flex-shrink: 0; }
.cal-day { font-size: 1.375rem; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
.cal-month { font-size: 0.6875rem; color: var(--text-secondary); }
.calendar-body { flex: 1; min-width: 0; }
.cal-title {
  font-weight: 600; color: var(--text-primary); font-size: 0.875rem;
  display: flex; align-items: center; gap: 6px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cal-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.cal-meta { margin-top: 4px; display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: var(--text-secondary); }
.cal-time { font-variant-numeric: tabular-nums; }

/* 舆情动态 */
.news-list { display: flex; flex-direction: column; gap: 10px; }
.news-item {
  padding: 10px 12px; border: 1px solid var(--card-border); border-radius: 10px;
  background: var(--hover-bg); transition: background 0.2s;
}
.news-item:hover { background: rgba(var(--accent-primary), 0.08); }
.news-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.news-title {
  font-size: 0.875rem; font-weight: 500; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.news-sub { font-size: 0.75rem; color: var(--text-secondary); display: flex; gap: 8px; margin-top: 2px; }
</style>
