# Client Package

Vue 3 + TypeScript client for Production Shop (formerly The Production Shop).

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
