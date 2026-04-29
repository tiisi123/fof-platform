<template>
  <div class="manager-detail-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="handleBack">返回</el-button>
        <div class="header-info" v-if="manager">
          <h2>{{ manager.manager_name }}</h2>
          <div class="header-tags">
            <el-tag :color="getPoolColor(manager.pool_category)" effect="dark" size="small">{{ getPoolLabel(manager.pool_category) }}</el-tag>
            <el-tag v-if="manager.primary_strategy" size="small" type="info">{{ getStrategyLabel(manager.primary_strategy) }}</el-tag>
            <el-tag v-if="manager.rating && manager.rating !== 'unrated'" :type="getRatingType(manager.rating)" size="small">{{ manager.rating }}</el-tag>
            <el-tag v-for="tag in tags" :key="tag.id" :color="tag.tag_color" effect="plain" size="small" closable @close="handleDeleteTag(tag)">{{ tag.tag_name }}</el-tag>
            <el-button size="small" link type="primary" @click="showTagDialog = true"><el-icon><Plus /></el-icon>标签</el-button>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleEdit">编辑</el-button>
        <el-button @click="handleTransfer">流转</el-button>
      </div>
    </div>

    <!-- 主体Tab -->
    <el-tabs v-model="activeTab" class="detail-tabs" v-loading="loading">
      <!-- Tab 1: 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <div class="tab-content" v-if="manager">
          <el-card class="info-card" shadow="never">
            <template #header><span>机构信息</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="管理人编号">{{ manager.manager_code }}</el-descriptions-item>
              <el-descriptions-item label="管理人名称">{{ manager.manager_name }}</el-descriptions-item>
              <el-descriptions-item label="管理人简称">{{ manager.short_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="备案编号">{{ manager.registration_no || '-' }}</el-descriptions-item>
              <el-descriptions-item label="成立日期">{{ manager.established_date || '-' }}</el-descriptions-item>
              <el-descriptions-item label="注册资本">{{ manager.registered_capital ? manager.registered_capital + '万元' : '-' }}</el-descriptions-item>
              <el-descriptions-item label="实缴资本">{{ manager.paid_capital ? manager.paid_capital + '万元' : '-' }}</el-descriptions-item>
              <el-descriptions-item label="员工人数">{{ manager.employee_count || '-' }}</el-descriptions-item>
              <el-descriptions-item label="管理规模">{{ manager.aum_range || '-' }}</el-descriptions-item>
              <el-descriptions-item label="内部评级">
                <el-tag v-if="manager.rating && manager.rating !== 'unrated'" :type="getRatingType(manager.rating)">{{ manager.rating }}</el-tag>
                <span v-else>未评级</span>
              </el-descriptions-item>
              <el-descriptions-item label="注册地址" :span="2">{{ manager.registered_address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="办公地址" :span="2">{{ manager.office_address || manager.address || '-' }}</el-descriptions-item>
              <el-descriptions-item label="官网" :span="2">
                <el-link v-if="manager.website" :href="manager.website" target="_blank" type="primary">{{ manager.website }}</el-link>
                <span v-else>-</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <template #header><span>策略与合作</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="一级策略">{{ getStrategyLabel(manager.primary_strategy) }}</el-descriptions-item>
              <el-descriptions-item label="二级策略">{{ manager.secondary_strategy || '-' }}</el-descriptions-item>
              <el-descriptions-item label="投资风格">
                <el-tag v-for="s in (manager.investment_style || [])" :key="s" size="small" style="margin-right: 4px">{{ s }}</el-tag>
                <span v-if="!manager.investment_style?.length">-</span>
              </el-descriptions-item>
              <el-descriptions-item label="基准指数">{{ manager.benchmark_index || '-' }}</el-descriptions-item>
              <el-descriptions-item label="合作开始">{{ manager.cooperation_start_date || '-' }}</el-descriptions-item>
              <el-descriptions-item label="合作结束">{{ manager.cooperation_end_date || '-' }}</el-descriptions-item>
              <el-descriptions-item label="备注" :span="2">{{ manager.remark || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 联系人 -->
          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <template #header>
              <div class="card-header-row"><span>联系人</span><el-button size="small" type="primary" link @click="showContactDialog = true"><el-icon><Plus /></el-icon>添加</el-button></div>
            </template>
            <el-table :data="manager.contacts || []" size="small" stripe>
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="position" label="职位" width="120" />
              <el-table-column prop="phone" label="电话" width="140" />
              <el-table-column prop="email" label="邮箱" width="180" />
              <el-table-column prop="wechat" label="微信" width="120" />
              <el-table-column prop="is_primary" label="主要" width="80">
                <template #default="{ row }"><el-tag v-if="row.is_primary" type="success" size="small">是</el-tag></template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="danger" size="small" @click="handleDeleteContact(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 流转历史 -->
          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <template #header><span>流转历史</span></template>
            <el-timeline v-if="transfers.length">
              <el-timeline-item v-for="item in transfers" :key="item.id" :timestamp="formatDateTime(item.created_at)" placement="top">
                <div class="transfer-item">
                  <el-tag size="small" :color="getPoolColor(item.from_pool)" effect="dark">{{ getPoolLabel(item.from_pool) }}</el-tag>
                  <span class="transfer-arrow">→</span>
                  <el-tag size="small" :color="getPoolColor(item.to_pool)" effect="dark">{{ getPoolLabel(item.to_pool) }}</el-tag>
                  <span class="transfer-reason">{{ item.reason }}</span>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无流转记录" :image-size="60" />
          </el-card>

          <!-- 编辑历史 -->
          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <template #header>
              <div class="card-header-row">
                <span>编辑历史</span>
                <el-tag size="small" v-if="editHistory.length">{{ editHistoryTotal }}条记录</el-tag>
              </div>
            </template>
            <el-timeline v-if="groupedEditHistory.length">
              <el-timeline-item v-for="group in groupedEditHistory" :key="group.batch_id" :timestamp="group.time" placement="top" color="#E6A23C">
                <div class="edit-history-group">
                  <div class="edit-operator" v-if="group.operator">{{ group.operator }} 修改了以下字段：</div>
                  <div class="edit-changes">
                    <div v-for="change in group.changes" :key="change.id" class="edit-change-item">
                      <el-tag size="small" type="warning">{{ change.field_label }}</el-tag>
                      <span class="old-val" v-if="change.old_value">{{ change.old_value }}</span>
                      <span class="change-arrow">→</span>
                      <span class="new-val">{{ change.new_value || '(空)' }}</span>
                    </div>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无编辑记录" :image-size="60" />
          </el-card>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 团队信息 -->
      <el-tab-pane label="团队信息" name="team">
        <el-card shadow="never">
          <template #header>
            <div class="card-header-row"><span>核心团队</span><el-button size="small" type="primary" link @click="showTeamDialog = true"><el-icon><Plus /></el-icon>添加</el-button></div>
          </template>
          <el-table :data="manager?.team_members || []" stripe>
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column prop="position" label="职位" width="150" />
            <el-table-column prop="years_of_experience" label="从业年限" width="100">
              <template #default="{ row }">{{ row.years_of_experience ? row.years_of_experience + '年' : '-' }}</template>
            </el-table-column>
            <el-table-column prop="education" label="教育背景" width="200" />
            <el-table-column prop="work_history" label="工作经历" min-width="300" show-overflow-tooltip />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="handleDeleteTeamMember(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Tab 3: 旗下产品 -->
      <el-tab-pane label="旗下产品" name="products">
        <el-card shadow="never">
          <template #header><span>旗下产品 ({{ products.length }})</span></template>
          <el-table :data="products" stripe @row-click="handleProductClick">
            <el-table-column prop="product_code" label="产品代码" width="120" />
            <el-table-column prop="product_name" label="产品名称" min-width="200" />
            <el-table-column prop="strategy_type" label="策略" width="100" />
            <el-table-column prop="latest_nav" label="最新净值" width="110" align="right">
              <template #default="{ row }">{{ row.latest_nav?.toFixed(4) || '-' }}</template>
            </el-table-column>
            <el-table-column prop="latest_nav_date" label="净值日期" width="110" />
            <el-table-column prop="cumulative_return" label="累计收益" width="110" align="right">
              <template #default="{ row }">
                <span v-if="row.cumulative_return != null" :class="row.cumulative_return >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(row.cumulative_return) }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="annualized_return" label="年化收益" width="110" align="right">
              <template #default="{ row }">
                <span v-if="row.annualized_return != null" :class="row.annualized_return >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(row.annualized_return) }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="nav_count" label="净值数" width="80" align="center" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : row.status === 'liquidated' ? 'danger' : 'info'" size="small">{{ row.status === 'active' ? '运行中' : row.status === 'liquidated' ? '已清盘' : row.status || '-' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Tab 4: 业绩汇总 -->
      <el-tab-pane label="业绩汇总" name="performance" lazy>
        <div v-if="perfSummary" class="performance-content">
          <!-- 关键指标卡片 -->
          <div class="perf-cards">
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">产品数量</div>
              <div class="perf-value">{{ perfSummary.active_products }} / {{ perfSummary.total_products }}</div>
              <div class="perf-sub">运行中 / 总计</div>
            </el-card>
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">平均累计收益</div>
              <div class="perf-value" :class="(perfSummary.weighted_cumulative_return || 0) >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(perfSummary.weighted_cumulative_return) }}</div>
            </el-card>
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">平均年化收益</div>
              <div class="perf-value" :class="(perfSummary.weighted_annualized_return || 0) >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(perfSummary.weighted_annualized_return) }}</div>
            </el-card>
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">平均最大回撤</div>
              <div class="perf-value text-red">{{ formatPercent(perfSummary.avg_max_drawdown) }}</div>
            </el-card>
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">平均夏普比率</div>
              <div class="perf-value">{{ perfSummary.avg_sharpe_ratio?.toFixed(2) || '-' }}</div>
            </el-card>
            <el-card shadow="never" class="perf-card">
              <div class="perf-label">平均波动率</div>
              <div class="perf-value">{{ formatPercent(perfSummary.avg_volatility) }}</div>
            </el-card>
          </div>

          <!-- 净值曲线 -->
          <el-card shadow="never" style="margin-top: 20px" v-if="perfSummary.nav_dates.length">
            <template #header><span>归一化净值曲线</span></template>
            <div ref="navChartRef" style="height: 350px"></div>
          </el-card>

          <!-- 产品绩效对比 -->
          <el-card shadow="never" style="margin-top: 20px" v-if="perfSummary.products_comparison.length">
            <template #header><span>产品绩效对比</span></template>
            <div ref="compChartRef" style="height: 350px"></div>
            <el-table :data="perfSummary.products_comparison" stripe size="small" style="margin-top: 15px">
              <el-table-column prop="product_name" label="产品" min-width="200" />
              <el-table-column prop="cumulative_return" label="累计收益" width="110" align="right">
                <template #default="{ row }"><span :class="(row.cumulative_return || 0) >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(row.cumulative_return) }}</span></template>
              </el-table-column>
              <el-table-column prop="annualized_return" label="年化收益" width="110" align="right">
                <template #default="{ row }"><span :class="(row.annualized_return || 0) >= 0 ? 'text-green' : 'text-red'">{{ formatPercent(row.annualized_return) }}</span></template>
              </el-table-column>
              <el-table-column prop="max_drawdown" label="最大回撤" width="110" align="right">
                <template #default="{ row }"><span class="text-red">{{ formatPercent(row.max_drawdown) }}</span></template>
              </el-table-column>
              <el-table-column prop="sharpe_ratio" label="夏普比率" width="100" align="right">
                <template #default="{ row }">{{ row.sharpe_ratio?.toFixed(2) || '-' }}</template>
              </el-table-column>
              <el-table-column prop="volatility" label="波动率" width="100" align="right">
                <template #default="{ row }">{{ formatPercent(row.volatility) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
        <el-empty v-else description="暂无业绩数据" />
      </el-tab-pane>

      <!-- Tab 5: 运营与合规 -->
      <el-tab-pane label="运营合规" name="compliance" lazy>
        <div v-if="manager" class="tab-content">
          <el-card class="info-card" shadow="never">
            <template #header><span>运营情况</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="运营状态">
                <el-tag v-if="manager.operation_status" :type="manager.operation_status === 'normal' ? 'success' : manager.operation_status === 'warning' ? 'warning' : 'danger'" size="small">
                  {{ { normal: '正常', abnormal: '异常', warning: '警告' }[manager.operation_status] || manager.operation_status }}
                </el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="管理规模">
                {{ manager.aum_scale ? manager.aum_scale + '亿元' : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="在管基金数">{{ manager.fund_count || '-' }}</el-descriptions-item>
              <el-descriptions-item label="最近尽调日期">{{ manager.last_inspection_date || '-' }}</el-descriptions-item>
              <el-descriptions-item label="运营备注" :span="2">{{ manager.operation_remark || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <template #header><span>财务与合规</span></template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="合规状态">
                <el-tag v-if="manager.compliance_status" :type="manager.compliance_status === 'compliant' ? 'success' : manager.compliance_status === 'under_review' ? 'warning' : 'danger'" size="small">
                  {{ { compliant: '合规', non_compliant: '不合规', under_review: '审查中' }[manager.compliance_status] || manager.compliance_status }}
                </el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="处罚记录">
                <el-tag v-if="manager.has_penalty" type="danger" size="small">有</el-tag>
                <el-tag v-else type="success" size="small">无</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="处罚详情" :span="2">{{ manager.penalty_details || '-' }}</el-descriptions-item>
              <el-descriptions-item label="最近审计日期">{{ manager.financial_audit_date || '-' }}</el-descriptions-item>
              <el-descriptions-item label="合规备注">{{ manager.compliance_remark || '-' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
          <!-- 讨论 -->
          <el-card class="info-card" shadow="never" style="margin-top: 20px">
            <CommentSection resource-type="manager" :resource-id="managerId" />
          </el-card>
        </div>
      </el-tab-pane>

      <!-- Tab 6: 舆情分析 -->
      <el-tab-pane label="舆情分析" name="sentiment" lazy>
        <div class="sentiment-content">
          <!-- 舆情摘要 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5" v-if="sentimentSummary">
            <el-card shadow="never" class="text-center">
              <div class="text-2xl font-bold">{{ sentimentSummary.total }}</div>
              <div class="text-sm text-dark-400 mt-1">舆情总数</div>
            </el-card>
            <el-card shadow="never" class="text-center">
              <div class="text-2xl font-bold text-emerald-400">{{ sentimentSummary.positive }}</div>
              <div class="text-sm text-dark-400 mt-1">正面</div>
            </el-card>
            <el-card shadow="never" class="text-center">
              <div class="text-2xl font-bold text-amber-400">{{ sentimentSummary.neutral }}</div>
              <div class="text-sm text-dark-400 mt-1">中性</div>
            </el-card>
            <el-card shadow="never" class="text-center">
              <div class="text-2xl font-bold text-red-400">{{ sentimentSummary.negative }}</div>
              <div class="text-sm text-dark-400 mt-1">负面</div>
            </el-card>
          </div>
          <!-- 关键词 -->
          <el-card shadow="never" class="mb-5" v-if="sentimentSummary?.top_keywords?.length">
            <template #header><span>热门关键词</span></template>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="kw in sentimentSummary.top_keywords" :key="kw.keyword" size="large">{{ kw.keyword }} ({{ kw.count }})</el-tag>
            </div>
          </el-card>
          <!-- 舆情趋势图 -->
          <el-card shadow="never" class="mb-5" v-if="sentimentArticles.length >= 3">
            <template #header><span>舆情趋势</span></template>
            <div ref="sentimentTrendRef" style="height: 280px"></div>
          </el-card>
          <!-- 关键事件时间轴 -->
          <el-card shadow="never" class="mb-5" v-if="keyEvents.length">
            <template #header><span>关键事件时间轴</span></template>
            <div class="event-timeline">
              <div class="event-timeline-line"></div>
              <div class="event-timeline-items">
                <div v-for="ev in keyEvents.slice(0, 20)" :key="ev.id" class="event-timeline-item" :class="ev.sentiment">
                  <div class="event-dot" :class="ev.sentiment"></div>
                  <div class="event-date">{{ ev.date }}</div>
                  <div class="event-card">
                    <div class="event-card-header">
                      <el-tag v-for="et in ev.event_types?.slice(0, 2)" :key="et" size="small"
                        :type="{ personnel: 'warning', liquidation: 'danger', penalty: 'danger', scale: 'success', risk: 'danger', alert: 'warning' }[et] || 'info'">
                        {{ eventTypeLabels[et] || et }}
                      </el-tag>
                      <el-tag v-if="ev.is_alert" type="danger" size="small" effect="dark">预警</el-tag>
                    </div>
                    <div class="event-card-title">{{ ev.title }}</div>
                    <div class="event-card-summary" v-if="ev.summary">{{ ev.summary }}</div>
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-if="keyEvents.length === 0" description="暂无关键事件" :image-size="40" />
          </el-card>

          <!-- 添加文章 + 列表 -->
          <el-card shadow="never">
            <template #header>
              <div class="card-header-row">
                <span>舆情时间线</span>
                <div class="flex gap-2">
                  <el-button size="small" @click="handleCrawlSentiment" :loading="crawling">自动爬取</el-button>
                  <el-button size="small" type="primary" @click="showArticleDialog = true"><el-icon><Plus /></el-icon>添加舆情</el-button>
                </div>
              </div>
            </template>
            <el-timeline v-if="sentimentArticles.length">
              <el-timeline-item v-for="article in sentimentArticles" :key="article.id" :timestamp="article.publish_date || article.created_at" placement="top"
                :color="article.sentiment === 'positive' ? '#67c23a' : article.sentiment === 'negative' ? '#f56c6c' : '#909399'">
                <div class="sentiment-article-item">
                  <div class="flex items-center gap-2 mb-1">
                    <el-tag :type="article.sentiment === 'positive' ? 'success' : article.sentiment === 'negative' ? 'danger' : 'info'" size="small">
                      {{ { positive: '正面', neutral: '中性', negative: '负面' }[article.sentiment] || article.sentiment }}
                    </el-tag>
                    <span class="font-medium">{{ article.title }}</span>
                    <el-tag v-if="article.is_alert" type="danger" size="small" effect="dark">预警</el-tag>
                  </div>
                  <div class="text-sm text-dark-400" v-if="article.summary">{{ article.summary }}</div>
                  <div class="flex gap-2 mt-1" v-if="article.keywords?.length">
                    <el-tag v-for="kw in article.keywords" :key="kw" size="small" type="info">{{ kw }}</el-tag>
                  </div>
                  <div class="flex items-center gap-2 mt-2">
                    <span class="text-xs text-dark-500">来源: {{ article.source || '未知' }}</span>
                    <el-link v-if="article.url" :href="article.url" target="_blank" type="primary" :underline="false" class="text-xs">原文</el-link>
                    <el-button link type="primary" size="small" @click="handleReanalyze(article)">重新分析</el-button>
                    <el-button link type="danger" size="small" @click="handleDeleteArticle(article)">删除</el-button>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无舆情数据" :image-size="60" />
          </el-card>
        </div>
      </el-tab-pane>

      <!-- Tab 6: 尽调资料 -->
      <el-tab-pane label="尽调资料" name="documents" lazy>
        <el-card shadow="never">
          <template #header>
            <div class="card-header-row">
              <div class="doc-filters">
                <el-select v-model="docCategory" placeholder="全部分类" clearable size="small" style="width: 140px" @change="loadDocuments">
                  <el-option v-for="opt in DOCUMENT_CATEGORY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
                <el-input v-model="docKeyword" placeholder="搜索文件名" clearable size="small" style="width: 180px" @keyup.enter="loadDocuments" />
              </div>
              <el-upload :show-file-list="false" :before-upload="handleDocUpload" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.jpg,.png,.zip">
                <el-button size="small" type="primary"><el-icon><Upload /></el-icon>上传资料</el-button>
              </el-upload>
            </div>
          </template>
          <el-table :data="documents" stripe v-loading="docLoading">
            <el-table-column prop="title" label="文件名" min-width="250" show-overflow-tooltip />
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">{{ getCategoryLabel(row.category) }}</template>
            </el-table-column>
            <el-table-column prop="file_type" label="类型" width="80" />
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
            </el-table-column>
            <el-table-column prop="uploaded_at" label="上传时间" width="160">
              <template #default="{ row }">{{ formatDateTime(row.uploaded_at) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!docLoading && documents.length === 0" description="暂无尽调资料" :image-size="60" />
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑管理人" width="800px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="管理人名称" prop="manager_name"><el-input v-model="editForm.manager_name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="简称"><el-input v-model="editForm.short_name" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="一级策略"><el-select v-model="editForm.primary_strategy" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in PRIMARY_STRATEGY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="管理规模"><el-select v-model="editForm.aum_range" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in AUM_RANGE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="评级"><el-select v-model="editForm.rating" placeholder="请选择" clearable style="width: 100%"><el-option v-for="opt in RATING_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="员工人数"><el-input-number v-model="editForm.employee_count" :min="0" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="联系人"><el-input v-model="editForm.contact_person" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="联系电话"><el-input v-model="editForm.contact_phone" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="联系邮箱"><el-input v-model="editForm.contact_email" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="editForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editDialogVisible = false">取消</el-button><el-button type="primary" @click="handleEditSubmit" :loading="submitting">保存</el-button></template>
    </el-dialog>

    <!-- 流转对话框 -->
    <el-dialog v-model="transferDialogVisible" title="跟踪池流转" width="500px">
      <el-form :model="transferForm" label-width="80px">
        <el-form-item label="当前分类"><el-tag :color="getPoolColor(manager?.pool_category)" effect="dark">{{ getPoolLabel(manager?.pool_category) }}</el-tag></el-form-item>
        <el-form-item label="目标分类" required><el-select v-model="transferForm.to_pool" placeholder="请选择" style="width: 100%"><el-option v-for="opt in POOL_CATEGORY_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" /></el-select></el-form-item>
        <el-form-item label="流转原因" required><el-input v-model="transferForm.reason" type="textarea" :rows="3" placeholder="请输入流转原因" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="transferDialogVisible = false">取消</el-button><el-button type="primary" @click="handleTransferSubmit" :loading="submitting">确定</el-button></template>
    </el-dialog>

    <!-- 添加联系人对话框 -->
    <el-dialog v-model="showContactDialog" title="添加联系人" width="500px">
      <el-form :model="contactForm" label-width="80px">
        <el-form-item label="姓名" required><el-input v-model="contactForm.name" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="contactForm.position" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="contactForm.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="contactForm.email" /></el-form-item>
        <el-form-item label="微信"><el-input v-model="contactForm.wechat" /></el-form-item>
        <el-form-item label="主要联系人"><el-switch v-model="contactForm.is_primary" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showContactDialog = false">取消</el-button><el-button type="primary" @click="handleAddContact" :loading="submitting">确定</el-button></template>
    </el-dialog>

    <!-- 添加团队成员对话框 -->
    <el-dialog v-model="showTeamDialog" title="添加团队成员" width="500px">
      <el-form :model="teamForm" label-width="80px">
        <el-form-item label="姓名" required><el-input v-model="teamForm.name" /></el-form-item>
        <el-form-item label="职位" required><el-input v-model="teamForm.position" /></el-form-item>
        <el-form-item label="从业年限"><el-input-number v-model="teamForm.years_of_experience" :min="0" style="width: 100%" /></el-form-item>
        <el-form-item label="教育背景"><el-input v-model="teamForm.education" /></el-form-item>
        <el-form-item label="工作经历"><el-input v-model="teamForm.work_history" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showTeamDialog = false">取消</el-button><el-button type="primary" @click="handleAddTeamMember" :loading="submitting">确定</el-button></template>
    </el-dialog>

    <!-- 添加舆情文章对话框 -->
    <el-dialog v-model="showArticleDialog" title="添加舆情" width="600px">
      <el-form :model="articleForm" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="articleForm.title" placeholder="新闻标题" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="articleForm.content" type="textarea" :rows="4" placeholder="新闻内容（用于AI分析）" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="articleForm.source" placeholder="如：东方财富、公众号等" /></el-form-item>
        <el-form-item label="原文链接"><el-input v-model="articleForm.url" placeholder="https://..." /></el-form-item>
        <el-form-item label="发布时间"><el-date-picker v-model="articleForm.publish_date" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="选择发布时间" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showArticleDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddArticle" :loading="submitting">添加并分析</el-button>
      </template>
    </el-dialog>

    <!-- 添加标签对话框 -->
    <el-dialog v-model="showTagDialog" title="添加标签" width="400px">
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签类型" required>
          <el-select v-model="tagForm.tag_type" style="width: 100%">
            <el-option v-for="opt in TAG_TYPE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签名称" required><el-input v-model="tagForm.tag_name" placeholder="输入标签名称" /></el-form-item>
        <el-form-item label="标签颜色"><el-color-picker v-model="tagForm.tag_color" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showTagDialog = false">取消</el-button><el-button type="primary" @click="handleAddTag" :loading="submitting">确定</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Upload } from '@element-plus/icons-vue'
import { managerApi } from '@/api'
import request from '@/api/request'
import CommentSection from '@/components/common/CommentSection.vue'
import type {
  Manager, PoolCategory, PrimaryStrategy, PoolTransfer, PoolTransferCreate,
  ManagerProductInfo, ManagerPerformanceSummary, ManagerTag, ManagerTagCreate, ManagerDocument
} from '@/types'
import {
  POOL_CATEGORY_OPTIONS, PRIMARY_STRATEGY_OPTIONS, RATING_OPTIONS, AUM_RANGE_OPTIONS,
  TAG_TYPE_OPTIONS, DOCUMENT_CATEGORY_OPTIONS
} from '@/types'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const managerId = ref(Number(route.params.id))

// 状态
const loading = ref(false)
const submitting = ref(false)
const manager = ref<Manager | null>(null)
const transfers = ref<PoolTransfer[]>([])
const products = ref<ManagerProductInfo[]>([])
const perfSummary = ref<ManagerPerformanceSummary | null>(null)
const tags = ref<ManagerTag[]>([])
const documents = ref<ManagerDocument[]>([])
const docLoading = ref(false)
const activeTab = ref('basic')

// 对话框
const editDialogVisible = ref(false)
const transferDialogVisible = ref(false)
const showContactDialog = ref(false)
const showTeamDialog = ref(false)
const showTagDialog = ref(false)
const showArticleDialog = ref(false)

// 表单
const editFormRef = ref()
const editForm = reactive<Record<string, any>>({})
const transferForm = reactive<PoolTransferCreate>({ to_pool: 'observation', reason: '' })
const contactForm = reactive({ name: '', position: '', phone: '', email: '', wechat: '', is_primary: false })
const teamForm = reactive({ name: '', position: '', years_of_experience: undefined as number | undefined, education: '', work_history: '' })
const tagForm = reactive<ManagerTagCreate>({ tag_type: 'custom', tag_name: '', tag_color: '#409EFF' })
const docCategory = ref('')
const docKeyword = ref('')
const articleForm = reactive({ title: '', content: '', source: '', url: '', publish_date: '' })
const sentimentSummary = ref<any>(null)
const sentimentArticles = ref<any[]>([])
const keyEvents = ref<any[]>([])
const eventTypeLabels = ref<Record<string, string>>({})
const editHistory = ref<any[]>([])
const editHistoryTotal = ref(0)
const crawling = ref(false)

// Charts
const navChartRef = ref<HTMLElement>()
const compChartRef = ref<HTMLElement>()
let navChart: echarts.ECharts | null = null
let compChart: echarts.ECharts | null = null
const sentimentTrendRef = ref<HTMLElement>()
let sentimentTrendChart: echarts.ECharts | null = null

// 工具函数
const getPoolLabel = (pool?: PoolCategory | string) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.label || pool || '-'
const getPoolColor = (pool?: PoolCategory | string) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.color || '#909399'
const getStrategyLabel = (strategy?: PrimaryStrategy | string) => PRIMARY_STRATEGY_OPTIONS.find(s => s.value === strategy)?.label || strategy || '-'
const getRatingType = (rating: string) => ({ S: 'success', A: 'success', B: 'warning', C: 'info', D: 'danger' }[rating] || 'info') as any
const getCategoryLabel = (cat: string) => DOCUMENT_CATEGORY_OPTIONS.find(c => c.value === cat)?.label || cat || '-'
const formatDateTime = (dateStr: string) => dateStr ? dateStr.replace('T', ' ').substring(0, 16) : ''
const formatPercent = (val?: number | null) => val != null ? (val * 100).toFixed(2) + '%' : '-'
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

// 数据加载
const loadManager = async () => {
  loading.value = true
  try {
    manager.value = await managerApi.getById(managerId.value)
  } catch (error) { console.error('加载管理人失败', error) } finally { loading.value = false }
}

const loadTransfers = async () => {
  try { transfers.value = await managerApi.getPoolTransfers(managerId.value) } catch (error) { console.error(error) }
}

const loadProducts = async () => {
  try { products.value = await managerApi.getProducts(managerId.value) } catch (error) { console.error(error) }
}

const loadPerformance = async () => {
  try {
    perfSummary.value = await managerApi.getPerformanceSummary(managerId.value)
    await nextTick()
    renderNavChart()
    renderCompChart()
  } catch (error) { console.error(error) }
}

const loadTags = async () => {
  try { tags.value = await managerApi.getTags(managerId.value) } catch (error) { console.error(error) }
}

const loadDocuments = async () => {
  docLoading.value = true
  try {
    const res = await managerApi.getDocuments(managerId.value, {
      category: docCategory.value || undefined,
      keyword: docKeyword.value || undefined
    })
    documents.value = res.items || []
  } catch (error) { console.error(error) } finally { docLoading.value = false }
}

const loadEditHistory = async () => {
  try {
    const res = await request.get(`/managers/${managerId.value}/edit-history`, { params: { limit: 100 } })
    editHistory.value = (res as any).items || []
    editHistoryTotal.value = (res as any).total || 0
  } catch (error) { console.error(error) }
}

// 分组编辑历史（按batch_id）
const groupedEditHistory = computed(() => {
  const groups: Record<string, { batch_id: string; time: string; operator: string; changes: any[] }> = {}
  for (const item of editHistory.value) {
    const key = item.batch_id || item.id
    if (!groups[key]) {
      groups[key] = {
        batch_id: key,
        time: formatDateTime(item.created_at),
        operator: item.operator_name || '',
        changes: []
      }
    }
    groups[key].changes.push(item)
  }
  return Object.values(groups)
})

const loadSentiment = async () => {
  try {
    const [summary, list, timeline] = await Promise.all([
      request.get(`/sentiment/manager/${managerId.value}/summary`),
      request.get('/sentiment/articles', { params: { manager_id: managerId.value, page_size: 50 } }),
      request.get(`/sentiment/manager/${managerId.value}/timeline`).catch(() => null),
    ])
    sentimentSummary.value = summary
    sentimentArticles.value = (list as any).items || []
    if (timeline) {
      keyEvents.value = (timeline as any).events || []
      eventTypeLabels.value = (timeline as any).event_type_labels || {}
    }
    await nextTick()
    renderSentimentTrend()
  } catch (error) { console.error(error) }
}

const renderSentimentTrend = () => {
  if (!sentimentTrendRef.value || sentimentArticles.value.length < 3) return
  sentimentTrendChart?.dispose()
  sentimentTrendChart = echarts.init(sentimentTrendRef.value)

  // 按月聚合
  const monthMap: Record<string, { positive: number; neutral: number; negative: number }> = {}
  for (const a of sentimentArticles.value) {
    const d = a.publish_date || a.created_at || ''
    const month = d.substring(0, 7) // YYYY-MM
    if (!month) continue
    if (!monthMap[month]) monthMap[month] = { positive: 0, neutral: 0, negative: 0 }
    const s = a.sentiment as string
    if (s === 'positive') monthMap[month].positive++
    else if (s === 'negative') monthMap[month].negative++
    else monthMap[month].neutral++
  }
  const months = Object.keys(monthMap).sort()
  const posData = months.map(m => monthMap[m].positive)
  const neuData = months.map(m => monthMap[m].neutral)
  const negData = months.map(m => monthMap[m].negative)

  sentimentTrendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['正面', '中性', '负面'] },
    grid: { left: 50, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '正面', type: 'bar', stack: 'total', data: posData, itemStyle: { color: '#67C23A' } },
      { name: '中性', type: 'bar', stack: 'total', data: neuData, itemStyle: { color: '#909399' } },
      { name: '负面', type: 'bar', stack: 'total', data: negData, itemStyle: { color: '#F56C6C' } },
    ]
  })
}

// Tab切换加载
watch(activeTab, (tab) => {
  if (tab === 'products' && products.value.length === 0) loadProducts()
  if (tab === 'performance' && !perfSummary.value) loadPerformance()
  if (tab === 'sentiment' && !sentimentSummary.value) loadSentiment()
  if (tab === 'documents' && documents.value.length === 0) loadDocuments()
})

// ECharts
const renderNavChart = () => {
  if (!navChartRef.value || !perfSummary.value?.nav_dates.length) return
  navChart?.dispose()
  navChart = echarts.init(navChartRef.value)
  navChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: perfSummary.value.nav_dates, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', min: 'dataMin' },
    series: [{ type: 'line', data: perfSummary.value.nav_values, smooth: true, lineStyle: { width: 2 }, areaStyle: { opacity: 0.15 }, itemStyle: { color: '#409EFF' } }]
  })
}

const renderCompChart = () => {
  if (!compChartRef.value || !perfSummary.value?.products_comparison.length) return
  compChart?.dispose()
  compChart = echarts.init(compChartRef.value)
  const names = perfSummary.value.products_comparison.map(p => p.product_name)
  const cumReturns = perfSummary.value.products_comparison.map(p => p.cumulative_return != null ? +(p.cumulative_return * 100).toFixed(2) : 0)
  const annReturns = perfSummary.value.products_comparison.map(p => p.annualized_return != null ? +(p.annualized_return * 100).toFixed(2) : 0)
  compChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['累计收益(%)', '年化收益(%)'] },
    grid: { left: 60, right: 30, top: 40, bottom: 60 },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: 30, interval: 0 } },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [
      { name: '累计收益(%)', type: 'bar', data: cumReturns, itemStyle: { color: '#409EFF' } },
      { name: '年化收益(%)', type: 'bar', data: annReturns, itemStyle: { color: '#67C23A' } }
    ]
  })
}

// 操作
const handleBack = () => router.push('/managers')
const handleProductClick = (row: ManagerProductInfo) => router.push(`/products/${row.id}`)

const handleEdit = () => {
  if (!manager.value) return
  Object.assign(editForm, {
    manager_name: manager.value.manager_name,
    short_name: manager.value.short_name,
    primary_strategy: manager.value.primary_strategy,
    aum_range: manager.value.aum_range,
    rating: manager.value.rating,
    employee_count: manager.value.employee_count,
    contact_person: manager.value.contact_person,
    contact_phone: manager.value.contact_phone,
    contact_email: manager.value.contact_email,
    remark: manager.value.remark
  })
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  submitting.value = true
  try {
    await managerApi.update(managerId.value, editForm)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadManager()
    loadEditHistory()
  } catch (error: any) { ElMessage.error(error.message || '更新失败') } finally { submitting.value = false }
}

const handleTransfer = () => {
  transferForm.to_pool = manager.value?.pool_category || 'observation'
  transferForm.reason = ''
  transferDialogVisible.value = true
}

const handleTransferSubmit = async () => {
  if (!transferForm.reason) { ElMessage.warning('请填写流转原因'); return }
  submitting.value = true
  try {
    await managerApi.transferPool(managerId.value, transferForm)
    ElMessage.success('流转成功')
    transferDialogVisible.value = false
    loadManager()
    loadTransfers()
  } catch (error: any) { ElMessage.error(error.message || '流转失败') } finally { submitting.value = false }
}

const handleAddContact = async () => {
  if (!contactForm.name) { ElMessage.warning('请填写姓名'); return }
  submitting.value = true
  try {
    await managerApi.addContact(managerId.value, contactForm)
    ElMessage.success('添加成功')
    showContactDialog.value = false
    Object.assign(contactForm, { name: '', position: '', phone: '', email: '', wechat: '', is_primary: false })
    loadManager()
  } catch (error: any) { ElMessage.error(error.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteContact = async (contact: any) => {
  await ElMessageBox.confirm(`确定删除联系人"${contact.name}"吗？`, '提示', { type: 'warning' })
  try { await managerApi.deleteContact(contact.id); ElMessage.success('删除成功'); loadManager() } catch (error: any) { ElMessage.error(error.message || '删除失败') }
}

const handleAddTeamMember = async () => {
  if (!teamForm.name || !teamForm.position) { ElMessage.warning('请填写姓名和职位'); return }
  submitting.value = true
  try {
    await managerApi.addTeamMember(managerId.value, teamForm)
    ElMessage.success('添加成功')
    showTeamDialog.value = false
    Object.assign(teamForm, { name: '', position: '', years_of_experience: undefined, education: '', work_history: '' })
    loadManager()
  } catch (error: any) { ElMessage.error(error.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteTeamMember = async (member: any) => {
  await ElMessageBox.confirm(`确定删除团队成员"${member.name}"吗？`, '提示', { type: 'warning' })
  try { await managerApi.deleteTeamMember(member.id); ElMessage.success('删除成功'); loadManager() } catch (error: any) { ElMessage.error(error.message || '删除失败') }
}

const handleAddTag = async () => {
  if (!tagForm.tag_name) { ElMessage.warning('请输入标签名称'); return }
  submitting.value = true
  try {
    await managerApi.addTag(managerId.value, tagForm)
    ElMessage.success('添加成功')
    showTagDialog.value = false
    tagForm.tag_name = ''
    loadTags()
  } catch (error: any) { ElMessage.error(error.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteTag = async (tag: ManagerTag) => {
  try { await managerApi.deleteTag(tag.id); ElMessage.success('删除成功'); loadTags() } catch (error: any) { ElMessage.error(error.message || '删除失败') }
}

const handleAddArticle = async () => {
  if (!articleForm.title) { ElMessage.warning('请输入标题'); return }
  submitting.value = true
  try {
    await request.post('/sentiment/articles', {
      ...articleForm,
      manager_id: managerId.value,
      publish_date: articleForm.publish_date || undefined,
    })
    ElMessage.success('添加成功，AI正在分析...')
    showArticleDialog.value = false
    Object.assign(articleForm, { title: '', content: '', source: '', url: '', publish_date: '' })
    loadSentiment()
  } catch (error: any) { ElMessage.error(error.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteArticle = async (article: any) => {
  await ElMessageBox.confirm(`确定删除舆情"${article.title}"吗？`, '提示', { type: 'warning' })
  try {
    await request.delete(`/sentiment/articles/${article.id}`)
    ElMessage.success('删除成功')
    loadSentiment()
  } catch (error: any) { ElMessage.error(error.message || '删除失败') }
}

const handleReanalyze = async (article: any) => {
  try {
    await request.post(`/sentiment/articles/${article.id}/analyze`)
    ElMessage.success('重新分析完成')
    loadSentiment()
  } catch (error: any) { ElMessage.error(error.message || '分析失败') }
}

const handleCrawlSentiment = async () => {
  crawling.value = true
  try {
    const res = await request.post(`/sentiment/crawl/manager/${managerId.value}`) as any
    ElMessage.success(`爬取完成，新增${res.new_articles || 0}条`)
    if (res.new_articles > 0) loadSentiment()
  } catch (error: any) { ElMessage.error(error.message || '爬取失败') } finally { crawling.value = false }
}

const handleDocUpload = async (file: File) => {
  try {
    await managerApi.uploadDocument(managerId.value, file, { category: docCategory.value || 'other' })
    ElMessage.success('上传成功')
    loadDocuments()
  } catch (error: any) { ElMessage.error(error.message || '上传失败') }
  return false
}

onMounted(() => {
  loadManager()
  loadTransfers()
  loadTags()
  loadEditHistory()
})
</script>

<style scoped>
.manager-detail-view { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.header-left { display: flex; align-items: flex-start; gap: 15px; }
.header-info h2 { margin: 0 0 8px 0; color: var(--text-primary); }
.header-tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.header-actions { display: flex; gap: 10px; }

.detail-tabs { background: var(--card-bg); border-radius: 8px; padding: 0 20px 20px; border: 1px solid var(--card-border); }
.tab-content { }

.info-card { background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }

.transfer-item { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.transfer-arrow { color: var(--text-muted); font-weight: bold; }
.transfer-reason { color: var(--text-secondary); font-size: 13px; margin-left: 8px; }

/* 中国A股习惯：红涨绿跌 */
.text-green { color: #F56C6C; }  /* 涨用红色 */
.text-red { color: #67C23A; }    /* 跌用绿色 */

/* 业绩汇总 */
.perf-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
.perf-card { text-align: center; background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
.perf-label { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.perf-value { font-size: 24px; font-weight: bold; color: var(--text-primary); }
.perf-sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* 尽调资料 */
.doc-filters { display: flex; gap: 10px; align-items: center; }

/* Element Plus 样式覆盖 */
:deep(.el-tabs__header) { margin-bottom: 20px; }
:deep(.el-card) { background: var(--card-bg) !important; border: 1px solid var(--card-border) !important; }
:deep(.el-card__header) { color: var(--text-primary); font-weight: 600; }
:deep(.el-descriptions) { --el-descriptions-item-bordered-label-background: var(--hover-bg); }

/* 编辑历史 */
.edit-history-group { }
.edit-operator { font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.edit-changes { display: flex; flex-direction: column; gap: 4px; }
.edit-change-item { display: flex; align-items: center; gap: 8px; font-size: 13px; flex-wrap: wrap; }
.old-val { color: var(--text-muted); text-decoration: line-through; }
.new-val { color: var(--accent-color); font-weight: 500; }
.change-arrow { color: var(--text-muted); }

/* 舆情关键事件时间轴 */
.event-timeline { position: relative; padding: 10px 0; }
.event-timeline-line { position: absolute; left: 80px; top: 0; bottom: 0; width: 2px; background: linear-gradient(to bottom, #409EFF, #67C23A, #E6A23C, #F56C6C); border-radius: 2px; }
.event-timeline-items { display: flex; flex-direction: column; gap: 16px; }
.event-timeline-item { display: flex; align-items: flex-start; gap: 20px; position: relative; }
.event-dot { position: absolute; left: 75px; top: 6px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--card-bg); z-index: 1; }
.event-dot.positive { background: #67C23A; }
.event-dot.negative { background: #F56C6C; }
.event-dot.neutral { background: #909399; }
.event-date { width: 60px; flex-shrink: 0; font-size: 12px; color: var(--text-secondary); text-align: right; padding-top: 2px; }
.event-card { flex: 1; background: var(--hover-bg); border-radius: 8px; padding: 12px 16px; margin-left: 20px; }
.event-card-header { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.event-card-title { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.event-card-summary { font-size: 12px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
</style>
