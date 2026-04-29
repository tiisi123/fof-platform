<template>
  <div class="nav-import-view">
    <div class="page-header">
      <h2>净值数据导入</h2>
      <p class="sub-title">支持4种Excel格式智能识别，自动匹配产品</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 单文件导入 -->
      <el-tab-pane label="单文件导入" name="single">
        <el-steps :active="stepActive" align-center style="margin-bottom: 24px">
          <el-step title="上传文件" />
          <el-step title="预览确认" />
          <el-step title="导入结果" />
        </el-steps>

        <!-- Step 1: 上传 -->
        <div v-show="stepActive === 0">
          <el-card shadow="never" class="section-card">
            <el-form :model="singleForm" label-width="120px">
              <el-form-item label="上传文件">
                <el-upload
                  ref="singleUploadRef"
                  :auto-upload="false"
                  :limit="1"
                  :on-change="onSingleFileChange"
                  :on-remove="onSingleFileRemove"
                  accept=".xls,.xlsx"
                  drag
                  class="upload-area"
                >
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">拖拽文件到此处，或 <em>点击上传</em></div>
                  <template #tip>
                    <div class="upload-tip">支持 .xls / .xlsx 格式，单文件最大 50MB</div>
                  </template>
                </el-upload>
              </el-form-item>
              <el-form-item label="指定产品">
                <el-select
                  v-model="singleForm.productId"
                  placeholder="留空则自动识别"
                  filterable
                  clearable
                  style="width: 100%"
                >
                  <el-option
                    v-for="p in products"
                    :key="p.id"
                    :label="`${p.product_code} - ${p.product_name}`"
                    :value="p.id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="导入选项">
                <el-checkbox v-model="singleForm.skipDuplicates">跳过重复数据</el-checkbox>
                <el-checkbox v-model="singleForm.updateExisting">更新已有数据</el-checkbox>
                <el-checkbox v-model="singleForm.autoDetect">自动识别产品</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :disabled="!singleForm.file"
                  :loading="previewLoading"
                  @click="handlePreview"
                >
                  预览文件
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <!-- Step 2: 预览 -->
        <div v-show="stepActive === 1">
          <el-card shadow="never" class="section-card">
            <template #header>
              <div class="card-header">
                <span>文件解析结果</span>
                <el-button size="small" @click="stepActive = 0">返回上传</el-button>
              </div>
            </template>

            <div v-if="previewResult" class="preview-info">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="识别格式">
                  <el-tag type="success" size="small">{{ previewResult.format_detected || '未知' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="数据行数">
                  {{ previewResult.total_rows ?? '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="日期范围">
                  {{ previewResult.date_range?.start || '-' }} ~ {{ previewResult.date_range?.end || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="产品代码" v-if="previewResult.product_codes?.length">
                  {{ previewResult.product_codes.join(', ') }}
                </el-descriptions-item>
                <el-descriptions-item label="产品名称" v-if="previewResult.product_names?.length">
                  {{ previewResult.product_names.join(', ') }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 警告信息 -->
              <el-alert
                v-for="(w, i) in previewResult.warnings || []"
                :key="'w' + i"
                :title="w"
                type="warning"
                show-icon
                :closable="false"
                style="margin-top: 8px"
              />

              <!-- 预览数据 -->
              <el-table
                v-if="previewResult.preview_data?.length"
                :data="previewResult.preview_data"
                stripe
                border
                style="margin-top: 16px"
                max-height="300"
              >
                <el-table-column prop="nav_date" label="日期" width="120" />
                <el-table-column prop="unit_nav" label="单位净值" width="120" align="right">
                  <template #default="{ row }">
                    {{ row.unit_nav?.toFixed(4) ?? '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="cumulative_nav" label="累计净值" width="120" align="right">
                  <template #default="{ row }">
                    {{ row.cumulative_nav?.toFixed(4) ?? '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="product_code" label="产品代码" width="140" />
                <el-table-column prop="product_name" label="产品名称" min-width="160" />
              </el-table>
            </div>

            <div style="margin-top: 16px; text-align: right">
              <el-button @click="stepActive = 0">返回修改</el-button>
              <el-button type="primary" :loading="importLoading" @click="handleImport">
                确认导入
              </el-button>
            </div>
          </el-card>
        </div>

        <!-- Step 3: 导入结果 -->
        <div v-show="stepActive === 2">
          <el-card shadow="never" class="section-card">
            <template #header>
              <span>导入结果</span>
            </template>
            <el-result
              v-if="importResult"
              :icon="importResult.success ? 'success' : 'warning'"
              :title="importResult.success ? '导入成功' : '导入完成（有异常）'"
              :sub-title="importResult.message"
            >
              <template #extra>
                <el-descriptions :column="3" border size="small" style="margin-bottom: 16px">
                  <el-descriptions-item label="总行数">{{ importResult.total_rows }}</el-descriptions-item>
                  <el-descriptions-item label="导入成功">
                    <span class="text-success">{{ importResult.imported_rows }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="跳过">{{ importResult.skipped_rows }}</el-descriptions-item>
                  <el-descriptions-item label="更新" v-if="importResult.updated_rows != null">
                    {{ importResult.updated_rows }}
                  </el-descriptions-item>
                  <el-descriptions-item label="失败">
                    <span :class="importResult.error_rows > 0 ? 'text-danger' : ''">
                      {{ importResult.error_rows }}
                    </span>
                  </el-descriptions-item>
                  <el-descriptions-item label="日期范围">
                    {{ importResult.date_range?.start || '-' }} ~ {{ importResult.date_range?.end || '-' }}
                  </el-descriptions-item>
                </el-descriptions>

                <!-- 错误列表 -->
                <el-alert
                  v-for="(err, i) in importResult.errors?.slice(0, 10) || []"
                  :key="'e' + i"
                  :title="err"
                  type="error"
                  show-icon
                  :closable="false"
                  style="margin-bottom: 4px"
                />

                <el-button type="primary" @click="handleReset">继续导入</el-button>
              </template>
            </el-result>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 数据质量 -->
      <el-tab-pane label="数据质量" name="quality">
        <el-card shadow="never" class="section-card">
          <el-form :inline="true">
            <el-form-item label="选择产品">
              <el-select
                v-model="qualityProductId"
                placeholder="请选择产品"
                filterable
                style="width: 320px"
              >
                <el-option
                  v-for="p in products"
                  :key="p.id"
                  :label="`${p.product_code} - ${p.product_name}`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :disabled="!qualityProductId"
                :loading="qualityLoading"
                @click="handleAnalyzeQuality"
              >
                分析数据质量
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 空状态 -->
        <el-empty v-if="!qualityReport && !qualityLoading" description="请选择产品并点击“分析数据质量”开始检测" :image-size="80" />

        <el-card v-if="qualityReport" shadow="never" class="section-card">
          <template #header>
            <div class="card-header">
              <span>{{ qualityReport.product_name }} - 数据质量报告</span>
              <el-tag
                :type="qualityReport.summary?.score >= 90 ? 'success' : qualityReport.summary?.score >= 70 ? 'warning' : 'danger'"
              >
                {{ qualityReport.summary?.level }} ({{ qualityReport.summary?.score }}分)
              </el-tag>
            </div>
          </template>

          <el-descriptions :column="4" border size="small" style="margin-bottom: 16px">
            <el-descriptions-item label="总记录数">{{ qualityReport.total_records }}</el-descriptions-item>
            <el-descriptions-item label="日期范围">
              {{ qualityReport.date_range?.start || '-' }} ~ {{ qualityReport.date_range?.end || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="重复数据">
              <span :class="qualityReport.summary?.duplicates > 0 ? 'text-danger' : 'text-success'">
                {{ qualityReport.summary?.duplicates ?? 0 }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="异常值">
              <span :class="qualityReport.summary?.outliers > 0 ? 'text-danger' : 'text-success'">
                {{ qualityReport.summary?.outliers ?? 0 }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="日期缺失">
              <span :class="qualityReport.summary?.gaps > 0 ? 'text-danger' : 'text-success'">
                {{ qualityReport.summary?.gaps ?? 0 }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="无效净值">
              <span :class="qualityReport.summary?.invalid_nav > 0 ? 'text-danger' : 'text-success'">
                {{ qualityReport.summary?.invalid_nav ?? 0 }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="净值跳跃">
              <span :class="qualityReport.summary?.jumps > 0 ? 'text-danger' : 'text-success'">
                {{ qualityReport.summary?.jumps ?? 0 }}
              </span>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 问题列表 -->
          <el-table
            v-if="qualityReport.issues?.length"
            :data="qualityReport.issues"
            stripe
            border
            max-height="400"
            style="margin-bottom: 16px"
          >
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="{ duplicate: 'warning', outlier: 'danger', gap: 'info', invalid: 'danger', jump: 'warning' }[row.type] || 'info'"
                  size="small"
                >
                  {{ { duplicate: '重复', outlier: '异常值', gap: '缺失', invalid: '无效', jump: '跳跃' }[row.type] || row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="{ error: 'danger', warning: 'warning', info: 'info' }[row.severity] || 'info'"
                  size="small"
                >
                  {{ { error: '严重', warning: '警告', info: '提示' }[row.severity] || row.severity }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="nav_date" label="日期" width="120" />
            <el-table-column prop="message" label="描述" min-width="300" show-overflow-tooltip />
          </el-table>

          <el-alert
            v-if="qualityReport.issues?.length === 0"
            title="数据质量良好，未检测到问题"
            type="success"
            show-icon
            :closable="false"
            style="margin-bottom: 16px"
          />

          <!-- 清洗操作 -->
          <div v-if="qualityReport.issue_summary?.total > 0" class="clean-actions">
            <span style="font-weight: 600; margin-right: 12px">数据清洗：</span>
            <el-checkbox v-model="cleanOptions.removeDuplicates">删除重复数据</el-checkbox>
            <el-checkbox v-model="cleanOptions.removeOutliers">删除异常值</el-checkbox>
            <el-checkbox v-model="cleanOptions.fillMissing">线性插值填充缺失</el-checkbox>
            <el-button
              type="danger"
              size="small"
              :loading="cleanLoading"
              @click="handleCleanData"
              style="margin-left: 16px"
            >
              执行清洗
            </el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 批量导入 -->
      <el-tab-pane label="批量导入" name="batch">
        <el-card shadow="never" class="section-card">
          <el-form label-width="120px">
            <el-form-item label="上传文件">
              <el-upload
                ref="batchUploadRef"
                :auto-upload="false"
                :limit="20"
                multiple
                :on-change="onBatchFileChange"
                :on-remove="onBatchFileRemove"
                accept=".xls,.xlsx"
                drag
                class="upload-area"
              >
                <el-icon class="upload-icon"><UploadFilled /></el-icon>
                <div class="upload-text">拖拽多个文件到此处，或 <em>点击上传</em></div>
                <template #tip>
                  <div class="upload-tip">支持最多 20 个 Excel 文件同时导入</div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item label="导入选项">
              <el-checkbox v-model="batchForm.skipDuplicates">跳过重复数据</el-checkbox>
              <el-checkbox v-model="batchForm.updateExisting">更新已有数据</el-checkbox>
              <el-checkbox v-model="batchForm.autoDetect">自动识别产品</el-checkbox>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :disabled="batchForm.files.length === 0"
                :loading="batchLoading"
                @click="handleBatchImport"
              >
                开始批量导入 ({{ batchForm.files.length }} 个文件)
              </el-button>
              <el-button v-if="batchResult" @click="handleResetBatch" style="margin-left: 12px">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 导入进度条 -->
          <el-progress
            v-if="batchLoading"
            :percentage="batchProgress"
            :status="batchProgress === 100 ? 'success' : undefined"
            style="margin-top: 12px"
          >
            <span class="progress-text">正在导入第 {{ batchCurrentFile }}/{{ batchForm.files.length }} 个文件...</span>
          </el-progress>
        </el-card>

        <!-- 批量导入结果 -->
        <el-card v-if="batchResult" shadow="never" class="section-card">
          <template #header><span>批量导入结果</span></template>
          <el-descriptions :column="3" border size="small" style="margin-bottom: 16px">
            <el-descriptions-item label="总文件数">{{ batchResult.total_files }}</el-descriptions-item>
            <el-descriptions-item label="成功">
              <span class="text-success">{{ batchResult.successful_files }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="失败">
              <span :class="batchResult.failed_files > 0 ? 'text-danger' : ''">
                {{ batchResult.failed_files }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
          <el-table :data="batchResult.results" stripe border max-height="400">
            <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column prop="success" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                  {{ row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="imported_rows" label="导入行数" width="100" align="right" />
            <el-table-column prop="message" label="信息" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { navApi } from '@/api/nav'
import { productApi } from '@/api/product'
import type { NavPreviewResult, NavImportResult, BatchImportResult } from '@/api/nav'
import type { UploadFile } from 'element-plus'
import type { Product } from '@/types'
import request from '@/api/request'

const activeTab = ref('single')

// 产品列表
const products = ref<Product[]>([])

// ========== 单文件导入 ==========
const stepActive = ref(0)
const singleUploadRef = ref()
const previewLoading = ref(false)
const importLoading = ref(false)
const previewResult = ref<NavPreviewResult | null>(null)
const importResult = ref<NavImportResult | null>(null)

const singleForm = reactive({
  file: null as File | null,
  productId: null as number | null,
  skipDuplicates: true,
  updateExisting: false,
  autoDetect: true
})

const onSingleFileChange = (f: UploadFile) => {
  singleForm.file = f.raw || null
}

const onSingleFileRemove = () => {
  singleForm.file = null
}

const handlePreview = async () => {
  if (!singleForm.file) return
  previewLoading.value = true
  try {
    previewResult.value = await navApi.preview(singleForm.file, 10)
    if (previewResult.value.success !== false) {
      stepActive.value = 1
    } else {
      ElMessage.error('文件解析失败：' + (previewResult.value.errors?.[0] || '未知错误'))
    }
  } catch (e: any) {
    ElMessage.error(e.message || '文件预览失败')
  } finally {
    previewLoading.value = false
  }
}

const handleImport = async () => {
  if (!singleForm.file) return
  importLoading.value = true
  try {
    importResult.value = await navApi.import({
      file: singleForm.file,
      product_id: singleForm.productId || undefined,
      skip_duplicates: singleForm.skipDuplicates,
      update_existing: singleForm.updateExisting,
      auto_detect_product: singleForm.autoDetect
    })
    stepActive.value = 2
    if (importResult.value.success) {
      ElMessage.success(`成功导入 ${importResult.value.imported_rows} 条数据`)
    }
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

const handleReset = () => {
  stepActive.value = 0
  singleForm.file = null
  singleForm.productId = null
  previewResult.value = null
  importResult.value = null
  singleUploadRef.value?.clearFiles()
}

// ========== 批量导入 ==========
const batchUploadRef = ref()
const batchLoading = ref(false)
const batchResult = ref<BatchImportResult | null>(null)
const batchProgress = ref(0)
const batchCurrentFile = ref(0)

const batchForm = reactive({
  files: [] as File[],
  skipDuplicates: true,
  updateExisting: false,
  autoDetect: true
})

const onBatchFileChange = (f: UploadFile) => {
  if (f.raw) batchForm.files.push(f.raw)
}

const onBatchFileRemove = (f: UploadFile) => {
  const idx = batchForm.files.findIndex(file => file.name === f.name)
  if (idx >= 0) batchForm.files.splice(idx, 1)
}

const handleBatchImport = async () => {
  if (batchForm.files.length === 0) return
  batchLoading.value = true
  batchProgress.value = 0
  batchCurrentFile.value = 0
  try {
    // 模拟进度，实际应该与后端协同处理
    const progressTimer = setInterval(() => {
      if (batchProgress.value < 90) batchProgress.value += 5
    }, 300)
    
    batchResult.value = await navApi.batchImport(batchForm.files, {
      skip_duplicates: batchForm.skipDuplicates,
      update_existing: batchForm.updateExisting,
      auto_detect_product: batchForm.autoDetect
    })
    
    clearInterval(progressTimer)
    batchProgress.value = 100
    batchCurrentFile.value = batchForm.files.length
    
    const r = batchResult.value
    ElMessage.success(`批量导入完成：${r.successful_files}/${r.total_files} 成功，共 ${r.total_imported_rows} 条`)
  } catch (e: any) {
    ElMessage.error(e.message || '批量导入失败')
  } finally {
    batchLoading.value = false
  }
}

const handleResetBatch = () => {
  batchForm.files = []
  batchResult.value = null
  batchProgress.value = 0
  batchCurrentFile.value = 0
  batchUploadRef.value?.clearFiles()
}

// ========== 数据质量 ==========
const qualityProductId = ref<number | null>(null)
const qualityLoading = ref(false)
const cleanLoading = ref(false)
const qualityReport = ref<any>(null)
const cleanOptions = reactive({
  removeDuplicates: true,
  removeOutliers: false,
  fillMissing: false
})

const handleAnalyzeQuality = async () => {
  if (!qualityProductId.value) return
  qualityLoading.value = true
  qualityReport.value = null
  try {
    const res = await request.get(`/nav/data-quality/${qualityProductId.value}`)
    qualityReport.value = res
  } catch (e: any) {
    ElMessage.error(e.message || '数据质量分析失败')
  } finally {
    qualityLoading.value = false
  }
}

const handleCleanData = async () => {
  if (!qualityProductId.value) return
  cleanLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('remove_duplicates', String(cleanOptions.removeDuplicates))
    params.append('remove_outliers', String(cleanOptions.removeOutliers))
    params.append('fill_missing', String(cleanOptions.fillMissing))
    const res = await request.post(`/nav/clean/${qualityProductId.value}?${params.toString()}`)
    ElMessage.success(res.message || '清洗完成')
    // 重新分析
    await handleAnalyzeQuality()
  } catch (e: any) {
    ElMessage.error(e.message || '数据清洗失败')
  } finally {
    cleanLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(async () => {
  try {
    const r = await productApi.getList({ skip: 0, limit: 500 })
    products.value = r.items
  } catch {
    // 静默
  }
})
</script>

<style scoped>
.nav-import-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.sub-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.section-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 30px 20px;
}

.upload-icon {
  font-size: 48px;
  color: var(--text-secondary);
}

.upload-text {
  color: var(--text-secondary);
  margin-top: 8px;
  font-size: 14px;
}

.upload-text em {
  color: #409EFF;
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.preview-info {
  margin-bottom: 12px;
}

.text-success { color: #67C23A; }
.text-danger { color: #F56C6C; }

.clean-actions {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--hover-bg, #f5f7fa);
  border-radius: 6px;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 8px;
}

/* 暗色主题适配 */
html.dark .section-card { background: var(--card-bg); }
html.dark .upload-area :deep(.el-upload-dragger) { background: var(--hover-bg); border-color: var(--card-border); }
html.dark .upload-icon, html.dark .upload-text, html.dark .upload-tip { color: var(--text-secondary); }
html.dark .clean-actions { background: var(--hover-bg); }

@media (max-width: 768px) {
  .nav-import-view { padding: 15px; }
}
</style>
