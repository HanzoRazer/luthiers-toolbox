# Vue Router Setup Complete

## ✅ Files Created

1. **`src/router/index.ts`** - Router configuration with all main routes
2. **`src/main.ts`** - App entry point with router integration
3. **`src/App.vue`** - Root component with `<router-view>`
4. **`index.html`** - HTML entry point
5. **`vite.config.ts`** - Vite configuration with API/WebSocket proxy
6. **`tsconfig.json`** - TypeScript configuration
7. **`tsconfig.node.json`** - TypeScript config for build tools
8. **`package.json`** - Dependencies including vue-router

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
cd packages/client
npm install
```

### 2. Start Dev Server
```bash
npm run dev
```

### 3. Access Routes

- **Home/RMOS:** `http://localhost:5173/`
- **Live Monitor:** `http://localhost:5173/rmos/live-monitor`
- **Analytics:** `http://localhost:5173/rmos/analytics`
- **Art Studio:** `http://localhost:5173/art-studio`
- **Pipeline Lab:** `http://localhost:5173/pipeline`
- **Blueprint Lab:** `http://localhost:5173/blueprint`

## 📋 Available Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | RosettePipelineView | RMOS main view (home) |
| `/rmos` | RosettePipelineView | RMOS main view |
| `/rmos/live-monitor` | RMOSLiveMonitorView | **N10.0 Real-time Monitoring** |
| `/rmos/analytics` | AnalyticsDashboard | N9.0/N9.1 Analytics |
| `/art-studio` | ArtStudio | Art Studio main |
| `/art-studio/v16` | ArtStudioV16 | Art Studio v16 |
| `/pipeline` | PipelineLabView | CAM Pipeline Lab |
| `/blueprint` | BlueprintLab | Blueprint Import |
| `/saw` | SawLabView | Saw Lab |
| `/cam-settings` | CamSettingsView | CAM Settings |
| `/bridge` | BridgeLabView | Bridge Calculator |
| `/cnc` | CncProductionView | CNC Production |
| `/compare` | CompareLabView | Compare Mode |

## 🔌 WebSocket Proxy

The Vite config includes WebSocket proxy for N10.0:

```typescript
'/ws': {
  target: 'ws://localhost:8000',
  ws: true,
}
```

This means `ws://localhost:5173/ws/monitor` automatically proxies to the FastAPI backend at `ws://localhost:8000/ws/monitor`.

## 🎯 Access Live Monitor

**Two ways to access:**

1. **Via routing:** Navigate to `/rmos/live-monitor`
2. **Via tab toggle:** Go to `/rmos` and click "Live Monitor" tab in right panel

## 🧪 Test WebSocket

With both servers running:

```bash
# Terminal 1: FastAPI
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Terminal 2: Vue dev server
cd packages/client
npm run dev

# Terminal 3: Run smoke test
cd ../..
.\Test-N10-WebSocket.ps1
```

Then visit `http://localhost:5173/rmos/live-monitor` and click "Connect".

## 📝 Adding New Routes

Edit `src/router/index.ts`:

```typescript
{
  path: '/your-route',
  name: 'YourRoute',
  component: () => import('@/views/YourView.vue'),
}
```

## ⚠️ Notes

- Router uses **lazy loading** (`() => import()`) for all routes except the home page
- All routes use the `@/` alias pointing to `src/`
- WebSocket connections automatically reconnect (1s → 16s exponential backoff)
- TypeScript strict mode is enabled for better type safety
