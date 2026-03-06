# Imprint Chatbot Deployment Guide

## Overview

- **Backend:** FastAPI on Render
- **Frontend:** Next.js on Vercel
- **Database:** Supabase (already configured)

---

## 1. Deploy Backend to Render

### Create New Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect to your GitHub repo: `lelandjfs/imprint`
4. Configure:
   - **Name:** `imprint-api`
   - **Root Directory:** `api`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free (or Starter for better performance)

### Set Environment Variables

In Render dashboard, add these environment variables:

```
DATABASE_URL=postgresql://postgres:leesbrainproject27!!@db.qvwqquyaxunxyiwtobsu.supabase.co:5432/postgres
SUPABASE_URL=https://qvwqquyaxunxyiwtobsu.supabase.co
SUPABASE_ANON_KEY=sb_publishable_9ijcCdSAe65T5fNwE2aQog_YLBK6gvX
OPENAI_API_KEY=<your-openai-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
LANGSMITH_API_KEY=<your-langsmith-key> (optional)
LANGSMITH_TRACING=true (optional)
LANGSMITH_PROJECT=imprint-chatbot (optional)
```

### Deploy

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Note your API URL: `https://imprint-api.onrender.com`

---

## 2. Deploy Frontend to Vercel

### Create New Project

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import `lelandjfs/imprint` repo
4. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** `web`
   - **Build Command:** (auto-detected)
   - **Output Directory:** (auto-detected)

### Set Environment Variables

Add this environment variable:

```
NEXT_PUBLIC_API_URL=https://imprint-api.onrender.com
```

(Update with your actual Render URL from step 1)

### Deploy

1. Click "Deploy"
2. Wait for deployment (2-3 minutes)
3. Your chatbot will be live at: `https://imprint-chat.vercel.app`

---

## 3. Test the Deployment

1. Visit your Vercel URL
2. Select a model (Claude 3.5 Sonnet or GPT-4)
3. Ask a question: "What do I have on NVDA?"
4. Check that:
   - Sources appear in the right panel
   - Response streams in real-time
   - Filters work (try selecting a sector)

---

## 4. Update CORS (if needed)

If you get CORS errors, update `api/config.py`:

```python
cors_origins: list[str] = [
    "http://localhost:3000",
    "https://imprint-chat.vercel.app",  # Add your Vercel domain
    "https://*.vercel.app"
]
```

Then redeploy the backend on Render.

---

## 5. Local Development

### Backend (API)

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### Frontend (Web)

```bash
cd web
npm install
npm run dev
# Runs on http://localhost:3000
```

---

## Troubleshooting

**Backend not starting:**
- Check Render logs for errors
- Verify all environment variables are set
- Ensure Supabase RPC function exists (run the SQL from plan)

**Frontend can't connect to API:**
- Verify `NEXT_PUBLIC_API_URL` is set in Vercel
- Check Network tab in browser for CORS errors
- Ensure Render service is running

**No documents returned:**
- Verify you have documents with `status='active'` in Supabase
- Check filter settings aren't too restrictive
- Test the `/api/filters` endpoint directly

---

## Monitoring

- **Backend logs:** Render dashboard → "Logs" tab
- **LangSmith traces:** https://smith.langchain.com (if enabled)
- **Frontend errors:** Vercel dashboard → "Runtime Logs"
