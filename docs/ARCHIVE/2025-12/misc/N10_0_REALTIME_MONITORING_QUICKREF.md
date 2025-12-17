# N10.0 Real-time Monitoring — Quick Reference

**Module:** Rosette Manufacturing OS (RMOS)  
**Version:** N10.0  
**Status:** ✅ Production Ready  
**Dependencies:** N8.6 (RMOS Stores), N9.0 (Analytics)

---

## Overview

N10.0 adds **real-time WebSocket monitoring** to RMOS, enabling live updates for job status, pattern creation, material changes, and metrics snapshots. Clients connect to a persistent WebSocket channel and receive instant notifications when RMOS entities are created, updated, or completed.

**Key Features:**
- WebSocket server with connection manager (`/ws/monitor`)
- Event broadcasting with filter subscriptions (`job`, `pattern`, `material`, `metrics`, `all`)
- Auto-reconnection with exponential backoff (1s → 16s max)
- Vue composable for client-side WebSocket management
- LiveMonitor.vue component with real-time event stream
- Status-specific job events (`job:created`, `job:updated`, `job:completed`, `job:failed`)

---

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitor')
```

### Server Messages

**Welcome:**
```json
{
  "type": "system:connected",
  "data": {"message": "Real-time monitoring active"},
  "timestamp": ""
}
```

**Entity Events:**
```json
{
  "type": "job:created" | "job:updated" | "job:completed" | "job:failed" | 
          "pattern:created" | "pattern:updated" | 
          "material:created" | "material:updated" | 
          "metrics:snapshot",
  "data": {
    // Full entity object (pattern, joblog, strip_family, or metrics)
  },
  "timestamp": "2025-01-06T12:34:56.789Z"
}
```

### Client Commands

**Subscribe to filters:**
```json
{
  "action": "subscribe",
  "filters": ["job", "pattern", "metrics"]
}
```

**Ping (keepalive):**
```json
{
  "action": "ping"
}
```

**Server Response:**
```json
{
  "type": "system:pong",
  "data": {},
  "timestamp": ""
}
```

---

## Vue Composable Usage

### Basic Setup
```typescript
import { useWebSocket } from '@/composables/useWebSocket'

const { connect, disconnect, isConnected, subscribe, ping } = useWebSocket()
```

### Connect and Subscribe
```typescript
// Connect to WebSocket
await connect()

// Subscribe to job and pattern events
const unsubscribe = subscribe(['job', 'pattern'], (event) => {
  console.log(`Event: ${event.type}`, event.data)
})

// Unsubscribe when done
onUnmounted(() => {
  unsubscribe()
  disconnect()
})
```

### Connection State
```vue
<template>
  <div v-if="isConnected" class="status-badge connected">
    ● Connected
  </div>
  <div v-else class="status-badge disconnected">
    ○ Disconnected
  </div>
</template>

<script setup lang="ts">
const { isConnected } = useWebSocket()
</script>
```

---

## LiveMonitor Component

### Usage
```vue
<template>
  <LiveMonitor />
</template>

<script setup lang="ts">
import LiveMonitor from '@/components/rmos/LiveMonitor.vue'
</script>
```

### Features
- **Connection Controls:** Connect/Disconnect button
- **Filter Panel:** Checkboxes for job/pattern/material/metrics
- **Event Stream:** Auto-scrolling list with color-coded events
- **Stats Footer:** Real-time event counts by type

### Event Colors
- **Blue border:** Job events (`job:*`)
- **Purple border:** Pattern events (`pattern:*`)
- **Orange border:** Material events (`material:*`)
- **Green border:** Metrics events (`metrics:*`)

---

## Backend Event Broadcasting

### Trigger Points

**Patterns:**
- `pattern:created` → POST `/api/rmos/stores/patterns`
- `pattern:updated` → PUT `/api/rmos/stores/patterns/{id}`

**JobLogs:**
- `job:created` → POST `/api/rmos/stores/joblogs`
- `job:updated` → PUT `/api/rmos/stores/joblogs/{id}` (status != completed/failed)
- `job:completed` → PUT `/api/rmos/stores/joblogs/{id}` (status = completed)
- `job:failed` → PUT `/api/rmos/stores/joblogs/{id}` (status = failed)

**Strip Families (Materials):**
- `material:created` → POST `/api/rmos/stores/strip-families`
- `material:updated` → PUT `/api/rmos/stores/strip-families/{id}`

### Manual Broadcasting
```python
from app.websocket.monitor import broadcast_job_event, broadcast_pattern_event

# Broadcast custom event
await broadcast_job_event("custom_status", {
    "id": "job-123",
    "status": "custom",
    "message": "Custom event data"
})
```

---

## Reconnection Behavior

The client automatically reconnects with **exponential backoff**:
1. Initial delay: **1 second**
2. 2nd attempt: **2 seconds**
3. 3rd attempt: **4 seconds**
4. 4th attempt: **8 seconds**
5. 5th attempt: **16 seconds** (max)
6. After 5 failures: **Connection abandoned**

**Manual reconnection:**
```typescript
// Force reconnect
disconnect()
await connect()
```

---

## Testing

### PowerShell Smoke Test
```powershell
# Run FastAPI server first
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# In another terminal, run test
cd ..\..
.\Test-N10-WebSocket.ps1
```

**Expected Output:**
```
=== N10.0 WebSocket Smoke Test ===

1. Testing server availability...
   ✓ Server is running

2. Checking WebSocket router registration...
   ✓ WebSocket endpoint registered at /ws/monitor

3. Testing RMOS entity creation...
   ✓ Pattern created: pattern-abc123
     (WebSocket event 'pattern:created' should have been broadcast)
   ✓ JobLog created: joblog-def456
     (WebSocket event 'job:created' should have been broadcast)

4. Testing joblog update (status change)...
   ✓ JobLog updated to 'completed'
     (WebSocket event 'job:completed' should have been broadcast)

5. Verifying WebSocket infrastructure...
   ✓ All broadcast functions importable
   ✓ ConnectionManager instance: ConnectionManager
   ✓ Active connections: 0

============================================
Tests Passed: 5
Tests Failed: 0

✓ All N10.0 WebSocket smoke tests passed!
```

### Manual WebSocket Test (wscat)
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/monitor

# Subscribe to events
> {"action":"subscribe","filters":["job","pattern"]}
< {"type":"system:subscribed","data":{"filters":["job","pattern"]},"timestamp":""}

# Trigger event via API (another terminal)
curl -X POST http://localhost:8000/api/rmos/stores/patterns \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Pattern","ring_count":3,"geometry":{"rings":[]}}'

# Observe broadcasted event
< {"type":"pattern:created","data":{...},"timestamp":"2025-01-06T12:34:56Z"}
```

### Browser Test
1. Open Vue dev server: `http://localhost:5173`
2. Navigate to **RMOS → Live Monitor** (if integrated)
3. Click **Connect** button
4. Use another browser tab to create patterns/jobs via RMOS UI
5. Observe real-time events in monitor

---

## Troubleshooting

### "WebSocket connection failed"
**Cause:** FastAPI server not running  
**Fix:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### "Max reconnection attempts reached"
**Cause:** Server down or network issue  
**Fix:**
1. Check server logs for errors
2. Verify WebSocket router is registered (`/ws/monitor` in OpenAPI spec)
3. Manually reconnect via UI button after fixing server

### "No events received"
**Cause:** Filter mismatch or no CRUD operations  
**Fix:**
1. Verify subscribed filters match entity types (`job`, `pattern`, `material`)
2. Ensure RMOS API endpoints are being called (create/update operations)
3. Check browser console for WebSocket errors

### "Events delayed or missing"
**Cause:** Broadcasting happens in async context  
**Fix:**
- All RMOS API endpoints with broadcasting are now `async def`
- If adding new events, ensure `await broadcast_*_event(...)`

---

## Architecture

### Server Components
```
services/api/app/
├── websocket/
│   └── monitor.py              # ConnectionManager + broadcast functions
├── routers/
│   └── websocket_router.py     # /ws/monitor endpoint
└── api/routes/
    └── rmos_stores_api.py      # CRUD endpoints with event broadcasting
```

### Client Components
```
packages/client/src/
├── composables/
│   └── useWebSocket.ts         # WebSocket connection manager
└── components/rmos/
    └── LiveMonitor.vue         # Real-time monitoring UI
```

### Event Flow
```
1. User action (API call) → POST /api/rmos/stores/patterns
2. Store operation → stores.patterns.create(...)
3. Broadcast event → await broadcast_pattern_event("created", pattern)
4. ConnectionManager → Iterate active connections
5. Filter check → Match "pattern" or "all" subscribers
6. Send JSON → ws.send_json({"type":"pattern:created",...})
7. Client handler → eventHandlers.forEach(h => h(event))
8. UI update → events.value.push(event)
```

---

## Configuration

### WebSocket URL (Client)
Default: `ws://${window.location.hostname}:8000/ws/monitor`

**Override:**
```typescript
await connect('ws://custom-host:8000/ws/monitor')
```

### Reconnection Settings
```typescript
const maxReconnectAttempts = 5
const initialDelay = 1000          // 1 second
const maxDelay = 16000             // 16 seconds (exponential backoff cap)
```

### Connection Manager Settings (Server)
```python
# app/websocket/monitor.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscription_filters: Dict[WebSocket, List[str]] = {}
```

---

## Known Limitations

1. **No event history:** Clients only receive events after connecting (no replay)
2. **No authentication:** WebSocket endpoint is unauthenticated (add JWT in production)
3. **No rate limiting:** High-frequency events may overwhelm slow clients
4. **No metrics snapshots yet:** `metrics:snapshot` event not implemented (future)

---

## Future Enhancements (N10.1+)

- [ ] **Event replay:** Send last N events on connect
- [ ] **Authentication:** JWT token validation for WebSocket connections
- [ ] **Rate limiting:** Throttle high-frequency events per client
- [ ] **Metrics snapshots:** Periodic stats push (every 5s)
- [ ] **Room/channel isolation:** Per-project or per-machine channels
- [ ] **Event persistence:** Store events in SQLite for audit trail

---

## See Also

- [N8.6 RMOS Stores](./N8_6_RMOS_STORES_QUICKREF.md) – RMOS SQLite stores
- [N9.0 Analytics Engine](./N9_0_ANALYTICS_QUICKREF.md) – Pattern/Job/Material analytics
- [N9.1 Advanced Analytics](./N9_1_ADVANCED_ANALYTICS_QUICKREF.md) – Correlation/Anomaly/Prediction
- [WebSocket Protocol (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) – WebSocket API reference

---

**Status:** ✅ N10.0 Complete  
**Next:** Add LiveMonitor to RMOS navigation → Test in full UI workflow
