# shared (OpenAPI SDK target)

Run `tools/codegen/generate_ts_sdk.sh` to generate TypeScript types from the API.

This package will contain:
- TypeScript type definitions generated from OpenAPI
- Shared interfaces between client and services
- Common utility types

## Usage

After SDK generation:

```typescript
import type { SimInput, ToolIn, MaterialIn } from '@toolbox/shared';
```
