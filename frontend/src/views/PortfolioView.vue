<template>
  <div class="portfolio-view p-6">
    <!-- 页面头部 -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold gradient-text">组合管理</h2>
        <p class="text-sm text-dark-400 mt-1">构建和分析投资组合，追踪组合业绩表现</p>
      </div>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon class="mr-1"><Plus /></el-icon>
        新建组合
      </el-button>
    </div>

    <!-- 组合列表 -->
    <div class="glass-card p-5 mb-6" v-if="!selectedPortfolio">
      <!-- 筛选栏 -->
      <div class="flex items-center gap-4 mb-5">
        <el-input 
          v-model="searchKey" 
          placeholder="搜索组合名称..." 
          style="width: 280px"
          clearable
          @clear="fetchPortfolios"
          @keyup.enter="fetchPortfolios"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 140px" @change="fetchPortfolios">
          <el-option v-for="s in PORTFOLIO_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <el-select v-model="typeFilter" placeholder="类型筛选" clearable style="width: 140px" @change="fetchPortfolios">
          <el-option v-for="t in PORTFOLIO_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-button @click="fetchPortfolios" :loading="loading">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>

      <!-- 组合卡片列表 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" v-if="portfolios.length > 0">
        <div 
          v-for="portfolio in portfolios" 
          :key="portfolio.id" 
          class="portfolio-card cursor-pointer"
          @click="selectPortfolio(portfolio.id)"
        >
          <div class="flex justify-between items-start mb-3">
            <div>
              <h4 class="text-lg font-semibold card-title">{{ portfolio.name }}</h4>
              <p class="text-xs card-desc mt-1" v-if="portfolio.portfolio_code">{{ portfolio.portfolio_code }}</p>
              <p class="text-sm card-desc mt-1 line-clamp-1">{{ portfolio.description || '暂无描述' }}</p>
            </div>
            <div class="flex gap-1">
              <el-tag :type="getTypeTagType(portfolio.portfolio_type)" size="small" effect="plain">
                {{ getTypeLabel(portfolio.portfolio_type) }}
              </el-tag>
              <el-tag :type="getStatusType(portfolio.status)" size="small">
                {{ getStatusLabel(portfolio.status) }}
              </el-tag>
            </div>
          </div>
          <div class="flex items-center gap-6 text-sm">
            <div>
              <span class="card-label">成分数量</span>
              <span class="ml-2 card-value font-medium">{{ portfolio.component_count }}</span>
            </div>
            <div>
              <span class="card-label">最新净值</span>
              <span class="ml-2 card-value font-medium">{{ portfolio.latest_nav != null ? Number(portfolio.latest_nav).toFixed(4) : '-' }}</span>
            </div>
            <div v-if="portfolio.total_return !== null && portfolio.total_return !== undefined">
              <span class="card-label">总收益</span>
              <span class="ml-2 font-medium" :class="portfolio.total_return >= 0 ? 'positive-value' : 'negative-value'">
                {{ formatPercent(portfolio.total_return) }}
              </span>
            </div>
          </div>
          <div class="mt-3 pt-3 card-divider flex justify-between items-center">
            <span class="text-xs card-label">创建于 {{ formatDate(portfolio.created_at) }}</span>
            <div class="flex gap-2" @click.stop>
              <el-button text size="small" @click.stop="showEditDialog(portfolio)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button text size="small" type="danger" @click.stop="handleDelete(portfolio.id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无组合数据，点击新建组合开始" />

      <!-- 分页 -->
      <div class="mt-5 flex justify-end" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchPortfolios"
        />
      </div>
    </div>

    <!-- 组合详情 -->
    <div v-if="selectedPortfolio" class="portfolio-detail">
      <!-- 返回按钮 -->
      <el-button text class="mb-4" @click="selectedPortfolio = null">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>
        返回列表
      </el-button>

      <!-- 组合概览 -->
      <div class="glass-card p-5 mb-6">
        <div class="flex justify-between items-start">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-xl font-bold card-title">{{ selectedPortfolio.name }}</h3>
              <el-tag :type="getTypeTagType(selectedPortfolio.portfolio_type)" size="small" effect="plain">
                {{ getTypeLabel(selectedPortfolio.portfolio_type) }}
              </el-tag>
            </div>
            <p class="text-xs card-desc mt-1" v-if="selectedPortfolio.portfolio_code">组合代码: {{ selectedPortfolio.portfolio_code }}</p>
            <p class="text-sm card-desc mt-1">{{ selectedPortfolio.description || '暂无描述' }}</p>
          </div>
          <div class="flex gap-2">
            <el-tag :type="getStatusType(selectedPortfolio.status)">
              {{ getStatusLabel(selectedPortfolio.status) }}
            </el-tag>
            <el-button size="small" @click="showEditDialog(selectedPortfolio)">编辑</el-button>
          </div>
        </div>

        <!-- 业绩指标卡片 -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mt-6" v-if="performance">
          <div class="metric-card">
            <span class="metric-label">总收益</span>
            <span class="metric-value" :class="performance.total_return >= 0 ? 'positive-value' : 'negative-value'">
              {{ formatPercent(performance.total_return) }}
            </span>
          </div>
          <div class="metric-card">
            <span class="metric-label">年化收益</span>
            <span class="metric-value" :class="performance.annualized_return >= 0 ? 'positive-value' : 'negative-value'">
              {{ formatPercent(performance.annualized_return) }}
            </span>
          </div>
          <div class="metric-card">
            <span class="metric-label">波动率</span>
            <span class="metric-value">{{ formatPercent(performance.volatility) }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">最大回撤</span>
            <span class="metric-value negative-value">{{ formatPercent(performance.max_drawdown) }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">夏普比率</span>
            <span class="metric-value">{{ performance.sharpe_ratio != null ? Number(performance.sharpe_ratio).toFixed(2) : '-' }}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">卡玛比率</span>
            <span class="metric-value">{{ performance.calmar_ratio != null ? Number(performance.calmar_ratio).toFixed(2) : '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" class="portfolio-tabs">
        <!-- 成分管理 -->
        <el-tab-pane label="组合成分" name="components">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">组合成分</h4>
              <el-button type="primary" size="small" @click="showAddComponentDialog">
                <el-icon class="mr-1"><Plus /></el-icon>
                添加成分
              </el-button>
            </div>
            
            <!-- 成分列表 -->
            <el-table :data="selectedPortfolio.components" stripe v-if="selectedPortfolio.components.length > 0">
              <el-table-column prop="product_name" label="产品名称" min-width="180">
                <template #default="{ row }">
                  <div>
                    <span class="text-white">{{ row.product_name }}</span>
                    <span class="text-xs text-dark-400 block">{{ row.product_code }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="manager_name" label="管理人" min-width="120" />
              <el-table-column prop="weight" label="权重" width="100" align="center">
                <template #default="{ row }">
                  <span class="font-medium text-primary-400">{{ (Number(row.weight) * 100).toFixed(1) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="join_date" label="加入日期" width="120" align="center">
                <template #default="{ row }">
                  {{ row.join_date || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" align="center">
                <template #default="{ row }">
                  <el-button text size="small" @click="showEditComponentDialog(row)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button text size="small" type="danger" @click="handleRemoveComponent(row.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无成分，点击添加成分开始构建组合" />

            <!-- 权重汇总 -->
            <div class="mt-4 p-4 weight-summary rounded-lg flex justify-between items-center" v-if="selectedPortfolio.components.length > 0">
              <span class="card-label">权重合计</span>
              <span class="text-xl font-bold" :class="totalWeight === 1 ? 'positive-value' : 'warning-value'">
                {{ (totalWeight * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </el-tab-pane>

        <!-- 净值走势 -->
        <el-tab-pane label="净值走势" name="nav">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">组合净值走势</h4>
              <el-radio-group v-model="selectedPeriod" size="small" @change="fetchPortfolioData">
                <el-radio-button v-for="p in PERIOD_OPTIONS" :key="p.value" :value="p.value">
                  {{ p.label }}
                </el-radio-button>
              </el-radio-group>
            </div>
            <div ref="navChartRef" style="height: 400px" v-loading="loadingNav"></div>
            <div v-if="navData?.nav_quality" class="mt-3 text-xs card-label flex flex-wrap gap-4">
              <span>
                数据等级:
                <el-tag size="small" effect="plain" :type="navCoverageLevel.type" class="ml-1">
                  {{ navCoverageLevel.label }}
                </el-tag>
              </span>
              <span>
                数据覆盖率:
                <span :class="getCoverageValueClass(navData.nav_quality.coverage_ratio)">
                  {{ formatPercent(navData.nav_quality.coverage_ratio) }}
                </span>
              </span>
              <span>
                权重覆盖率:
                <span :class="getCoverageValueClass(navData.nav_quality.avg_weight_coverage)">
                  {{ formatPercent(navData.nav_quality.avg_weight_coverage) }}
                </span>
              </span>
              <span>补值日期数: {{ navData.nav_quality.carry_forward_dates }}</span>
              <span>跳过日期数: {{ navData.nav_quality.skipped_dates }}</span>
              <span class="text-dark-400">分级口径: 覆盖率与权重覆盖率取较低值</span>
            </div>
            <el-alert
              v-if="navQualityAlert"
              class="mt-3"
              :type="navQualityAlert.type"
              :closable="false"
              show-icon
              :title="navQualityAlert.title"
              :description="navQualityAlert.description"
            />
          </div>
        </el-tab-pane>

        <!-- 贡献分析 + Brinson归因 + 风险归因 -->
        <el-tab-pane label="归因分析" name="contribution">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">成分贡献分析</h4>
              <span class="text-sm card-label" v-if="contribution">
                组合收益: 
                <span :class="contribution.portfolio_return >= 0 ? 'positive-value' : 'negative-value'">
                  {{ formatPercent(contribution.portfolio_return) }}
                </span>
              </span>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div ref="contributionPieRef" style="height: 300px" v-loading="loadingContribution"></div>
              <div ref="contributionBarRef" style="height: 300px" v-loading="loadingContribution"></div>
            </div>
          </div>

          <!-- Brinson BHB 归因 -->
          <div class="glass-card p-5 mt-4">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">Brinson BHB 归因</h4>
              <span class="text-sm card-label" v-if="brinsonData">
                超额收益: <span :class="brinsonData.excess_return >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(brinsonData.excess_return) }}</span>
              </span>
            </div>
            <div v-if="brinsonData" v-loading="loadingBrinson">
              <!-- 汇总指标 -->
              <div class="grid grid-cols-3 gap-4 mb-4">
                <div class="metric-card">
                  <span class="metric-label">配置效应</span>
                  <span class="metric-value" :class="brinsonData.total_allocation_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(brinsonData.total_allocation_effect) }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">选择效应</span>
                  <span class="metric-value" :class="brinsonData.total_selection_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(brinsonData.total_selection_effect) }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">交互效应</span>
                  <span class="metric-value" :class="brinsonData.total_interaction_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(brinsonData.total_interaction_effect) }}</span>
                </div>
              </div>
              <!-- 按策略明细 -->
              <el-table :data="brinsonData.attributions" stripe size="small">
                <el-table-column prop="strategy" label="策略" min-width="100" />
                <el-table-column label="组合权重" width="100" align="center">
                  <template #default="{ row }">{{ (row.portfolio_weight * 100).toFixed(1) }}%</template>
                </el-table-column>
                <el-table-column label="基准权重" width="100" align="center">
                  <template #default="{ row }">{{ (row.benchmark_weight * 100).toFixed(1) }}%</template>
                </el-table-column>
                <el-table-column label="配置效应" width="100" align="center">
                  <template #default="{ row }"><span :class="row.allocation_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.allocation_effect) }}</span></template>
                </el-table-column>
                <el-table-column label="选择效应" width="100" align="center">
                  <template #default="{ row }"><span :class="row.selection_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.selection_effect) }}</span></template>
                </el-table-column>
                <el-table-column label="总效应" width="100" align="center">
                  <template #default="{ row }"><span :class="row.total_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.total_effect) }}</span></template>
                </el-table-column>
              </el-table>
            </div>
            <el-empty v-else-if="!loadingBrinson" description="无法计算Brinson归因" />
          </div>

          <!-- 风险贡献归因 -->
          <div class="glass-card p-5 mt-4">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">风险贡献归因</h4>
              <span class="text-sm card-label" v-if="riskContribData">组合波动率: {{ formatPercent(riskContribData.portfolio_volatility) }}</span>
            </div>
            <el-table v-if="riskContribData" :data="riskContribData.contributions" stripe size="small" v-loading="loadingRiskContrib">
              <el-table-column prop="product_name" label="产品" min-width="150" />
              <el-table-column label="权重" width="90" align="center">
                <template #default="{ row }">{{ (row.weight * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="MCTR" width="110" align="center">
                <template #default="{ row }">{{ (row.mctr * 100).toFixed(2) }}%</template>
              </el-table-column>
              <el-table-column label="CCTR" width="110" align="center">
                <template #default="{ row }">{{ (row.cctr * 100).toFixed(2) }}%</template>
              </el-table-column>
              <el-table-column label="风险贡献占比" width="120" align="center">
                <template #default="{ row }">
                  <el-progress :percentage="Math.min(Math.abs(row.risk_contribution_pct), 100)" :stroke-width="8" :show-text="false" />
                  <span class="text-xs">{{ row.risk_contribution_pct.toFixed(1) }}%</span>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else-if="!loadingRiskContrib" description="无法计算风险贡献" />
          </div>

          <!-- Brinson 第3层 管理人选择归因 -->
          <div class="glass-card p-5 mt-4">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">Brinson 第3层 — 管理人选择归因</h4>
              <span class="text-sm card-label" v-if="managerAttrData">总选择效应: <span :class="managerAttrData.total_selection_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(managerAttrData.total_selection_effect) }}</span></span>
            </div>
            <el-table v-if="managerAttrData" :data="managerAttrData.attributions" stripe size="small" v-loading="loadingManagerAttr">
              <el-table-column prop="manager_name" label="管理人" min-width="140" />
              <el-table-column prop="strategy" label="策略" width="100" />
              <el-table-column label="组合权重" width="100" align="center">
                <template #default="{ row }">{{ (row.portfolio_weight * 100).toFixed(1) }}%</template>
              </el-table-column>
              <el-table-column label="管理人收益" width="110" align="center">
                <template #default="{ row }"><span :class="row.portfolio_return >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.portfolio_return) }}</span></template>
              </el-table-column>
              <el-table-column label="基准收益" width="110" align="center">
                <template #default="{ row }">{{ formatPercent(row.benchmark_return) }}</template>
              </el-table-column>
              <el-table-column label="选择效应" width="110" align="center">
                <template #default="{ row }"><span :class="row.selection_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.selection_effect) }}</span></template>
              </el-table-column>
            </el-table>
            <el-empty v-else-if="!loadingManagerAttr" description="无法计算管理人归因" />
          </div>

          <!-- Brinson 第4层 个券选择归因 -->
          <div class="glass-card p-5 mt-4">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">Brinson 第4层 — 个券选择归因</h4>
              <div class="flex items-center gap-3" v-if="securityAttrData">
                <span class="text-xs card-label">选股效应: <span :class="securityAttrData.total_stock_selection >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(securityAttrData.total_stock_selection) }}</span></span>
                <span class="text-xs card-label">行业配置: <span :class="securityAttrData.total_sector_allocation >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(securityAttrData.total_sector_allocation) }}</span></span>
              </div>
            </div>
            <el-table v-if="securityAttrData" :data="securityAttrData.attributions" stripe size="small" v-loading="loadingSecurityAttr" max-height="400">
              <el-table-column prop="security_code" label="证券代码" width="100" />
              <el-table-column prop="security_name" label="证券名称" min-width="120" />
              <el-table-column prop="product_name" label="所属产品" min-width="140" />
              <el-table-column label="权重" width="80" align="center">
                <template #default="{ row }">{{ (row.weight * 100).toFixed(2) }}%</template>
              </el-table-column>
              <el-table-column label="个券收益" width="100" align="center">
                <template #default="{ row }"><span :class="row.return_rate >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.return_rate) }}</span></template>
              </el-table-column>
              <el-table-column label="选股效应" width="100" align="center">
                <template #default="{ row }"><span :class="row.stock_selection_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.stock_selection_effect) }}</span></template>
              </el-table-column>
              <el-table-column label="行业配置" width="100" align="center">
                <template #default="{ row }"><span :class="row.sector_allocation_effect >= 0 ? 'positive-value' : 'negative-value'">{{ formatPercent(row.sector_allocation_effect) }}</span></template>
              </el-table-column>
            </el-table>
            <el-empty v-else-if="!loadingSecurityAttr" description="无底层持仓明细数据，请先导入四级估值表" />
          </div>
        </el-tab-pane>

        <!-- 因子分析 -->
        <el-tab-pane label="因子分析" name="factorAnalysis">
          <div class="glass-card p-5" v-loading="loadingFactor">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">Barra 多因子分析</h4>
              <span class="text-sm card-label" v-if="factorData">分析期间: {{ factorData.start_date }} ~ {{ factorData.end_date }}</span>
            </div>
            <div v-if="factorData">
              <!-- 组合因子暴露雷达图 + 因子收益分解柱状图 -->
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div>
                  <h5 class="text-sm font-medium card-title mb-2">组合因子暴露</h5>
                  <div ref="factorRadarRef" style="height: 350px"></div>
                </div>
                <div>
                  <h5 class="text-sm font-medium card-title mb-2">因子收益贡献</h5>
                  <div ref="factorBarRef" style="height: 350px"></div>
                </div>
              </div>
              <!-- 产品因子明细表 -->
              <h5 class="text-sm font-medium card-title mb-2">产品因子明细</h5>
              <el-table :data="factorData.product_details" stripe size="small">
                <el-table-column prop="product_name" label="产品" min-width="150" />
                <el-table-column label="Alpha(年化)" width="110" align="center">
                  <template #default="{ row }"><span :class="row.alpha >= 0 ? 'positive-value' : 'negative-value'">{{ (row.alpha * 100).toFixed(2) }}%</span></template>
                </el-table-column>
                <el-table-column label="残差(年化)" width="110" align="center">
                  <template #default="{ row }">{{ (row.residual * 100).toFixed(2) }}%</template>
                </el-table-column>
                <el-table-column label="R²" width="80" align="center">
                  <template #default="{ row }">{{ row.r_squared.toFixed(3) }}</template>
                </el-table-column>
                <el-table-column v-for="(factor, idx) in factorLabels" :key="idx" :label="factor" width="90" align="center">
                  <template #default="{ row }">
                    <span v-if="row.exposures[idx]">{{ row.exposures[idx].exposure.toFixed(2) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <el-empty v-else description="数据不足，无法进行因子分析" />
          </div>
        </el-tab-pane>

        <!-- 持仓明细 -->
        <el-tab-pane label="持仓明细" name="holdings">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">持仓明细</h4>
              <div class="flex items-center gap-3">
                <el-select v-model="holdingDate" placeholder="选择日期" clearable style="width: 180px" @change="fetchHoldings">
                  <el-option v-for="d in holdingDates" :key="d" :label="d" :value="d" />
                </el-select>
                <el-button type="primary" size="small" @click="showAddHoldingDialog">
                  <el-icon class="mr-1"><Plus /></el-icon>
                  录入持仓
                </el-button>
              </div>
            </div>

            <!-- 持仓汇总 -->
            <div class="grid grid-cols-3 gap-4 mb-4" v-if="holdingsData && holdingsData.items.length > 0">
              <div class="metric-card">
                <span class="metric-label">总市值</span>
                <span class="metric-value">{{ formatAmount(holdingsData.total_market_value) }}</span>
              </div>
              <div class="metric-card">
                <span class="metric-label">总盈亏</span>
                <span class="metric-value" :class="holdingsData.total_pnl >= 0 ? 'positive-value' : 'negative-value'">
                  {{ formatAmount(holdingsData.total_pnl) }}
                </span>
              </div>
              <div class="metric-card">
                <span class="metric-label">持仓数</span>
                <span class="metric-value">{{ holdingsData.total }}</span>
              </div>
            </div>

            <!-- 持仓表格 -->
            <el-table :data="holdingsData?.items || []" stripe v-loading="loadingHoldings">
              <el-table-column prop="product_name" label="产品名称" min-width="160">
                <template #default="{ row }">
                  <div>
                    <span class="text-white">{{ row.product_name }}</span>
                    <span class="text-xs text-dark-400 block">{{ row.product_code }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="shares" label="份额" width="120" align="right">
                <template #default="{ row }">
                  {{ row.shares?.toLocaleString() || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="market_value" label="市值" width="140" align="right">
                <template #default="{ row }">
                  {{ formatAmount(row.market_value) }}
                </template>
              </el-table-column>
              <el-table-column prop="weight" label="占比" width="100" align="center">
                <template #default="{ row }">
                  <span class="font-medium text-primary-400">{{ (row.weight * 100).toFixed(1) }}%</span>
                </template>
              </el-table-column>
              <el-table-column prop="cost" label="成本" width="140" align="right">
                <template #default="{ row }">
                  {{ formatAmount(row.cost) }}
                </template>
              </el-table-column>
              <el-table-column prop="pnl" label="盈亏" width="140" align="right">
                <template #default="{ row }">
                  <span :class="row.pnl >= 0 ? 'positive-value' : 'negative-value'">
                    {{ formatAmount(row.pnl) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="pnl_ratio" label="盈亏比" width="100" align="center">
                <template #default="{ row }">
                  <span :class="row.pnl_ratio >= 0 ? 'positive-value' : 'negative-value'">
                    {{ formatPercent(row.pnl_ratio) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!holdingsData || holdingsData.items.length === 0" description="暂无持仓数据" />

            <!-- 资产配置饼图 -->
            <div class="mt-6" v-if="holdingsData && holdingsData.items.length > 0">
              <h5 class="text-base font-semibold card-title mb-3">资产配置</h5>
              <div ref="allocationPieRef" style="height: 300px"></div>
            </div>
          </div>

          <!-- 底层持仓分析(四级估值表) -->
          <div class="glass-card p-5 mt-4">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">底层持仓分析 (四级估值表)</h4>
              <el-button type="primary" size="small" @click="showImportDetailDialog">
                <el-icon class="mr-1"><Plus /></el-icon>
                导入底层持仓
              </el-button>
            </div>
            <div v-if="holdingsAnalysis" v-loading="loadingHoldingsAnalysis">
              <!-- 集中度指标 -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div class="metric-card">
                  <span class="metric-label">前5大集中度</span>
                  <span class="metric-value">{{ formatPercent(holdingsAnalysis.concentration.top5_weight) }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">前10大集中度</span>
                  <span class="metric-value">{{ formatPercent(holdingsAnalysis.concentration.top10_weight) }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">前20大集中度</span>
                  <span class="metric-value">{{ formatPercent(holdingsAnalysis.concentration.top20_weight) }}</span>
                </div>
                <div class="metric-card">
                  <span class="metric-label">HHI指数</span>
                  <span class="metric-value">{{ holdingsAnalysis.concentration.hhi.toFixed(4) }}</span>
                </div>
              </div>
              <!-- 行业分布 + 市值分布 -->
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-4">
                <div>
                  <h5 class="text-sm font-medium card-title mb-2">行业分布 (申万一级)</h5>
                  <div ref="industryPieRef" style="height: 300px"></div>
                </div>
                <div>
                  <h5 class="text-sm font-medium card-title mb-2">市值分布</h5>
                  <div ref="capDistPieRef" style="height: 300px"></div>
                </div>
              </div>
              <!-- 证券类型分布 -->
              <div class="mt-4">
                <h5 class="text-sm font-medium card-title mb-2">证券类型分布</h5>
                <el-table :data="holdingsAnalysis.security_type_dist" stripe size="small">
                  <el-table-column prop="label" label="类型" width="120" />
                  <el-table-column label="权重" width="120" align="center">
                    <template #default="{ row }">{{ formatPercent(row.weight) }}</template>
                  </el-table-column>
                  <el-table-column prop="count" label="数量" width="100" align="center" />
                </el-table>
              </div>
            </div>
            <el-empty v-else-if="!loadingHoldingsAnalysis" description="无底层持仓数据，请导入四级估值表" />
          </div>
        </el-tab-pane>

        <!-- 调仓历史 -->
        <el-tab-pane label="调仓历史" name="adjustments">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">调仓历史</h4>
              <el-button type="primary" size="small" @click="showRecordAdjustmentDialog">
                <el-icon class="mr-1"><Plus /></el-icon>
                记录调仓
              </el-button>
            </div>

            <el-timeline v-if="adjustments.length > 0">
              <el-timeline-item 
                v-for="adj in adjustments" 
                :key="adj.id" 
                :timestamp="adj.adjust_date" 
                placement="top"
                :type="getAdjustmentTimelineType(adj.adjust_type)"
              >
                <div class="glass-card p-4">
                  <div class="flex items-center gap-2 mb-2">
                    <el-tag size="small" :type="getAdjustmentTagType(adj.adjust_type)">
                      {{ getAdjustmentLabel(adj.adjust_type) }}
                    </el-tag>
                    <span class="text-xs card-label">{{ adj.created_at?.split('T')[0] }}</span>
                  </div>
                  <p class="text-sm card-desc" v-if="adj.description">{{ adj.description }}</p>
                  <div class="mt-2 text-xs card-label" v-if="adj.before_weights || adj.after_weights">
                    <span v-if="adj.before_weights">调整前: {{ adj.before_weights }}</span>
                    <span v-if="adj.after_weights" class="ml-3">调整后: {{ adj.after_weights }}</span>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无调仓记录" />
          </div>
        </el-tab-pane>

        <!-- 调仓模拟 -->
        <el-tab-pane label="调仓模拟" name="simulate">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">调仓模拟 (What-if)</h4>
              <el-button type="primary" size="small" @click="runSimulation" :loading="loadingSimulate">运行模拟</el-button>
            </div>
            <!-- 权重调整输入 -->
            <div class="mb-4" v-if="selectedPortfolio">
              <el-table :data="simWeights" stripe size="small">
                <el-table-column prop="product_name" label="产品" min-width="160" />
                <el-table-column label="当前权重" width="110" align="center">
                  <template #default="{ row }">{{ (row.original_weight * 100).toFixed(1) }}%</template>
                </el-table-column>
                <el-table-column label="模拟权重" width="160" align="center">
                  <template #default="{ row }">
                    <el-input-number v-model="row.new_weight" :min="0" :max="100" :step="5" :precision="1" size="small" style="width: 120px" />
                  </template>
                </el-table-column>
              </el-table>
              <div class="mt-2 text-sm card-label">模拟权重合计: <span :class="simWeightTotal === 100 ? 'positive-value' : 'warning-value'">{{ simWeightTotal.toFixed(1) }}%</span></div>
            </div>
            <!-- 模拟结果 -->
            <div v-if="simulateResult" class="mt-4">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div class="metric-card" v-for="(label, key) in {total_return:'总收益', volatility:'波动率', max_drawdown:'最大回撤', sharpe_ratio:'夏普比率'}" :key="key">
                  <span class="metric-label">{{ label }}</span>
                  <div class="flex justify-center gap-3">
                    <span class="text-xs card-label">原: {{ key === 'sharpe_ratio' ? simulateResult.original_metrics[key]?.toFixed(2) : formatPercent(simulateResult.original_metrics[key]) }}</span>
                    <span class="text-xs" :class="compareMetric(key) ? 'positive-value' : 'negative-value'">模: {{ key === 'sharpe_ratio' ? simulateResult.simulated_metrics[key]?.toFixed(2) : formatPercent(simulateResult.simulated_metrics[key]) }}</span>
                  </div>
                </div>
              </div>
              <div ref="simulateChartRef" style="height: 350px"></div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 风险监控 -->
        <el-tab-pane label="风险监控" name="riskMonitor">
          <div class="glass-card p-5">
            <div class="flex justify-between items-center mb-4">
              <h4 class="text-lg font-semibold card-title">风险预算配置</h4>
              <el-button type="primary" size="small" @click="saveRiskBudget" :loading="savingRiskBudget">保存配置</el-button>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <span class="text-xs card-label">最大回撤阈值</span>
                <el-input-number v-model="riskBudgetForm.max_drawdown" :min="0" :max="100" :step="1" :precision="1" size="small" style="width: 100%" />
                <span class="text-xs card-desc">%</span>
              </div>
              <div>
                <span class="text-xs card-label">波动率阈值</span>
                <el-input-number v-model="riskBudgetForm.volatility" :min="0" :max="100" :step="1" :precision="1" size="small" style="width: 100%" />
                <span class="text-xs card-desc">%</span>
              </div>
              <div>
                <span class="text-xs card-label">最低夏普比率</span>
                <el-input-number v-model="riskBudgetForm.sharpe_min" :min="-10" :max="10" :step="0.1" :precision="2" size="small" style="width: 100%" />
              </div>
              <div>
                <span class="text-xs card-label">单一成分最大权重</span>
                <el-input-number v-model="riskBudgetForm.max_single_weight" :min="0" :max="100" :step="5" :precision="1" size="small" style="width: 100%" />
                <span class="text-xs card-desc">%</span>
              </div>
            </div>

            <!-- 告警状态 -->
            <div v-if="riskCheckResult">
              <h5 class="text-base font-semibold card-title mb-3">风险检查结果</h5>
              <div v-if="riskCheckResult.alerts.length > 0" class="space-y-2">
                <el-alert v-for="(alert, idx) in riskCheckResult.alerts" :key="idx"
                  :title="`${alert.label}: 当前 ${formatPercent4(alert.current)} / 阈值 ${formatPercent4(alert.threshold)}`"
                  :type="alert.severity === 'danger' ? 'error' : 'warning'" show-icon :closable="false" />
              </div>
              <el-result v-else icon="success" title="所有指标均在安全范围内" />
            </div>
          </div>

          <!-- 穿透分析 -->
          <div class="glass-card p-5 mt-4">
            <h4 class="text-lg font-semibold card-title mb-4">穿透分析</h4>
            <div v-if="lookthroughData" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h5 class="text-sm font-medium card-title mb-2">按策略类型</h5>
                <div ref="strategyPieRef" style="height: 280px"></div>
              </div>
              <div>
                <h5 class="text-sm font-medium card-title mb-2">按管理人</h5>
                <div ref="managerPieRef" style="height: 280px"></div>
              </div>
            </div>
            <el-empty v-else description="无穿透数据" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 创建/编辑组合对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑组合' : '新建组合'" 
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="组合名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入组合名称" />
        </el-form-item>
        <el-form-item label="组合代码" prop="portfolio_code">
          <el-input v-model="formData.portfolio_code" placeholder="请输入组合代码（如 FOF001）" />
        </el-form-item>
        <el-form-item label="组合类型" prop="portfolio_type">
          <el-radio-group v-model="formData.portfolio_type">
            <el-radio-button v-for="t in PORTFOLIO_TYPE_OPTIONS" :key="t.value" :value="t.value">
              {{ t.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="组合描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入组合描述" />
        </el-form-item>
        <el-form-item label="初始金额" prop="initial_amount">
          <el-input-number v-model="formData.initial_amount" :min="0" :precision="2" :step="100000" placeholder="请输入初始金额" style="width: 100%" />
        </el-form-item>
        <el-form-item label="基准指数" prop="benchmark_code">
          <el-select v-model="formData.benchmark_code" placeholder="请选择基准指数" clearable style="width: 100%">
            <el-option 
              v-for="b in BENCHMARK_OPTIONS" 
              :key="b.value" 
              :label="b.label" 
              :value="b.value" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="起始日期" prop="start_date">
          <el-date-picker 
            v-model="formData.start_date" 
            type="date" 
            placeholder="选择起始日期" 
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status" v-if="isEdit">
          <el-select v-model="formData.status" style="width: 100%">
            <el-option v-for="s in PORTFOLIO_STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑成分对话框 -->
    <el-dialog 
      v-model="componentDialogVisible" 
      :title="isEditComponent ? '编辑成分' : '添加成分'" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="componentFormData" :rules="componentFormRules" ref="componentFormRef" label-width="100px">
        <el-form-item label="选择产品" prop="product_id" v-if="!isEditComponent">
          <el-select 
            v-model="componentFormData.product_id" 
            placeholder="搜索并选择产品" 
            filterable 
            remote
            :remote-method="searchProducts"
            :loading="searchingProducts"
            style="width: 100%"
          >
            <el-option 
              v-for="p in productOptions" 
              :key="p.id" 
              :label="`${p.product_name} (${p.product_code})`" 
              :value="p.id"
            >
              <div class="flex justify-between items-center">
                <span>{{ p.product_name }}</span>
                <span class="text-xs text-dark-400">{{ p.product_code }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="权重" prop="weight">
          <el-input-number 
            v-model="componentFormData.weight" 
            :min="0" 
            :max="100" 
            :precision="1"
            :step="5"
            style="width: 100%"
          >
            <template #suffix>%</template>
          </el-input-number>
        </el-form-item>
        <el-form-item label="加入日期" prop="join_date" v-if="!isEditComponent">
          <el-date-picker 
            v-model="componentFormData.join_date" 
            type="date" 
            placeholder="选择加入日期" 
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="componentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleComponentSubmit" :loading="submittingComponent">确定</el-button>
      </template>
    </el-dialog>

    <!-- 持仓录入对话框 -->
    <el-dialog v-model="holdingDialogVisible" title="录入持仓" width="700px" :close-on-click-modal="false">
      <el-form :model="holdingFormData" label-width="100px">
        <el-form-item label="持仓日期" required>
          <el-date-picker v-model="holdingFormData.holding_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-divider content-position="left">持仓明细</el-divider>
        <div v-for="(item, idx) in holdingFormData.holdings" :key="idx" class="flex items-center gap-2 mb-3">
          <el-select v-model="item.product_id" placeholder="选择产品" filterable remote :remote-method="searchProducts" :loading="searchingProducts" style="width: 200px">
            <el-option v-for="p in productOptions" :key="p.id" :label="p.product_name" :value="p.id" />
          </el-select>
          <el-input-number v-model="item.shares" :min="0" placeholder="份额" style="width: 130px" />
          <el-input-number v-model="item.market_value" :min="0" :precision="2" placeholder="市值" style="width: 150px" />
          <el-input-number v-model="item.cost" :min="0" :precision="2" placeholder="成本" style="width: 150px" />
          <el-button text type="danger" @click="holdingFormData.holdings.splice(idx, 1)"><el-icon><Delete /></el-icon></el-button>
        </div>
        <el-button size="small" @click="holdingFormData.holdings.push({ product_id: null, shares: 0, market_value: 0, cost: 0 })">
          <el-icon class="mr-1"><Plus /></el-icon>添加一行
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="holdingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveHoldings" :loading="savingHoldings">保存</el-button>
      </template>
    </el-dialog>

    <!-- 调仓记录对话框 -->
    <el-dialog v-model="adjustmentDialogVisible" title="记录调仓" width="600px" :close-on-click-modal="false">
      <el-form :model="adjustmentFormData" label-width="100px">
        <el-form-item label="调仓日期" required>
          <el-date-picker v-model="adjustmentFormData.adjust_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="调仓类型" required>
          <el-select v-model="adjustmentFormData.adjust_type" style="width: 100%">
            <el-option v-for="t in ADJUSTMENT_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="adjustmentFormData.description" type="textarea" :rows="3" placeholder="请输入调仓说明" />
        </el-form-item>
        <el-divider content-position="left">调整后权重</el-divider>
        <div v-for="(item, idx) in adjustmentFormData.components" :key="idx" class="flex items-center gap-2 mb-3">
          <el-select v-model="item.product_id" placeholder="选择产品" filterable remote :remote-method="searchProducts" :loading="searchingProducts" style="width: 220px">
            <el-option v-for="p in productOptions" :key="p.id" :label="p.product_name" :value="p.id" />
          </el-select>
          <el-input-number v-model="item.weight" :min="0" :max="100" :precision="1" :step="5" style="width: 140px">
            <template #suffix>%</template>
          </el-input-number>
          <el-button text type="danger" @click="adjustmentFormData.components.splice(idx, 1)"><el-icon><Delete /></el-icon></el-button>
        </div>
        <el-button size="small" @click="adjustmentFormData.components.push({ product_id: null as any, weight: 0 })">
          <el-icon class="mr-1"><Plus /></el-icon>添加成分
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="adjustmentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRecordAdjustment" :loading="savingAdjustment">保存</el-button>
      </template>
    </el-dialog>

    <!-- 底层持仓导入对话框 -->
    <el-dialog v-model="importDetailDialogVisible" title="导入底层持仓（四级估值表）" width="500px">
      <div class="mb-4">
        <p class="text-sm card-desc mb-2">支持Excel文件，列名要求：证券代码、证券名称、持仓数量、市值、成本、所属产品ID</p>
        <el-upload
          ref="importUploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleImportFileChange"
          drag
        >
          <el-icon class="text-3xl mb-2"><Plus /></el-icon>
          <div>点击或拖拽Excel文件到此处</div>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="importDetailDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImportDetail" :loading="importingDetail">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete, ArrowLeft } from '@element-plus/icons-vue'
import { portfolioApi } from '@/api/portfolio'
import { productApi } from '@/api/product'
import * as echarts from 'echarts'
import type { 
  Portfolio, PortfolioListItem, PortfolioCreate, PortfolioUpdate,
  PortfolioPerformance, PortfolioNavResponse, PortfolioContribution,
  PortfolioComponent, ComponentCreate, PortfolioType,
  HoldingsResponse, PortfolioAdjustment, AdjustmentType
} from '@/types/portfolio'
import { PORTFOLIO_STATUS_OPTIONS, PORTFOLIO_TYPE_OPTIONS, BENCHMARK_OPTIONS, PERIOD_OPTIONS, ADJUSTMENT_TYPE_OPTIONS } from '@/types/portfolio'

// 状态
const loading = ref(false)
const portfolios = ref<PortfolioListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const searchKey = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 组合详情
const selectedPortfolio = ref<Portfolio | null>(null)
const performance = ref<PortfolioPerformance | null>(null)
const navData = ref<PortfolioNavResponse | null>(null)
const contribution = ref<PortfolioContribution | null>(null)
const activeTab = ref('components')
const selectedPeriod = ref('3m')
const loadingNav = ref(false)
const loadingContribution = ref(false)
const loadingHoldings = ref(false)

// 持仓明细
const holdingsData = ref<HoldingsResponse | null>(null)
const holdingDate = ref('')
const holdingDates = ref<string[]>([])

// 调仓历史
const adjustments = ref<PortfolioAdjustment[]>([])
const loadingAdjustments = ref(false)

// Brinson归因 + 风险归因
const brinsonData = ref<any>(null)
const loadingBrinson = ref(false)
const riskContribData = ref<any>(null)
const loadingRiskContrib = ref(false)

// Brinson 第3层 管理人归因
const managerAttrData = ref<any>(null)
const loadingManagerAttr = ref(false)

// Brinson 第4层 个券归因
const securityAttrData = ref<any>(null)
const loadingSecurityAttr = ref(false)

// 多因子分析
const factorData = ref<any>(null)
const loadingFactor = ref(false)
const factorLabels = computed(() => factorData.value?.portfolio_exposures?.map((e: any) => e.factor_label) || [])

// 底层持仓分析
const holdingsAnalysis = ref<any>(null)
const loadingHoldingsAnalysis = ref(false)

// 调仓模拟
const simWeights = ref<any[]>([])
const simulateResult = ref<any>(null)
const loadingSimulate = ref(false)

// 风险监控
const riskBudgetForm = ref({ max_drawdown: null as number | null, volatility: null as number | null, sharpe_min: null as number | null, max_single_weight: null as number | null })
const riskCheckResult = ref<any>(null)
const savingRiskBudget = ref(false)
const lookthroughData = ref<any>(null)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref()
const formData = ref<PortfolioCreate & { status?: string }>({
  name: '',
  portfolio_code: '',
  portfolio_type: 'invested' as PortfolioType,
  description: '',
  benchmark_code: '',
  start_date: '',
  initial_amount: undefined
})

// 成分对话框
const componentDialogVisible = ref(false)
const isEditComponent = ref(false)
const submittingComponent = ref(false)
const componentFormRef = ref()
const componentFormData = ref({
  product_id: null as number | null,
  weight: 10,
  join_date: ''
})
const editingComponentId = ref<number | null>(null)

// 产品搜索
const searchingProducts = ref(false)
const productOptions = ref<any[]>([])

// 图表引用
const navChartRef = ref<HTMLElement>()
const contributionPieRef = ref<HTMLElement>()
const contributionBarRef = ref<HTMLElement>()
const allocationPieRef = ref<HTMLElement>()
const simulateChartRef = ref<HTMLElement>()
const strategyPieRef = ref<HTMLElement>()
const managerPieRef = ref<HTMLElement>()
const factorRadarRef = ref<HTMLElement>()
const factorBarRef = ref<HTMLElement>()
const industryPieRef = ref<HTMLElement>()
const capDistPieRef = ref<HTMLElement>()
let navChart: echarts.ECharts | null = null
let contributionPieChart: echarts.ECharts | null = null
let contributionBarChart: echarts.ECharts | null = null
let allocationPieChart: echarts.ECharts | null = null
let simulateChart: echarts.ECharts | null = null
let strategyPieChart: echarts.ECharts | null = null
let managerPieChart: echarts.ECharts | null = null
let factorRadarChart: echarts.ECharts | null = null
let factorBarChart: echarts.ECharts | null = null
let industryPieChart: echarts.ECharts | null = null
let capDistPieChart: echarts.ECharts | null = null

const resizeAllCharts = () => {
  navChart?.resize()
  contributionPieChart?.resize()
  contributionBarChart?.resize()
  allocationPieChart?.resize()
  simulateChart?.resize()
  strategyPieChart?.resize()
  managerPieChart?.resize()
  factorRadarChart?.resize()
  factorBarChart?.resize()
  industryPieChart?.resize()
  capDistPieChart?.resize()
}

const disposeAllCharts = () => {
  navChart?.dispose(); navChart = null
  contributionPieChart?.dispose(); contributionPieChart = null
  contributionBarChart?.dispose(); contributionBarChart = null
  allocationPieChart?.dispose(); allocationPieChart = null
  simulateChart?.dispose(); simulateChart = null
  strategyPieChart?.dispose(); strategyPieChart = null
  managerPieChart?.dispose(); managerPieChart = null
  factorRadarChart?.dispose(); factorRadarChart = null
  factorBarChart?.dispose(); factorBarChart = null
  industryPieChart?.dispose(); industryPieChart = null
  capDistPieChart?.dispose(); capDistPieChart = null
}

// 计算属性
const totalWeight = computed(() => {
  if (!selectedPortfolio.value) return 0
  return selectedPortfolio.value.components.reduce((sum, c) => sum + Number(c.weight), 0)
})

const navCoverageLevel = computed(() => {
  const quality = navData.value?.nav_quality
  if (!quality) {
    return {
      label: '未知',
      type: 'info',
      description: '暂无可用覆盖率数据。',
      risk: false,
      level: 'unknown' as const
    }
  }

  const score = Math.min(
    Number(quality.coverage_ratio ?? 0),
    Number(quality.avg_weight_coverage ?? 0)
  )

  if (score >= 0.98) {
    return {
      label: '高',
      type: 'success',
      description: '净值数据覆盖充分，结果解释性较强。',
      risk: false,
      level: 'high' as const
    }
  }
  if (score >= 0.9) {
    return {
      label: '中',
      type: 'warning',
      description: '存在少量缺失，建议结合调仓和底层净值做复核。',
      risk: false,
      level: 'medium' as const
    }
  }
  return {
    label: '低',
    type: 'danger',
    description: '缺失较多，建议先补齐底层净值后再解读收益归因。',
    risk: true,
    level: 'low' as const
  }
})

const navQualityAlert = computed(() => {
  const quality = navData.value?.nav_quality
  if (!quality) return null

  const level = navCoverageLevel.value.level
  if (level === 'low') {
    return {
      type: 'error',
      title: '净值数据完整度偏低',
      description: `当前有效日期 ${quality.effective_dates} 天，仅成功计算 ${quality.calculated_dates} 天。建议先补齐底层净值再做业绩解读。`
    }
  }
  if (level === 'medium') {
    return {
      type: 'warning',
      title: '净值数据完整度中等',
      description: `当前覆盖率 ${formatPercent(quality.coverage_ratio)}，权重覆盖率 ${formatPercent(quality.avg_weight_coverage)}。建议重点复核跳过日期与补值日期。`
    }
  }
  if (quality.carry_forward_dates > 0 || quality.skipped_dates > 0) {
    return {
      type: 'info',
      title: '净值数据存在补值',
      description: `本期补值日期 ${quality.carry_forward_dates} 天，跳过日期 ${quality.skipped_dates} 天。建议在重大调仓节点复核底层净值完整性。`
    }
  }
  return null
})

const getCoverageValueClass = (ratio: number | null | undefined) => {
  const value = Number(ratio ?? 0)
  if (value >= 0.98) return 'positive-value'
  if (value >= 0.9) return 'warning-value'
  return 'negative-value'
}

// 表单校验规则
const formRules = {
  name: [{ required: true, message: '请输入组合名称', trigger: 'blur' }]
}

const componentFormRules = {
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  weight: [{ required: true, message: '请输入权重', trigger: 'blur' }]
}

// 方法
const fetchPortfolios = async () => {
  loading.value = true
  try {
    const res: any = await portfolioApi.getList({
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize,
      status: statusFilter.value || undefined,
      search: searchKey.value || undefined
    })
    // 兼容响应拦截器返回 response.data 或完整 AxiosResponse
    const data = res?.data ?? res
    if (data && Array.isArray(data.items)) {
      portfolios.value = data.items
      total.value = data.total ?? 0
    } else if (Array.isArray(res)) {
      portfolios.value = res
      total.value = res.length
    } else {
      console.warn('组合列表响应格式异常:', res)
      portfolios.value = []
      total.value = 0
    }
  } catch (error: any) {
    console.error('获取组合列表失败:', error)
    ElMessage.error('获取组合列表失败: ' + (error?.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const selectPortfolio = async (id: number) => {
  try {
    const portfolio = await portfolioApi.getById(id)
    selectedPortfolio.value = portfolio
    activeTab.value = 'components'
    await fetchPortfolioData()
  } catch (error) {
    ElMessage.error('获取组合详情失败')
  }
}

const fetchPortfolioData = async () => {
  if (!selectedPortfolio.value) return
  
  const portfolioId = selectedPortfolio.value.id
  
  // 获取业绩指标
  try {
    performance.value = await portfolioApi.getPerformance(portfolioId, selectedPeriod.value)
  } catch (error) {
    console.error('获取业绩指标失败:', error)
    performance.value = null
  }

  // 根据当前标签页加载数据
  if (activeTab.value === 'nav') {
    await fetchNavData()
  } else if (activeTab.value === 'contribution') {
    await fetchContribution()
  } else if (activeTab.value === 'holdings') {
    await fetchHoldings()
  } else if (activeTab.value === 'adjustments') {
    await fetchAdjustments()
  }
}

const formatLocalDate = (value: Date) => {
  const y = value.getFullYear()
  const m = String(value.getMonth() + 1).padStart(2, '0')
  const d = String(value.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const formatSignedPercent = (value: number | null | undefined, digits = 2) => {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '-'
  const pct = Number(value) * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(digits)}%`
}

const getPeriodDates = (period: string): { startDate?: string; endDate?: string } => {
  const end = new Date()
  const endStr = formatLocalDate(end)
  let start = new Date()
  switch (period) {
    case '1w': start.setDate(start.getDate() - 7); break
    case '1m': start.setMonth(start.getMonth() - 1); break
    case '3m': start.setMonth(start.getMonth() - 3); break
    case '6m': start.setMonth(start.getMonth() - 6); break
    case '1y': start.setFullYear(start.getFullYear() - 1); break
    case 'ytd': start = new Date(end.getFullYear(), 0, 1); break
    case 'inception': return {} // 成立以来返回全历史区间
    default: start.setMonth(start.getMonth() - 3)
  }
  return { startDate: formatLocalDate(start), endDate: endStr }
}

const fetchNavData = async () => {
  if (!selectedPortfolio.value) return
  loadingNav.value = true
  try {
    const { startDate, endDate } = getPeriodDates(selectedPeriod.value)
    navData.value = await portfolioApi.getNav(selectedPortfolio.value.id, startDate, endDate)
    await nextTick()
    // 等待 tab-pane DOM 渲染完成
    await new Promise(resolve => setTimeout(resolve, 50))
    renderNavChart()
  } catch (error) {
    console.error('获取净值数据失败:', error)
  } finally {
    loadingNav.value = false
  }
}

const fetchContribution = async () => {
  if (!selectedPortfolio.value) return
  loadingContribution.value = true
  try {
    contribution.value = await portfolioApi.getContribution(selectedPortfolio.value.id)
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))
    renderContributionCharts()
  } catch (error) {
    console.error('获取贡献数据失败:', error)
  } finally {
    loadingContribution.value = false
  }
}

const renderNavChart = () => {
  if (!navChartRef.value || !navData.value) return

  if (!navChart || navChart.getDom() !== navChartRef.value) {
    navChart?.dispose()
    navChart = echarts.init(navChartRef.value)
  }

  const series = navData.value.nav_series || []
  if (series.length === 0) {
    navChart.setOption({
      title: {
        text: '暂无净值数据',
        left: 'center',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 14, fontWeight: 400 }
      },
      xAxis: { show: false },
      yAxis: { show: false },
      series: []
    }, true)
    navChart.resize()
    return
  }

  const dates = series.map(p => p.date)
  const values = series.map(p => Number(p.nav))
  const baseNav = values[0] || 1

  navChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(59, 130, 246, 0.3)',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        const data = params[0]
        const point = series[data.dataIndex]
        const pointNav = Number(point?.nav ?? data.value)
        const dailyReturn = point?.daily_return ?? 0
        const cumulativeReturn = baseNav > 0 ? pointNav / baseNav - 1 : 0
        return [
          `${data.name}`,
          `净值: ${pointNav.toFixed(4)}`,
          `日收益: ${formatSignedPercent(dailyReturn)}`,
          `区间累计: ${formatSignedPercent(cumulativeReturn)}`
        ].join('<br/>')
      }
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#1e293b' } },
      min: (value: any) => Number((value.min * 0.99).toFixed(4))
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#3b82f6', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
        ])
      }
    }]
  }, true)
  navChart.resize()
}

const fetchHoldings = async () => {
  if (!selectedPortfolio.value) return
  loadingHoldings.value = true
  try {
    const res = await portfolioApi.getHoldings(selectedPortfolio.value.id, holdingDate.value || undefined)
    holdingsData.value = res
    holdingDates.value = res.available_dates || []
    if (!holdingDate.value && holdingDates.value.length > 0) {
      holdingDate.value = holdingDates.value[0]
    }
    await nextTick()
    renderAllocationPie()
  } catch (error) {
    console.error('获取持仓数据失败:', error)
  } finally {
    loadingHoldings.value = false
  }
}

const fetchAdjustments = async () => {
  if (!selectedPortfolio.value) return
  loadingAdjustments.value = true
  try {
    const res = await portfolioApi.getAdjustments(selectedPortfolio.value.id)
    adjustments.value = res.items || []
  } catch (error) {
    console.error('获取调仓记录失败:', error)
  } finally {
    loadingAdjustments.value = false
  }
}

const renderAllocationPie = () => {
  if (!allocationPieRef.value || !holdingsData.value || holdingsData.value.items.length === 0) return

  if (!allocationPieChart) {
    allocationPieChart = echarts.init(allocationPieRef.value)
  }

  const pieData = holdingsData.value.items.map(h => ({
    name: h.product_name || '未知',
    value: h.market_value
  }))

  allocationPieChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(59, 130, 246, 0.3)',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        return `${params.name}<br/>市值: ${formatAmount(params.value)}<br/>占比: ${params.percent}%`
      }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#94a3b8' }
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: {
        label: { show: true, fontWeight: 'bold' }
      },
      data: pieData
    }]
  })
}

const renderContributionCharts = () => {
  if (!contribution.value) return
  
  // 饼图
  if (contributionPieRef.value) {
    if (contributionPieChart) contributionPieChart.dispose()
    contributionPieChart = echarts.init(contributionPieRef.value)
    
    const pieData = contribution.value.contributions.map(c => ({
      name: c.product_name,
      value: Math.abs(c.contribution * 100)
    }))
    
    contributionPieChart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: 'rgba(59, 130, 246, 0.3)',
        textStyle: { color: '#fff' },
        formatter: '{b}: {d}%'
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#94a3b8' }
      },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        emphasis: {
          label: { show: true, fontWeight: 'bold' }
        },
        data: pieData
      }]
    })
  }
  
  // 柱状图
  if (contributionBarRef.value) {
    if (contributionBarChart) contributionBarChart.dispose()
    contributionBarChart = echarts.init(contributionBarRef.value)
    
    const sorted = [...contribution.value.contributions].sort((a, b) => b.contribution - a.contribution)
    const names = sorted.map(c => c.product_name)
    const values = sorted.map(c => (c.contribution * 100).toFixed(2))
    const colors = sorted.map(c => c.contribution >= 0 ? '#10b981' : '#ef4444')
    
    contributionBarChart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: 'rgba(59, 130, 246, 0.3)',
        textStyle: { color: '#fff' },
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '5%',
        bottom: '3%',
        top: '5%',
        containLabel: true
      },
      xAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { 
          color: '#94a3b8',
          formatter: '{value}%'
        },
        splitLine: { lineStyle: { color: '#1e293b' } }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: '#334155' } },
        axisLabel: { color: '#94a3b8' }
      },
      series: [{
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: colors[i] }
        })),
        barWidth: 20
      }]
    })
  }
}

// 对话框方法
const showCreateDialog = () => {
  isEdit.value = false
  formData.value = {
    name: '',
    portfolio_code: '',
    portfolio_type: 'invested' as PortfolioType,
    description: '',
    benchmark_code: '',
    start_date: '',
    initial_amount: undefined
  }
  dialogVisible.value = true
}

const showEditDialog = (portfolio: PortfolioListItem | Portfolio) => {
  isEdit.value = true
  formData.value = {
    name: portfolio.name,
    portfolio_code: portfolio.portfolio_code || '',
    portfolio_type: portfolio.portfolio_type || 'invested',
    description: portfolio.description || '',
    benchmark_code: (portfolio as Portfolio).benchmark_code || '',
    start_date: portfolio.start_date || '',
    initial_amount: (portfolio as Portfolio).initial_amount || undefined,
    status: portfolio.status
  }
  editingComponentId.value = portfolio.id
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    if (isEdit.value && editingComponentId.value) {
      await portfolioApi.update(editingComponentId.value, formData.value as PortfolioUpdate)
      ElMessage.success('更新成功')
      if (selectedPortfolio.value?.id === editingComponentId.value) {
        await selectPortfolio(editingComponentId.value)
      }
    } else {
      await portfolioApi.create(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchPortfolios()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除该组合吗？', '确认删除', {
      type: 'warning'
    })
    await portfolioApi.delete(id)
    ElMessage.success('删除成功')
    fetchPortfolios()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 成分管理方法
const searchProducts = async (query: string) => {
  if (!query) {
    productOptions.value = []
    return
  }
  searchingProducts.value = true
  try {
    const res = await productApi.getList({ search: query, limit: 20 })
    productOptions.value = res.items
  } catch (error) {
    console.error('搜索产品失败:', error)
  } finally {
    searchingProducts.value = false
  }
}

const showAddComponentDialog = () => {
  isEditComponent.value = false
  componentFormData.value = {
    product_id: null,
    weight: 10,
    join_date: ''
  }
  productOptions.value = []
  componentDialogVisible.value = true
}

const showEditComponentDialog = (component: PortfolioComponent) => {
  isEditComponent.value = true
  componentFormData.value = {
    product_id: component.product_id,
    weight: Number(component.weight) * 100,
    join_date: component.join_date || ''
  }
  editingComponentId.value = component.id
  componentDialogVisible.value = true
}

const handleComponentSubmit = async () => {
  const valid = await componentFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  if (!selectedPortfolio.value) return
  
  submittingComponent.value = true
  try {
    if (isEditComponent.value && editingComponentId.value) {
      await portfolioApi.updateComponent(editingComponentId.value, {
        weight: componentFormData.value.weight / 100
      })
      ElMessage.success('更新成功')
    } else {
      await portfolioApi.addComponent(selectedPortfolio.value.id, {
        product_id: componentFormData.value.product_id!,
        weight: componentFormData.value.weight / 100,
        join_date: componentFormData.value.join_date || undefined
      })
      ElMessage.success('添加成功')
    }
    componentDialogVisible.value = false
    await selectPortfolio(selectedPortfolio.value.id)
  } catch (error) {
    ElMessage.error(isEditComponent.value ? '更新失败' : '添加失败')
  } finally {
    submittingComponent.value = false
  }
}

const handleRemoveComponent = async (componentId: number) => {
  if (!selectedPortfolio.value) return
  
  try {
    await ElMessageBox.confirm('确定要移除该成分吗？', '确认移除', {
      type: 'warning'
    })
    await portfolioApi.removeComponent(componentId)
    ElMessage.success('移除成功')
    await selectPortfolio(selectedPortfolio.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// 工具函数
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

const formatPercent = (value: number | string | undefined) => {
  if (value === undefined || value === null) return '-'
  const num = Number(value)
  if (isNaN(num)) return '-'
  return (num * 100).toFixed(2) + '%'
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    active: 'success',
    archived: 'warning'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const option = PORTFOLIO_STATUS_OPTIONS.find(s => s.value === status)
  return option?.label || status
}

const getTypeTagType = (type: string) => {
  return type === 'invested' ? 'primary' : 'warning'
}

const getTypeLabel = (type: string) => {
  const option = PORTFOLIO_TYPE_OPTIONS.find(t => t.value === type)
  return option?.label || type
}

const formatAmount = (value: number | undefined | null) => {
  if (value === undefined || value === null) return '-'
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getAdjustmentLabel = (type: string) => {
  const option = ADJUSTMENT_TYPE_OPTIONS.find(t => t.value === type)
  return option?.label || type
}

const getAdjustmentTagType = (type: string) => {
  const map: Record<string, string> = {
    rebalance: 'primary',
    add: 'success',
    remove: 'danger',
    weight_change: 'warning'
  }
  return map[type] || 'info'
}

const getAdjustmentTimelineType = (type: string) => {
  const map: Record<string, string> = {
    rebalance: 'primary',
    add: 'success',
    remove: 'danger',
    weight_change: 'warning'
  }
  return map[type] || 'primary'
}

// ============ 持仓录入 ============
const holdingDialogVisible = ref(false)
const savingHoldings = ref(false)
const holdingFormData = ref<{ holding_date: string; holdings: { product_id: number | null; shares: number; market_value: number; cost: number }[] }>({
  holding_date: '',
  holdings: [{ product_id: null, shares: 0, market_value: 0, cost: 0 }]
})

const showAddHoldingDialog = () => {
  holdingFormData.value = {
    holding_date: formatLocalDate(new Date()),
    holdings: selectedPortfolio.value?.components
      .filter(c => c.is_active !== false)
      .map(c => ({ product_id: c.product_id, shares: 0, market_value: 0, cost: 0 })) || [{ product_id: null, shares: 0, market_value: 0, cost: 0 }]
  }
  holdingDialogVisible.value = true
}

const handleSaveHoldings = async () => {
  if (!selectedPortfolio.value || !holdingFormData.value.holding_date) {
    ElMessage.warning('请填写持仓日期'); return
  }
  const valid = holdingFormData.value.holdings.filter(h => h.product_id && h.market_value > 0)
  if (valid.length === 0) { ElMessage.warning('请至少填写一条有效持仓'); return }
  savingHoldings.value = true
  try {
    await portfolioApi.saveHoldings(selectedPortfolio.value.id, {
      holding_date: holdingFormData.value.holding_date,
      holdings: valid
    })
    ElMessage.success('持仓录入成功')
    holdingDialogVisible.value = false
    fetchHoldings()
  } catch (e) { ElMessage.error('录入失败') } finally { savingHoldings.value = false }
}

// ============ 调仓记录 ============
const adjustmentDialogVisible = ref(false)
const savingAdjustment = ref(false)
const adjustmentFormData = ref<{ adjust_date: string; adjust_type: AdjustmentType; description: string; components: { product_id: number; weight: number }[] }>({
  adjust_date: '',
  adjust_type: 'rebalance',
  description: '',
  components: []
})

const showRecordAdjustmentDialog = () => {
  adjustmentFormData.value = {
    adjust_date: formatLocalDate(new Date()),
    adjust_type: 'rebalance',
    description: '',
    components: selectedPortfolio.value?.components
      .filter(c => c.is_active !== false)
      .map(c => ({ product_id: c.product_id, weight: Number(c.weight) * 100 })) || []
  }
  adjustmentDialogVisible.value = true
}

const handleRecordAdjustment = async () => {
  if (!selectedPortfolio.value || !adjustmentFormData.value.adjust_date) {
    ElMessage.warning('请填写调仓日期'); return
  }
  savingAdjustment.value = true
  try {
    await portfolioApi.recordAdjustment(selectedPortfolio.value.id, {
      adjust_date: adjustmentFormData.value.adjust_date,
      adjust_type: adjustmentFormData.value.adjust_type,
      description: adjustmentFormData.value.description || undefined,
      components: adjustmentFormData.value.components
        .filter(c => c.product_id)
        .map(c => ({ product_id: c.product_id, weight: c.weight / 100 }))
    })
    ElMessage.success('调仓记录已保存')
    adjustmentDialogVisible.value = false
    fetchAdjustments()
  } catch (e) { ElMessage.error('保存失败') } finally { savingAdjustment.value = false }
}

// ============ Brinson归因 + 风险归因 ============
const fetchBrinsonAttribution = async () => {
  if (!selectedPortfolio.value) return
  loadingBrinson.value = true
  try {
    brinsonData.value = await portfolioApi.getBrinsonAttribution(selectedPortfolio.value.id)
  } catch (e) { brinsonData.value = null } finally { loadingBrinson.value = false }
}

const fetchRiskContribution = async () => {
  if (!selectedPortfolio.value) return
  loadingRiskContrib.value = true
  try {
    riskContribData.value = await portfolioApi.getRiskContribution(selectedPortfolio.value.id)
  } catch (e) { riskContribData.value = null } finally { loadingRiskContrib.value = false }
}

// ============ Brinson 第3层 管理人归因 ============
const fetchManagerAttr = async () => {
  if (!selectedPortfolio.value) return
  loadingManagerAttr.value = true
  try {
    managerAttrData.value = await portfolioApi.getBrinsonManagerAttribution(selectedPortfolio.value.id)
  } catch (e) { managerAttrData.value = null } finally { loadingManagerAttr.value = false }
}

// ============ Brinson 第4层 个券归因 ============
const fetchSecurityAttr = async () => {
  if (!selectedPortfolio.value) return
  loadingSecurityAttr.value = true
  try {
    securityAttrData.value = await portfolioApi.getBrinsonSecurityAttribution(selectedPortfolio.value.id)
  } catch (e) { securityAttrData.value = null } finally { loadingSecurityAttr.value = false }
}

// ============ 多因子分析 ============
const fetchFactorAnalysis = async () => {
  if (!selectedPortfolio.value) return
  loadingFactor.value = true
  try {
    factorData.value = await portfolioApi.getFactorAnalysis(selectedPortfolio.value.id)
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))
    renderFactorCharts()
  } catch (e) { factorData.value = null } finally { loadingFactor.value = false }
}

const renderFactorCharts = () => {
  if (!factorData.value) return
  const exposures = factorData.value.portfolio_exposures

  // 雷达图
  if (factorRadarRef.value) {
    if (factorRadarChart) factorRadarChart.dispose()
    factorRadarChart = echarts.init(factorRadarRef.value)
    const maxVal = Math.max(...exposures.map((x: any) => Math.abs(x.exposure))) * 1.5 || 1
    const indicators = exposures.map((e: any) => ({ name: e.factor_label, max: maxVal, min: -maxVal }))
    factorRadarChart.setOption({
      tooltip: { backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(59,130,246,0.3)', textStyle: { color: '#fff' },
        formatter: (params: any) => {
          const data = params.data || params
          if (!data.value) return ''
          return data.value.map((v: number, i: number) => `${exposures[i].factor_label}: ${v.toFixed(4)}`).join('<br/>')
        }
      },
      radar: { indicator: indicators, shape: 'circle', center: ['50%', '55%'],
        axisLine: { lineStyle: { color: '#334155' } }, splitLine: { lineStyle: { color: '#1e293b' } },
        axisName: { color: '#94a3b8', fontSize: 11 },
        splitArea: { areaStyle: { color: ['rgba(30,41,59,0.3)', 'rgba(15,23,42,0.3)'] } }
      },
      series: [{ type: 'radar', data: [{ value: exposures.map((e: any) => e.exposure), name: '因子暴露',
        areaStyle: { color: 'rgba(59,130,246,0.2)' }, lineStyle: { color: '#3b82f6', width: 2 }, itemStyle: { color: '#3b82f6' } }] }]
    })
    factorRadarChart.resize()
  }

  // 因子收益贡献柱状图
  if (factorBarRef.value) {
    if (factorBarChart) factorBarChart.dispose()
    factorBarChart = echarts.init(factorBarRef.value)
    const labels = exposures.map((e: any) => e.factor_label)
    const contributions = exposures.map((e: any) => Number((e.contribution * 100).toFixed(4)))
    const colors = exposures.map((e: any) => e.contribution >= 0 ? '#10b981' : '#ef4444')
    factorBarChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(59,130,246,0.3)', textStyle: { color: '#fff' }, axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const p = params[0]
          return `${p.name}<br/>贡献: ${Number(p.value).toFixed(4)}%`
        }
      },
      grid: { left: '3%', right: '5%', bottom: '3%', top: '5%', containLabel: true },
      xAxis: { type: 'category', data: labels, axisLabel: { color: '#94a3b8', rotate: 30 }, axisLine: { lineStyle: { color: '#334155' } } },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#1e293b' } } },
      series: [{ type: 'bar', data: contributions.map((v: number, i: number) => ({ value: v, itemStyle: { color: colors[i] } })), barWidth: 30 }]
    })
    factorBarChart.resize()
  }
}

// ============ 底层持仓分析 ============
const fetchHoldingsAnalysis = async () => {
  if (!selectedPortfolio.value) return
  loadingHoldingsAnalysis.value = true
  try {
    holdingsAnalysis.value = await portfolioApi.getHoldingsDetailAnalysis(selectedPortfolio.value.id)
    await nextTick()
    renderHoldingsAnalysisCharts()
  } catch (e) { holdingsAnalysis.value = null } finally { loadingHoldingsAnalysis.value = false }
}

const renderHoldingsAnalysisCharts = () => {
  if (!holdingsAnalysis.value) return
  const makePie = (el: HTMLElement | undefined, chart: echarts.ECharts | null, data: any[]) => {
    if (!el) return null
    if (!chart) chart = echarts.init(el)
    chart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(59,130,246,0.3)', textStyle: { color: '#fff' } },
      legend: { orient: 'vertical', right: '5%', top: 'center', textStyle: { color: '#94a3b8' }, type: 'scroll' },
      series: [{ type: 'pie', radius: ['40%', '65%'], center: ['35%', '50%'], label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } }, data }]
    })
    return chart
  }
  industryPieChart = makePie(industryPieRef.value, industryPieChart, holdingsAnalysis.value.industry_l1.map((i: any) => ({ name: i.industry, value: i.weight })))
  capDistPieChart = makePie(capDistPieRef.value, capDistPieChart, holdingsAnalysis.value.market_cap_dist.map((i: any) => ({ name: i.cap_label, value: i.weight })))
}

// ============ 底层持仓导入 ============
const importDetailDialogVisible = ref(false)
const importingDetail = ref(false)
const importUploadRef = ref()
const importFile = ref<File | null>(null)

const showImportDetailDialog = () => {
  importFile.value = null
  importDetailDialogVisible.value = true
}

const handleImportFileChange = (file: any) => {
  importFile.value = file.raw || file
}

const handleImportDetail = async () => {
  if (!selectedPortfolio.value || !importFile.value) {
    ElMessage.warning('请选择文件'); return
  }
  importingDetail.value = true
  try {
    // 读取Excel文件
    const arrayBuffer = await importFile.value.arrayBuffer()
    const { read, utils } = await import('xlsx')
    const wb = read(arrayBuffer, { type: 'array' })
    const ws = wb.Sheets[wb.SheetNames[0]]
    const rows: any[] = utils.sheet_to_json(ws)

    // 列名映射
    const colMap: Record<string, string> = {
      '证券代码': 'security_code', '证券名称': 'security_name',
      '持仓数量': 'quantity', '市值': 'market_value', '成本': 'cost',
      '所属产品ID': 'product_id', 'product_id': 'product_id',
      'security_code': 'security_code', 'security_name': 'security_name',
      'quantity': 'quantity', 'market_value': 'market_value', 'cost': 'cost'
    }
    const items = rows.map(r => {
      const mapped: Record<string, any> = {}
      for (const [key, val] of Object.entries(r)) {
        const target = colMap[key]
        if (target) mapped[target] = val
      }
      return mapped
    }).filter(i => i.security_code)

    if (items.length === 0) { ElMessage.warning('未解析到有效数据'); return }

    await portfolioApi.importHoldingsDetail(selectedPortfolio.value.id, { items })
    ElMessage.success(`成功导入${items.length}条底层持仓`)
    importDetailDialogVisible.value = false
    fetchHoldingsAnalysis()
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally { importingDetail.value = false }
}

// ============ 调仓模拟 ============
const simWeightTotal = computed(() => simWeights.value.reduce((s, w) => s + (w.new_weight || 0), 0))

const initSimWeights = () => {
  if (!selectedPortfolio.value) return
  simWeights.value = selectedPortfolio.value.components
    .filter(c => c.is_active !== false)
    .map(c => ({
      product_id: c.product_id,
      product_name: c.product_name || c.product_code || String(c.product_id),
      original_weight: Number(c.weight) * 100,
      new_weight: Number(c.weight) * 100
    }))
  simulateResult.value = null
}

const runSimulation = async () => {
  if (!selectedPortfolio.value) return
  loadingSimulate.value = true
  try {
    const weights = simWeights.value.map(w => ({ product_id: w.product_id, weight: w.new_weight / 100 }))
    simulateResult.value = await portfolioApi.simulateRebalance(selectedPortfolio.value.id, { weights })
    await nextTick()
    renderSimulateChart()
  } catch (e) { ElMessage.error('模拟失败') } finally { loadingSimulate.value = false }
}

const compareMetric = (key: string) => {
  if (!simulateResult.value) return true
  const o = simulateResult.value.original_metrics[key] ?? 0
  const s = simulateResult.value.simulated_metrics[key] ?? 0
  if (key === 'max_drawdown' || key === 'volatility') return s <= o
  return s >= o
}

const renderSimulateChart = () => {
  if (!simulateChartRef.value || !simulateResult.value) return
  if (!simulateChart) simulateChart = echarts.init(simulateChartRef.value)
  const origDates = simulateResult.value.original_nav.map((p: any) => p.date)
  const origNav = simulateResult.value.original_nav.map((p: any) => p.nav)
  const simNav = simulateResult.value.simulated_nav.map((p: any) => p.nav)
  simulateChart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(59,130,246,0.3)', textStyle: { color: '#fff' } },
    legend: { data: ['原组合', '模拟组合'], textStyle: { color: '#94a3b8' } },
    grid: { left: '3%', right: '3%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: origDates, axisLabel: { color: '#94a3b8' }, axisLine: { lineStyle: { color: '#334155' } } },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b' } } },
    series: [
      { name: '原组合', type: 'line', data: origNav, smooth: true, symbol: 'none', lineStyle: { color: '#3b82f6', width: 2 } },
      { name: '模拟组合', type: 'line', data: simNav, smooth: true, symbol: 'none', lineStyle: { color: '#f59e0b', width: 2, type: 'dashed' } }
    ]
  })
}

// ============ 风险监控 ============
const fetchRiskBudget = async () => {
  if (!selectedPortfolio.value) return
  try {
    const res = await portfolioApi.getRiskBudget(selectedPortfolio.value.id)
    const cfg = res.config || {}
    riskBudgetForm.value = {
      max_drawdown: cfg.max_drawdown != null ? cfg.max_drawdown * 100 : null,
      volatility: cfg.volatility != null ? cfg.volatility * 100 : null,
      sharpe_min: cfg.sharpe_min ?? null,
      max_single_weight: cfg.max_single_weight != null ? cfg.max_single_weight * 100 : null
    }
  } catch (e) { /* ignore */ }
  // 检查超限
  try {
    riskCheckResult.value = await portfolioApi.checkRiskBudget(selectedPortfolio.value.id, '3m')
  } catch (e) { riskCheckResult.value = null }
}

const saveRiskBudget = async () => {
  if (!selectedPortfolio.value) return
  savingRiskBudget.value = true
  try {
    const cfg: any = {}
    if (riskBudgetForm.value.max_drawdown != null) cfg.max_drawdown = riskBudgetForm.value.max_drawdown / 100
    if (riskBudgetForm.value.volatility != null) cfg.volatility = riskBudgetForm.value.volatility / 100
    if (riskBudgetForm.value.sharpe_min != null) cfg.sharpe_min = riskBudgetForm.value.sharpe_min
    if (riskBudgetForm.value.max_single_weight != null) cfg.max_single_weight = riskBudgetForm.value.max_single_weight / 100
    await portfolioApi.updateRiskBudget(selectedPortfolio.value.id, cfg)
    ElMessage.success('风险预算已保存')
    riskCheckResult.value = await portfolioApi.checkRiskBudget(selectedPortfolio.value.id, '3m')
  } catch (e) { ElMessage.error('保存失败') } finally { savingRiskBudget.value = false }
}

const formatPercent4 = (v: number) => {
  if (v === undefined || v === null) return '-'
  return v < 1 ? (v * 100).toFixed(2) + '%' : v.toFixed(2) + '%'
}

// ============ 穿透分析 ============
const fetchLookthrough = async () => {
  if (!selectedPortfolio.value) return
  try {
    lookthroughData.value = await portfolioApi.getLookthrough(selectedPortfolio.value.id)
    await nextTick()
    renderLookthroughPies()
  } catch (e) { lookthroughData.value = null }
}

const renderLookthroughPies = () => {
  const renderPie = (el: HTMLElement | undefined, chart: echarts.ECharts | null, data: any[]) => {
    if (!el) return null
    if (!chart) chart = echarts.init(el)
    chart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: 'rgba(59,130,246,0.3)', textStyle: { color: '#fff' } },
      legend: { orient: 'vertical', right: '5%', top: 'center', textStyle: { color: '#94a3b8' } },
      series: [{ type: 'pie', radius: ['40%', '65%'], center: ['35%', '50%'], label: { show: false }, emphasis: { label: { show: true, fontWeight: 'bold' } }, data }]
    })
    return chart
  }
  if (lookthroughData.value) {
    strategyPieChart = renderPie(strategyPieRef.value, strategyPieChart, lookthroughData.value.by_strategy.map((g: any) => ({ name: g.name, value: g.weight })))
    managerPieChart = renderPie(managerPieRef.value, managerPieChart, lookthroughData.value.by_manager.map((g: any) => ({ name: g.name, value: g.weight })))
  }
}

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'nav') {
    fetchNavData()
  } else if (newTab === 'contribution') {
    fetchContribution()
    fetchBrinsonAttribution()
    fetchRiskContribution()
    fetchManagerAttr()
    fetchSecurityAttr()
  } else if (newTab === 'holdings') {
    fetchHoldings()
    fetchHoldingsAnalysis()
  } else if (newTab === 'adjustments') {
    fetchAdjustments()
  } else if (newTab === 'simulate') {
    initSimWeights()
  } else if (newTab === 'riskMonitor') {
    fetchRiskBudget()
    fetchLookthrough()
  } else if (newTab === 'factorAnalysis') {
    fetchFactorAnalysis()
  }
})

// 初始化
onMounted(() => {
  fetchPortfolios()
  window.addEventListener('resize', resizeAllCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeAllCharts)
  disposeAllCharts()
})
</script>

<style scoped>
.portfolio-view {
  min-height: 100vh;
}

/* 组合卡片 - 使用CSS变量自适应主题 */
.portfolio-card {
  background: var(--card-bg, rgba(15, 23, 42, 0.6));
  border: 1px solid var(--card-border, rgba(71, 85, 105, 0.3));
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

.portfolio-card:hover {
  border-color: var(--accent-color, #3b82f6);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* 卡片标题 */
.card-title {
  color: var(--text-primary, #ffffff);
}

/* 卡片描述 */
.card-desc {
  color: var(--text-muted, #94a3b8);
}

/* 卡片标签 */
.card-label {
  color: var(--text-muted, #94a3b8);
}

/* 卡片数值 */
.card-value {
  color: var(--text-primary, #ffffff);
}

/* 卡片分隔线 */
.card-divider {
  border-top: 1px solid var(--card-border, rgba(71, 85, 105, 0.3));
}

/* 指标卡片 */
.metric-card {
  background: var(--hover-bg, rgba(15, 23, 42, 0.5));
  border: 1px solid var(--card-border, transparent);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  margin-bottom: 6px;
}

.metric-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #fff);
}

/* 正负值颜色 */
.positive-value {
  color: #10b981 !important;
}

.negative-value {
  color: #ef4444 !important;
}

.warning-value {
  color: #f59e0b !important;
}

/* 权重汇总 */
.weight-summary {
  background: var(--hover-bg, rgba(15, 23, 42, 0.5));
}

/* 标签页 */
.portfolio-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}

.portfolio-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.portfolio-tabs :deep(.el-tabs__item) {
  color: var(--text-muted, #94a3b8);
}

.portfolio-tabs :deep(.el-tabs__item.is-active) {
  color: var(--accent-color, #3b82f6);
}

.portfolio-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--accent-color, #3b82f6);
}
</style>

