# SDK Endpoints (H8.3) - Architecture & Implementation

## Overview

The **endpoints module** provides **typed, per-endpoint helpers** that wrap the SDK transport layer, replacing ad-hoc `fetch()` calls throughout the frontend with consistent, type-safe API interfaces.

## Architecture

```
src/sdk/
├── core/
│   ├── apiFetch.ts           # Simple transport (returns data only)
│   ├── apiFetchRaw.ts        # H8.3 raw transport (returns {data, response})
│   ├── errors.ts             # ApiError with request-id context
│   └── headers.ts            # Deprecation + request-id detection
├── endpoints/
│   ├── index.ts              # Top-level exports (cam, etc.)
│   └── cam/
│       ├── cam.ts            # CAM namespace aggregator
│       ├── types.ts          # Typed payloads/responses
│       ├── roughing.ts       # roughingGcode(), roughingGcodeIntent()
│       ├── pipeline.ts       # runPipeline(FormData)
│       ├── USAGE.md          # Usage examples and migration guide
│       └── __tests__/
│           └── cam.endpoints.test.ts  # Vitest test suite
└── index.ts                  # Main SDK export
```

## Design Principles

### 1. **Typed Payloads & Responses**

Every endpoint has explicit TypeScript interfaces:

```typescript
// types.ts
export interface RoughingGcodeRequest {
  entities: unknown[];
  tool_diameter: number;
  depth_per_pass: number;
  // ... complete contract
}

export interface RoughingGcodeResult {
  gcode: string;
  summary: CamSummary | null;
  requestId: string;
}
```

### 2. **Header Parsing in Helpers**

Custom header logic stays in the helper, not in components:

```typescript
// roughing.ts
async function roughingGcode(payload: RoughingGcodeRequest): Promise<RoughingGcodeResult> {
  const { data, response } = await postRaw<string>("/cam/roughing_gcode", payload);
  
  return {
    gcode: data,
    summary: parseCamSummary(response),  // Header parsing here
    requestId: extractRequestId(response),
  };
}
```

### 3. **Consistent Return Shape**

All helpers return objects with `requestId` for correlation:

```typescript
// Every helper returns:
{
  /* domain-specific data */,
  requestId: string
}
```

### 4. **Transport Layer Separation**

- **apiFetch**: Simple transport, returns data directly (existing)
- **apiFetchRaw**: H8.3 transport, returns `{data, response}` for header access

```typescript
// core/apiFetchRaw.ts
export async function apiFetchRaw<T>(
  url: string,
  options?: RequestInit
): Promise<{ data: T; response: Response }> {
  const response = await fetch(url, options);
  if (!response.ok) throw ApiError.fromResponse(response);
  
  const data = await response.json();
  return { data, response };
}
```

### 5. **FormData Special Handling**

FormData requires omitting `Content-Type` (browser sets multipart boundary):

```typescript
// core/apiFetchRaw.ts
export async function postFormRaw<T>(
  url: string,
  form: FormData
): Promise<{ data: T; response: Response }> {
  const headers = new Headers();
  delete headers.delete("Content-Type"); // Let browser set boundary
  
  return apiFetchRaw<T>(url, {
    method: "POST",
    headers,
    body: form,
  });
}
```

## Implementation Pattern

### Step 1: Define Types

```typescript
// endpoints/cam/types.ts
export interface MyOperationRequest {
  param1: string;
  param2: number;
}

export interface MyOperationResult {
  output: string;
  requestId: string;
}
```

### Step 2: Create Helper

```typescript
// endpoints/cam/myOperation.ts
import { postRaw } from "@/sdk/core/apiFetchRaw";
import { extractRequestId } from "@/sdk/core/headers";
import type { MyOperationRequest, MyOperationResult } from "./types";

export async function myOperation(
  payload: MyOperationRequest
): Promise<MyOperationResult> {
  const { data, response } = await postRaw<string>("/cam/my_operation", payload);
  
  return {
    output: data,
    requestId: extractRequestId(response),
  };
}
```

### Step 3: Add to Namespace

```typescript
// endpoints/cam/cam.ts
export * from "./myOperation";
```

### Step 4: Write Tests

```typescript
// endpoints/cam/__tests__/cam.endpoints.test.ts
import { describe, it, expect, vi } from "vitest";
import { myOperation } from "../myOperation";
import * as apiFetchRaw from "@/sdk/core/apiFetchRaw";

describe("myOperation", () => {
  it("returns output + requestId", async () => {
    const mockResponse = new Response("result_data", {
      headers: { "X-Request-Id": "req-123" },
    });
    
    vi.spyOn(apiFetchRaw, "postRaw").mockResolvedValueOnce({
      data: "result_data",
      response: mockResponse,
    });
    
    const result = await myOperation({ param1: "test", param2: 42 });
    
    expect(result).toEqual({
      output: "result_data",
      requestId: "req-123",
    });
  });
});
```

## Migration Guide

### Before: Ad-hoc fetch()

```typescript
// Component.vue
const response = await fetch("/api/cam/roughing_gcode", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Request-Id": generateRequestId(),
  },
  body: JSON.stringify(payload),
});

if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail || "Request failed");
}

const gcode = await response.text();
const summaryHeader = response.headers.get("X-CAM-Summary");
let summary = null;
try {
  summary = summaryHeader ? JSON.parse(summaryHeader) : null;
} catch {
  console.warn("Failed to parse X-CAM-Summary");
}
```

### After: Typed helper

```typescript
// Component.vue
import { cam } from "@/sdk/endpoints";

const { gcode, summary, requestId } = await cam.roughingGcode(payload);
// Header parsing, error handling, request-id automatic
```

## Error Handling

All helpers throw `ApiError` with request-id context:

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk";

try {
  const result = await cam.roughingGcode(payload);
} catch (err) {
  if (err instanceof ApiError) {
    console.error(`[${err.status}] ${err.message}`);
    console.error("Request ID:", err.details?.requestId);
    
    if (err.is(422)) {
      // Validation error
      showValidationErrors(err.details);
    } else if (err.isServerError()) {
      // 5xx error
      showServerErrorAlert(err.message);
    }
  }
}
```

## Current Coverage

### CAM Endpoints (3)

| Endpoint | Helper | Return Shape | Notes |
|----------|--------|--------------|-------|
| `POST /cam/roughing_gcode` | `cam.roughingGcode()` | `{gcode, summary, requestId}` | Legacy entity-based |
| `POST /cam/roughing_gcode_intent` | `cam.roughingGcodeIntent()` | `{gcode, summary, requestId}` | Intent-native with strict mode |
| `POST /cam/pipeline/run` | `cam.runPipeline()` | `{result, requestId}` | FormData submission |

### Header Parsing

| Header | Parser | Return Type | Error Handling |
|--------|--------|-------------|----------------|
| `X-CAM-Summary` | `parseCamSummary()` | `CamSummary \| null` | Graceful on malformed JSON |
| `X-Request-Id` | `extractRequestId()` | `string` | Empty string fallback |

## Testing

Run the test suite:

```bash
cd packages/client
npm run test -- src/sdk/endpoints/cam/__tests__/cam.endpoints.test.ts
```

**Coverage:**
- ✅ roughingGcode with X-CAM-Summary header
- ✅ roughingGcode without X-CAM-Summary (graceful null)
- ✅ roughingGcode with malformed X-CAM-Summary (logs warning, returns null)
- ✅ roughingGcodeIntent with strict mode query param
- ✅ roughingGcodeIntent without strict mode
- ✅ runPipeline with FormData (no Content-Type override)

## Roadmap

### Phase 1: Foundation (Complete)
- ✅ Create `apiFetchRaw` transport layer
- ✅ Define CAM types with loose schemas
- ✅ Implement 3 initial helpers (roughing × 2, pipeline × 1)
- ✅ Write comprehensive test suite
- ✅ Document usage patterns

### Phase 2: Expand Coverage
- [ ] Add adaptive pocketing helpers
- [ ] Add helical ramping helpers
- [ ] Add drilling pattern helpers
- [ ] Add V-carve helpers
- [ ] Add compare endpoints
- [ ] Add RMOS endpoints

### Phase 3: Schema Tightening
- [ ] Replace `unknown[]` with specific types as schemas stabilize
- [ ] Add Zod runtime validation
- [ ] Create endpoint-specific error types

### Phase 4: Component Migration
- [ ] Migrate CamPipelineRunner.vue
- [ ] Migrate CAMEssentialsLab.vue
- [ ] Migrate DrillingLab.vue
- [ ] Track legacy fetch() usage via CI gate

## Benefits Summary

1. **Type Safety**: Compiler catches payload/response mismatches
2. **Consistency**: All endpoints follow same patterns
3. **Maintainability**: API changes update 1 helper vs N components
4. **Testability**: Mock 1 helper function vs fetch() everywhere
5. **Debuggability**: Request-id propagation for correlation
6. **Error Context**: ApiError includes status, url, request-id
7. **Header Parsing**: Custom logic in helpers, not components
8. **Deprecation Tracking**: Automatic detection via middleware

## See Also

- [USAGE.md](./cam/USAGE.md) - Detailed usage examples
- [../core/apiFetchRaw.ts](../core/apiFetchRaw.ts) - Transport layer implementation
- [../core/errors.ts](../core/errors.ts) - ApiError with request-id context
- [../../VITEST_QUICKREF.md](../../VITEST_QUICKREF.md) - Testing guide
