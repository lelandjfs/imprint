# Imprint — System Overview

**Last Updated:** March 30, 2026

---

## Purpose

Imprint is a personal research knowledge base for investment research. It ingests documents from multiple sources, tags them with market-linkable metadata, and provides semantic search + RAG chat for surfacing relevant insights.

**Core workflow:**
1. Ingest documents from Gmail, Safari bookmarks, Google Drive (automated daily at 9pm)
2. Auto-tag with LLM using structured outputs (topic, sector, entities, sentiment, etc.)
3. Review and refine tags via web UI
4. Chat with your research using hybrid RAG retrieval
5. Build investment theses with drag-and-drop citations

---

## Architecture

### Tech Stack

**Backend (Python/FastAPI)**
- FastAPI for REST API
- LangChain for RAG pipeline
- Anthropic Claude (tagging + chat)
- OpenAI (embeddings: text-embedding-3-large @ 1536 dims)
- Supabase Python client + psycopg2
- Deployed on Render (auto-deploy from GitHub main branch)

**Frontend (Next.js 14)**
- Next.js 14 App Router + TypeScript
- Tailwind CSS for styling
- Server-Sent Events (SSE) for streaming chat
- Deployed on Vercel (auto-deploy from GitHub main branch)

**Database (Supabase)**
- Postgres with pgvector extension
- Vector similarity search with RPC functions
- Stores: documents, embeddings, metadata, ingestion logs

---

## Tag Schema

Documents are tagged with the following metadata:

| Field | Type | Description | Examples |
|-------|------|-------------|----------|
| **topic** | string | Specific mechanism/domain (snake_case) | `ai_inference_economics`, `gpu_supply_constraints` |
| **entities** | array | Companies (tickers), people, orgs | `["NVDA", "OpenAI", "Jerome Powell"]` |
| **sector** | string | High-level industry classification | `Semiconductors`, `Infra`, `Software`, `Macro` |
| **sentiment** | string | Author's directional tone | `bullish`, `bearish`, `neutral`, `mixed` |
| **document_type** | string | Format/style of document | `article`, `blog`, `whitepaper`, `earnings`, `report`, `x_post`, `image` |
| **catalyst_window** | string (optional) | Time horizon for signal | `immediate`, `near_term`, `medium_term`, `long_term`, `structural` |
| **summary** | string | One-sentence takeaway | "Hyperscaler AI spending accelerating..." |
| **weighting** | int (optional) | Importance score (1-5) | `4` |

**Reference:** See `Imprint_Tag_Dictionary.md` for detailed definitions and examples.

---

## Ingestion Pipelines

Imprint has 4 automated ingestion pipelines:

### 1. Email (`ingest_email.py`)
- **Source:** Gmail messages with "Imprint" label
- **Content:** Plain text from email body
- **Tagging:** Claude Haiku with structured outputs (Pydantic + tool calling)
- **Schedule:** Daily at 9pm (launchd)

### 2. Bookmarks (`ingest_bookmark.py`)
- **Source:** Safari "Imprint" bookmarks folder
- **Fetch:** Jina Reader API → Parallel Extract API (for paywalls/CAPTCHAs)
- **Tagging:** Claude Haiku with structured outputs
- **Schedule:** Daily at 9pm (launchd)

### 3. PDF (`ingest_pdf.py`)
- **Source:** Google Drive "Imprint" folder (root)
- **Extraction:** PyMuPDF text extraction + LLM-based content cleaning
- **Tagging:** Claude Haiku with structured outputs
- **Schedule:** Daily at 9pm (launchd)

### 4. Vision (`ingest_vision.py`)
- **Source:** Google Drive "Imprint/Vision" subfolder
- **Extraction:** GPT-4o vision for charts/screenshots
- **Tagging:** Claude Haiku with structured outputs
- **Schedule:** Daily at 9pm (launchd)

### Master Script
- **`ingest_all.py`** orchestrates all 4 pipelines
- **`run_ingestion.sh`** wrapper script that:
  - Quits Safari (required for bookmarks access)
  - Runs master script via launchd (9:00 PM daily)
  - Logs to `logs/ingestion_YYYYMMDD_HHMMSS.log`
- **`refresh_google_auth.py`** - tool for refreshing Google OAuth tokens
- Sends email summary after completion to `leland.speth@gmail.com`

### Ingestion Flow
1. Fetch content from source
2. Clean and normalize text (`imprint_utils.py` - LLM-based ad/chrome removal)
3. **Propose tags via Claude using structured outputs** (`propose_tags()`)
   - Uses Anthropic tool calling with `tool_choice` to force schema compliance
   - Pydantic `DocumentTags` model ensures valid output
   - **No more JSON parsing errors** - schema is guaranteed
4. Generate embedding via OpenAI (text-embedding-3-large @ 1536 dims)
5. Store in Supabase with `status='pending_review'`
6. Log to `ingestion_log` table

### Google OAuth Token Management
- **Published app** - no more 7-day token expiration
- **Auto-refresh** - tokens automatically refreshed before API calls via `get_google_credentials()`
- **Manual refresh:** Run `python3 refresh_google_auth.py` if token expires
- Tokens stored in `token.json` (gitignored)

### Safari Bookmarks Access
- **Full Disk Access required** - Python executable must have Full Disk Access permission
- **Safari must be quit** - `run_ingestion.sh` automatically quits Safari before accessing bookmarks
- Location: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`
- Grant access: System Settings → Privacy & Security → Full Disk Access

---

## Tag Approval Workflow

**Web UI:** `web/components/TagApproval.tsx`

1. User opens Tag Approval page
2. View all documents with `status='pending_review'`
3. Edit tags inline (auto-saves to backend via PATCH)
4. **Approve:** Sets `status='active'`, document becomes searchable
5. **Reject:** Deletes document + optionally deletes source file (Gmail label removal, Drive trash)

**Features:**
- Ultra-compact 3-column layout for tags
- Real-time auto-save (1 second debounce)
- Inline entity management (add/remove with Enter)
- Weighting selector (1-5 buttons)
- Source deletion for rejected documents

---

## Thesis Notebook

**Web UI:** `web/app/thesis/page.tsx` + `web/components/thesis/`

A dedicated workspace for building structured investment theses with drag-and-drop citations from chat results.

**Features:**
- **Multi-thesis management** - Create and switch between multiple theses
- **Structured sections** - Organize arguments with custom section headers
- **Drag-and-drop citations** - Drag documents from chat sidebar directly into thesis
- **Citation management** - Each section tracks cited documents with metadata
- **Export** - Copy thesis text with citations for external use
- **Persistent state** - Theses saved in browser localStorage

**Workflow:**
1. Chat with research in sidebar
2. Drag relevant documents into active thesis
3. Organize into logical sections
4. Build comprehensive investment argument
5. Export for presentation or further analysis

**Components:**
- `ThesisNotebook.tsx` - Main thesis editor with sections
- `ChatSidebar.tsx` - Chat interface with draggable source cards
- `SidebarSourceCard.tsx` - Individual source card with drag handle
- `ThesisList.tsx` - Thesis switcher/creator

---

## Chat Interface

**Backend:** `api/routers/chat.py` + `api/services/rag_chain.py`

**RAG Pipeline:**
1. **Condense question** (if chat history exists) - rephrases follow-up questions as standalone queries
   - Uses dedicated prompt with strict "no answering" rules to prevent hallucination
2. **Query analysis** - Extract metadata from user question using structured outputs
   - Topic, entities, sectors, sentiment intent, catalyst window, search intent
   - Automatically applies metadata filters for precision retrieval
3. **Hybrid retrieval** - Two-path approach for maximum recall:
   - **Path 1:** Metadata-filtered search (if filters extracted)
   - **Path 2:** Semantic search with similarity threshold (0.3)
   - Combines results, deduplicates, takes top 5 by similarity
4. **Document analysis** - LLM analyzes each document for thesis utility
   - Summary, key excerpt, thesis signal (bullish/bearish/neutral/mixed)
   - Thesis utility explanation for investment use
5. **Anti-hallucination safeguards** - Strict prompt rules prevent LLM from inventing documents
   - "NEVER invent, fabricate, or hallucinate document titles or content"
   - Must use exact titles from context, direct quotes only
   - Returns "No documents found" if context is empty
6. **Format context** - Inject retrieved document chunks into prompt
7. **Stream response** - Server-Sent Events (SSE) for real-time token streaming

**Models available:**
- Claude Sonnet 4.5 (claude-sonnet-4-5-20250929) — **default**
- Claude Opus 4.5 (claude-opus-4-5)
- GPT-4o
- GPT-4o Mini

**Frontend:** `web/app/page.tsx` + `web/components/ChatInterface.tsx`
- Streaming chat with SSE
- Source citations with analysis (summary, excerpt, thesis signal, thesis utility)
- Query analysis display (shows extracted metadata)
- Filter sidebar (sector, entities, sentiment)
- Model selector
- Session management
- LangSmith feedback (thumbs up/down)

**LangSmith Tracing:**
- Enabled in production for debugging and monitoring
- Tracks full RAG pipeline execution
- User feedback collection via thumbs up/down
- Project: `imprint-chatbot`

---

## Database Schema

### `imprint_documents`
```sql
CREATE TABLE imprint_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  author TEXT,
  content TEXT NOT NULL,
  source_type TEXT NOT NULL,  -- 'email', 'url', 'pdf', 'image'
  source TEXT,
  source_url TEXT,
  published_date TIMESTAMP,

  -- Tags
  topic TEXT,
  sector TEXT,
  entities TEXT[],
  sentiment TEXT,
  document_type TEXT,
  catalyst_window TEXT,
  summary TEXT,
  weighting INTEGER CHECK (weighting >= 1 AND weighting <= 5),

  -- Embedding
  embedding VECTOR(1536),

  -- Metadata
  status TEXT DEFAULT 'pending_review',  -- 'pending_review', 'active', 'archived'
  ingested_date TIMESTAMP DEFAULT NOW(),

  -- Indexes
  CONSTRAINT sentiment_check CHECK (sentiment IN ('bullish', 'bearish', 'neutral', 'mixed')),
  CONSTRAINT document_type_check CHECK (document_type IN ('article', 'blog', 'whitepaper', 'transcript', 'presentation', 'earnings', 'report', 'image', 'x_post', 'other')),
  CONSTRAINT unique_source_url UNIQUE (source_url)  -- Prevents race condition duplicates
);

CREATE INDEX idx_status ON imprint_documents(status);
CREATE INDEX idx_sector ON imprint_documents(sector);
CREATE INDEX idx_sentiment ON imprint_documents(sentiment);
CREATE INDEX idx_document_type ON imprint_documents(document_type);
CREATE INDEX idx_embedding ON imprint_documents USING ivfflat (embedding vector_cosine_ops);
```

### `ingestion_log`
```sql
CREATE TABLE ingestion_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT NOT NULL,
  source_identifier TEXT NOT NULL,
  status TEXT NOT NULL,  -- 'success', 'failed', 'restricted'
  error_message TEXT,
  document_id UUID REFERENCES imprint_documents(id),
  ingested_at TIMESTAMP DEFAULT NOW()
);
```

### RPC Function: `match_imprint_documents`
Vector similarity search with metadata filters:
```sql
CREATE OR REPLACE FUNCTION match_imprint_documents(
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 5,
  filter_sector TEXT[] DEFAULT NULL,
  filter_entities TEXT[] DEFAULT NULL,
  filter_sentiment TEXT[] DEFAULT NULL,
  filter_status TEXT DEFAULT 'active'
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  content TEXT,
  summary TEXT,
  topic TEXT,
  sector TEXT,
  entities TEXT[],
  sentiment TEXT,
  document_type TEXT,
  catalyst_window TEXT,
  weighting INTEGER,
  source_url TEXT,
  similarity FLOAT
)
```

---

## Deployment

### Backend (Render)
- **URL:** https://imprint-api.onrender.com
- **Auto-deploy:** GitHub main branch → Render (on push)
- **Environment:** Python 3.13, 512MB RAM, Free tier
- **Health check:** `/health` endpoint

### Frontend (Vercel)
- **URL:** https://imprint-ruddy.vercel.app
- **Auto-deploy:** GitHub main branch → Vercel (on push)
- **Environment:** Next.js 14, Node 20

### Ingestion (Local launchd)
- **Schedule:** Daily at 9:00 PM (macOS launchd via `com.imprint.ingestion.plist`)
- **Agent:** `~/Library/LaunchAgents/com.imprint.ingestion.plist`
- **Scheduler:** Uses **launchd only** (no cron) to prevent race conditions
- **Advantage:** Catches up missed runs if Mac was asleep (unlike cron)
- **Logs:** `logs/ingestion_YYYYMMDD_HHMMSS.log`
- **Email summary:** Sent to `leland.speth@gmail.com` after each run
- **Check status:** `launchctl list | grep imprint`

---

## File Structure

```
imprint/
├── api/                          # Backend (FastAPI)
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings (Supabase, API keys)
│   ├── routers/
│   │   ├── chat.py               # Chat + streaming endpoint
│   │   ├── documents.py          # Document CRUD + approval
│   │   └── filters.py            # Get filter options
│   ├── services/
│   │   ├── rag_chain.py          # RAG pipeline logic
│   │   ├── retriever.py          # Supabase vector retriever
│   │   └── memory.py             # Conversation memory
│   └── utils.py                  # Database utilities
│
├── web/                          # Frontend (Next.js 14)
│   ├── app/
│   │   ├── page.tsx              # Chat interface (main page)
│   │   └── tag-approval/
│   │       └── page.tsx          # Tag approval interface
│   ├── components/
│   │   ├── ChatInterface.tsx     # Chat UI + streaming
│   │   ├── FilterSidebarModern.tsx  # Filter sidebar
│   │   ├── SourcesPanel.tsx      # Source citations
│   │   └── TagApproval.tsx       # Tag editing UI
│   └── lib/
│       └── types.ts              # TypeScript types
│
├── migrations/                   # SQL migrations
│   ├── 001_add_investing_schema.sql
│   ├── 002_update_rpc_sentiment.sql
│   ├── 003_add_document_type_catalyst.sql
│   ├── 004_update_rpc_final_schema.sql
│   └── 008_add_unique_source_url_constraint.sql
│
├── logs/                         # Ingestion logs (gitignored)
│
├── ingest_email.py               # Email ingestion pipeline
├── ingest_bookmark.py            # Bookmark ingestion pipeline
├── ingest_pdf.py                 # PDF ingestion pipeline
├── ingest_vision.py              # Vision ingestion pipeline
├── ingest_all.py                 # Master orchestrator
├── imprint_utils.py              # Shared utilities (cleaning, logging, email)
├── run_ingestion.sh              # launchd wrapper script
├── refresh_google_auth.py        # Tool: refresh Google OAuth tokens
│
├── Imprint_Tag_Dictionary.md     # Tag schema documentation
├── DEPLOYMENT.md                 # Deployment guide
├── SYSTEM_OVERVIEW.md            # This file
├── .env                          # Environment variables (gitignored)
├── token.json                    # Google OAuth token (gitignored)
├── credentials.json              # Google OAuth credentials (gitignored)
└── requirements.txt              # Python dependencies
```

---

## Admin Utilities

**Refresh Google OAuth tokens:**
```bash
python3 refresh_google_auth.py
```
Run this if Gmail/Drive ingestion fails with "Token has been expired or revoked" error. Opens browser for re-authentication.

**Run ingestion manually:**
```bash
python3 ingest_all.py
```
Runs all 4 pipelines and sends email summary.

**Run single pipeline:**
```bash
python3 ingest_email.py
python3 ingest_bookmark.py
python3 ingest_pdf.py
python3 ingest_vision.py
```

**Check launchd status:**
```bash
launchctl list | grep imprint
```
Shows if ingestion agent is loaded (status 0 = running).

---

## Configuration

### Environment Variables (`.env`)

**Database:**
- `DATABASE_URL` - Postgres connection string
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon key

**LLM APIs:**
- `OPENAI_API_KEY` - OpenAI API key (embeddings)
- `ANTHROPIC_API_KEY` - Anthropic API key (Claude)
- `PARALLEL_API_KEY` - Parallel API key (web scraping)

**Google APIs:**
- `GOOGLE_CREDENTIALS_PATH` - Path to Google service account JSON
- (Gmail and Drive APIs enabled)

**LangSmith (optional):**
- `LANGSMITH_API_KEY`
- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT=imprint-chatbot`

**CORS:**
- `CORS_ORIGINS` - Comma-separated list of allowed origins

---

## Key Features

### 1. Market-Linkable Tagging with Structured Outputs
- Entities use **tickers** for public companies (NVDA, AMZN)
- Topics are **specific mechanisms** (not vague labels like "AI")
- Sentiment captures directional tone
- Catalyst window captures timing signals
- **Pydantic + tool calling** ensures valid tags (no JSON parsing errors)

### 2. Automated Ingestion with Error Prevention
- 4 parallel pipelines ingest from different sources
- **Database-level duplicate prevention:** Unique constraint on `source_url` prevents race conditions
- Application-level duplicate detection by source_url AND title
- LLM-based content cleaning removes ads/tracking/chrome
- **Structured outputs** guarantee valid tags every time
- **Google OAuth auto-refresh** - tokens refresh automatically before API calls
- **Safari bookmarks access** - Python has Full Disk Access, Safari auto-quit before ingestion
- **Single scheduler** - launchd only (no cron) prevents concurrent runs
- launchd catches up missed runs if Mac was asleep

### 3. Tag Approval Workflow
- Ultra-compact UI for fast review
- Auto-save (no manual save button)
- Inline entity management
- Source deletion for rejected documents

### 4. Hybrid RAG with Anti-Hallucination
- **Hybrid retrieval:** Metadata filtering + semantic search (0.3 threshold)
- **Query analysis:** Auto-extracts metadata from questions
- **Document analysis:** LLM provides thesis utility for each result
- **Anti-hallucination safeguards:** Strict prompt prevents invented documents
- Streaming responses for low-latency UX
- Conversational memory (follow-up questions)
- Source citations with similarity scores and analysis

### 5. Thesis Notebook
- Drag-and-drop citations from chat into structured theses
- Multiple thesis management
- Section-based organization
- Export for presentation

### 6. Production-Ready with Observability
- Auto-deployment (GitHub → Vercel/Render)
- **LangSmith tracing** for full pipeline visibility
- User feedback collection (thumbs up/down)
- Error logging and monitoring
- Ingestion summaries via email
- Health checks and uptime monitoring

---

## Future Enhancements

**V1 Improvements:**
- [ ] Batch re-tagging of documents (admin interface)
- [ ] Export chat conversations to markdown
- [ ] Advanced filters (date range, weighting, catalyst window)
- [ ] Document similarity explorer
- [ ] Tag analytics dashboard (most common entities, sentiment breakdown)

**V2 - Market Integration:**
- [ ] Live stock prices for entity tickers
- [ ] Prediction market data (Polymarket, Kalshi, Metaculus)
- [ ] Price alerts + research correlation
- [ ] Portfolio tracking + research alignment
- [ ] Automated summaries by entity/sector

---

## Support

**Documentation:**
- `Imprint_Tag_Dictionary.md` - Tag schema and examples
- `DEPLOYMENT.md` - Deployment guide

**GitHub:**
- Repository: (Add repo URL here)
- Issues: Report bugs and feature requests

**Logs:**
- Backend: Render dashboard logs
- Frontend: Vercel dashboard logs
- Ingestion: `logs/ingestion_*.log` files

---

**Built with Claude Code**
