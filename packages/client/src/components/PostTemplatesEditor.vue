<template>
  <div class="post-templates-editor">
    <h3>Post Processor Templates Editor</h3>
    
    <div class="controls">
      <button @click="loadTemplates" :disabled="loading">
        {{ loading ? 'Loading...' : 'Load Templates' }}
      </button>
      <button @click="saveTemplates" :disabled="loading">
        {{ loading ? 'Saving...' : 'Save Templates' }}
      </button>
      <span v-if="feedback.message" :class="['feedback', feedback.type]">
        {{ feedback.message }}
      </span>
    </div>

    <div class="schema-help">
      <strong>Schema:</strong> Array of objects with:
      <code>id</code> (string),
      <code>title</code> (string),
      <code>controller</code> (string),
      <code>line_numbers</code> (object with enabled/start/step/prefix),
      <code>header</code> (array),
      <code>footer</code> (array),
      <code>tokens</code> (object)
    </div>

    <textarea 
      v-model="rawJson" 
      class="json-editor"
      placeholder="Paste JSON array here..."
      spellcheck="false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const rawJson = ref<string>('')
const loading = ref<boolean>(false)
const feedback = ref<{ message: string; type: 'success' | 'error' | '' }>({
  message: '',
  type: ''
})

async function loadTemplates() {
  loading.value = true
  feedback.value = { message: '', type: '' }
  
  try {
    const res = await fetch('/api/posts')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    
    const data = await res.json()
    rawJson.value = JSON.stringify(data, null, 2)
    feedback.value = { message: 'Templates loaded successfully ✓', type: 'success' }
  } catch (err: any) {
    feedback.value = { message: `Load failed: ${err.message}`, type: 'error' }
  } finally {
    loading.value = false
  }
}

async function saveTemplates() {
  loading.value = true
  feedback.value = { message: '', type: '' }
  
  try {
    // Validate JSON structure
    const parsed = JSON.parse(rawJson.value)
    if (!Array.isArray(parsed)) {
      throw new Error('JSON must be an array')
    }
    
    // Check required fields
    for (const post of parsed) {
      if (!post.id || !post.title || !post.controller) {
        throw new Error('Each post must have id, title, and controller')
      }
      if (!Array.isArray(post.header) || !Array.isArray(post.footer)) {
        throw new Error('header and footer must be arrays')
      }
    }
    
    // Check duplicate IDs
    const ids = parsed.map((p: any) => p.id)
    const duplicates = ids.filter((id: string, i: number) => ids.indexOf(id) !== i)
    if (duplicates.length > 0) {
      throw new Error(`Duplicate post IDs: ${duplicates.join(', ')}`)
    }
    
    // Send to server
    const res = await fetch('/api/posts', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: rawJson.value
    })
    
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    
    feedback.value = { message: 'Templates saved successfully ✓', type: 'success' }
  } catch (err: any) {
    feedback.value = { message: `Save failed: ${err.message}`, type: 'error' }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.post-templates-editor {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

button {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.feedback {
  padding: 0.5rem;
  border-radius: 4px;
}

.feedback.success {
  background: #d4edda;
  color: #155724;
}

.feedback.error {
  background: #f8d7da;
  color: #721c24;
}

.schema-help {
  background: #f0f0f0;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.schema-help code {
  background: white;
  padding: 2px 4px;
  border-radius: 2px;
}

.json-editor {
  width: 100%;
  min-height: 400px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
}
</style>
