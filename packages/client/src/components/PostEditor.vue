<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-dialog" @click.stop>
      <div class="dialog-header">
        <h2>{{ isEditMode ? 'Edit Post' : 'Create New Post' }}</h2>
        <button @click="$emit('close')" class="btn-close">×</button>
      </div>

      <div class="dialog-body">
        <div v-if="loading" class="loading">Loading...</div>
        <div v-if="error" class="error">{{ error }}</div>

        <form v-if="!loading" @submit.prevent="handleSave">
          <div class="form-group">
            <label>Post ID *</label>
            <input 
              v-model="form.id" 
              type="text" 
              placeholder="e.g., CUSTOM_HAAS"
              pattern="[A-Z0-9_]+"
              :disabled="isEditMode"
              required
            />
            <small>Uppercase letters, numbers, and underscores only</small>
          </div>

          <div class="form-group">
            <label>Name *</label>
            <input 
              v-model="form.name" 
              type="text" 
              placeholder="e.g., Haas VF-2 with Tool Changer"
              required
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea 
              v-model="form.description" 
              placeholder="Brief description of this post-processor..."
              rows="2"
            />
          </div>

          <div class="form-group">
            <label>Header Lines *</label>
            <div class="array-editor">
              <div v-for="(line, i) in form.header" :key="`header-${i}`" class="array-item">
                <input v-model="form.header[i]" type="text" placeholder="G-code line or comment" />
                <button @click="removeHeaderLine(i)" type="button" class="btn-remove">×</button>
              </div>
              <button @click="addHeaderLine" type="button" class="btn-add">+ Add Header Line</button>
            </div>
            <small>G-code lines or comments to insert at program start</small>
          </div>

          <div class="form-group">
            <label>Footer Lines *</label>
            <div class="array-editor">
              <div v-for="(line, i) in form.footer" :key="`footer-${i}`" class="array-item">
                <input v-model="form.footer[i]" type="text" placeholder="G-code line or comment" />
                <button @click="removeFooterLine(i)" type="button" class="btn-remove">×</button>
              </div>
              <button @click="addFooterLine" type="button" class="btn-add">+ Add Footer Line</button>
            </div>
            <small>G-code lines or comments to insert at program end</small>
          </div>

          <div class="form-group">
            <label>Metadata (Optional)</label>
            <div class="metadata-fields">
              <div class="metadata-row">
                <input v-model="form.metadata.controller_family" type="text" placeholder="Controller family (e.g., grbl)" />
                <input v-model="form.metadata.gcode_dialect" type="text" placeholder="G-code dialect (e.g., LinuxCNC)" />
              </div>
              <div class="metadata-row">
                <label class="checkbox-label">
                  <input v-model="form.metadata.supports_arcs" type="checkbox" />
                  Supports Arcs (G2/G3)
                </label>
                <label class="checkbox-label">
                  <input v-model="form.metadata.has_tool_changer" type="checkbox" />
                  Has Tool Changer
                </label>
              </div>
            </div>
          </div>

          <div class="validation-messages" v-if="validationResult">
            <div v-if="validationResult.errors.length > 0" class="errors">
              <strong>Errors:</strong>
              <ul>
                <li v-for="(err, i) in validationResult.errors" :key="`err-${i}`">{{ err }}</li>
              </ul>
            </div>
            <div v-if="validationResult.warnings.length > 0" class="warnings">
              <strong>Warnings:</strong>
              <ul>
                <li v-for="(warn, i) in validationResult.warnings" :key="`warn-${i}`">{{ warn }}</li>
              </ul>
            </div>
          </div>

          <div class="dialog-actions">
            <button @click="$emit('close')" type="button" class="btn-cancel">Cancel</button>
            <button @click="handleValidate" type="button" class="btn-validate">Validate</button>
            <button type="submit" class="btn-save" :disabled="saving">
              {{ saving ? 'Saving...' : (isEditMode ? 'Update' : 'Create') }}
            </button>
          </div>
        </form>

        <div class="token-helper">
          <h4>Available Tokens</h4>
          <div class="token-list">
            <div v-for="(desc, token) in availableTokens" :key="token" class="token-item">
              <code>{{ formatToken(token) }}</code>
              <span>{{ desc }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { getPost, createPost, updatePost, validatePost, listTokens, type PostConfig, type ValidationResult } from '@/api/post';

const props = defineProps<{
  postId?: string | null;
}>();

const emit = defineEmits(['close', 'saved']);

const isEditMode = computed(() => !!props.postId);
const loading = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const validationResult = ref<ValidationResult | null>(null);
const availableTokens = ref<Record<string, string>>({});

const formatToken = (token: string) => `{{${token}}}`;

const form = reactive({
  id: '',
  name: '',
  description: '',
  header: ['G21', 'G90', 'G17'],
  footer: ['M30'],
  tokens: {},
  metadata: {
    controller_family: '',
    gcode_dialect: '',
    supports_arcs: true,
    max_line_length: 255,
    comment_style: 'parentheses',
    has_tool_changer: false
  }
});

async function loadPost() {
  if (!props.postId) return;
  
  loading.value = true;
  error.value = null;
  
  try {
    const post = await getPost(props.postId);
    form.id = post.id;
    form.name = post.name;
    form.description = post.description;
    form.header = [...post.header];
    form.footer = [...post.footer];
    form.tokens = { ...post.tokens };
    if (post.metadata) {
      form.metadata = { ...form.metadata, ...post.metadata };
    }
  } catch (err: any) {
    error.value = err.message;
    console.error('Failed to load post:', err);
  } finally {
    loading.value = false;
  }
}

async function loadTokens() {
  try {
    availableTokens.value = await listTokens();
  } catch (err: any) {
    console.error('Failed to load tokens:', err);
  }
}

function addHeaderLine() {
  form.header.push('');
}

function removeHeaderLine(index: number) {
  if (form.header.length > 1) {
    form.header.splice(index, 1);
  }
}

function addFooterLine() {
  form.footer.push('');
}

function removeFooterLine(index: number) {
  if (form.footer.length > 1) {
    form.footer.splice(index, 1);
  }
}

async function handleValidate() {
  validationResult.value = null;
  error.value = null;
  
  try {
    const config = {
      id: form.id,
      name: form.name,
      description: form.description,
      header: form.header.filter(l => l.trim()),
      footer: form.footer.filter(l => l.trim()),
      tokens: form.tokens,
      metadata: form.metadata
    };
    
    validationResult.value = await validatePost(config);
  } catch (err: any) {
    error.value = err.message;
    console.error('Validation failed:', err);
  }
}

async function handleSave() {
  saving.value = true;
  error.value = null;
  
  try {
    const config = {
      id: form.id,
      name: form.name,
      description: form.description,
      header: form.header.filter(l => l.trim()),
      footer: form.footer.filter(l => l.trim()),
      tokens: form.tokens,
      metadata: form.metadata
    };
    
    if (isEditMode.value && props.postId) {
      await updatePost(props.postId, config);
    } else {
      await createPost(config);
    }
    
    emit('saved');
  } catch (err: any) {
    error.value = err.message;
    console.error('Failed to save post:', err);
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadPost();
  loadTokens();
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  overflow-y: auto;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ddd;
}

.dialog-header h2 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #666;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
}

.btn-close:hover {
  color: #333;
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.loading, .error {
  padding: 20px;
  text-align: center;
}

.error {
  color: #f44336;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #666;
  font-size: 0.9em;
}

.array-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.array-item {
  display: flex;
  gap: 8px;
}

.array-item input {
  flex: 1;
}

.btn-remove {
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 8px 12px;
  font-size: 18px;
  line-height: 1;
}

.btn-remove:hover {
  background: #d32f2f;
}

.btn-add {
  align-self: flex-start;
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-add:hover {
  background: #45a049;
}

.metadata-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metadata-row {
  display: flex;
  gap: 10px;
}

.metadata-row input[type="text"] {
  flex: 1;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
}

.validation-messages {
  margin-top: 20px;
  padding: 12px;
  border-radius: 4px;
}

.validation-messages .errors {
  background: #ffebee;
  color: #c62828;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 4px;
}

.validation-messages .warnings {
  background: #fff3e0;
  color: #e65100;
  padding: 10px;
  border-radius: 4px;
}

.validation-messages ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #ddd;
  margin-top: 20px;
}

.btn-cancel, .btn-validate, .btn-save {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-cancel {
  background: #ddd;
}

.btn-cancel:hover {
  background: #ccc;
}

.btn-validate {
  background: #FF9800;
  color: white;
}

.btn-validate:hover {
  background: #F57C00;
}

.btn-save {
  background: #4CAF50;
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: #45a049;
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.token-helper {
  margin-top: 30px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.token-helper h4 {
  margin-top: 0;
  margin-bottom: 12px;
}

.token-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 10px;
}

.token-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  font-size: 0.9em;
}

.token-item code {
  background: #e0e0e0;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.95em;
  font-weight: 600;
}

.token-item span {
  color: #666;
}
</style>
