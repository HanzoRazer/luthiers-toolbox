<template>
  <div
    :class="styles.modalOverlay"
    @click="$emit('close')"
  >
    <div
      :class="styles.modalDialog"
      @click.stop
    >
      <div :class="styles.dialogHeader">
        <h2>{{ isEditMode ? 'Edit Post' : 'Create New Post' }}</h2>
        <button
          :class="styles.btnClose"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>

      <div :class="styles.dialogBody">
        <div
          v-if="loading"
          :class="styles.loading"
        >
          Loading...
        </div>
        <div
          v-if="error"
          :class="styles.error"
        >
          {{ error }}
        </div>

        <form
          v-if="!loading"
          @submit.prevent="handleSave"
        >
          <div :class="styles.formGroup">
            <label>Post ID *</label>
            <input
              v-model="form.id"
              type="text"
              placeholder="e.g., CUSTOM_HAAS"
              pattern="[A-Z0-9_]+"
              :disabled="isEditMode"
              required
            >
            <small>Uppercase letters, numbers, and underscores only</small>
          </div>

          <div :class="styles.formGroup">
            <label>Name *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="e.g., Haas VF-2 with Tool Changer"
              required
            >
          </div>

          <div :class="styles.formGroup">
            <label>Description</label>
            <textarea
              v-model="form.description"
              placeholder="Brief description of this post-processor..."
              rows="2"
            />
          </div>

          <div :class="styles.formGroup">
            <label>Header Lines *</label>
            <div :class="styles.arrayEditor">
              <div
                v-for="(line, i) in form.header"
                :key="`header-${i}`"
                :class="styles.arrayItem"
              >
                <input
                  v-model="form.header[i]"
                  type="text"
                  placeholder="G-code line or comment"
                >
                <button
                  type="button"
                  :class="styles.btnRemove"
                  @click="removeHeaderLine(i)"
                >
                  ×
                </button>
              </div>
              <button
                type="button"
                :class="styles.btnAdd"
                @click="addHeaderLine"
              >
                + Add Header Line
              </button>
            </div>
            <small>G-code lines or comments to insert at program start</small>
          </div>

          <div :class="styles.formGroup">
            <label>Footer Lines *</label>
            <div :class="styles.arrayEditor">
              <div
                v-for="(line, i) in form.footer"
                :key="`footer-${i}`"
                :class="styles.arrayItem"
              >
                <input
                  v-model="form.footer[i]"
                  type="text"
                  placeholder="G-code line or comment"
                >
                <button
                  type="button"
                  :class="styles.btnRemove"
                  @click="removeFooterLine(i)"
                >
                  ×
                </button>
              </div>
              <button
                type="button"
                :class="styles.btnAdd"
                @click="addFooterLine"
              >
                + Add Footer Line
              </button>
            </div>
            <small>G-code lines or comments to insert at program end</small>
          </div>

          <div :class="styles.formGroup">
            <label>Metadata (Optional)</label>
            <div :class="styles.metadataFields">
              <div :class="styles.metadataRow">
                <input
                  v-model="form.metadata.controller_family"
                  type="text"
                  placeholder="Controller family (e.g., grbl)"
                >
                <input
                  v-model="form.metadata.gcode_dialect"
                  type="text"
                  placeholder="G-code dialect (e.g., LinuxCNC)"
                >
              </div>
              <div :class="styles.metadataRow">
                <label :class="styles.checkboxLabel">
                  <input
                    v-model="form.metadata.supports_arcs"
                    type="checkbox"
                  >
                  Supports Arcs (G2/G3)
                </label>
                <label :class="styles.checkboxLabel">
                  <input
                    v-model="form.metadata.has_tool_changer"
                    type="checkbox"
                  >
                  Has Tool Changer
                </label>
              </div>
            </div>
          </div>

          <div
            v-if="validationResult"
            :class="styles.validationMessages"
          >
            <div
              v-if="validationResult.errors.length > 0"
              :class="styles.errors"
            >
              <strong>Errors:</strong>
              <ul>
                <li
                  v-for="(err, i) in validationResult.errors"
                  :key="`err-${i}`"
                >
                  {{ err }}
                </li>
              </ul>
            </div>
            <div
              v-if="validationResult.warnings.length > 0"
              :class="styles.warnings"
            >
              <strong>Warnings:</strong>
              <ul>
                <li
                  v-for="(warn, i) in validationResult.warnings"
                  :key="`warn-${i}`"
                >
                  {{ warn }}
                </li>
              </ul>
            </div>
          </div>

          <div :class="styles.dialogActions">
            <button
              type="button"
              :class="styles.btnCancel"
              @click="$emit('close')"
            >
              Cancel
            </button>
            <button
              type="button"
              :class="styles.btnValidate"
              @click="handleValidate"
            >
              Validate
            </button>
            <button
              type="submit"
              :class="styles.btnSave"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : (isEditMode ? 'Update' : 'Create') }}
            </button>
          </div>
        </form>

        <div :class="styles.tokenHelper">
          <h4>Available Tokens</h4>
          <div :class="styles.tokenList">
            <div
              v-for="(desc, token) in availableTokens"
              :key="token"
              :class="styles.tokenItem"
            >
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
import styles from './PostEditor.module.css';

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
