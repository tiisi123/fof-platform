<template>
  <div class="comment-section">
    <div class="flex items-center justify-between mb-3">
      <h4 class="text-base font-semibold">讨论 ({{ comments.length }})</h4>
    </div>

    <!-- 发表评论 -->
    <div class="flex gap-2 mb-4">
      <el-input
        v-model="newComment"
        type="textarea"
        :rows="2"
        placeholder="添加评论..."
        resize="none"
      />
      <el-button type="primary" @click="handleSubmit" :loading="submitting" :disabled="!newComment.trim()">
        发送
      </el-button>
    </div>

    <!-- 评论列表 -->
    <div v-if="comments.length" class="comment-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-header">
          <span class="comment-user">{{ comment.user_name }}</span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <el-button link type="danger" size="small" @click="handleDelete(comment.id)" class="ml-auto">删除</el-button>
        </div>
        <div class="comment-content">{{ comment.content }}</div>
        <!-- 回复列表 -->
        <div v-if="comment.replies?.length" class="reply-list">
          <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
            <span class="comment-user">{{ reply.user_name }}</span>
            <span class="comment-time">{{ formatTime(reply.created_at) }}</span>
            <span class="reply-content">{{ reply.content }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="text-center text-sm" style="color: var(--text-secondary); padding: 16px">
      暂无讨论
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const props = defineProps<{
  resourceType: string
  resourceId: number
}>()

const comments = ref<any[]>([])
const newComment = ref('')
const submitting = ref(false)

const formatTime = (dt: string) => dt ? dt.replace('T', ' ').substring(0, 16) : ''

const loadComments = async () => {
  try {
    const res: any = await request.get('/comments', {
      params: { resource_type: props.resourceType, resource_id: props.resourceId },
    })
    comments.value = res.items || []
  } catch { /* silent */ }
}

const handleSubmit = async () => {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    await request.post('/comments', {
      resource_type: props.resourceType,
      resource_id: props.resourceId,
      content: newComment.value.trim(),
    })
    newComment.value = ''
    loadComments()
  } catch (e: any) { ElMessage.error(e.message || '评论失败') } finally { submitting.value = false }
}

const handleDelete = async (commentId: number) => {
  try {
    await request.delete(`/comments/${commentId}`)
    loadComments()
  } catch { /* handled */ }
}

watch(() => props.resourceId, () => { if (props.resourceId) loadComments() })
onMounted(() => { if (props.resourceId) loadComments() })
</script>

<style scoped>
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-item {
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--hover-bg, rgba(255,255,255,0.03));
  border: 1px solid var(--card-border, rgba(255,255,255,0.06));
}
.comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.comment-user { font-weight: 600; font-size: 13px; color: var(--text-primary); }
.comment-time { font-size: 12px; color: var(--text-secondary, #999); }
.comment-content { font-size: 14px; line-height: 1.6; color: var(--text-primary); white-space: pre-wrap; }
.reply-list { margin-top: 8px; padding-left: 16px; border-left: 2px solid var(--card-border, #333); }
.reply-item { display: flex; gap: 6px; align-items: baseline; font-size: 13px; margin-bottom: 4px; }
.reply-content { color: var(--text-primary); }
</style>
