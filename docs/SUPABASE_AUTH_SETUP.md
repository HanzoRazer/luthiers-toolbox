# Supabase Authentication Setup

This guide walks through setting up Supabase authentication for The Production Shop.

## Prerequisites

- A Supabase account (free tier works)
- Access to Railway dashboard (for production deployment)

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in:
   - **Name**: `production-shop` (or similar)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
4. Wait for project to be created (~2 minutes)

## Step 2: Get Project Credentials

Navigate to **Settings > API** and note:

| Key | Location | Purpose |
|-----|----------|---------|
| `SUPABASE_URL` | Project URL | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | anon/public key | Client-side auth |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key | Server-side admin operations |
| `SUPABASE_JWT_SECRET` | Settings > API > JWT Settings | JWT verification |

Navigate to **Settings > Database** and get:

| Key | Location | Purpose |
|-----|----------|---------|
| `DATABASE_URL` | Connection String > URI | PostgreSQL connection |

## Step 3: Configure Environment Variables

### Local Development

Create/update `.env` in project root:

```bash
# Supabase Auth
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...your-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJ...your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql://postgres:YOUR-PASSWORD@db.your-project.supabase.co:5432/postgres

# Auth mode
AUTH_MODE=supabase
```

For frontend, update `packages/client/.env.local`:

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...your-anon-key
```

### Railway Production

Add these secrets in Railway dashboard:

1. Go to your Railway project
2. Click on the API service
3. Go to **Variables**
4. Add each environment variable

## Step 4: Run Database Migrations

The auth tables need to be created in your Supabase database.

### Option A: Using Alembic (Recommended)

```bash
cd services/api
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run migrations
alembic upgrade head
```

### Option B: Manual SQL

Run this SQL in Supabase SQL Editor (**SQL Editor > New Query**):

```sql
-- User profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'pro')),
    tier_expires_at TIMESTAMPTZ,
    display_name VARCHAR(128),
    avatar_url VARCHAR(512),
    stripe_customer_id VARCHAR(128),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature flags for tier gating
CREATE TABLE IF NOT EXISTS feature_flags (
    feature_key VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(128) NOT NULL,
    description TEXT,
    min_tier VARCHAR(20) DEFAULT 'free' CHECK (min_tier IN ('free', 'pro')),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed initial feature flags
INSERT INTO feature_flags (feature_key, display_name, description, min_tier) VALUES
    ('basic_dxf_export', 'Basic DXF Export', 'Export designs to DXF format', 'free'),
    ('gcode_generation', 'G-code Generation', 'Generate CNC G-code', 'free'),
    ('blueprint_import', 'Blueprint Import', 'Import blueprint images', 'free'),
    ('ai_vision', 'AI Vision Analysis', 'AI-powered design analysis', 'pro'),
    ('batch_processing', 'Batch Processing', 'Process multiple files at once', 'pro'),
    ('advanced_cam', 'Advanced CAM Features', 'Advanced toolpath strategies', 'pro'),
    ('custom_posts', 'Custom Post Processors', 'Create custom post processors', 'pro')
ON CONFLICT (feature_key) DO NOTHING;

-- Enable Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Service role can manage all profiles" ON user_profiles
    FOR ALL USING (auth.role() = 'service_role');
```

## Step 5: Enable Auth Providers

In Supabase dashboard, go to **Authentication > Providers**:

### Email/Password (Required)
- Already enabled by default
- Configure email templates under **Authentication > Email Templates**

### Google OAuth (Optional)
1. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add redirect URL: `https://your-project.supabase.co/auth/v1/callback`
3. Enter Client ID and Secret in Supabase

### GitHub OAuth (Optional)
1. Create OAuth App in [GitHub Developer Settings](https://github.com/settings/developers)
2. Add callback URL: `https://your-project.supabase.co/auth/v1/callback`
3. Enter Client ID and Secret in Supabase

## Step 6: Configure Email Settings (Production)

For production, configure SMTP in **Settings > Auth > SMTP Settings**:

- Use your own SMTP server (SendGrid, Mailgun, etc.)
- This ensures email deliverability

## Step 7: Verify Setup

### Backend Health Check

```bash
curl http://localhost:8000/api/auth/health
# Should return: {"status": "ok", "service": "auth"}
```

### Frontend Login Test

1. Start the development server: `npm run dev`
2. Navigate to `/auth/login`
3. Create an account and verify login works

## Troubleshooting

### "JWT secret not configured"
- Ensure `SUPABASE_JWT_SECRET` is set
- Restart the API server after adding env vars

### "Invalid token" errors
- Check that `SUPABASE_JWT_SECRET` matches your Supabase project
- Ensure tokens haven't expired

### Database connection errors
- Verify `DATABASE_URL` is correct
- Check Supabase database is running (not paused)
- For connection pooling, use port 6543 instead of 5432

### RLS policy errors
- Ensure the API uses `SUPABASE_SERVICE_ROLE_KEY` (bypasses RLS)
- Check policies are correctly defined

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Vue Frontend  │────▶│  FastAPI Backend │────▶│    Supabase     │
│                 │     │                  │     │                 │
│ - useAuthStore  │     │ - auth_router    │     │ - auth.users    │
│ - Supabase SDK  │     │ - tier_gate      │     │ - user_profiles │
│ - Route guards  │     │ - supabase_prov  │     │ - feature_flags │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Security Notes

- **SUPABASE_SERVICE_ROLE_KEY** is SECRET - never expose to frontend
- **SUPABASE_ANON_KEY** is safe for frontend use
- Enable RLS on all user data tables
- Use `SUPABASE_JWT_SECRET` for server-side JWT verification
