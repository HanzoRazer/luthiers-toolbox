# Client Package

Vue 3 + TypeScript client for Luthier's Tool Box.

## Components

- `SimLab.vue` - Arc rendering + time scrubbing (I1.2)
- `SimLabWorker.vue` - Web Worker variant for large files (I1.3)

## Setup

```bash
npm install
npm run dev
```

## Proxy Configuration

Vite dev server proxies `/api` → `http://localhost:8000`
