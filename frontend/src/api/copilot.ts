import request from './request'

export interface CopilotCard {
  label: string
  value: string
}

export interface CopilotContext {
  module_key: string
  module_name: string
  role: string
  questions: string[]
  planning: string[]
  core_data: Record<string, any>
  cards: CopilotCard[]
  disclaimer: string
  generated_at: string
}

export interface CopilotMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface CopilotAttachmentResult {
  filename: string
  content_type: string
  size: number
  kind: 'file' | 'image'
  extract_status: string
  summary?: string
  text?: string
  image?: {
    width: number
    height: number
    format?: string
    mode?: string
  }
}

export interface CopilotChatResponse {
  answer: string
  module_key: string
  module_name: string
  used_questions: string[]
  attachments?: CopilotAttachmentResult[]
  provider?: string
  generated_at: string
}

export interface CopilotProvider {
  key: string
  name: string
  model: string
  enabled: boolean
  is_default: boolean
}

export const copilotApi = {
  getProviders() {
    return request.get('/copilot/providers') as Promise<CopilotProvider[]>
  },

  getContext(params: { path?: string; module_key?: string }) {
    return request.get('/copilot/context', { params }) as Promise<CopilotContext>
  },

  chat(payload: {
    question: string
    path?: string
    module_key?: string
    provider?: string
    history?: CopilotMessage[]
    stream?: boolean
  }) {
    return request.post('/copilot/chat', payload) as Promise<CopilotChatResponse>
  },

  /**
   * 流式聊天 - 返回 ReadableStream 用于打字机效果
   */
  async chatStream(
    payload: {
      question: string
      path?: string
      module_key?: string
      provider?: string
      history?: CopilotMessage[]
    },
    onChunk: (content: string) => void,
    onDone?: () => void,
    onError?: (error: Error) => void
  ) {
    try {
      const token = localStorage.getItem('token') || ''
      // 使用与 axios 相同的 baseURL 配置
      const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
      const url = `${baseURL}/copilot/chat`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...payload,
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data:')) continue

          const data = line.slice(5).trim()
          if (!data) continue

          try {
            const json = JSON.parse(data)

            if (json.content) {
              onChunk(json.content)
            }

            if (json.done) {
              onDone?.()
              return
            }

            if (json.error) {
              throw new Error(json.error)
            }
          } catch (e) {
            if (e instanceof SyntaxError) continue
            throw e
          }
        }
      }
    } catch (error) {
      onError?.(error as Error)
      throw error
    }
  },

  chatWithFiles(payload: {
    question: string
    path?: string
    module_key?: string
    provider?: string
    history?: CopilotMessage[]
    files: File[]
  }) {
    const formData = new FormData()
    formData.append('question', payload.question)
    if (payload.path) formData.append('path', payload.path)
    if (payload.module_key) formData.append('module_key', payload.module_key)
    if (payload.provider) formData.append('provider', payload.provider)
    formData.append('history', JSON.stringify(payload.history || []))
    payload.files.forEach((file) => formData.append('files', file, file.name))

    return request.post('/copilot/chat-with-files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    }) as Promise<CopilotChatResponse>
  }
}
