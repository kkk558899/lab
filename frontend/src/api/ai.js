import request from '@/utils/request'

// 获取常用推荐提问列表
export function getAiPromptsApi() {
  return request({
    url: '/ai/prompts',
    method: 'get'
  })
}

// 知识库文档列表与状态
export function getKnowledgeListApi() {
  return request({
    url: '/ai/knowledge',
    method: 'get'
  })
}

// SSE 流式对话请求
export async function sendAiChatMessageStream({ messages, message, conversationId, onChunk, onToolCall, onComplete, onError }) {
  const token = localStorage.getItem('token')
  try {
    const payload = {
      conversation_id: conversationId,
      message: message
    }
    if (messages && Array.isArray(messages) && messages.length > 0) {
      payload.messages = messages
    } else if (message) {
      payload.messages = [{ role: 'user', content: message }]
    }

    const response = await fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(payload)
    })

    if (response.status === 401) {
      throw new Error('登录凭据已失效或未登录，请先登录（账号：student 或 admin，密码：123456）')
    }

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}))
      throw new Error(errJson.detail || errJson.message || errJson.msg || `网络响应错误 (${response.status})`)
    }

    const contentType = response.headers.get('content-type') || ''
    if (!contentType.includes('text/event-stream')) {
      const errJson = await response.json().catch(() => ({}))
      throw new Error(errJson.detail || errJson.message || '流式接口返回异常')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''

      for (const chunk of chunks) {
        const line = chunk
          .split('\n')
          .map((item) => item.trim())
          .find((item) => item.startsWith('data:'))
        if (!line) continue

        const dataStr = line.slice(5).trim()
        if (!dataStr || dataStr === '[DONE]') {
          if (onComplete) onComplete()
          return
        }

        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.type === 'done') {
            if (onComplete) onComplete()
            return
          } else if (parsed.type === 'error') {
            if (onChunk) onChunk(`\n\n⚠️ ${parsed.message || '大模型调用异常'}`)
          } else if (parsed.type === 'status') {
            if (onToolCall) onToolCall({ name: '思考', desc: parsed.message })
          } else if (parsed.type === 'tool_start') {
            if (onToolCall) onToolCall({ name: parsed.label || parsed.name, desc: '正在执行中…' })
          } else if (parsed.type === 'tool_end') {
            if (onToolCall) onToolCall({ name: parsed.label || parsed.name, desc: parsed.preview || '执行完成' })
          } else if (parsed.type === 'token') {
            if (onChunk) onChunk(parsed.content || '')
          } else if (parsed.content) {
            if (onChunk) onChunk(parsed.content)
          }
        } catch (e) {
          if (onChunk) onChunk(dataStr)
        }
      }
    }
    if (onComplete) onComplete()
  } catch (err) {
    console.error('AI Stream Error:', err)
    if (onError) onError(err)
  }
}
