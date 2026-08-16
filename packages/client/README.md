# Client Package

Vue 3 + TypeScript client for Production Shop (formerly The Production Shop).

## Node engine floor

`package.json` → `engines.node` is the **single source of truth** for the
minimum Node version. Do not restate the range in Dockerfiles or CI comments.

- Assert locally / in CI: `npm run check:node` (runs `scripts/check-node-engine.mjs`)
- Docker entry points COPY that script and run it before `npm ci`
- Drift gate: `src/testing/__tests__/nodeEngineFloor.spec.ts`

## Components

- `SimLab.vue` - Arc rendering + time scrubbing (I1.2)
- `SimLabWorker.vue` - Web Worker variant for large files (I1.3)

## Setup

```bash
npm install
npm run check:node
npm run dev
```

## Proxy Configuration

Vite dev server proxies `/api` → `http://localhost:8000`
