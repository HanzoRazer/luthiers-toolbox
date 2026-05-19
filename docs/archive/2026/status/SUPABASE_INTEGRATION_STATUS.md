# Supabase Integration Status

> **Last assessed:** 2026-03-10
> **Supabase org:** `ytyspjxrehyqbxuouolu`
> **Overall status:** ~70% coded, 0% operational

All individual pieces — migration, provider, router, guards, store, views — are internally consistent and well-written. None of them are connected to the running application.

---

## What's Built

### Backend (FastAPI)

| Component | File | Status |
|-----------|------|--------|
| Supabase JWT decoder + Principal mapper | `services/api/app/auth/supabase_provider.py` | Complete |
| Auth router (`/me`, `/me` PATCH, `/tier`) | `services/api/app/routers/auth_router.py` | Complete |
| Tier gate middleware (`require_feature`, `require_pro`) | `services/api/app/middleware/tier_gate.py` | Complete |
| Alembic migration (user_profiles, projects, feature_flags + seeds) | `services/api/app/db/migrations/versions/0001_supabase_auth_tables.py` | Complete |
| Auth + tier tests (23 total) | `services/api/tests/test_auth_supabase.py`, `tests/test_tier_gate.py` | Complete |
| PyJWT dependency | `services/api/requirements.txt` line 52 | Installed |

### Frontend (Vue 3)

| Component | File | Status |
|-----------|------|--------|
| Supabase client singleton | `packages/client/src/auth/supabase.ts` | Complete |
| Auth types (UserProfile, TierInfo, credentials) | `packages/client/src/auth/types.ts` | Complete |
| Auth Pinia store (signIn, signUp, OAuth, profile) | `packages/client/src/stores/useAuthStore.ts` | Complete |
| Route guards (auth, guest, tier, feature, init) | `packages/client/src/router/guards.ts` | Complete (5 guards) |
| Login view + LoginForm component | `packages/client/src/views/auth/LoginView.vue`, `components/auth/LoginForm.vue` | Complete |
| Signup view | `packages/client/src/views/auth/SignupView.vue` | Complete |
| OAuth callback view | `packages/client/src/views/auth/CallbackView.vue` | Complete |
| Upgrade view ($19/mo pricing page) | `packages/client/src/views/auth/UpgradeView.vue` | Complete |
| TierBadge component | `packages/client/src/components/auth/TierBadge.vue` | Complete |
| `@supabase/supabase-js ^2.45.0` | `packages/client/package.json` line 19 | Installed |

### Configuration

| File | Supabase Vars | Status |
|------|--------------|--------|
| `.env.example` | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, `AUTH_MODE=header` | Placeholder values |
| `packages/client/.env.local.example` | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Placeholder values |
| `packages/client/.env.production` | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | **Empty strings** |

---

## Critical Wiring Gaps

These are the reasons the system is 0% operational despite having all the pieces.

### 1. Auth router not registered in `main.py`

`services/api/app/routers/auth_router.py` defines 3 endpoints but is **not imported or registered** in `main.py` or `router_registry.py`. The `/api/auth/me` and `/api/auth/tier` endpoints are unreachable at runtime.

### 2. `initAuthGuard` not applied as global `router.beforeEach()`

`packages/client/src/router/guards.ts` exports `initAuthGuard` but it is never called in `packages/client/src/router/index.ts`. Auth state never initializes on navigation.

### 3. `requireAuth` not used on any route

The guard exists but no route in the router has `beforeEnter: requireAuth`. Every page is publicly accessible.

### 4. `requireTier` / `requireFeature` not used on any route

Both guard factories exist in `guards.ts` but are not applied anywhere. No tier-gated pages.

### 5. No backend endpoint uses tier gating

`require_feature()`, `require_tier()`, and `require_pro` exist in `tier_gate.py` but no actual route depends on them.

### 6. `AUTH_MODE` defaults to `"header"`

The backend defaults to dev-mode header-based auth. Production would need an explicit `AUTH_MODE=supabase` environment variable.

### 7. Auth store uses raw `fetch()` instead of SDK

`useAuthStore.ts` calls `fetch("/api/auth/me")` directly instead of using the project's typed SDK (`@/sdk/endpoints`). Violates the project convention (copilot-instructions rule #3).

### 8. Alembic migration never run

The 3 tables (`user_profiles`, `projects`, `feature_flags`) exist as migration code but presumably haven't been applied to the Supabase database.

### 9. Planning docs not updated

`docs/UNFINISHED_REMEDIATION_EFFORTS.md` (lines 335–395) and `docs/PHASE_2_3_IMPLEMENTATION_PLAN.md` (line 460) still say auth is "❌ Not started" — hasn't been updated to reflect partial implementation.

---

## Completely Missing

| Item | Notes |
|------|-------|
| Stripe integration | `UpgradeView.vue` shows $19/mo pricing but no payment flow exists |
| Email templates | Not configured in Supabase dashboard |
| OAuth provider credentials | Google and GitHub OAuth not set up |
| SMTP for production | No email delivery configured |
| RLS policies | SQL exists in `SUPABASE_AUTH_SETUP.md` but needs to be executed in Supabase |
| SDK endpoint wrappers for auth | Auth calls should go through `@/sdk/endpoints`, not raw `fetch()` |

---

## Steps to Make Operational

1. Register auth router in `main.py`:
   ```python
   from app.routers.auth_router import router as auth_router
   app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
   ```

2. Apply `initAuthGuard` in `packages/client/src/router/index.ts`:
   ```typescript
   import { initAuthGuard } from './guards'
   router.beforeEach(initAuthGuard)
   ```

3. Add `requireAuth` to protected routes in the router.

4. Set real Supabase credentials in `.env` and `.env.production` (from the Supabase dashboard at `https://supabase.com/dashboard/org/ytyspjxrehyqbxuouolu`).

5. Run Alembic migration against the Supabase database:
   ```bash
   cd services/api
   alembic upgrade head
   ```

6. Execute RLS policies SQL in Supabase SQL Editor (documented in `SUPABASE_AUTH_SETUP.md`).

7. Switch `AUTH_MODE=supabase` in production environment.

8. Configure OAuth providers and email templates in Supabase dashboard.

9. Refactor auth store to use SDK helpers instead of raw `fetch()`.

10. Apply `require_feature()` / `require_pro` to endpoints that should be tier-gated.

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/SUPABASE_AUTH_SETUP.md` | How-to guide for Supabase setup (instructions, not status) |
| `docs/PHASE_2_3_IMPLEMENTATION_PLAN.md` | SaaS conversion plan; auth is Week 1-2 of Phase 3 |
| `docs/UNFINISHED_REMEDIATION_EFFORTS.md` | Tracks auth as incomplete (items #19, gap section 3.1) |
