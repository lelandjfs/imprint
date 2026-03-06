# Imprint Project Log

**Last Updated:** 2025-03-03

---

## Current Focus: V1 - Research Knowledge Base

Build a searchable library of research content with tagging and semantic search.

### Ingestion Sources (4 pipelines)
- [x] **Email** — Gmail `Imprint` label — simple, single agent
- [x] **Bookmark** — Safari `Imprint` folder — fetch URL, extract, single agent
- [x] **PDF** — Drive `Imprint/` root — text extraction, LLM cleaning
- [x] **Vision** — Drive `Imprint/Vision/` — GPT-4o vision for charts/screenshots

### Stack Decisions
- **Database:** Supabase (Postgres + pgvector)
- **Embeddings:** OpenAI `text-embedding-3-large` @ 1536 dimensions
- **Hosting:** Supabase (free tier)

### Credentials
- `credentials.json` — Google OAuth client (Gmail + Drive)
- `token.json` — Auth token (auto-refreshes)
- `.env` — Supabase connection strings (do not commit)

---

## Active Work

_None - V1 ingestion complete._

---

## Files

| File | Purpose |
|------|---------|
| `ingest_email.py` | Gmail newsletter ingestion |
| `ingest_bookmark.py` | Safari bookmark ingestion |
| `ingest_pdf.py` | Google Drive PDF ingestion |
| `ingest_vision.py` | GPT-4o vision for charts/screenshots |
| `ingest_all.py` | Master script - runs all + sends email |
| `review.py` | CLI for reviewing/approving tags |
| `imprint_utils.py` | Shared utilities (logging, email, cleaning) |

---

## Decisions Log

| Date | Decision | Notes |
|------|----------|-------|
| 2025-03-03 | V1 only for now | V2 (signals) deferred |
| 2025-03-03 | text-embedding-3-large | Cost negligible at scale |
| 2025-03-03 | Supabase over local | Enables future mobile querying |
| 2025-03-03 | 1536 dimensions | Supabase pgvector caps at 2000 |
| 2025-03-03 | Claude for tagging, OpenAI for embeddings | Best of both |
| 2025-03-03 | Email notifications after ingestion | Summary sent to Gmail |
| 2025-03-03 | pending_review status | Docs await approval before active |
| 2025-03-05 | Parallel Search as fallback | Better at bypassing bot detection than Jina |

---

## Completed

| Date | Item |
|------|------|
| 2025-03-03 | Verified access to all 3 ingestion sources |
| 2025-03-03 | Set up Supabase with pgvector, created imprint_documents table |
| 2025-03-03 | Built email ingestion pipeline |
| 2025-03-03 | Built bookmark ingestion pipeline (handles Twitter/X + articles) |
| 2025-03-03 | Built PDF ingestion pipeline |
| 2025-03-03 | Added ingestion_log table for tracking failures/restricted |
| 2025-03-03 | Built master ingestion script with email notification |
| 2025-03-03 | Tested all pipelines with sample content |
| 2025-03-04 | Added ad/tracking content cleaner (40% reduction on newsletters) |
| 2025-03-04 | Built vision pipeline with GPT-4o (extracts charts/graphs from PDFs) |
| 2025-03-05 | Added Parallel Search API fallback for bot-protected sites (Seeking Alpha, etc.) |
| 2025-03-06 | Pushed to GitHub (lelandjfs/imprint) with .gitignore for credentials |

---

## Future Work

**Infrastructure:**
- [x] Push to GitHub — https://github.com/lelandjfs/imprint — DONE
- [x] Add .gitignore for credentials (.env, token.json, credentials.json) — DONE
- [ ] Daily cron job or GitHub Action to check all sources for new content

**Ingestion Enhancements:**
- [x] Vision pipeline (Drive `Imprint/Vision/` folder) — GPT-4o for charts/screenshots — DONE
- [x] Parse out ad content from newsletters/articles — DONE
- [x] Parallel Search fallback for bot-protected sites — DONE

**Query & Review:**
- [ ] Chatbot for querying knowledge base
- [ ] Web UI with pending tags tab
- [ ] Reply-to-approve email flow
