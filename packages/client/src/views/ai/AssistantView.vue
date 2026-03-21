<script setup lang="ts">
/**
 * AssistantView - AI Production Assistant Chat Interface (D-4)
 * Ask questions about lutherie, get guidance on builds
 *
 * Connected to API endpoints:
 *   POST /api/ai/assistant/chat
 *   GET  /api/ai/assistant/history
 *   DELETE /api/ai/assistant/history
 *   GET  /api/ai/assistant/status
 *
 * D-4 project context routes:
 *   ?project_id= (canonical query); legacy ?projectId= also accepted
 *   /ai/assistant/:project_id? (optional segment); legacy path param projectId also read if present
 *   Instrument Hub singleton (useInstrumentProject) when no query/param — D-4 hub fallback
 */
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useInstrumentProject } from '@/instrument-workspace/shared-state/useInstrumentProject'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function firstRouteString(
  v: string | string[] | undefined | null
): string | null {
  if (v == null) return null
  if (Array.isArray(v)) {
    const s = v[0]
    return s != null && String(s) !== '' ? String(s) : null
  }
  return String(v) !== '' ? String(v) : null
}

function greetingForProject(pid: string | null): string {
  return pid
    ? "Hello! I'm your AI Production Assistant. I can see you have a project loaded \u2014 ask me anything about your build, wood selection, or lutherie techniques."
    : "Hello! I'm your AI Production Assistant. I can help with questions about guitar building, wood selection, techniques, troubleshooting, and more. What would you like to know?"
}

const route = useRoute()
const { projectId: hubProjectId } = useInstrumentProject()

/**
 * D-4 hub project wiring: resolve active project as
 * route query `project_id` / legacy `projectId` → path `project_id` then legacy `projectId` → Instrument Hub.
 */
const projectId = computed(() => {
  const fromQuery = firstRouteString(
    route.query.project_id as string | string[] | undefined
  )
  const fromLegacyQuery = firstRouteString(
    route.query.projectId as string | string[] | undefined
  )
  const fromPathSnake = firstRouteString(
    route.params.project_id as string | string[] | undefined
  )
  const fromPathLegacy = firstRouteString(
    route.params.projectId as string | string[] | undefined
  )
  const fromHub = hubProjectId.value
  return (
    fromQuery ||
    fromLegacyQuery ||
    fromPathSnake ||
    fromPathLegacy ||
    fromHub ||
    null
  )
})

/** D-4: Session persistence via sessionStorage (keyed by project) */
function getSessionKey(): string {
  return `assistant_session_${projectId.value || 'global'}`
}

const storedSessionId = sessionStorage.getItem(getSessionKey())
const sessionId = ref<string>(storedSessionId || crypto.randomUUID())
if (!storedSessionId) {
  sessionStorage.setItem(getSessionKey(), sessionId.value)
}

/** D-4: Service status indicator */
const serviceAvailable = ref<boolean | null>(null)
const isLoadingHistory = ref(false)

function formatApiError(err: unknown, fallback: string): string {
  if (err == null || typeof err !== 'object') return fallback
  const detail = (err as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item != null && typeof item === 'object' && 'msg' in item) {
          const m = (item as { msg?: unknown }).msg
          return typeof m === 'string' ? m : null
        }
        return null
      })
      .filter((s): s is string => s != null && s !== '')
    if (parts.length > 0) return parts.join('; ')
  }
  return fallback
}

function makeWelcomeMessage(): Message {
  return {
    id: 1,
    role: 'assistant',
    content: greetingForProject(projectId.value),
    timestamp: new Date(),
  }
}

const messages = ref<Message[]>([makeWelcomeMessage()])

watch(
  projectId,
  (next, prev) => {
    if (next === prev) return
    // Update session key when project changes
    const newKey = `assistant_session_${next || 'global'}`
    const existingSession = sessionStorage.getItem(newKey)
    if (existingSession) {
      sessionId.value = existingSession
    } else {
      sessionId.value = crypto.randomUUID()
      sessionStorage.setItem(newKey, sessionId.value)
    }

    if (messages.value.length === 1 && messages.value[0]?.role === 'assistant') {
      messages.value[0] = {
        ...messages.value[0],
        content: greetingForProject(next),
        timestamp: new Date(),
      }
      return
    }
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: next
        ? "Project context updated \u2014 I can see this build now. Ask me anything about it."
        : "Project context cleared \u2014 I'm answering in general mode now.",
      timestamp: new Date(),
    })
  },
  { flush: 'post' }
)

const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const quickPrompts = [
  'What wood is best for a classical guitar top?',
  'How do I calculate fret positions?',
  'Explain bracing patterns for acoustics',
  'Troubleshooting buzzing frets',
]

/** D-4: Check if AI service is available */
async function checkServiceStatus(): Promise<void> {
  try {
    const res = await fetch('/api/ai/assistant/status', {
      credentials: 'include',
    })
    if (res.ok) {
      const data = await res.json()
      serviceAvailable.value = data.ok === true
    } else {
      serviceAvailable.value = false
    }
  } catch {
    serviceAvailable.value = false
  }
}

/** D-4: Load conversation history from server */
async function loadHistory(): Promise<void> {
  isLoadingHistory.value = true
  try {
    const res = await fetch(`/api/ai/assistant/history?session_id=${encodeURIComponent(sessionId.value)}&limit=50`, {
      credentials: 'include',
    })
    if (res.ok) {
      const data = await res.json()
      if (data.messages && data.messages.length > 0) {
        messages.value = data.messages.map((msg: any, idx: number) => ({
          id: idx + 1,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.timestamp),
        }))
      }
    }
  } catch {
    // Keep welcome message on error
  } finally {
    isLoadingHistory.value = false
  }
}

/** D-4: Clear conversation history */
async function clearHistory(): Promise<void> {
  try {
    await fetch(`/api/ai/assistant/history?session_id=${encodeURIComponent(sessionId.value)}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    // Generate new session
    sessionId.value = crypto.randomUUID()
    sessionStorage.setItem(getSessionKey(), sessionId.value)
    messages.value = [makeWelcomeMessage()]
  } catch {
    // Silently fail
  }
}

onMounted(async () => {
  await checkServiceStatus()
  await loadHistory()
})

async function sendMessage() {
  if (!inputText.value.trim()) return

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: inputText.value,
    timestamp: new Date(),
  }
  messages.value.push(userMessage)
  const messageText = inputText.value
  inputText.value = ''

  await nextTick()
  scrollToBottom()

  isTyping.value = true

  try {
    const body: Record<string, string | undefined> = {
      message: messageText,
      session_id: sessionId.value,
    }
    const pid = projectId.value
    if (pid) body.project_id = pid
    const res = await fetch('/api/ai/assistant/chat', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const errPayload = await res.json().catch(() => ({}))
      if (res.status === 401 && pid) {
        throw new Error(
          `${formatApiError(errPayload, 'Authentication required')} Please sign in to use the assistant with project context.`
        )
      }
      throw new Error(formatApiError(errPayload, `HTTP ${res.status}`))
    }

    const data = await res.json()

    const assistantMessage: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: data.response,
      timestamp: new Date(),
    }
    messages.value.push(assistantMessage)
  } catch (e: any) {
    const errorMessage: Message = {
      id: Date.now() + 1,
      role: 'assistant',
      content: `I'm having trouble connecting right now. ${e.message || 'Please try again later.'}`,
      timestamp: new Date(),
    }
    messages.value.push(errorMessage)
  } finally {
    isTyping.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function useQuickPrompt(prompt: string) {
  inputText.value = prompt
  sendMessage()
}
</script>

<template>
  <div class="assistant-view">
    <div class="header">
      <div class="header-row">
        <div class="header-title">
          <h1>AI Assistant</h1>
          <p class="subtitle">Your personal luthier's knowledge base</p>
          <p v-if="projectId" class="project-context-badge">
            Project context active — <code>{{ projectId }}</code>
          </p>
        </div>
        <div class="header-actions">
          <span
            class="status-dot"
            :class="{ online: serviceAvailable === true, offline: serviceAvailable === false, pending: serviceAvailable === null }"
            :title="serviceAvailable === true ? 'Service online' : serviceAvailable === false ? 'Service offline' : 'Checking...'"
          ></span>
          <button class="btn btn-sm btn-ghost" @click="clearHistory" title="Clear conversation">
            Clear
          </button>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="chat-container">
        <div v-if="isLoadingHistory" class="loading-history">
          Loading conversation...
        </div>
        <div class="messages" ref="messagesContainer">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              {{ message.role === 'assistant' ? '\ud83e\udd16' : '\ud83d\udc64' }}
            </div>
            <div class="message-content">
              <p>{{ message.content }}</p>
              <span class="timestamp">
                {{ message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
              </span>
            </div>
          </div>

          <div v-if="isTyping" class="message assistant typing">
            <div class="message-avatar">\ud83e\udd16</div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="input-area">
          <div class="quick-prompts">
            <button
              v-for="prompt in quickPrompts"
              :key="prompt"
              class="quick-prompt"
              @click="useQuickPrompt(prompt)"
            >
              {{ prompt }}
            </button>
          </div>
          <div class="input-row">
            <input
              type="text"
              v-model="inputText"
              placeholder="Ask about lutherie, techniques, materials..."
              @keyup.enter="sendMessage"
            />
            <button class="btn btn-primary" @click="sendMessage" :disabled="!inputText.trim()">
              Send
            </button>
          </div>
        </div>
      </div>

      <div class="sidebar">
        <div class="panel session-panel">
          <h3>Session</h3>
          <div class="session-info">
            <div class="session-row">
              <span class="session-label">ID:</span>
              <code class="session-value">{{ sessionId.slice(0, 8) }}...</code>
            </div>
            <div class="session-row">
              <span class="session-label">Project:</span>
              <span class="session-value">{{ projectId || 'None' }}</span>
            </div>
            <div class="session-row">
              <span class="session-label">Messages:</span>
              <span class="session-value">{{ messages.length }}</span>
            </div>
          </div>
        </div>

        <div class="panel topics-panel">
          <h3>Popular Topics</h3>
          <ul class="topic-list">
            <li>\ud83e\udeb5 Wood Selection</li>
            <li>\ud83d\udcd0 Fret Calculations</li>
            <li>\ud83c\udfb8 Bracing Patterns</li>
            <li>\ud83d\udd27 Setup & Adjustment</li>
            <li>\u2728 Finishing Techniques</li>
            <li>\ud83d\udd0a Tone Optimization</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.assistant-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; display: flex; flex-direction: column; }
.header { max-width: 1400px; margin: 0 auto 2rem; width: 100%; }
.header-row { display: flex; justify-content: space-between; align-items: flex-start; }
.header-title h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }
.project-context-badge { margin: 0.75rem 0 0; font-size: 0.8rem; color: #60a5fa; }
.project-context-badge code { background: #262626; padding: 0.1rem 0.35rem; border-radius: 0.25rem; font-size: 0.75rem; }
.header-actions { display: flex; align-items: center; gap: 0.75rem; }

.status-dot { width: 10px; height: 10px; border-radius: 50%; }
.status-dot.online { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-dot.offline { background: #ef4444; }
.status-dot.pending { background: #888; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.btn-sm { padding: 0.375rem 0.75rem; font-size: 0.75rem; }
.btn-ghost { background: transparent; border: 1px solid #333; color: #888; }
.btn-ghost:hover { border-color: #60a5fa; color: #60a5fa; }

.content { max-width: 1400px; margin: 0 auto; flex: 1; display: grid; grid-template-columns: 1fr 280px; gap: 1.5rem; width: 100%; }

.chat-container { background: #1a1a1a; border-radius: 0.75rem; display: flex; flex-direction: column; height: 600px; position: relative; }
.loading-history { position: absolute; top: 0; left: 0; right: 0; padding: 0.5rem; background: #262626; text-align: center; font-size: 0.75rem; color: #888; border-radius: 0.75rem 0.75rem 0 0; }

.messages { flex: 1; overflow-y: auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
.message { display: flex; gap: 0.75rem; }
.message.user { flex-direction: row-reverse; }
.message-avatar { width: 36px; height: 36px; background: #262626; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
.message-content { max-width: 70%; padding: 0.75rem 1rem; border-radius: 0.75rem; }
.message.assistant .message-content { background: #262626; }
.message.user .message-content { background: #2563eb; }
.message-content p { margin: 0; line-height: 1.5; }
.timestamp { font-size: 0.625rem; color: #666; margin-top: 0.25rem; display: block; }

.typing-indicator { display: flex; gap: 4px; }
.typing-indicator span { width: 8px; height: 8px; background: #666; border-radius: 50%; animation: typing 1.4s infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-4px); } }

.input-area { padding: 1rem 1.5rem; border-top: 1px solid #333; }
.quick-prompts { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem; }
.quick-prompt { padding: 0.375rem 0.75rem; background: #262626; border: 1px solid #333; border-radius: 1rem; color: #888; font-size: 0.75rem; cursor: pointer; }
.quick-prompt:hover { border-color: #60a5fa; color: #60a5fa; }

.input-row { display: flex; gap: 0.75rem; }
.input-row input { flex: 1; padding: 0.75rem 1rem; background: #262626; border: 1px solid #333; border-radius: 0.5rem; color: #e5e5e5; }
.btn { padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }

.sidebar { display: flex; flex-direction: column; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }

.session-panel .session-info { display: flex; flex-direction: column; gap: 0.5rem; }
.session-row { display: flex; justify-content: space-between; font-size: 0.875rem; }
.session-label { color: #666; }
.session-value { color: #e5e5e5; }
.session-value code { font-family: monospace; color: #60a5fa; }

.topic-list { list-style: none; padding: 0; margin: 0; }
.topic-list li { padding: 0.5rem 0; border-bottom: 1px solid #262626; font-size: 0.875rem; cursor: pointer; }
.topic-list li:hover { color: #60a5fa; }

@media (max-width: 1000px) { .content { grid-template-columns: 1fr; } .sidebar { display: none; } }
</style>
