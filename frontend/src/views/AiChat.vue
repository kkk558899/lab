<template>
  <div class="ai-chat-container">
    <div class="chat-main-card">
      <!-- 顶部标题与操作栏 -->
      <div class="chat-header">
        <div class="header-left">
          <div class="bot-avatar">
            <el-icon :size="24"><Service /></el-icon>
          </div>
          <div class="bot-info">
            <div class="bot-title">
              <span>智能实验室 Agent 助手</span>
              <el-tag size="small" type="success" effect="dark">LangGraph + RAG + Tool Calling</el-tag>
            </div>
            <div class="bot-status">
              <span class="status-dot"></span>
              <span>支持自然语言智能预约、排期查询与知识库问答</span>
            </div>
          </div>
        </div>

        <div class="header-right">
          <el-button size="small" :icon="Delete" @click="handleClearHistory">清空对话</el-button>
        </div>
      </div>

      <!-- 消息列表滚动区域 -->
      <div ref="chatBodyRef" class="chat-body">
        <!-- 欢迎卡片 -->
        <div v-if="messages.length === 0" class="welcome-box">
          <div class="welcome-icon">
            <el-icon :size="48" color="#409eff"><Cpu /></el-icon>
          </div>
          <h3>你好！我是实验室智能预约助手</h3>
          <p class="welcome-desc">
            我可以帮您快速查询空闲实验室排期、根据您的需求自动创建预约单、解答实验室操作规程及借用规则。
          </p>

          <div class="prompt-chips-title">💡 尝试这样问我：</div>
          <div class="prompt-chips">
            <div
              v-for="(p, index) in quickPrompts"
              :key="index"
              class="chip-item"
              @click="handleSendPrompt(p)"
            >
              {{ p }}
            </div>
          </div>
        </div>

        <!-- 聊天气泡列表 -->
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="{ 'user-row': msg.role === 'user', 'ai-row': msg.role === 'assistant' }"
        >
          <div class="msg-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="38" :src="userAvatar">
              {{ user.nickname?.charAt(0) || user.username?.charAt(0) || 'U' }}
            </el-avatar>
            <div v-else class="ai-avatar-box">
              <el-icon :size="22"><Service /></el-icon>
            </div>
          </div>

          <div class="msg-content-wrapper">
            <!-- 角色与时间 -->
            <div class="msg-meta">
              <span class="msg-sender">{{ msg.role === 'user' ? (user.nickname || '我') : '实验室智能助手' }}</span>
              <span class="msg-time">{{ msg.time }}</span>
            </div>

            <!-- Agent 工具调用及思考过程展示 -->
            <div v-if="msg.toolCalls && msg.toolCalls.length > 0" class="tool-call-box">
              <div class="tool-title">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>Agent 正在执行调度与工具调用：</span>
              </div>
              <div v-for="(tool, tIdx) in msg.toolCalls" :key="tIdx" class="tool-item">
                <span class="tool-tag">⚡ {{ tool.name || 'Tool' }}</span>
                <span class="tool-desc">{{ tool.desc || tool.result || tool }}</span>
              </div>
            </div>

            <!-- 消息文本 -->
            <div class="msg-bubble">
              <div class="bubble-text">{{ msg.content }}</div>
              <span v-if="msg.isStreaming" class="streaming-cursor"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入框与推荐芯片 -->
      <div class="chat-footer">
        <!-- 快捷问答提示 -->
        <div v-if="messages.length > 0" class="mini-chips">
          <span
            v-for="(p, index) in quickPrompts.slice(0, 3)"
            :key="index"
            class="mini-chip"
            @click="handleSendPrompt(p)"
          >
            {{ p }}
          </span>
        </div>

        <div class="input-box">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="2"
            placeholder="输入您想咨询或预约的需求（例如：我想预约明天下午的人工智能实验室...）"
            resize="none"
            :disabled="isGenerating"
            @keydown.enter.prevent="handleSend"
          />
          <div class="action-buttons">
            <el-button
              type="primary"
              :icon="Promotion"
              :loading="isGenerating"
              :disabled="!inputMessage.trim()"
              @click="handleSend"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Service, Cpu, Delete, Promotion, Loading } from '@element-plus/icons-vue'
import { sendAiChatMessageStream } from '@/api/ai'

const inputMessage = ref('')
const isGenerating = ref(false)
const chatBodyRef = ref(null)
const conversationId = ref(Date.now().toString())

const quickPrompts = ref([
  '我想预约明天下午的人工智能实验室进行模型训练',
  '查询当前有哪些实验室是开放状态的？',
  '实验室有哪些安全使用规章与开放时间？',
  '查询我的预约申请记录和审批状态'
])

const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是实验室预约智能助手。你可以直接用自然语言告诉我你想预约哪个实验室、什么时间，或者咨询相关实验室规章，我会自动为你规划并执行！',
    time: new Date().toLocaleTimeString().slice(0, 5),
    toolCalls: []
  }
])

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch (e) {
    return {}
  }
})

const userAvatar = computed(() => {
  if (user.value.avatar) {
    if (user.value.avatar.startsWith('http')) return user.value.avatar
    return `/api${user.value.avatar}`
  }
  return ''
})

onMounted(() => {
  scrollToBottom()
})

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}

const handleClearHistory = () => {
  ElMessageBox.confirm('确定要清空当前的对话记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    conversationId.value = Date.now().toString()
    messages.value = []
    ElMessage.success('对话已清空')
  }).catch(() => {})
}

const handleSendPrompt = (prompt) => {
  inputMessage.value = prompt
  handleSend()
}

const handleSend = async () => {
  const text = inputMessage.value.trim()
  if (!text || isGenerating.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    time: new Date().toLocaleTimeString().slice(0, 5)
  })

  inputMessage.value = ''
  isGenerating.value = true
  scrollToBottom()

  // 提取历史多轮对话上下文（包含刚才添加的最新用户消息，排除占位空消息）
  const historyList = messages.value
    .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content && m.content.trim())
    .map(m => ({ role: m.role, content: m.content.trim() }))

  // 构造助手响应占位消息
  const aiMsgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    time: new Date().toLocaleTimeString().slice(0, 5),
    isStreaming: true,
    toolCalls: []
  })

  try {
    await sendAiChatMessageStream({
      messages: historyList,
      message: text,
      conversationId: conversationId.value,
      onChunk: (chunk) => {
        messages.value[aiMsgIndex].content += chunk
        scrollToBottom()
      },
      onToolCall: (toolData) => {
        if (!messages.value[aiMsgIndex].toolCalls) {
          messages.value[aiMsgIndex].toolCalls = []
        }
        const existing = messages.value[aiMsgIndex].toolCalls.find(t => t.name === toolData.name)
        if (existing) {
          existing.desc = toolData.desc
        } else {
          messages.value[aiMsgIndex].toolCalls.push(toolData)
        }
        scrollToBottom()
      },
      onComplete: () => {
        messages.value[aiMsgIndex].isStreaming = false
        isGenerating.value = false
        scrollToBottom()
      },
      onError: (err) => {
        messages.value[aiMsgIndex].isStreaming = false
        messages.value[aiMsgIndex].content += '\n\n*(请求异常，请检查后端AI服务配置)*'
        isGenerating.value = false
        scrollToBottom()
      }
    })
  } catch (err) {
    messages.value[aiMsgIndex].isStreaming = false
    isGenerating.value = false
  }
}
</script>

<style scoped>
.ai-chat-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.chat-main-card {
  flex: 1;
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  height: 64px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: #fafafa;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bot-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.bot-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #262626;
}

.bot-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #52c41a;
}

.chat-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-box {
  margin: auto;
  max-width: 520px;
  text-align: center;
  padding: 30px 20px;
}

.welcome-icon {
  margin-bottom: 16px;
}

.welcome-box h3 {
  font-size: 18px;
  color: #262626;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.6;
  margin-bottom: 24px;
}

.prompt-chips-title {
  font-size: 13px;
  font-weight: 600;
  color: #595959;
  text-align: left;
  margin-bottom: 10px;
}

.prompt-chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chip-item {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  color: #409eff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.chip-item:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
}

.message-row {
  display: flex;
  gap: 12px;
}

.user-row {
  flex-direction: row-reverse;
}

.ai-avatar-box {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-content-wrapper {
  max-width: 75%;
  display: flex;
  flex-direction: column;
}

.user-row .msg-content-wrapper {
  align-items: flex-end;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #bfbfbf;
  margin-bottom: 4px;
}

.msg-sender {
  font-weight: 500;
  color: #8c8c8c;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  position: relative;
}

.user-row .msg-bubble {
  background: #1890ff;
  color: #ffffff;
  border-top-right-radius: 2px;
}

.ai-row .msg-bubble {
  background: #f5f7fa;
  color: #262626;
  border-top-left-radius: 2px;
}

.bubble-text {
  white-space: pre-wrap;
}

.tool-call-box {
  background: #fafafa;
  border-left: 3px solid #faad14;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  font-size: 12px;
}

.tool-title {
  color: #faad14;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.tool-item {
  color: #595959;
  display: flex;
  gap: 6px;
  margin-top: 2px;
}

.tool-tag {
  font-weight: 600;
}

.streaming-cursor {
  display: inline-block;
  width: 6px;
  height: 14px;
  background-color: #409eff;
  vertical-align: middle;
  margin-left: 4px;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.chat-footer {
  border-top: 1px solid #f0f0f0;
  padding: 12px 20px;
  background: #ffffff;
}

.mini-chips {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  overflow-x: auto;
  white-space: nowrap;
}

.mini-chip {
  background: #f0f2f5;
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 11px;
  color: #595959;
  cursor: pointer;
  transition: all 0.2s;
}

.mini-chip:hover {
  background: #e6f7ff;
  color: #1890ff;
}

.input-box {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
</style>
