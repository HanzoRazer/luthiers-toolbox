# Vitest Quick Reference

## Installation
```powershell
cd client
npm install
```

## Running Tests

### Run all tests once
```powershell
npm run test
```

### Run tests in watch mode (development)
```powershell
npm run test:watch
```

### Run specific test file
```powershell
npx vitest src/utils/math/__tests__/curveRadius.spec.ts
```

### Run tests with UI (interactive)
```powershell
npx vitest --ui
```

## Coverage

### Generate coverage report
```powershell
npm run test
# Opens: client/coverage/index.html
```

### View coverage in terminal
```powershell
npm run test -- --coverage.reporter=text
```

## Test Files Structure

```
client/src/utils/math/
├── curveRadius.ts              # Math utilities
├── compoundRadius.ts           # Math utilities
└── __tests__/
    ├── curveRadius.spec.ts     # 12 tests
    └── compoundRadius.spec.ts  # 11 tests
```

## Example Test
```typescript
import { describe, it, expect } from 'vitest'
import { radiusFromChordSagitta } from '../curveRadius'

describe('curveRadius', () => {
  it('should calculate radius from chord and sagitta', () => {
    const result = radiusFromChordSagitta(300, 12)
    expect(result.R).toBeCloseTo(938.5, 0)
  })
})
```

## CI/CD
Tests run automatically on:
- Push to `main` branch
- Pull requests to `main` branch

See: `.github/workflows/client_smoke.yml`
