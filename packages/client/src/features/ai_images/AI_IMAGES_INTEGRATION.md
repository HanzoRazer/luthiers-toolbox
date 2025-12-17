# AI Images Feature — Integration Guide

## Overview

User-side AI image generation layer for design visualization and customer approval mockups.

**Key boundaries:**
- Images are PROJECT ASSETS, not run artifacts
- RMOS cannot see these images unless explicitly referenced
- No imports from `services/api/app/rmos/*`

## File Structure

```
packages/client/src/features/ai_images/
├── index.ts              # Public API exports
├── types.ts              # TypeScript definitions
├── api.ts                # Server API client
├── useAiImageStore.ts    # Pinia state management
├── AiImagePanel.vue      # Main panel (prompt + options + gallery)
├── AiImageGallery.vue    # Grid display with actions
└── AiImageProperties.vue # Detail panel for selected image
```

**Total: ~3,150 lines**

## Installation

### 1. Copy Files

```bash
cp -r ai_images/ packages/client/src/features/
```

### 2. Add to Pinia

```ts
// packages/client/src/stores/index.ts
import { useAiImageStore } from '@/features/ai_images';

export { useAiImageStore };
```

### 3. Register Nanoid

```bash
cd packages/client
npm install nanoid
```

## Usage

### Basic Integration

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { AiImagePanel } from '@/features/ai_images';

const projectId = ref('my-project-id');
const showPanel = ref(true);

function handleImageSelect(id: string) {
  console.log('Selected:', id);
}

function handleAttach(imageId: string, targetId: string) {
  // Attach image to design element
  console.log('Attach:', imageId, 'to', targetId);
}
</script>

<template>
  <AiImagePanel
    v-if="showPanel"
    :project-id="projectId"
    @image:select="handleImageSelect"
    @image:attach="handleAttach"
    @close="showPanel = false"
  />
</template>
```

### With Properties Panel

```vue
<script setup lang="ts">
import {
  AiImagePanel,
  AiImageProperties,
  useAiImageStore,
} from '@/features/ai_images';

const store = useAiImageStore();
const projectId = ref('my-project');

function handleRegenerate() {
  if (store.selectedImage) {
    store.generate({
      prompt: store.selectedImage.userPrompt,
      projectId: projectId.value,
    });
  }
}
</script>

<template>
  <div class="layout">
    <AiImagePanel
      :project-id="projectId"
      class="left-panel"
    />
    
    <div class="canvas">
      <!-- Your design canvas -->
    </div>
    
    <AiImageProperties
      :image="store.selectedImage"
      class="right-panel"
      @attach="handleAttach"
      @download="store.downloadImage(store.selectedId!)"
      @regenerate="handleRegenerate"
      @delete="store.deleteImage(store.selectedId!)"
      @rate="(r) => store.rateImage(store.selectedId!, r)"
    />
  </div>
</template>
```

### Direct Store Access

```ts
import { useAiImageStore } from '@/features/ai_images';

const store = useAiImageStore();

// Initialize for project
await store.initialize('project-123');

// Generate images
const assets = await store.generate({
  prompt: 'sunburst les paul gold hardware',
  numImages: 2,
  quality: 'standard',
  style: 'product',
});

// Access state
console.log(store.images);           // All images
console.log(store.selectedImage);    // Current selection
console.log(store.sessionCost);      // Cost this session

// Actions
store.selectImage(assets[0].id);
store.rateImage(assets[0].id, 5);
store.downloadImage(assets[0].id);
store.deleteImage(assets[0].id);
```

## API Endpoints Required

The feature expects these server endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/vision/generate` | Generate images |
| POST | `/api/vision/prompt` | Preview prompt engineering |
| POST | `/api/vision/feedback` | Submit rating feedback |
| GET | `/api/vision/vocabulary` | Get dropdown options |
| GET | `/api/vision/providers` | List available providers |
| GET | `/api/projects/:id/assets/ai_images` | Get project assets |
| POST | `/api/projects/:id/assets/ai_images` | Upload asset |
| DELETE | `/api/projects/:id/assets/ai_images/:assetId` | Delete asset |

These endpoints are implemented in:
- `guitar_vision_routes.py` (generation)
- Asset routes (to be built)

## CSS Variables

The components use these CSS variables (provide your own or use defaults):

```css
:root {
  --bg-panel: #16213e;
  --bg-input: #0f1629;
  --border: #2a3f5f;
  --accent: #4fc3f7;
  --accent-hover: #81d4fa;
  --text: #e0e0e0;
  --text-dim: #8892a0;
  --success: #4caf50;
  --warning: #ff9800;
}
```

## Events

### AiImagePanel

| Event | Payload | Description |
|-------|---------|-------------|
| `image:select` | `id: string` | Image selected in gallery |
| `image:attach` | `imageId: string, targetId: string` | User wants to attach image |
| `close` | — | Panel close requested |

### AiImageGallery

| Event | Payload | Description |
|-------|---------|-------------|
| `select` | `id: string` | Image clicked |
| `attach` | `id: string` | Attach button clicked |
| `download` | `id: string` | Download button clicked |
| `delete` | `id: string` | Delete button clicked |
| `rate` | `id: string, rating: number` | Rating submitted |

### AiImageProperties

| Event | Payload | Description |
|-------|---------|-------------|
| `attach` | — | Attach button clicked |
| `download` | — | Download button clicked |
| `regenerate` | — | Regenerate button clicked |
| `delete` | — | Delete button clicked |
| `rate` | `rating: number` | Rating submitted |

## Asset Storage

Images persist to:

```
data/projects/{projectId}/
└── assets/
    └── ai_images/
        ├── manifest.json    # Metadata index
        ├── img_abc123.png   # Image files
        └── ...
```

Manifest schema:

```json
{
  "version": "1.0",
  "projectId": "project-123",
  "images": [
    {
      "id": "img_abc123",
      "filename": "img_abc123.png",
      "path": "assets/ai_images/img_abc123.png",
      "url": "/projects/project-123/assets/ai_images/img_abc123.png",
      "status": "ready",
      "userPrompt": "emerald les paul",
      "engineeredPrompt": "professional product photography...",
      "provider": "dalle3",
      "category": "electric",
      "bodyShape": "les paul",
      "finish": "green",
      "size": "1024x1024",
      "quality": "standard",
      "style": "product",
      "cost": 0.04,
      "createdAt": "2025-12-16T23:00:00Z",
      "updatedAt": "2025-12-16T23:00:00Z",
      "rating": 5
    }
  ],
  "stats": {
    "totalGenerated": 12,
    "totalCost": 0.52
  }
}
```

## Governance

### Hard Rules

1. **No RMOS imports** — This feature doesn't touch execution
2. **Images are assets** — Not run artifacts
3. **Explicit attachment** — Images only enter designs when user attaches them
4. **Server-side keys** — API keys never touch the client

### Soft Guidelines

- Rate images to train the router
- Use "Attach to Design" for reference images
- Download for external use
- Delete unused generations to save space
