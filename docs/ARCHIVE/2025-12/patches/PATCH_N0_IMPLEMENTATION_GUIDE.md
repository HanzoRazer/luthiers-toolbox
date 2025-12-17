# Patch N.0: Smart Post Configurator — Implementation Guide

**Status:** 🚀 Ready for Implementation  
**Date:** November 5, 2025  
**Reference:** [PATCH_N0_SMART_POST_SCAFFOLD.md](./PATCH_N0_SMART_POST_SCAFFOLD.md)

---

## 🎯 Quick Start

This guide provides step-by-step implementation instructions for building the Smart Post Configurator. Follow the phases in order.

---

## Phase 1: Backend Router (2-3 hours)

### **Step 1.1: Create Post Router** (`services/api/app/routers/post_router.py`)

```python
"""
Post-Processor CRUD Router
Manages custom CNC post-processor configurations.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/posts", tags=["posts"])

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "posts"
CUSTOM_POSTS_FILE = DATA_DIR / "custom_posts.json"
BUILTIN_POST_IDS = ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"]


# ============================================================================
# Schemas
# ============================================================================

class PostMetadata(BaseModel):
    """Post-processor metadata"""
    controller_family: Optional[str] = None
    gcode_dialect: Optional[str] = None
    supports_arcs: bool = True
    max_line_length: int = 255
    comment_style: str = "parentheses"  # or "semicolon"
    has_tool_changer: bool = False


class PostConfig(BaseModel):
    """Complete post-processor configuration"""
    id: str = Field(..., max_length=32, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=500)
    builtin: bool = False
    header: List[str] = Field(..., min_items=1)
    footer: List[str] = Field(..., min_items=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('id')
    def validate_id(cls, v):
        """Ensure ID doesn't conflict with builtins"""
        if any(v.startswith(prefix) for prefix in BUILTIN_POST_IDS):
            raise ValueError(f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}")
        return v


class PostCreateIn(BaseModel):
    """Input for creating new post"""
    id: str = Field(..., max_length=32, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=500)
    header: List[str] = Field(..., min_items=1)
    footer: List[str] = Field(..., min_items=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None


class PostUpdateIn(BaseModel):
    """Input for updating existing post (partial)"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    header: Optional[List[str]] = Field(None, min_items=1)
    footer: Optional[List[str]] = Field(None, min_items=1)
    tokens: Optional[Dict[str, str]] = None
    metadata: Optional[PostMetadata] = None


class PostListItem(BaseModel):
    """Post summary for list view"""
    id: str
    name: str
    builtin: bool
    description: str


class ValidationResult(BaseModel):
    """Validation result"""
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


# ============================================================================
# Storage Functions
# ============================================================================

def load_builtin_posts() -> List[PostConfig]:
    """Load all builtin post configurations from individual JSON files"""
    posts = []
    for post_id in BUILTIN_POST_IDS:
        file_path = DATA_DIR / f"{post_id.lower()}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                posts.append(PostConfig(
                    id=post_id,
                    name=data.get('name', post_id),
                    description=data.get('description', ''),
                    builtin=True,
                    header=data.get('header', []),
                    footer=data.get('footer', []),
                    tokens=data.get('tokens', {}),
                    metadata=PostMetadata(**data.get('metadata', {})) if 'metadata' in data else None
                ))
    return posts


def load_custom_posts() -> List[PostConfig]:
    """Load custom posts from custom_posts.json"""
    if not CUSTOM_POSTS_FILE.exists():
        return []
    
    with open(CUSTOM_POSTS_FILE, 'r') as f:
        data = json.load(f)
        return [PostConfig(**post) for post in data.get('posts', [])]


def save_custom_posts(posts: List[PostConfig]):
    """Save custom posts to custom_posts.json"""
    CUSTOM_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'version': '1.0',
        'posts': [post.dict() for post in posts]
    }
    
    with open(CUSTOM_POSTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_all_posts() -> List[PostConfig]:
    """Load all posts (builtin + custom)"""
    return load_builtin_posts() + load_custom_posts()


def find_post(post_id: str) -> Optional[PostConfig]:
    """Find post by ID"""
    for post in load_all_posts():
        if post.id == post_id:
            return post
    return None


def is_builtin(post_id: str) -> bool:
    """Check if post is builtin"""
    return any(post_id.startswith(prefix) for prefix in BUILTIN_POST_IDS)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=Dict[str, List[PostListItem]])
def list_posts():
    """List all posts (builtin + custom)"""
    posts = load_all_posts()
    items = [
        PostListItem(
            id=post.id,
            name=post.name,
            builtin=post.builtin,
            description=post.description
        )
        for post in posts
    ]
    return {"posts": items}


@router.get("/{post_id}", response_model=PostConfig)
def get_post(post_id: str):
    """Get single post configuration"""
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    return post


@router.post("/", response_model=Dict[str, Any])
def create_post(body: PostCreateIn):
    """Create new custom post"""
    # Check if ID already exists
    if find_post(body.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post '{body.id}' already exists"
        )
    
    # Check reserved prefixes
    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}"
        )
    
    # Create new post
    now = datetime.utcnow().isoformat() + 'Z'
    post = PostConfig(
        **body.dict(),
        builtin=False,
        created_at=now,
        updated_at=now
    )
    
    # Save to custom posts
    custom_posts = load_custom_posts()
    custom_posts.append(post)
    save_custom_posts(custom_posts)
    
    return {
        "id": post.id,
        "name": post.name,
        "builtin": False,
        "created_at": now
    }


@router.put("/{post_id}", response_model=Dict[str, Any])
def update_post(post_id: str, body: PostUpdateIn):
    """Update existing custom post"""
    # Find post
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    
    # Check builtin protection
    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot edit builtin post '{post_id}'"
        )
    
    # Update fields
    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    post.updated_at = datetime.utcnow().isoformat() + 'Z'
    
    # Save custom posts
    custom_posts = load_custom_posts()
    for i, p in enumerate(custom_posts):
        if p.id == post_id:
            custom_posts[i] = post
            break
    save_custom_posts(custom_posts)
    
    return {
        "id": post.id,
        "updated_at": post.updated_at
    }


@router.delete("/{post_id}", response_model=Dict[str, Any])
def delete_post(post_id: str):
    """Delete custom post"""
    # Find post
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    
    # Check builtin protection
    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete builtin post '{post_id}'"
        )
    
    # Remove from custom posts
    custom_posts = load_custom_posts()
    custom_posts = [p for p in custom_posts if p.id != post_id]
    save_custom_posts(custom_posts)
    
    return {
        "id": post_id,
        "deleted": True
    }


@router.post("/validate", response_model=ValidationResult)
def validate_post(body: PostCreateIn):
    """Validate post configuration without saving"""
    errors = []
    warnings = []
    
    # Check ID conflicts
    if find_post(body.id):
        errors.append(f"Post ID '{body.id}' already exists")
    
    # Check reserved prefixes
    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        errors.append(f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}")
    
    # Check header/footer not empty
    if not body.header:
        errors.append("Header cannot be empty")
    if not body.footer:
        errors.append("Footer cannot be empty")
    
    # Check line lengths
    for i, line in enumerate(body.header):
        if len(line) > 255:
            warnings.append(f"Header line {i+1} exceeds 255 characters")
    for i, line in enumerate(body.footer):
        if len(line) > 255:
            warnings.append(f"Footer line {i+1} exceeds 255 characters")
    
    # TODO: Check for undefined tokens (future enhancement)
    
    return ValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors
    )
```

### **Step 1.2: Create Token Expansion Utility** (`services/api/app/util/post_tokens.py`)

```python
"""
Post-Processor Token Expansion
Handles dynamic token replacement in post-processor headers/footers.
"""
from typing import Dict, List, Optional
from datetime import datetime
import re

# Token Registry
TOKEN_REGISTRY = {
    'POST_ID': 'Post-processor identifier',
    'UNITS': 'Units (mm or inch)',
    'DATE': 'ISO 8601 timestamp',
    'TOOL_DIAMETER': 'Tool diameter',
    'TOOL_NUMBER': 'Tool number (for tool changers)',
    'MATERIAL': 'Material name',
    'MACHINE_ID': 'Machine profile ID',
    'FEED_XY': 'Cutting feed rate',
    'FEED_Z': 'Plunge feed rate',
    'SPINDLE_RPM': 'Spindle speed',
}

# Default values
DEFAULT_TOKENS = {
    'DATE': lambda: datetime.utcnow().isoformat() + 'Z',
    'UNITS': 'mm',
}


def expand_tokens(lines: List[str], context: Dict[str, any]) -> List[str]:
    """
    Expand tokens in header/footer lines.
    
    Args:
        lines: List of lines with {{TOKEN}} placeholders
        context: Dictionary of token values
    
    Returns:
        List of expanded lines
    """
    expanded = []
    
    # Merge context with defaults
    tokens = {}
    for key, value in DEFAULT_TOKENS.items():
        tokens[key] = value() if callable(value) else value
    tokens.update(context)
    
    # Expand each line
    for line in lines:
        expanded_line = line
        
        # Find all {{TOKEN}} patterns
        pattern = r'\{\{([A-Z_]+)\}\}'
        matches = re.findall(pattern, line)
        
        for token_name in matches:
            if token_name in tokens:
                # Replace with value
                value = str(tokens[token_name])
                expanded_line = expanded_line.replace(f'{{{{{token_name}}}}}', value)
            # else: leave unreplaced (will show as warning in validation)
        
        expanded.append(expanded_line)
    
    return expanded


def validate_tokens(lines: List[str]) -> Dict[str, List[str]]:
    """
    Validate tokens in header/footer lines.
    
    Returns:
        Dictionary with 'valid', 'undefined', 'warnings'
    """
    result = {
        'valid': [],
        'undefined': [],
        'warnings': []
    }
    
    pattern = r'\{\{([A-Z_]+)\}\}'
    
    for line in lines:
        matches = re.findall(pattern, line)
        for token_name in matches:
            if token_name in TOKEN_REGISTRY:
                result['valid'].append(token_name)
            else:
                result['undefined'].append(token_name)
                result['warnings'].append(
                    f"Token '{token_name}' not in registry (will remain unexpanded)"
                )
    
    return result


def get_token_info(token_name: str) -> Optional[str]:
    """Get description for a token"""
    return TOKEN_REGISTRY.get(token_name)


def list_all_tokens() -> Dict[str, str]:
    """Get all available tokens with descriptions"""
    return TOKEN_REGISTRY.copy()
```

### **Step 1.3: Create Custom Posts Data File** (`services/api/app/data/posts/custom_posts.json`)

```json
{
  "version": "1.0",
  "posts": []
}
```

### **Step 1.4: Register Router in Main App** (`services/api/app/main.py`)

Add import and registration:

```python
# Add to imports section
from .routers import post_router

# Add to router registration section
app.include_router(post_router.router)
```

---

## Phase 2: Frontend Components (3-4 hours)

### **Step 2.1: Create API Client** (`packages/client/src/api/post.ts`)

```typescript
/**
 * Post-Processor API Client
 */

export interface PostMetadata {
  controller_family?: string;
  gcode_dialect?: string;
  supports_arcs: boolean;
  max_line_length: number;
  comment_style: string;
  has_tool_changer: boolean;
}

export interface PostConfig {
  id: string;
  name: string;
  description: string;
  builtin: boolean;
  header: string[];
  footer: string[];
  tokens: Record<string, string>;
  metadata?: PostMetadata;
  created_at?: string;
  updated_at?: string;
}

export interface PostListItem {
  id: string;
  name: string;
  builtin: boolean;
  description: string;
}

export interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

const API_BASE = '/api/posts';

export async function listPosts(): Promise<PostListItem[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) throw new Error('Failed to list posts');
  const data = await response.json();
  return data.posts;
}

export async function getPost(postId: string): Promise<PostConfig> {
  const response = await fetch(`${API_BASE}/${postId}`);
  if (!response.ok) throw new Error(`Failed to get post ${postId}`);
  return response.json();
}

export async function createPost(config: Omit<PostConfig, 'builtin' | 'created_at' | 'updated_at'>): Promise<any> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create post');
  }
  return response.json();
}

export async function updatePost(postId: string, updates: Partial<PostConfig>): Promise<any> {
  const response = await fetch(`${API_BASE}/${postId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update post');
  }
  return response.json();
}

export async function deletePost(postId: string): Promise<any> {
  const response = await fetch(`${API_BASE}/${postId}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete post');
  }
  return response.json();
}

export async function validatePost(config: Omit<PostConfig, 'builtin' | 'created_at' | 'updated_at'>): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE}/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  if (!response.ok) throw new Error('Failed to validate post');
  return response.json();
}
```

### **Step 2.2: Create Post Manager Component** (`packages/client/src/components/PostManager.vue`)

```vue
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
  font-weight: 500;
}

.btn-cancel {
  background: #ddd;
  color: #333;
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
```

*(Continues in next response due to length...)*

---

## Quick Command Reference

```powershell
# Start backend with new router
cd services/api
uvicorn app.main:app --reload --port 8000

# Test endpoints
Invoke-RestMethod -Uri "http://localhost:8000/api/posts/" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/posts/GRBL" -Method GET

# Create custom post
$body = @{
  id = "TEST_POST"
  name = "Test Post"
  description = "Test"
  header = @("G90", "G21")
  footer = @("M30")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/posts/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

**Next:** Continue with PostEditor.vue component (Step 2.3) and remaining phases.
