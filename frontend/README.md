# Medical Coding — Frontend

Next.js 14 reviewer UI, deployable to Vercel.

## Quick Start (Local)

```powershell
# 1. Install Node.js first: https://nodejs.org (LTS recommended)

# 2. Install dependencies
cd frontend
npm install

# 3. Configure environment
copy .env.local.example .env.local
# Edit .env.local — set BACKEND_URL if you have a running backend
# Leave DEMO_MODE=true to use built-in mock data (no backend needed)

# 4. Run dev server
npm run dev
# → Open http://localhost:3000
```

## Deploy to Vercel (zero-config)

```bash
# Option A: Vercel CLI
npm install -g vercel
cd frontend
vercel

# Option B: GitHub → vercel.com → Import Repository
# Root directory: frontend
# Framework: Next.js (auto-detected)
```

**Environment variables to set in Vercel dashboard:**

| Variable       | Value                            | Required |
|---------------|----------------------------------|----------|
| `DEMO_MODE`    | `true` (demo) or `false` (live) | Yes      |
| `BACKEND_URL`  | `https://your-api.onrender.com`  | Live only|

## Deploy Backend to Render

```bash
# From repo root (not frontend/)
# 1. Push repo to GitHub
# 2. Create new Web Service at render.com → connect repo
# 3. Build command:  pip install -r backend/requirements.txt
# 4. Start command:  uvicorn backend.app:app --host 0.0.0.0 --port $PORT
# 5. Add env var:    GOOGLE_API_KEY=your-key
# 6. Copy the Render URL → paste into Vercel's BACKEND_URL
```

## Architecture

```
Browser → Vercel (Next.js) → /api/process (proxy) → Render (FastAPI) → Gemini/OpenAI
```
