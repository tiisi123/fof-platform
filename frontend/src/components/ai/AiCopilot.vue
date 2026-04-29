<template>
  <button class="copilot-fab" @click="openCopilot" title="AI Copilot">
    <el-icon :size="22"><ChatDotRound /></el-icon>
    <span>AI助手</span>
  </button>

  <transition name="copilot-mask">
    <div v-if="visible" class="copilot-backdrop" @click="visible = false"></div>
  </transition>

  <transition name="copilot-panel">
    <aside v-if="visible" class="copilot-drawer">
      <header class="copilot-header">
        <button class="icon-btn" @click="visible = false" title="关闭">
          <el-icon :size="20"><Close /></el-icon>
        </button>
        <div class="copilot-title">
          <el-icon :size="22"><ChatDotRound /></el-icon>
          <div>
            <h3>{{ context?.module_name || pageTitle }} AI Copilot</h3>
            <p>{{ context?.role || 'FOF投研助手' }}</p>
          </div>
        </div>
        <button class="icon-btn" @click="refreshContext" title="刷新模块数据">
          <el-icon :size="18"><Refresh /></el-icon>
        </button>
        <button class="icon-btn" @click="clearConversation" title="清空当前对话">
          <el-icon :size="18"><Delete /></el-icon>
        </button>
      </header>

      <section class="copilot-warning">
        <el-icon><WarningFilled /></el-icon>
        <span>{{ context?.disclaimer || 'AI 生成内容仅供研究参考，可能存在偏差或错误，不构成任何投资建议。' }}</span>
      </section>

      <el-tabs v-model="activeTab" class="copilot-tabs">
        <el-tab-pane label="智能问答" name="chat">
          <div class="module-entry">
            <div class="entry-line">
              当前在【{{ context?.module_name || pageTitle }}】页面，你可以问：
              <span v-if="messages.length" class="saved-hint">已自动保存</span>
            </div>
            <div class="question-chips">
              <button
                v-for="question in context?.questions || defaultQuestions"
                :key="question"
                class="question-chip"
                @click="askPreset(question)"
              >
                {{ question }}
              </button>
            </div>
          </div>

          <div ref="messagesRef" class="message-list">
            <div v-if="messages.length === 0" class="empty-state">
              <el-icon :size="28"><MagicStick /></el-icon>
              <span>已自动带入当前模块核心数据</span>
            </div>
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="message-row"
              :class="message.role"
            >
              <div 
                class="message-bubble" 
                :class="{ streaming: message.role === 'assistant' && index === messages.length - 1 && sending }"
              >
                {{ message.content }}
              </div>
            </div>
            <div v-if="sending" class="message-row assistant">
              <div class="message-bubble loading-bubble">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <div v-if="attachments.length" class="attachment-list">
            <div v-for="item in attachments" :key="item.id" class="attachment-item">
              <el-icon><Picture v-if="item.isImage" /><Document v-else /></el-icon>
              <span>{{ item.file.name }}</span>
              <button class="attachment-remove" @click="removeAttachment(item.id)" title="移除附件">
                <el-icon><Close /></el-icon>
              </button>
            </div>
          </div>

          <form class="input-bar" @submit.prevent="sendQuestion()" @paste="handlePaste">
            <input
              ref="fileInputRef"
              class="file-input"
              type="file"
              multiple
              accept=".txt,.md,.csv,.json,.xlsx,.xls,.pdf,.docx,image/*"
              @change="handleFileSelect"
            />
            <button type="button" class="attach-btn" title="上传文件或图片" @click="fileInputRef?.click()">
              <el-icon><Paperclip /></el-icon>
            </button>
            <el-input
              v-model="draft"
              :autosize="{ minRows: 1, maxRows: 4 }"
              type="textarea"
              resize="none"
              placeholder="问我任何关于当前模块的问题，可粘贴截图或上传文件..."
              @keydown.enter.exact.prevent="sendQuestion()"
            />
            <el-button type="primary" class="send-btn" :loading="sending" @click="sendQuestion()">
              <el-icon><Promotion /></el-icon>
            </el-button>
          </form>
        </el-tab-pane>

        <el-tab-pane label="模块数据" name="data">
          <div v-loading="loading" class="data-pane">
            <div class="data-grid">
              <div v-for="card in context?.cards || []" :key="card.label" class="data-card">
                <span>{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
              </div>
            </div>
            <div class="planning-block">
              <h4>引导规划</h4>
              <ol>
                <li v-for="item in context?.planning || []" :key="item">{{ item }}</li>
              </ol>
            </div>
            <pre class="json-preview">{{ formattedCoreData }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </aside>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Close, Delete, Document, MagicStick, Paperclip, Picture, Promotion, Refresh, WarningFilled } from '@element-plus/icons-vue'
import { copilotApi } from '@/api/copilot'
import type { CopilotContext, CopilotMessage } from '@/api/copilot'

interface ConversationRecord {
  path: string
  moduleName?: string
  updatedAt: string
  messages: CopilotMessage[]
}

interface PendingAttachment {
  id: string
  file: File
  isImage: boolean
}

const CONVERSATION_STORAGE_KEY = 'fof-ai-copilot-conversations-v1'
const MAX_SAVED_MESSAGES = 40
const MAX_MESSAGE_LENGTH = 8000
const MAX_ATTACHMENTS = 5
const MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024

const route = useRoute()
const visible = ref(false)
const loading = ref(false)
const sending = ref(false)
const activeTab = ref('chat')
const draft = ref('')
const context = ref<CopilotContext | null>(null)
const messages = ref<CopilotMessage[]>([])
const messagesRef = ref<HTMLElement>()
const fileInputRef = ref<HTMLInputElement>()
const attachments = ref<PendingAttachment[]>([])

const defaultQuestions = ['当前模块有什么重点风险？', '下一步应该优先做什么？', '有哪些数据需要补充？']

const pageTitle = computed(() => String(route.meta.title || '当前模块'))
const conversationKey = computed(() => `path:${route.path}`)
const formattedCoreData = computed(() => {
  if (!context.value?.core_data) return ''
  return JSON.stringify(context.value.core_data, null, 2)
})

const openCopilot = async () => {
  visible.value = true
  activeTab.value = 'chat'
  if (!context.value) {
    await refreshContext()
  }
}

const refreshContext = async () => {
  loading.value = true
  try {
    context.value = await copilotApi.getContext({ path: route.path })
    persistConversation()
  } catch (error) {
    console.error('加载Copilot上下文失败:', error)
    ElMessage.error('AI Copilot 数据加载失败')
  } finally {
    loading.value = false
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const askPreset = (question: string) => {
  draft.value = question
  sendQuestion(question)
}

const sendQuestion = async (preset?: string) => {
  const question = (preset || draft.value).trim()
  if ((!question && attachments.value.length === 0) || sending.value) return

  if (!context.value) {
    await refreshContext()
  }

  const pendingFiles = attachments.value.map((item) => item.file)
  const attachmentNote = pendingFiles.length
    ? `\n\n[本轮附件：${pendingFiles.map((file) => file.name).join('、')}]`
    : ''

  draft.value = ''
  attachments.value = []
  messages.value.push({ role: 'user', content: (question || '请分析附件内容。') + attachmentNote })
  await scrollToBottom()

  sending.value = true
  
  // 如果有附件，使用普通模式
  if (pendingFiles.length) {
    try {
      const payload = {
        question: question || '请分析我上传的附件，并结合当前模块数据给出判断。',
        path: route.path,
        module_key: context.value?.module_key,
        history: messages.value.slice(0, -1),
        files: pendingFiles
      }
      const res = await copilotApi.chatWithFiles(payload)
      messages.value.push({ role: 'assistant', content: res.answer })
      await scrollToBottom()
    } catch (error) {
      console.error('Copilot问答失败:', error)
      messages.value.push({
        role: 'assistant',
        content: '当前 AI Copilot 暂时无法生成回答，请稍后重试，或先查看模块数据页的核心指标。'
      })
    } finally {
      sending.value = false
    }
    return
  }

  // 无附件时使用流式模式
  const assistantMessageIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  
  try {
    const payload = {
      question: question || '请分析我上传的附件，并结合当前模块数据给出判断。',
      path: route.path,
      module_key: context.value?.module_key,
      history: messages.value.slice(0, -2)
    }
    
    await copilotApi.chatStream(
      payload,
      // onChunk: 接收到内容片段
      (content: string) => {
        messages.value[assistantMessageIndex].content += content
        scrollToBottom()
      },
      // onDone: 完成
      () => {
        sending.value = false
      },
      // onError: 错误处理
      (error: Error) => {
        console.error('Copilot流式问答失败:', error)
        if (!messages.value[assistantMessageIndex].content) {
          messages.value[assistantMessageIndex].content = '当前 AI Copilot 暂时无法生成回答，请稍后重试，或先查看模块数据页的核心指标。'
        }
        sending.value = false
      }
    )
  } catch (error) {
    console.error('Copilot问答失败:', error)
    if (!messages.value[assistantMessageIndex].content) {
      messages.value[assistantMessageIndex].content = '当前 AI Copilot 暂时无法生成回答，请稍后重试，或先查看模块数据页的核心指标。'
    }
    sending.value = false
  }
}

const addFiles = (files: File[]) => {
  const next = [...attachments.value]
  for (const file of files) {
    if (next.length >= MAX_ATTACHMENTS) {
      ElMessage.warning(`最多同时上传 ${MAX_ATTACHMENTS} 个附件`)
      break
    }
    if (file.size > MAX_ATTACHMENT_SIZE) {
      ElMessage.warning(`${file.name} 超过10MB，已跳过`)
      continue
    }
    next.push({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      file,
      isImage: file.type.startsWith('image/')
    })
  }
  attachments.value = next
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  addFiles(Array.from(input.files || []))
  input.value = ''
}

const handlePaste = (event: ClipboardEvent) => {
  const files: File[] = []
  Array.from(event.clipboardData?.items || []).forEach((item, index) => {
    if (item.kind === 'file') {
      const file = item.getAsFile()
      if (file) {
        const ext = file.type.split('/')[1] || 'png'
        files.push(new File([file], file.name || `粘贴图片-${index + 1}.${ext}`, { type: file.type }))
      }
    }
  })
  if (files.length) {
    event.preventDefault()
    addFiles(files)
    ElMessage.success('已添加粘贴的图片')
  }
}

const removeAttachment = (id: string) => {
  attachments.value = attachments.value.filter((item) => item.id !== id)
}

const readConversationStore = (): Record<string, ConversationRecord> => {
  try {
    const raw = localStorage.getItem(CONVERSATION_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

const writeConversationStore = (store: Record<string, ConversationRecord>) => {
  try {
    localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(store))
  } catch (error) {
    console.warn('保存Copilot对话失败:', error)
  }
}

const normalizeMessages = (items: unknown) => {
  if (!Array.isArray(items)) return []

  return items
    .filter((item): item is CopilotMessage => {
      return Boolean(
        item &&
        typeof item === 'object' &&
        ((item as CopilotMessage).role === 'user' || (item as CopilotMessage).role === 'assistant')
      )
    })
    .slice(-MAX_SAVED_MESSAGES)
    .map((item) => ({
      role: item.role,
      content: String(item.content || '').slice(0, MAX_MESSAGE_LENGTH)
    }))
}

const loadConversation = () => {
  const store = readConversationStore()
  const record = store[conversationKey.value]
  messages.value = record?.messages ? normalizeMessages(record.messages) as CopilotMessage[] : []
}

const persistConversation = () => {
  const store = readConversationStore()
  const savedMessages = normalizeMessages(messages.value) as CopilotMessage[]

  if (savedMessages.length === 0) {
    delete store[conversationKey.value]
    writeConversationStore(store)
    return
  }

  store[conversationKey.value] = {
    path: route.path,
    moduleName: context.value?.module_name || pageTitle.value,
    updatedAt: new Date().toISOString(),
    messages: savedMessages
  }
  writeConversationStore(store)
}

const clearConversation = async () => {
  if (!messages.value.length) {
    ElMessage.info('当前页面暂无已保存对话')
    return
  }

  try {
    await ElMessageBox.confirm('确定清空当前页面的AI对话记录吗？', '清空对话', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning'
    })
    messages.value = []
    attachments.value = []
    persistConversation()
    ElMessage.success('当前页面对话已清空')
  } catch {
    // 用户取消
  }
}

watch(
  () => route.fullPath,
  () => {
    context.value = null
    loadConversation()
    if (visible.value) {
      refreshContext()
    }
  },
  { immediate: true }
)

watch(
  messages,
  () => {
    persistConversation()
  },
  { deep: true }
)
</script>

<style scoped>
.copilot-fab {
  position: fixed;
  right: 0;
  top: 58%;
  z-index: 2100;
  width: 50px;
  height: 112px;
  border: none;
  border-radius: 14px 0 0 14px;
  background: linear-gradient(180deg, #2563eb 0%, #0f766e 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-direction: column;
  cursor: pointer;
  box-shadow: -10px 14px 30px rgba(15, 23, 42, 0.22);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.copilot-fab span {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.1;
}

.copilot-fab:hover {
  transform: translateX(-4px);
  box-shadow: -12px 16px 36px rgba(37, 99, 235, 0.32);
}

.copilot-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2200;
  background: rgba(2, 6, 23, 0.48);
}

.copilot-drawer {
  position: fixed;
  right: 0;
  top: 0;
  z-index: 2210;
  width: min(560px, 100vw);
  height: 100vh;
  background: var(--card-bg);
  color: var(--text-primary);
  box-shadow: -24px 0 56px rgba(15, 23, 42, 0.26);
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--card-border);
}

.copilot-header {
  height: 76px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--card-border);
  flex-shrink: 0;
}

.copilot-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.copilot-title h3 {
  margin: 0;
  font-size: 18px;
  line-height: 1.25;
  color: var(--text-primary);
}

.copilot-title p {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.icon-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 8px;
  color: var(--text-secondary);
  background: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.icon-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.copilot-warning {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 18px 20px 10px;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.13);
  color: #d97706;
  font-size: 13px;
  line-height: 1.6;
}

.copilot-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 20px 18px;
}

.copilot-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}

.copilot-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.module-entry {
  border: 1px solid var(--card-border);
  background: var(--hover-bg);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 14px;
}

.entry-line {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.saved-hint {
  margin-left: 8px;
  color: #0f766e;
  font-size: 12px;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.question-chip {
  border: none;
  border-radius: 6px;
  padding: 7px 10px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--accent-color);
  cursor: pointer;
  font-size: 13px;
  line-height: 1.3;
}

.question-chip:hover {
  background: rgba(59, 130, 246, 0.2);
}

.message-list {
  flex: 1;
  min-height: 220px;
  overflow-y: auto;
  padding: 4px 2px 14px;
}

.empty-state {
  height: 100%;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.message-row {
  display: flex;
  margin: 10px 0;
}

.message-row.user {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 86%;
  border-radius: 8px;
  padding: 11px 13px;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-row.user .message-bubble {
  background: var(--accent-color);
  color: #fff;
}

.message-row.assistant .message-bubble {
  background: var(--hover-bg);
  color: var(--text-primary);
  border: 1px solid var(--card-border);
}

/* 流式输出时的打字机光标 */
.message-row.assistant:last-child .message-bubble.streaming::after {
  content: '▋';
  animation: blink 1s infinite;
  margin-left: 2px;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.loading-bubble {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}

.loading-bubble span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: copilotTyping 1s infinite ease-in-out;
}

.loading-bubble span:nth-child(2) {
  animation-delay: 0.15s;
}

.loading-bubble span:nth-child(3) {
  animation-delay: 0.3s;
}

.input-bar {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-shrink: 0;
  padding-top: 10px;
  border-top: 1px solid var(--card-border);
}

.file-input {
  display: none;
}

.attach-btn {
  width: 38px;
  min-width: 38px;
  height: 38px;
  border: 1px solid var(--card-border);
  border-radius: 8px;
  background: var(--hover-bg);
  color: var(--text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.attach-btn:hover {
  color: var(--accent-color);
  border-color: rgba(var(--accent-primary), 0.45);
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0 0;
  border-top: 1px solid var(--card-border);
}

.attachment-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--card-border);
  border-radius: 8px;
  background: var(--hover-bg);
  color: var(--text-secondary);
  font-size: 12px;
}

.attachment-item span {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-remove {
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.attachment-remove:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.send-btn {
  width: 46px;
  min-width: 46px;
  height: 38px;
  padding: 0;
}

.data-pane {
  overflow-y: auto;
  padding-right: 4px;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.data-card {
  border: 1px solid var(--card-border);
  border-radius: 8px;
  background: var(--hover-bg);
  padding: 12px;
  min-width: 0;
}

.data-card span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: 6px;
}

.data-card strong {
  color: var(--text-primary);
  font-size: 17px;
  line-height: 1.25;
  word-break: break-word;
}

.planning-block {
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}

.planning-block h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.planning-block ol {
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.8;
}

.json-preview {
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.18);
  color: var(--text-secondary);
  overflow: auto;
  font-size: 12px;
  line-height: 1.55;
}

.copilot-mask-enter-active,
.copilot-mask-leave-active,
.copilot-panel-enter-active,
.copilot-panel-leave-active {
  transition: all 0.22s ease;
}

.copilot-mask-enter-from,
.copilot-mask-leave-to {
  opacity: 0;
}

.copilot-panel-enter-from,
.copilot-panel-leave-to {
  transform: translateX(100%);
}

@keyframes copilotTyping {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

@media (max-width: 640px) {
  .copilot-fab {
    top: auto;
    right: 14px;
    bottom: 18px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
  }

  .copilot-fab span {
    writing-mode: horizontal-tb;
    font-size: 11px;
  }

  .copilot-header {
    padding: 14px 14px;
  }

  .copilot-warning {
    margin: 14px 14px 8px;
  }

  .copilot-tabs {
    padding: 0 14px 14px;
  }

  .data-grid {
    grid-template-columns: 1fr;
  }
}
</style>
