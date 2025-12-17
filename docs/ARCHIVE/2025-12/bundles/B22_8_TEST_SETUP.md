# B22.8: Unit Test Setup Guide

## Vitest Configuration for CompareLab State Machine Tests

### Quick Start

```powershell
# Navigate to client directory
cd client

# Install Vitest (if not already installed)
npm install -D vitest @vitest/ui

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Open Vitest UI
npm run test:ui
```

### Package.json Scripts

Add these scripts to `client/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage"
  }
}
```

### Vite Config

Ensure `client/vite.config.ts` includes test configuration:

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'], // Optional
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/composables/**/*.ts'],
      exclude: ['**/*.spec.ts', '**/*.test.ts']
    }
  }
})
```

### Optional: Test Setup File

Create `client/src/test/setup.ts` for global test configuration:

```typescript
// client/src/test/setup.ts
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/vue'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Add custom matchers if needed
expect.extend({
  // Custom matchers here
})
```

### Running Specific Tests

```powershell
# Run only useCompareState tests
npm run test useCompareState

# Run with pattern matching
npm run test -- --grep "overlayDisabled"

# Run in watch mode for specific file
npm run test:watch useCompareState.spec.ts
```

### Test Coverage Report

After running `npm run test:coverage`, check:
- Console output for coverage summary
- `client/coverage/` directory for detailed HTML report
- Open `client/coverage/index.html` in browser

**Target Coverage for B22.8:**
- `useCompareState.ts`: **100%** (all state machine logic)
- `overlayDisabled` computed: **100%** (critical guard)
- `runWithCompareSkeleton`: **100%** (double-click protection)

### CI Integration

Add to `.github/workflows/b22_tests.yml`:

```yaml
name: B22.8 Tests

on:
  push:
    branches: [feature/comparelab-b22-arc]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: client/package-lock.json
      
      - name: Install dependencies
        working-directory: client
        run: npm ci
      
      - name: Run tests
        working-directory: client
        run: npm run test
      
      - name: Run coverage
        working-directory: client
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./client/coverage/coverage-final.json
          flags: b22-state-machine
```

### Debugging Tests

**VS Code Launch Configuration** (`client/.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Vitest Tests",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "test:watch"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
```

Set breakpoints in `.spec.ts` files and press F5 to debug.

### Common Test Patterns

#### 1. Testing Async Operations
```typescript
it('waits for async operation', async () => {
  const state = useCompareState()
  const promise = state.runWithCompareSkeleton(async () => 'result')
  
  // Check intermediate state
  expect(state.isComputingDiff.value).toBe(true)
  
  const result = await promise
  await nextTick() // Wait for reactive updates
  
  // Check final state
  expect(state.isComputingDiff.value).toBe(false)
  expect(result).toBe('result')
})
```

#### 2. Testing Error Handling
```typescript
it('handles errors gracefully', async () => {
  const state = useCompareState()
  const error = new Error('Test error')
  
  await state.runWithCompareSkeleton(async () => {
    throw error
  })
  
  expect(state.diffDisabledReason.value).toBeTruthy()
})
```

#### 3. Testing Computed Properties
```typescript
it('recomputes when dependencies change', () => {
  const state = useCompareState()
  
  expect(state.overlayDisabled.value).toBe(true) // Initial
  
  state.compareResult.value = mockResult
  expect(state.overlayDisabled.value).toBe(false) // After change
})
```

### Troubleshooting

#### Tests not running
```powershell
# Clear cache
npm run test -- --clearCache

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### TypeScript errors in tests
```powershell
# Check tsconfig includes test files
# Ensure "types": ["vitest/globals"] in tsconfig.json
```

#### Mock fetch not working
```typescript
// Add to test file
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ data: 'mock' })
})
```

### Test Maintenance

**When to update tests:**
- ✅ Adding new state properties to `CompareState`
- ✅ Changing `overlayDisabled` logic
- ✅ Modifying `runWithCompareSkeleton` behavior
- ✅ Adding new actions to composable

**When NOT to change tests:**
- ❌ UI component changes (unless they affect state machine)
- ❌ Styling changes
- ❌ Non-state logic changes

### Success Criteria

**Before committing B22.8:**
- [ ] All 40+ tests pass (`npm run test`)
- [ ] Coverage ≥ 95% for `useCompareState.ts`
- [ ] No console warnings during test run
- [ ] Tests complete in < 5 seconds

---

**Last Updated:** December 2, 2025  
**Status:** ✅ Test suite complete for B22.8 state machine
