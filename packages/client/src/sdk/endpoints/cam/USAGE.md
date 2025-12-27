# H8.3 CAM Endpoint Helpers - Usage Examples

## Overview

H8.3 introduces **typed endpoint helpers** that wrap the SDK transport layer, providing:
- Consistent return shapes with `requestId` for correlation
- Automatic header parsing (e.g., `X-CAM-Summary`)
- Type-safe payloads and responses
- Consistent error handling with `ApiError`

## Import Pattern

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk";
```

## 1. Roughing G-code (Legacy Entity-Based)

**Endpoint**: `POST /cam/roughing_gcode`

```typescript
import { cam } from "@/sdk/endpoints";

try {
  const { gcode, summary, requestId } = await cam.roughingGcode({
    entities: [/* boundary entities */],
    tool_diameter: 6.0,
    depth_per_pass: 2.0,
    stock_thickness: 10.0,
    feed_xy: 1200,
    feed_z: 300,
    safe_z: 5.0,
    tabs_count: 4,
    tab_width: 5.0,
    tab_height: 1.0,
    post: "GRBL",
  });

  console.log("Generated G-code:", gcode);
  console.log("Request ID:", requestId);
  
  if (summary) {
    console.log("Metrics:", summary.metrics);
    if (summary.intent_issues?.length) {
      console.warn("Intent issues:", summary.intent_issues);
    }
  }
} catch (err) {
  if (err instanceof ApiError) {
    console.error("API Error:", err.message);
    console.error("Request ID:", err.details?.requestId);
    console.error("Status:", err.status);
  }
}
```

## 2. Roughing G-code (Intent-Native)

**Endpoint**: `POST /cam/roughing_gcode_intent`

### Non-Strict Mode (Default)

Returns 200 with issues in summary header:

```typescript
import { cam } from "@/sdk/endpoints";

const { gcode, summary, requestId } = await cam.roughingGcodeIntent({
  design: {
    mode: "roughing",
    boundaries: [/* geometry */],
    // ... design intent
  },
  machine: {
    post_id: "GRBL",
    safe_z_mm: 5.0,
    // ... machine intent
  },
  tool: {
    diameter_mm: 6.0,
    flute_count: 2,
    // ... tool intent
  },
});

// Check for normalization issues
if (summary?.intent_issues?.length) {
  console.warn("Normalization issues:", summary.intent_issues);
  // Still have gcode, but may want to review intent
}
```

### Strict Mode

Returns 422 on any normalization issues:

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk";

try {
  const { gcode, summary, requestId } = await cam.roughingGcodeIntent(
    {
      design: { /* ... */ },
      machine: { /* ... */ },
      tool: { /* ... */ },
    },
    true // strict mode
  );

  // If we get here, intent was fully valid
  console.log("Clean intent, G-code generated:", gcode);
} catch (err) {
  if (err instanceof ApiError && err.is(422)) {
    console.error("Intent validation failed:", err.details);
    // Show validation errors to user
  }
}
```

## 3. CAM Pipeline Runner (FormData)

**Endpoint**: `POST /cam/pipeline/run`

```typescript
import { cam } from "@/sdk/endpoints";

const formData = new FormData();
formData.append("config", JSON.stringify({
  operation: "adaptive_pocket",
  tool_id: "tool_123",
}));
formData.append("dxf_file", dxfFile); // File object

const { result, requestId } = await cam.runPipeline(formData);

console.log("Pipeline result:", result);
console.log("Request ID:", requestId);
```

## 4. Error Handling Pattern

All helpers throw `ApiError` on failure:

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk";

try {
  const result = await cam.roughingGcode(payload);
  // success path
} catch (err) {
  if (err instanceof ApiError) {
    // Structured error with status, url, details
    console.error(`[${err.status}] ${err.message}`);
    console.error("Request ID:", err.details?.requestId);
    
    if (err.isClientError()) {
      // 4xx - validation or bad request
      showValidationErrors(err.details);
    } else if (err.isServerError()) {
      // 5xx - server failure
      showServerErrorAlert(err.message);
    }
  } else {
    // Network error or other failure
    console.error("Unexpected error:", err);
  }
}
```

## 5. Request ID Correlation

All helpers return `requestId` for end-to-end tracing:

```typescript
const { gcode, summary, requestId } = await cam.roughingGcode(payload);

// Show in UI for debugging
console.log(`Generated G-code (request: ${requestId})`);

// Include in error reports
if (hasProblem) {
  reportIssue({
    operation: "roughing_gcode",
    requestId,
    timestamp: new Date().toISOString(),
  });
}
```

## 6. Deprecation Warnings

Configure deprecation handler to catch legacy endpoint usage:

```typescript
import { setDeprecationHandler } from "@/sdk";

// In main.ts or App.vue setup
setDeprecationHandler((event) => {
  console.warn(
    `[DEPRECATION] ${event.method} ${event.url}`,
    event.deprecation
  );
  
  // Optional: track deprecation usage
  analytics.track("api_deprecation", {
    endpoint: event.url,
    suggestion: event.suggestion,
  });
});
```

## Migration from Raw fetch()

### Before (ad-hoc fetch)

```typescript
const response = await fetch("/api/cam/roughing_gcode", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Request-Id": generateRequestId(),
  },
  body: JSON.stringify(payload),
});

if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}

const gcode = await response.text();
const summaryHeader = response.headers.get("X-CAM-Summary");
const summary = summaryHeader ? JSON.parse(summaryHeader) : null;
```

### After (typed helper)

```typescript
import { cam } from "@/sdk/endpoints";

const { gcode, summary, requestId } = await cam.roughingGcode(payload);
// Header parsing, error handling, and request-id propagation automatic
```

## Benefits

1. **Type Safety**: Payloads and responses are typed
2. **Consistency**: All helpers return `{ ..., requestId }`
3. **Header Parsing**: Automatic parsing of custom headers (X-CAM-Summary)
4. **Error Context**: ApiError includes request-id, status, details
5. **Request Tracing**: End-to-end correlation via request-id
6. **Deprecation Tracking**: Automatic detection of legacy endpoint usage
7. **Testability**: Easy to mock in tests (single function per endpoint)

## Next Steps

- Add more CAM endpoints as needed (adaptive pocketing, helical, drilling)
- Tighten types as schemas stabilize (replace `unknown[]` with `Issue[]`)
- Add Zod validation for runtime schema checking
- Create endpoint-specific error subtypes for better error handling
