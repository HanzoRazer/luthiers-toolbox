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

export async function listTokens(): Promise<Record<string, string>> {
  const response = await fetch(`${API_BASE}/tokens/list`);
  if (!response.ok) throw new Error('Failed to list tokens');
  return response.json();
}
