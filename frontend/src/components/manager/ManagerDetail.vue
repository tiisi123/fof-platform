<template>
  <div class="manager-detail">
    <!-- 基本信息 -->
    <el-descriptions title="基本信息" :column="2" border>
      <el-descriptions-item label="管理人编号">{{ manager.manager_code }}</el-descriptions-item>
      <el-descriptions-item label="管理人名称">{{ manager.manager_name }}</el-descriptions-item>
      <el-descriptions-item label="简称">{{ manager.short_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="备案编号">{{ manager.registration_no || '-' }}</el-descriptions-item>
      <el-descriptions-item label="跟踪池">
        <el-tag :color="getPoolColor(manager.pool_category)" effect="dark">
          {{ getPoolLabel(manager.pool_category) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="一级策略">{{ getStrategyLabel(manager.primary_strategy) }}</el-descriptions-item>
      <el-descriptions-item label="二级策略">{{ manager.secondary_strategy || '-' }}</el-descriptions-item>
      <el-descriptions-item label="管理规模">{{ manager.aum_range || '-' }}</el-descriptions-item>
      <el-descriptions-item label="评级">
        <el-tag v-if="manager.rating && manager.rating !== 'unrated'" :type="getRatingType(manager.rating)">
          {{ manager.rating }}
        </el-tag>
        <span v-else>未评级</span>
      </el-descriptions-item>
      <el-descriptions-item label="成立日期">{{ manager.established_date || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系人">{{ manager.contact_person || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系电话">{{ manager.contact_phone || '-' }}</el-descriptions-item>
      <el-descriptions-item label="联系邮箱" :span="2">{{ manager.contact_email || '-' }}</el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">{{ manager.remark || '-' }}</el-descriptions-item>
    </el-descriptions>

    <!-- 联系人列表 -->
    <div class="section" v-if="manager.contacts?.length">
      <h4>联系人</h4>
      <el-table :data="manager.contacts" size="small">
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="position" label="职位" width="120" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="is_primary" label="主要联系人" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_primary" type="success" size="small">是</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 核心团队 -->
    <div class="section" v-if="manager.team_members?.length">
      <h4>核心团队</h4>
      <el-table :data="manager.team_members" size="small">
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="position" label="职位" width="120" />
        <el-table-column prop="years_of_experience" label="从业年限" width="100" />
        <el-table-column prop="education" label="教育背景" />
      </el-table>
    </div>

    <!-- 旗下产品 -->
    <div class="section">
      <h4>旗下产品 ({{ manager.product_count || 0 }})</h4>
      <el-empty v-if="!manager.product_count" description="暂无产品" />
    </div>

    <!-- 流转历史 -->
    <div class="section">
      <h4>流转历史</h4>
      <el-timeline v-if="transfers.length">
        <el-timeline-item v-for="item in transfers" :key="item.id" :timestamp="formatDateTime(item.created_at)" placement="top">
          <el-card>
            <div class="transfer-content">
              <el-tag size="small" :color="getPoolColor(item.from_pool)">{{ getPoolLabel(item.from_pool) }}</el-tag>
              <span style="margin: 0 8px">→</span>
              <el-tag size="small" :color="getPoolColor(item.to_pool)">{{ getPoolLabel(item.to_pool) }}</el-tag>
            </div>
            <p class="transfer-reason">{{ item.reason }}</p>
            <p class="transfer-operator">操作人：{{ item.operator_name || '-' }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无流转记录" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { managerApi } from '@/api'
import type { Manager, PoolTransfer, PoolCategory, PrimaryStrategy } from '@/types'
import { POOL_CATEGORY_OPTIONS, PRIMARY_STRATEGY_OPTIONS } from '@/types'

const props = defineProps<{ manager: Manager }>()
const emit = defineEmits(['refresh'])

const transfers = ref<PoolTransfer[]>([])

const getPoolLabel = (pool?: PoolCategory) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.label || pool || '-'
const getPoolColor = (pool?: PoolCategory) => POOL_CATEGORY_OPTIONS.find(p => p.value === pool)?.color || '#909399'
const getStrategyLabel = (strategy?: PrimaryStrategy) => PRIMARY_STRATEGY_OPTIONS.find(s => s.value === strategy)?.label || strategy || '-'
const getRatingType = (rating: string) => {
  const map: Record<string, string> = { S: 'success', A: 'success', B: 'warning', C: 'info', D: 'danger' }
  return map[rating] || 'info'
}
const formatDateTime = (dateStr: string) => dateStr ? dateStr.replace('T', ' ').substring(0, 16) : ''

const loadTransfers = async () => {
  try {
    transfers.value = await managerApi.getPoolTransfers(props.manager.id)
  } catch (error) {
    console.error('加载流转历史失败', error)
  }
}

watch(() => props.manager.id, loadTransfers, { immediate: true })
</script>

<style scoped>
.manager-detail { padding: 10px; }
.section { margin-top: 20px; }
.section h4 { margin: 0 0 15px 0; }
.transfer-content { margin-bottom: 8px; }
.transfer-reason { margin: 8px 0; color: #606266; }
.transfer-operator { font-size: 12px; color: #909399; margin: 0; }
</style>
