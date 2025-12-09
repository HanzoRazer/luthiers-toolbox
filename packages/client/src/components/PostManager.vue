<template>
  <div class="post-manager">
    <div class="manager-header">
      <h2>Post-Processor Manager</h2>
      <div class="actions">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search posts..." 
          class="search-input"
        />
        <button @click="showCreateDialog = true" class="btn-create">
          + Create New Post
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading posts...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="post-grid">
      <div 
        v-for="post in filteredPosts" 
        :key="post.id" 
        class="post-card"
        :class="{ builtin: post.builtin }"
      >
        <div class="card-header">
          <h3>{{ post.name }}</h3>
          <span v-if="post.builtin" class="badge-builtin">Built-in</span>
        </div>
        <p class="card-description">{{ post.description }}</p>
        <div class="card-footer">
          <span class="post-id">{{ post.id }}</span>
          <div class="card-actions">
            <button @click="editPost(post.id)" class="btn-edit">Edit</button>
            <button 
              v-if="!post.builtin" 
              @click="confirmDelete(post.id)" 
              class="btn-delete"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <PostEditor 
      v-if="showCreateDialog || editingPostId" 
      :postId="editingPostId"
      @close="closeDialog"
      @saved="handleSaved"
    />

    <!-- Delete Confirmation -->
    <div v-if="deletingPostId" class="modal-overlay" @click="deletingPostId = null">
      <div class="modal-content" @click.stop>
        <h3>Confirm Delete</h3>
        <p>Are you sure you want to delete post "{{ deletingPostId }}"?</p>
        <div class="modal-actions">
          <button @click="deletingPostId = null" class="btn-cancel">Cancel</button>
          <button @click="handleDelete" class="btn-confirm-delete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { listPosts, deletePost, type PostListItem } from '@/api/post';
import PostEditor from './PostEditor.vue';

const posts = ref<PostListItem[]>([]);
const searchQuery = ref('');
const showCreateDialog = ref(false);
const editingPostId = ref<string | null>(null);
const deletingPostId = ref<string | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const filteredPosts = computed(() => {
  if (!searchQuery.value) return posts.value;
  const query = searchQuery.value.toLowerCase();
  return posts.value.filter(p => 
    p.name.toLowerCase().includes(query) ||
    p.id.toLowerCase().includes(query) ||
    p.description.toLowerCase().includes(query)
  );
});

async function loadPosts() {
  loading.value = true;
  error.value = null;
  try {
    posts.value = await listPosts();
  } catch (err: any) {
    error.value = err.message;
    console.error('Failed to load posts:', err);
  } finally {
    loading.value = false;
  }
}

function editPost(postId: string) {
  editingPostId.value = postId;
}

function confirmDelete(postId: string) {
  deletingPostId.value = postId;
}

async function handleDelete() {
  if (!deletingPostId.value) return;
  
  try {
    await deletePost(deletingPostId.value);
    await loadPosts(); // Refresh list
    deletingPostId.value = null;
  } catch (err: any) {
    error.value = err.message;
    console.error('Failed to delete post:', err);
  }
}

function closeDialog() {
  showCreateDialog.value = false;
  editingPostId.value = null;
}

async function handleSaved() {
  closeDialog();
  await loadPosts(); // Refresh list
}

onMounted(() => {
  loadPosts();
});
</script>

<style scoped>
.post-manager {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.manager-header h2 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 10px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  min-width: 250px;
}

.btn-create {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-create:hover {
  background: #45a049;
}

.loading, .error {
  padding: 20px;
  text-align: center;
  color: #666;
}

.error {
  color: #f44336;
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.post-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card.builtin {
  border-color: #2196F3;
  background: #f5f9ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.badge-builtin {
  background: #2196F3;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.card-description {
  color: #666;
  margin: 0;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.post-id {
  font-family: monospace;
  color: #888;
  font-size: 14px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn-edit, .btn-delete {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-edit {
  background: #2196F3;
  color: white;
}

.btn-edit:hover {
  background: #1976D2;
}

.btn-delete {
  background: #f44336;
  color: white;
}

.btn-delete:hover {
  background: #d32f2f;
}

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
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin-top: 0;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-cancel, .btn-confirm-delete {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  background: #ddd;
}

.btn-cancel:hover {
  background: #ccc;
}

.btn-confirm-delete {
  background: #f44336;
  color: white;
}

.btn-confirm-delete:hover {
  background: #d32f2f;
}
</style>
