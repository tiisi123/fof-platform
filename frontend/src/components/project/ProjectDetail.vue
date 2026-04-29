<template>
  <div class="project-detail">
    <!-- 基本信息 -->
    <el-descriptions title="基本信息" :column="2" border>
      <el-descriptions-item label="项目编号">{{ project.project_code }}</el-descriptions-item>
      <el-descriptions-item label="项目名称">{{ project.project_name }}</el-descriptions-item>
      <el-descriptions-item label="行业">{{ getIndustryLabel(project.industry) }}</el-descriptions-item>
      <el-descriptions-item label="细分领域">{{ project.sub_industry || '-' }}</el-descriptions-item>
      <el-descriptions-item label="项目来源">{{ project.source || '-' }}</el-descriptions-item>
      <el-descriptions-item label="来源渠道">{{ project.source_channel || '-' }}</el-descriptions-item>
      <el-descriptions-item label="当前阶段">
        <el-tag :color="getStageColor(project.stage)" effect="dark">
          {{ getStageLabel(project.stage) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="负责人">{{ project.assigned_user_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系人">{{ project.contact_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系电话">{{ project.contact_phone || '-' }}</el-descriptions-item>
      <el-descriptions-item label="初步介绍" :span="2">{{ project.initial_intro || '-' }}</el-descriptions-item>
    </el-descriptions>

    <!-- 阶段信息统一展示 -->
    <div class="section">
      <div class="section-header">
        <h4>阶段详情</h4>
        <el-button type="primary" size="small" @click="openStageEditDialog">
          <el-icon><Edit /></el-icon>编辑阶段信息
        </el-button>
      </div>

      <!-- 初筛信息 -->
      <el-descriptions v-if="project.screening_date || project.screening_result || project.screening_notes" title="初筛信息" :column="2" border class="mb-3">
        <el-descriptions-item label="初筛日期">{{ project.screening_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="初筛结果">{{ project.screening_result || '-' }}</el-descriptions-item>
        <el-descriptions-item label="初筛备注" :span="2">{{ project.screening_notes || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 尽调信息 -->
      <el-descriptions v-if="project.dd_start_date || project.dd_conclusion" title="尽调信息" :column="2" border class="mb-3">
        <el-descriptions-item label="尽调开始">{{ project.dd_start_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="尽调结束">{{ project.dd_end_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="尽调结论" :span="2">{{ project.dd_conclusion || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 投决信息 -->
      <el-descriptions v-if="project.ic_date || project.ic_result" title="投决信息" :column="2" border class="mb-3">
        <el-descriptions-item label="投决日期">{{ project.ic_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="投决结果">{{ project.ic_result || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 投资信息 -->
      <el-descriptions v-if="project.investment_amount" title="投资信息" :column="2" border class="mb-3">
        <el-descriptions-item label="投资金额">{{ project.investment_amount?.toLocaleString() }} 万元</el-descriptions-item>
        <el-descriptions-item label="估值">{{ project.valuation?.toLocaleString() || '-' }} 万元</el-descriptions-item>
        <el-descriptions-item label="持股比例">{{ project.shareholding_ratio != null ? project.shareholding_ratio + '%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="投资日期">{{ project.investment_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="董事席位">{{ project.board_seat ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 退出信息 -->
      <el-descriptions v-if="project.exit_date || project.exit_method" title="退出信息" :column="2" border>
        <el-descriptions-item label="退出方式">{{ project.exit_method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="退出日期">{{ project.exit_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="退出金额">{{ project.exit_amount?.toLocaleString() || '-' }} 万元</el-descriptions-item>
        <el-descriptions-item label="IRR">{{ project.irr ? (project.irr * 100).toFixed(2) + '%' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="MOIC">{{ project.moic?.toFixed(2) || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 尚无阶段信息 -->
      <el-empty v-if="!project.screening_date && !project.screening_result && !project.dd_start_date && !project.dd_conclusion && !project.ic_date && !project.investment_amount && !project.exit_date" description="尚无阶段信息，点击“编辑阶段信息”录入" :image-size="40" />
    </div>

    <!-- 跟进记录 -->
    <div class="section">
      <div class="section-header">
        <h4>跟进记录</h4>
        <el-button type="primary" size="small" @click="showFollowUpDialog = true">
          <el-icon><Plus /></el-icon>
          添加跟进
        </el-button>
      </div>
      <el-timeline v-if="project.follow_ups?.length">
        <el-timeline-item
          v-for="item in project.follow_ups"
          :key="item.id"
          :timestamp="item.follow_date"
          placement="top"
        >
          <el-card>
            <div class="follow-up-header">
              <el-tag size="small">{{ item.follow_type || '其他' }}</el-tag>
              <span class="follow-user">{{ item.follow_user_name }}</span>
            </div>
            <p>{{ item.content }}</p>
            <p v-if="item.next_plan" class="next-plan">
              <strong>下一步：</strong>{{ item.next_plan }}
            </p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无跟进记录" />
    </div>

    <!-- 评审意见 -->
    <div class="section">
      <div class="section-header">
        <h4>评审意见</h4>
        <el-button type="primary" size="small" @click="showReviewDialog = true">
          <el-icon><Plus /></el-icon>添加评审意见
        </el-button>
      </div>

      <!-- 评审结果汇总 -->
      <div v-if="reviewSummary" class="review-summary">
        <el-tag type="success" effect="dark" size="small">通过 {{ reviewSummary.approve }}</el-tag>
        <el-tag type="danger" effect="dark" size="small">否决 {{ reviewSummary.reject }}</el-tag>
        <el-tag type="warning" effect="dark" size="small">有条件 {{ reviewSummary.conditional }}</el-tag>
        <el-tag type="info" effect="dark" size="small">弃权 {{ reviewSummary.abstain }}</el-tag>
      </div>

      <!-- 评审列表 -->
      <el-table :data="reviews" size="small" stripe v-if="reviews.length" class="mt-2">
        <el-table-column prop="meeting_date" label="会议日期" width="110" />
        <el-table-column prop="reviewer_name" label="评审人" width="100" />
        <el-table-column prop="reviewer_role" label="职位" width="100" />
        <el-table-column prop="result" label="结果" width="90">
          <template #default="{ row }">
            <el-tag :type="reviewResultType(row.result)" size="small">{{ reviewResultLabel(row.result) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="opinion" label="评审意见" min-width="200" show-overflow-tooltip />
        <el-table-column prop="conditions" label="附加条件" min-width="150" show-overflow-tooltip />
        <el-table-column prop="risk_notes" label="风险提示" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="60">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="handleDeleteReview(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无评审意见" :image-size="40" />
    </div>

    <!-- 现金流与IRR/MOIC -->
    <div class="section">
      <div class="section-header">
        <h4>现金流 / IRR / MOIC</h4>
        <div class="flex gap-2">
          <el-button type="success" size="small" @click="handleCalcIRR" :loading="calcLoading">计算IRR/MOIC</el-button>
          <el-button type="primary" size="small" @click="showCashflowDialog = true"><el-icon><Plus /></el-icon>添加现金流</el-button>
        </div>
      </div>
      <div v-if="irrResult" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <el-card shadow="never" class="text-center p-3">
          <div class="text-lg font-bold" :class="(irrResult.irr || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ irrResult.irr != null ? (irrResult.irr * 100).toFixed(2) + '%' : '-' }}</div>
          <div class="text-xs text-gray-400 mt-1">IRR</div>
        </el-card>
        <el-card shadow="never" class="text-center p-3">
          <div class="text-lg font-bold">{{ irrResult.moic?.toFixed(2) || '-' }}x</div>
          <div class="text-xs text-gray-400 mt-1">MOIC</div>
        </el-card>
        <el-card shadow="never" class="text-center p-3">
          <div class="text-lg font-bold">{{ irrResult.total_invested?.toLocaleString() || 0 }}</div>
          <div class="text-xs text-gray-400 mt-1">总投入(万)</div>
        </el-card>
        <el-card shadow="never" class="text-center p-3">
          <div class="text-lg font-bold">{{ irrResult.total_distributed?.toLocaleString() || 0 }}</div>
          <div class="text-xs text-gray-400 mt-1">总回收(万)</div>
        </el-card>
      </div>
      <el-table :data="cashflows" size="small" stripe v-if="cashflows.length">
        <el-table-column prop="cashflow_date" label="日期" width="120" />
        <el-table-column prop="cashflow_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.cashflow_type === 'investment' ? 'danger' : row.cashflow_type === 'distribution' ? 'success' : 'info'" size="small">
              {{ { investment: '投入', distribution: '回收', fee: '费用', other: '其他' }[row.cashflow_type] || row.cashflow_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额(万)" width="120" align="right">
          <template #default="{ row }"><span :class="row.amount >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ row.amount?.toLocaleString() }}</span></template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="handleDeleteCashflow(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无现金流记录" :image-size="40" />
    </div>

    <!-- 退出情景模拟 -->
    <div class="section">
      <div class="section-header">
        <h4>退出情景模拟</h4>
        <el-button type="primary" size="small" @click="handleRunSimulation" :loading="simLoading">计算模拟</el-button>
      </div>
      <div class="sim-scenarios">
        <div v-for="(sc, idx) in simScenarios" :key="idx" class="flex items-center gap-2 mb-2">
          <el-input v-model="sc.name" placeholder="场景名称" style="width: 120px" size="small" />
          <el-select v-model="sc.exit_method" placeholder="退出方式" size="small" style="width: 100px">
            <el-option v-for="m in EXIT_METHOD_OPTIONS" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
          <el-date-picker v-model="sc.exit_date" type="date" value-format="YYYY-MM-DD" placeholder="退出日期" size="small" style="width: 150px" />
          <el-input-number v-model="sc.exit_amount" :min="0" :precision="2" placeholder="退出金额(万)" size="small" style="width: 160px" />
          <el-button text type="danger" size="small" @click="simScenarios.splice(idx, 1)"><el-icon><Delete /></el-icon></el-button>
        </div>
        <el-button size="small" @click="simScenarios.push({ name: `场景${simScenarios.length + 1}`, exit_method: 'IPO', exit_date: '', exit_amount: 0 })">
          <el-icon class="mr-1"><Plus /></el-icon>添加场景
        </el-button>
      </div>
      <el-table v-if="simResults.length" :data="simResults" size="small" stripe class="mt-3">
        <el-table-column prop="name" label="场景" width="100" />
        <el-table-column prop="exit_method" label="退出方式" width="90" />
        <el-table-column prop="exit_date" label="退出日期" width="110" />
        <el-table-column prop="exit_amount" label="退出金额(万)" width="120" align="right">
          <template #default="{ row }">{{ row.exit_amount?.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="IRR" width="100" align="right">
          <template #default="{ row }">
            <span :class="(row.irr || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'">{{ row.irr != null ? (row.irr * 100).toFixed(2) + '%' : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="MOIC" width="80" align="right">
          <template #default="{ row }">{{ row.moic?.toFixed(2) || '-' }}x</template>
        </el-table-column>
        <el-table-column label="总回收(万)" width="110" align="right">
          <template #default="{ row }">{{ row.total_distributed?.toLocaleString() }}</template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 现金流预测 -->
    <div class="section">
      <div class="section-header">
        <h4>现金流预测</h4>
        <div class="flex gap-2 items-center">
          <el-date-picker v-model="forecastExit.exit_date" type="date" value-format="YYYY-MM-DD" placeholder="预期退出日" size="small" style="width: 150px" />
          <el-input-number v-model="forecastExit.exit_amount" :min="0" :precision="2" placeholder="退出金额(万)" size="small" style="width: 160px" />
          <el-button type="primary" size="small" @click="handleForecast" :loading="forecastLoading">生成预测</el-button>
        </div>
      </div>
      <div ref="forecastChartRef" style="height: 320px; width: 100%" v-if="forecastData.length"></div>
      <el-empty v-else description="设置预期退出参数并点击“生成预测”" :image-size="40" />
    </div>

    <!-- 阶段变更历史 -->
    <div class="section">
      <h4>阶段变更历史</h4>
      <el-table :data="project.stage_changes" v-if="project.stage_changes?.length" size="small">
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="变更">
          <template #default="{ row }">
            <el-tag size="small" :color="getStageColor(row.from_stage)">{{ getStageLabel(row.from_stage) }}</el-tag>
            <span style="margin: 0 8px">→</span>
            <el-tag size="small" :color="getStageColor(row.to_stage)">{{ getStageLabel(row.to_stage) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" />
        <el-table-column prop="operator_name" label="操作人" width="100" />
      </el-table>
      <el-empty v-else description="暂无变更记录" />
    </div>

    <!-- 讨论区 -->
    <div class="section">
      <CommentSection resource-type="project" :resource-id="project.id" />
    </div>

    <!-- 添加现金流对话框 -->
    <el-dialog v-model="showCashflowDialog" title="添加现金流" width="500px">
      <el-form :model="cashflowForm" label-width="80px">
        <el-form-item label="日期" required>
          <el-date-picker v-model="cashflowForm.cashflow_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="cashflowForm.cashflow_type" style="width: 100%">
            <el-option value="investment" label="投入" />
            <el-option value="distribution" label="回收/分配" />
            <el-option value="fee" label="费用" />
            <el-option value="other" label="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额(万)" required>
          <el-input-number v-model="cashflowForm.amount" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="cashflowForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCashflowDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddCashflow" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑阶段信息对话框 -->
    <el-dialog v-model="stageEditDialogVisible" title="编辑阶段信息" width="650px" :close-on-click-modal="false">
      <el-tabs v-model="stageEditTab">
        <el-tab-pane label="初筛" name="screening">
          <el-form :model="stageEditForm" label-width="90px">
            <el-form-item label="初筛日期"><el-date-picker v-model="stageEditForm.screening_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="初筛结果"><el-input v-model="stageEditForm.screening_result" /></el-form-item>
            <el-form-item label="初筛备注"><el-input v-model="stageEditForm.screening_notes" type="textarea" :rows="3" /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="尽调" name="dd">
          <el-form :model="stageEditForm" label-width="90px">
            <el-form-item label="开始日期"><el-date-picker v-model="stageEditForm.dd_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="结束日期"><el-date-picker v-model="stageEditForm.dd_end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="尽调结论"><el-input v-model="stageEditForm.dd_conclusion" type="textarea" :rows="4" /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="投决" name="ic">
          <el-form :model="stageEditForm" label-width="90px">
            <el-form-item label="投决日期"><el-date-picker v-model="stageEditForm.ic_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="投决结果"><el-input v-model="stageEditForm.ic_result" placeholder="通过 / 否决 / 有条件通过" /></el-form-item>
            <el-form-item label="投资金额(万)"><el-input-number v-model="stageEditForm.investment_amount" :min="0" :precision="2" style="width: 100%" /></el-form-item>
            <el-form-item label="估值(万)"><el-input-number v-model="stageEditForm.valuation" :min="0" :precision="2" style="width: 100%" /></el-form-item>
            <el-form-item label="持股比例(%)"><el-input-number v-model="stageEditForm.shareholding_ratio" :min="0" :max="100" :precision="2" style="width: 100%" /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="投后" name="post">
          <el-form :model="stageEditForm" label-width="90px">
            <el-form-item label="投资日期"><el-date-picker v-model="stageEditForm.investment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="董事席位"><el-switch v-model="stageEditForm.board_seat" /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="退出" name="exit">
          <el-form :model="stageEditForm" label-width="90px">
            <el-form-item label="退出方式">
              <el-select v-model="stageEditForm.exit_method" style="width: 100%">
                <el-option v-for="m in EXIT_METHOD_OPTIONS" :key="m.value" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="退出日期"><el-date-picker v-model="stageEditForm.exit_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
            <el-form-item label="退出金额(万)"><el-input-number v-model="stageEditForm.exit_amount" :min="0" :precision="2" style="width: 100%" /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="stageEditDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveStageInfo" :loading="savingStageInfo">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加跟进对话框 -->
    <el-dialog v-model="showFollowUpDialog" title="添加跟进记录" width="500px">
      <el-form :model="followUpForm" label-width="80px">
        <el-form-item label="跟进日期" required>
          <el-date-picker v-model="followUpForm.follow_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="跟进方式">
          <el-select v-model="followUpForm.follow_type" placeholder="请选择" style="width: 100%">
            <el-option v-for="opt in FOLLOW_TYPE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="跟进内容" required>
          <el-input v-model="followUpForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="下一步">
          <el-input v-model="followUpForm.next_plan" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFollowUpDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddFollowUp" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    <!-- 添加评审意见对话框 -->
    <el-dialog v-model="showReviewDialog" title="添加评审意见" width="550px">
      <el-form :model="reviewForm" label-width="90px">
        <el-form-item label="评审类型">
          <el-select v-model="reviewForm.review_type" style="width: 100%">
            <el-option value="screening" label="初筛评审" />
            <el-option value="dd" label="尽调评审" />
            <el-option value="ic" label="投决会评审" />
          </el-select>
        </el-form-item>
        <el-form-item label="会议日期">
          <el-date-picker v-model="reviewForm.meeting_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="评审人" required>
              <el-input v-model="reviewForm.reviewer_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="reviewForm.reviewer_role" placeholder="如：投决委员" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="评审结果" required>
          <el-radio-group v-model="reviewForm.result">
            <el-radio-button value="approve">通过</el-radio-button>
            <el-radio-button value="conditional">有条件通过</el-radio-button>
            <el-radio-button value="reject">否决</el-radio-button>
            <el-radio-button value="abstain">弃权</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="评审意见">
          <el-input v-model="reviewForm.opinion" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item v-if="reviewForm.result === 'conditional'" label="附加条件">
          <el-input v-model="reviewForm.conditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="风险提示">
          <el-input v-model="reviewForm.risk_notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddReview" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Edit } from '@element-plus/icons-vue'
import { projectApi } from '@/api'
import request from '@/api/request'
import * as echarts from 'echarts'
import CommentSection from '@/components/common/CommentSection.vue'
import type { Project, ProjectFollowUpCreate, ProjectStage, ProjectIndustry } from '@/types'
import { PROJECT_STAGE_OPTIONS, PROJECT_INDUSTRY_OPTIONS, FOLLOW_TYPE_OPTIONS, EXIT_METHOD_OPTIONS } from '@/types'

const props = defineProps<{
  project: Project
}>()

const emit = defineEmits(['refresh'])

const showFollowUpDialog = ref(false)
const showCashflowDialog = ref(false)
const submitting = ref(false)
const calcLoading = ref(false)
const cashflows = ref<any[]>([])
const irrResult = ref<any>(null)
const cashflowForm = reactive({ cashflow_date: '', cashflow_type: 'investment', amount: 0, description: '' })

// ============ 评审意见 ============
const showReviewDialog = ref(false)
const reviews = ref<any[]>([])
const reviewSummary = ref<any>(null)
const reviewForm = reactive({
  review_type: 'ic',
  meeting_date: new Date().toISOString().split('T')[0],
  reviewer_name: '',
  reviewer_role: '',
  result: 'approve',
  opinion: '',
  conditions: '',
  risk_notes: '',
})

const reviewResultLabel = (r: string) => ({ approve: '通过', reject: '否决', conditional: '有条件通过', abstain: '弃权' }[r] || r)
const reviewResultType = (r: string) => ({ approve: 'success', reject: 'danger', conditional: 'warning', abstain: 'info' }[r] || '')

const loadReviews = async () => {
  try {
    const res: any = await request.get(`/projects/${props.project.id}/reviews`)
    reviews.value = res.items || []
    reviewSummary.value = res.summary || null
  } catch { /* silent */ }
}

const handleAddReview = async () => {
  if (!reviewForm.reviewer_name || !reviewForm.result) { ElMessage.warning('请填写评审人和结果'); return }
  submitting.value = true
  try {
    await request.post(`/projects/${props.project.id}/reviews`, reviewForm)
    ElMessage.success('评审意见已添加')
    showReviewDialog.value = false
    Object.assign(reviewForm, { reviewer_name: '', reviewer_role: '', result: 'approve', opinion: '', conditions: '', risk_notes: '' })
    loadReviews()
  } catch (e: any) { ElMessage.error(e.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteReview = async (reviewId: number) => {
  await ElMessageBox.confirm('确定删除该评审意见？', '提示', { type: 'warning' })
  try {
    await request.delete(`/projects/${props.project.id}/reviews/${reviewId}`)
    ElMessage.success('已删除')
    loadReviews()
  } catch { /* handled */ }
}

const loadCashflows = async () => {
  try {
    const res: any = await request.get(`/projects/${props.project.id}/cashflows`)
    cashflows.value = res.items || []
  } catch { /* silent */ }
}

const handleAddCashflow = async () => {
  if (!cashflowForm.cashflow_date || !cashflowForm.amount) { ElMessage.warning('请填写日期和金额'); return }
  submitting.value = true
  try {
    await request.post(`/projects/${props.project.id}/cashflows`, cashflowForm)
    ElMessage.success('添加成功')
    showCashflowDialog.value = false
    Object.assign(cashflowForm, { cashflow_date: '', cashflow_type: 'investment', amount: 0, description: '' })
    loadCashflows()
  } catch (e: any) { ElMessage.error(e.message || '添加失败') } finally { submitting.value = false }
}

const handleDeleteCashflow = async (cfId: number) => {
  await ElMessageBox.confirm('确定删除该现金流记录？', '提示', { type: 'warning' })
  try {
    await request.delete(`/projects/${props.project.id}/cashflows/${cfId}`)
    ElMessage.success('已删除')
    loadCashflows()
  } catch { /* handled */ }
}

const handleCalcIRR = async () => {
  calcLoading.value = true
  try {
    irrResult.value = await request.post(`/projects/${props.project.id}/calculate-irr`)
    ElMessage.success('计算完成')
  } catch (e: any) { ElMessage.error(e.message || '计算失败') } finally { calcLoading.value = false }
}

// ============ 阶段信息编辑 ============
const stageEditDialogVisible = ref(false)
const savingStageInfo = ref(false)
const stageEditTab = ref('screening')
const stageEditForm = ref<any>({})

const stageTabMap: Record<string, string> = {
  sourcing: 'screening', screening: 'screening', due_diligence: 'dd',
  ic: 'ic', post_investment: 'post', exit: 'exit'
}

const openStageEditDialog = () => {
  stageEditTab.value = stageTabMap[props.project.stage] || 'screening'
  stageEditForm.value = {
    screening_date: props.project.screening_date || '',
    screening_result: props.project.screening_result || '',
    screening_notes: props.project.screening_notes || '',
    dd_start_date: props.project.dd_start_date || '',
    dd_end_date: props.project.dd_end_date || '',
    dd_conclusion: props.project.dd_conclusion || '',
    ic_date: props.project.ic_date || '',
    ic_result: props.project.ic_result || '',
    investment_amount: props.project.investment_amount || undefined,
    valuation: props.project.valuation || undefined,
    shareholding_ratio: props.project.shareholding_ratio || undefined,
    investment_date: props.project.investment_date || '',
    board_seat: props.project.board_seat || false,
    exit_method: props.project.exit_method || '',
    exit_date: props.project.exit_date || '',
    exit_amount: props.project.exit_amount || undefined,
  }
  stageEditDialogVisible.value = true
}

const handleSaveStageInfo = async () => {
  savingStageInfo.value = true
  try {
    // 只发送有值的字段
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(stageEditForm.value)) {
      if (v !== '' && v !== undefined && v !== null) payload[k] = v
    }
    await projectApi.update(props.project.id, payload)
    ElMessage.success('阶段信息已更新')
    stageEditDialogVisible.value = false
    emit('refresh')
  } catch (e: any) { ElMessage.error(e.message || '保存失败') } finally { savingStageInfo.value = false }
}

// ============ 退出情景模拟 ============
const simLoading = ref(false)
const simScenarios = ref<{ name: string; exit_method: string; exit_date: string; exit_amount: number }[]>([
  { name: '乐观', exit_method: 'IPO', exit_date: '', exit_amount: 0 },
  { name: '中性', exit_method: '并购', exit_date: '', exit_amount: 0 },
  { name: '悲观', exit_method: '回购', exit_date: '', exit_amount: 0 },
])
const simResults = ref<any[]>([])

const handleRunSimulation = async () => {
  const valid = simScenarios.value.filter(s => s.exit_date && s.exit_amount > 0)
  if (!valid.length) { ElMessage.warning('请填写至少一个完整场景'); return }
  simLoading.value = true
  try {
    const res: any = await request.post(`/projects/${props.project.id}/exit-simulation`, { scenarios: valid })
    simResults.value = res.scenarios || []
    ElMessage.success('模拟完成')
  } catch (e: any) { ElMessage.error(e.message || '模拟失败') } finally { simLoading.value = false }
}

// ============ 现金流预测 ============
const forecastLoading = ref(false)
const forecastChartRef = ref<HTMLElement>()
const forecastData = ref<any[]>([])
const forecastExit = reactive({ exit_date: '', exit_amount: 0 })
let forecastChart: echarts.ECharts | null = null

const handleForecast = async () => {
  forecastLoading.value = true
  try {
    const res: any = await request.post(`/projects/${props.project.id}/cashflow-forecast`, {
      exit_date: forecastExit.exit_date || undefined,
      exit_amount: forecastExit.exit_amount || undefined,
    })
    forecastData.value = res.items || []
    await nextTick()
    renderForecastChart()
  } catch (e: any) { ElMessage.error(e.message || '预测失败') } finally { forecastLoading.value = false }
}

const renderForecastChart = () => {
  if (!forecastChartRef.value || !forecastData.value.length) return
  if (forecastChart) forecastChart.dispose()
  forecastChart = echarts.init(forecastChartRef.value)

  const dates = forecastData.value.map(d => d.date)
  const histAmounts = forecastData.value.map(d => d.is_forecast ? null : d.amount)
  const fcAmounts = forecastData.value.map(d => d.is_forecast ? d.amount : null)
  const cumulative = forecastData.value.map(d => d.cumulative)

  forecastChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史现金流', '预测现金流', '累计现金流'] },
    grid: { left: 60, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', name: '金额(万)', axisLabel: { fontSize: 11 } },
      { type: 'value', name: '累计', axisLabel: { fontSize: 11 } },
    ],
    series: [
      { name: '历史现金流', type: 'bar', data: histAmounts, itemStyle: { color: '#409eff' } },
      { name: '预测现金流', type: 'bar', data: fcAmounts, itemStyle: { color: '#e6a23c', borderType: 'dashed' } },
      { name: '累计现金流', type: 'line', yAxisIndex: 1, data: cumulative, smooth: true, lineStyle: { color: '#67c23a', width: 2 }, symbol: 'circle', symbolSize: 6 },
    ],
  })
}

onMounted(() => {
  loadCashflows()
  loadReviews()
})

const followUpForm = reactive<ProjectFollowUpCreate>({
  follow_date: new Date().toISOString().split('T')[0],
  follow_type: '',
  content: '',
  next_plan: ''
})

const getStageLabel = (stage?: ProjectStage) => {
  return PROJECT_STAGE_OPTIONS.find(s => s.value === stage)?.label || stage || '-'
}

const getStageColor = (stage?: ProjectStage) => {
  return PROJECT_STAGE_OPTIONS.find(s => s.value === stage)?.color || '#909399'
}

const getIndustryLabel = (industry?: ProjectIndustry) => {
  return PROJECT_INDUSTRY_OPTIONS.find(i => i.value === industry)?.label || industry || '-'
}

const formatDateTime = (dateStr: string) => {
  return dateStr ? dateStr.replace('T', ' ').substring(0, 16) : ''
}

const handleAddFollowUp = async () => {
  if (!followUpForm.follow_date || !followUpForm.content) {
    ElMessage.warning('请填写跟进日期和内容')
    return
  }
  
  submitting.value = true
  try {
    await projectApi.addFollowUp(props.project.id, followUpForm)
    ElMessage.success('添加成功')
    showFollowUpDialog.value = false
    followUpForm.content = ''
    followUpForm.next_plan = ''
    emit('refresh')
  } catch (error: any) {
    ElMessage.error(error.message || '添加失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.project-detail {
  padding: 10px;
}

.section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h4 {
  margin: 0;
}

.follow-up-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.follow-user {
  color: #909399;
  font-size: 12px;
}

.next-plan {
  color: #E6A23C;
  font-size: 13px;
  margin-top: 10px;
}

.review-summary {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.mt-2 { margin-top: 8px; }
</style>
