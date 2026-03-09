<script setup lang="ts">
/**
 * AssistantView - AI Production Assistant Chat Interface
 * Ask questions about lutherie, get guidance on builds
 *
 * Connected to API endpoints:
 *   POST /api/ai/assistant/chat
 *   GET  /api/ai/assistant/history
 */
import { ref, nextTick } from 'vue'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const messages = ref<Message[]>([
  {
    id: 1,
    role: 'assistant',
    content: "Hello! I'm your AI Production Assistant. I can help with questions about guitar building, wood selection, techniques, troubleshooting, and more. What would you like to know?",
    timestamp: new Date(),
  },
])

const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const quickPrompts = [
  'What wood is best for a classical guitar top?',
  'How do I calculate fret positions?',
  'Explain bracing patterns for acoustics',
  'Troubleshooting buzzing frets',
]

async function sendMessage() {
  if (!inputText.value.trim()) return

  const userMessage: Message = {
    id: Date.now(),
    role: 'user',
    content: inputText.value,
    timestamp: new Date(),
  }
  messages.value.push(userMessage)
  inputText.value = ''

  await nextTick()
  scrollToBottom()

  isTyping.value = true

  // Simulated AI response
  await new Promise(resolve => setTimeout(resolve, 1500))

  const assistantMessage: Message = {
    id: Date.now() + 1,
    role: 'assistant',
    content: getSimulatedResponse(userMessage.content),
    timestamp: new Date(),
  }
  messages.value.push(assistantMessage)
  isTyping.value = false

  await nextTick()
  scrollToBottom()
}

function getSimulatedResponse(query: string): string {
  const responses: Record<string, string> = {
    default: "That's a great question about lutherie! This AI assistant feature is currently in development. Soon you'll be able to get detailed guidance on all aspects of instrument building, from wood selection to finishing techniques.",
  }
  return responses.default
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
      <h1>AI Assistant</h1>
      <p class="subtitle">Your personal luthier's knowledge base</p>
    </div>

    <div class="content">
      <div class="chat-container">
        <div class="messages" ref="messagesContainer">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              {{ message.role === 'assistant' ? '🤖' : '👤' }}
            </div>
            <div class="message-content">
              <p>{{ message.content }}</p>
              <span class="timestamp">
                {{ message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
              </span>
            </div>
          </div>

          <div v-if="isTyping" class="message assistant typing">
            <div class="message-avatar">🤖</div>
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
        <div class="panel topics-panel">
          <h3>Popular Topics</h3>
          <ul class="topic-list">
            <li>🪵 Wood Selection</li>
            <li>📐 Fret Calculations</li>
            <li>🎸 Bracing Patterns</li>
            <li>🔧 Setup & Adjustment</li>
            <li>✨ Finishing Techniques</li>
            <li>🔊 Tone Optimization</li>
          </ul>
        </div>

        <div class="panel history-panel">
          <h3>Recent Conversations</h3>
          <div class="history-list">
            <div class="history-item">
              <span class="history-title">Spruce vs Cedar tops</span>
              <span class="history-date">Today</span>
            </div>
            <div class="history-item">
              <span class="history-title">Fret leveling technique</span>
              <span class="history-date">Yesterday</span>
            </div>
            <div class="history-item">
              <span class="history-title">Neck relief adjustment</span>
              <span class="history-date">Mar 4</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full AI assistant with context-aware responses and build history integration coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.assistant-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; display: flex; flex-direction: column; }
.header { max-width: 1400px; margin: 0 auto 2rem; width: 100%; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; flex: 1; display: grid; grid-template-columns: 1fr 280px; gap: 1.5rem; width: 100%; }

.chat-container { background: #1a1a1a; border-radius: 0.75rem; display: flex; flex-direction: column; height: 600px; }

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

.topic-list { list-style: none; padding: 0; margin: 0; }
.topic-list li { padding: 0.5rem 0; border-bottom: 1px solid #262626; font-size: 0.875rem; cursor: pointer; }
.topic-list li:hover { color: #60a5fa; }

.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { padding: 0.5rem; background: #262626; border-radius: 0.375rem; cursor: pointer; }
.history-item:hover { background: #333; }
.history-title { display: block; font-size: 0.875rem; font-weight: 500; }
.history-date { font-size: 0.75rem; color: #888; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; width: 100%; }

@media (max-width: 1000px) { .content { grid-template-columns: 1fr; } .sidebar { display: none; } }
</style>
