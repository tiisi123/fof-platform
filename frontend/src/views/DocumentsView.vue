<template>
  <div class="documents-view">
    <div class="page-header">
      <div class="header-left">
        <h1>尽调资料</h1>
        <p class="subtitle">管理尽调报告、法律文件、财务资料等</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_count || 0 }}</div>
        <div class="stat-label">文件总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_size_mb || 0 }} MB</div>
        <div class="stat-label">占用空间</div>
      </div>
      <div class="stat-card" v-for="(count, cat) in stats.by_category" :key="cat">
        <div class="stat-value">{{ count }}</div>
        <div class="stat-label">{{ getCategoryName(cat) }}</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索文件名、标题、描述..."
        clearable
        style="width: 300px"
        @keyup.enter="loadDocuments"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="filters.category" placeholder="资料分类" clearable style="width: 150px">
        <el-option
          v-for="cat in categories"
          :key="cat.key"
          :label="cat.name"
          :value="cat.key"
        />
      </el-select>
      
      <el-select v-model="filters.relation_type" placeholder="关联类型" clearable style="width: 150px">
        <el-option label="管理人" value="manager" />
        <el-option label="产品" value="product" />
        <el-option label="一级项目" value="project" />
      </el-select>
      
      <el-button @click="loadDocuments">
        <el-icon><Search /></el-icon>
        搜索
      </el-button>
    </div>

    <!-- 文件列表 -->
    <div class="documents-table">
      <div class="batch-bar" v-if="selectedDocs.length > 0">
        <span>已选 {{ selectedDocs.length }} 个文件</span>
        <el-button size="small" @click="batchDownload">
          <el-icon><Download /></el-icon>
          批量下载
        </el-button>
        <el-button size="small" type="danger" @click="batchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
      <el-table :data="documents" v-loading="loading" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column label="文件" min-width="300">
          <template #default="{ row }">
            <div class="file-info">
              <div class="file-icon" :class="getFileIconClass(row.file_type)">
                {{ getFileIcon(row.file_type) }}
              </div>
              <div class="file-details">
                <div class="file-title">{{ row.title || row.filename }}</div>
                <div class="file-meta">
                  {{ row.filename }} · {{ formatFileSize(row.file_size) }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getCategoryType(row.category)">
              {{ getCategoryName(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="关联" width="150">
          <template #default="{ row }">
            <span v-if="row.relation_type">
              {{ getRelationTypeName(row.relation_type) }} #{{ row.relation_id }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="上传人" width="100" prop="uploader_name" />
        
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.uploaded_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                size="small" 
                @click="previewDocument(row)"
                :disabled="!isPreviewable(row.file_type)"
              >
                <el-icon><View /></el-icon>
              </el-button>
              <el-button size="small" @click="downloadDocument(row)">
                <el-icon><Download /></el-icon>
              </el-button>
              <el-button size="small" @click="editDocument(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click="deleteDocument(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadDocuments"
          @current-change="loadDocuments"
        />
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文件" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">拖拽文件到这里，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word、Excel、PPT、图片等格式，最大50MB</div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="可选，默认使用文件名" />
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category" style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat.key"
              :label="cat.name"
              :value="cat.key"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联类型">
          <el-select v-model="uploadForm.relation_type" clearable style="width: 100%">
            <el-option label="管理人" value="manager" />
            <el-option label="产品" value="product" />
            <el-option label="一级项目" value="project" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联ID" v-if="uploadForm.relation_type">
          <el-input-number v-model="uploadForm.relation_id" :min="1" style="width: 100%" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑文件信息" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat.key"
              :label="cat.name"
              :value="cat.key"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input v-model="editForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="editing">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog 
      v-model="showPreviewDialog" 
      :title="previewDoc?.title || previewDoc?.filename"
      width="80%"
      top="5vh"
    >
      <div class="preview-container">
        <!-- 可预览文件 -->
        <iframe
          v-if="previewUrl && isPreviewable(previewDoc?.file_type)"
          :src="previewUrl"
          style="width: 100%; height: 70vh; border: none;"
        />
        <!-- 不可预览的文件 fallback -->
        <div v-else class="preview-fallback">
          <div class="fallback-icon">
            <el-icon :size="64"><Document /></el-icon>
          </div>
          <h3>该文件类型不支持在线预览</h3>
          <p>文件类型: {{ previewDoc?.file_type?.toUpperCase() || '未知' }}</p>
          <el-button type="primary" @click="downloadDocument(previewDoc)">
            <el-icon><Download /></el-icon>
            下载文件查看
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search, View, Download, Edit, Delete, Document } from '@element-plus/icons-vue'
import type { Ref } from 'vue'
import request from '@/api/request'

// 状态
const loading = ref(false)
const uploading = ref(false)
const editing = ref(false)
const documents = ref<any[]>([])
const stats = ref<any>({})
const categories = ref<any[]>([])
const selectedDocs: Ref<any[]> = ref([])

// 对话框
const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const showPreviewDialog = ref(false)
const previewDoc = ref<any>(null)
const previewUrl = ref('')
const uploadRef = ref<any>(null)

// 筛选
const filters = reactive({
  keyword: '',
  category: '',
  relation_type: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 上传表单
const uploadForm = reactive({
  file: null as File | null,
  title: '',
  category: 'other',
  relation_type: '',
  relation_id: null as number | null,
  description: '',
  tags: ''
})

// 编辑表单
const editForm = reactive({
  id: 0,
  title: '',
  category: '',
  description: '',
  tags: ''
})

// 分类映射
const categoryMap: Record<string, string> = {
  dd_report: '尽调报告',
  legal: '法律文件',
  financial: '财务资料',
  contract: '合同协议',
  presentation: '路演材料',
  meeting: '会议纪要',
  other: '其他'
}

const getCategoryName = (key: string) => categoryMap[key] || key

const getCategoryType = (key: string) => {
  const types: Record<string, string> = {
    dd_report: 'primary',
    legal: 'warning',
    financial: 'success',
    contract: 'info',
    presentation: '',
    meeting: 'danger',
    other: 'info'
  }
  return types[key] || 'info'
}

const getRelationTypeName = (type: string) => {
  const map: Record<string, string> = {
    manager: '管理人',
    product: '产品',
    project: '项目'
  }
  return map[type] || type
}

// 文件图标
const getFileIcon = (type: string) => {
  const icons: Record<string, string> = {
    pdf: 'PDF',
    doc: 'DOC',
    docx: 'DOC',
    xls: 'XLS',
    xlsx: 'XLS',
    ppt: 'PPT',
    pptx: 'PPT',
    jpg: 'IMG',
    jpeg: 'IMG',
    png: 'IMG',
    gif: 'IMG',
    zip: 'ZIP',
    rar: 'ZIP'
  }
  return icons[type] || 'FILE'
}

const getFileIconClass = (type: string) => {
  const classes: Record<string, string> = {
    pdf: 'icon-pdf',
    doc: 'icon-doc',
    docx: 'icon-doc',
    xls: 'icon-xls',
    xlsx: 'icon-xls',
    ppt: 'icon-ppt',
    pptx: 'icon-ppt',
    jpg: 'icon-img',
    jpeg: 'icon-img',
    png: 'icon-img',
    gif: 'icon-img'
  }
  return classes[type] || 'icon-default'
}

const isPreviewable = (type: string) => {
  return ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(type)
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return dateStr.slice(0, 19).replace('T', ' ')
}

// 加载分类
const loadCategories = async () => {
  try {
    const res = await request.get('/documents/categories')
    categories.value = res.data || res || []
  } catch (e) {
    console.error('加载分类失败', e)
  }
}

// 加载统计
const loadStats = async () => {
  try {
    const res = await request.get('/documents/statistics')
    stats.value = res.data || res || {}
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.category) params.category = filters.category
    if (filters.relation_type) params.relation_type = filters.relation_type
    
    const res = await request.get('/documents', { params })
    documents.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (e) {
    console.error('加载文档失败', e)
  } finally {
    loading.value = false
  }
}

// 文件选择
const handleFileChange = (file: any) => {
  uploadForm.file = file.raw
}

// 提交上传
const submitUpload = async () => {
  if (!uploadForm.file) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('category', uploadForm.category)
    if (uploadForm.title) formData.append('title', uploadForm.title)
    if (uploadForm.description) formData.append('description', uploadForm.description)
    if (uploadForm.tags) formData.append('tags', uploadForm.tags)
    if (uploadForm.relation_type) formData.append('relation_type', uploadForm.relation_type)
    if (uploadForm.relation_id) formData.append('relation_id', String(uploadForm.relation_id))
    
    await request.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    
    // 重置表单
    uploadForm.file = null
    uploadForm.title = ''
    uploadForm.category = 'other'
    uploadForm.relation_type = ''
    uploadForm.relation_id = null
    uploadForm.description = ''
    uploadForm.tags = ''
    
    loadDocuments()
    loadStats()
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 预览
const previewDocument = async (doc: any) => {
  previewDoc.value = doc
  // 获取预览URL
  const token = localStorage.getItem('token')
  previewUrl.value = `/api/v1/documents/${doc.id}/preview?token=${token}`
  showPreviewDialog.value = true
}

// 下载
const downloadDocument = async (doc: any) => {
  try {
    const response = await request.get(`/documents/${doc.id}/download`, {
      responseType: 'blob'
    })
    
    const blob = new Blob([response as any])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = doc.filename
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (e: any) {
    ElMessage.error(e.message || '下载失败')
  }
}

// 编辑
const editDocument = (doc: any) => {
  editForm.id = doc.id
  editForm.title = doc.title || ''
  editForm.category = doc.category
  editForm.description = doc.description || ''
  editForm.tags = doc.tags || ''
  showEditDialog.value = true
}

// 提交编辑
const submitEdit = async () => {
  editing.value = true
  try {
    await request.put(`/documents/${editForm.id}`, {
      title: editForm.title,
      category: editForm.category,
      description: editForm.description,
      tags: editForm.tags
    })
    
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadDocuments()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    editing.value = false
  }
}

// 批量选择
const handleSelectionChange = (rows: any[]) => {
  selectedDocs.value = rows
}

// 批量下载
const batchDownload = () => {
  selectedDocs.value.forEach((doc) => {
    downloadDocument(doc)
  })
}

// 批量删除
const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定删除已选的 ${selectedDocs.value.length} 个文件吗？`, '确认删除', { type: 'warning' })
    for (const doc of selectedDocs.value) {
      await request.delete(`/documents/${doc.id}`)
    }
    ElMessage.success(`已删除 ${selectedDocs.value.length} 个文件`)
    selectedDocs.value = []
    loadDocuments()
    loadStats()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.message || '删除失败')
  }
}

// 删除
const deleteDocument = async (doc: any) => {
  try {
    await ElMessageBox.confirm(`确定删除文件 "${doc.filename}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    await request.delete(`/documents/${doc.id}`)
    ElMessage.success('删除成功')
    loadDocuments()
    loadStats()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadCategories()
  loadStats()
  loadDocuments()
})
</script>

<style scoped>
.documents-view {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.page-header .subtitle {
  color: var(--text-secondary);
  margin: 0;
}

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 16px 24px;
  min-width: 120px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.documents-table {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 16px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.icon-pdf { background: #e74c3c; }
.icon-doc { background: #3498db; }
.icon-xls { background: #27ae60; }
.icon-ppt { background: #e67e22; }
.icon-img { background: #9b59b6; }
.icon-default { background: #95a5a6; }

.file-details {
  flex: 1;
  min-width: 0;
}

.file-title {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.text-muted {
  color: var(--text-secondary);
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.preview-container {
  min-height: 400px;
}

.preview-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
  color: var(--text-secondary);
}

.preview-fallback .fallback-icon {
  color: var(--text-muted);
  margin-bottom: 16px;
}

.preview-fallback h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.preview-fallback p {
  margin: 0 0 20px 0;
  font-size: 14px;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin-bottom: 12px;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
}

/* 暗色主题覆盖 */
:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-header-bg-color: var(--hover-bg);
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: var(--hover-bg);
}

:deep(.el-table th.el-table__cell) {
  background: var(--hover-bg);
  color: var(--text-secondary);
}

:deep(.el-table td.el-table__cell) {
  border-bottom-color: var(--card-border);
}

:deep(.el-dialog) {
  background: var(--card-bg);
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid var(--card-border);
}

:deep(.el-dialog__title) {
  color: var(--text-primary);
}
</style>
