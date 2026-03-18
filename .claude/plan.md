# Implementation Plan: Feedback & Enhanced Document Display

## Feature 1: Thumbs Up/Down for LangSmith Evals

### Overview
Add feedback buttons under each assistant response to capture user ratings and send them to LangSmith for building eval datasets.

### Architecture

```
User clicks 👍/👎 → Frontend sends run_id + score → API endpoint → LangSmith Feedback API
```

### Implementation Steps

#### 1.1 Backend: Track and Return Run IDs
**File: `api/routers/chat.py`**
- Modify the trace context to capture the run_id
- Include `run_id` in the SSE "done" event so frontend can reference it for feedback

```python
# In event_stream(), after trace completes:
yield {"type": "done", "full_response": full_response, "run_id": run_id}
```

#### 1.2 Backend: Create Feedback Endpoint
**File: `api/routers/chat.py`**
- New POST endpoint `/api/feedback`
- Accepts: `run_id`, `score` (1 for thumbs up, 0 for thumbs down), optional `comment`
- Sends feedback to LangSmith using their SDK

```python
from langsmith import Client

@router.post("/api/feedback")
async def submit_feedback(run_id: str, score: int, comment: str = None):
    client = Client()
    client.create_feedback(run_id, key="user_rating", score=score, comment=comment)
```

#### 1.3 Frontend: Add Feedback Buttons
**File: `web/components/thesis/ChatSidebar.tsx`**
- Store `run_id` in message state
- Add thumbs up/down buttons below each assistant message
- Call feedback API on click
- Show visual confirmation (button highlights, or checkmark)

#### 1.4 Frontend: API Call
**File: `web/lib/api.ts`**
- Add `submitFeedback(runId: string, score: number)` function

### Files to Modify
1. `api/routers/chat.py` - Add run_id tracking + feedback endpoint
2. `web/lib/types.ts` - Add run_id to StreamEvent
3. `web/lib/api.ts` - Add submitFeedback function
4. `web/components/thesis/ChatSidebar.tsx` - Add feedback UI

---

## Feature 2: Enhanced Document Return Format

### Overview
Instead of showing raw document metadata, display structured information that's immediately useful for thesis development:
- **Summary**: Concise takeaway from the document
- **Key Excerpt**: Most relevant quote/passage for this query
- **Thesis Utility**: How this could support a thesis (bullish/bearish signal, risk factor, etc.)

### Architecture

```
Retrieved Docs → LLM Analysis Call → Structured Document Cards
```

### Implementation Steps

#### 2.1 Backend: Add Document Analysis Chain
**File: `api/services/rag_chain.py`**
- After retrieving documents, run a secondary LLM call to analyze each document
- Use structured output to get consistent format

```python
class DocumentAnalysis(BaseModel):
    summary: str = Field(description="2-3 sentence summary of key insight")
    key_excerpt: str = Field(description="Most relevant direct quote (50-100 words)")
    thesis_signal: Literal["bullish", "bearish", "neutral", "mixed"]
    thesis_utility: str = Field(description="How this could be used in an investment thesis")
```

#### 2.2 Backend: Analysis Prompt
```
For each document, analyze:
1. Summary: What is the key insight relevant to the user's query?
2. Key Excerpt: What's the most important direct quote?
3. Thesis Signal: Is this bullish, bearish, neutral, or mixed for the topic?
4. Thesis Utility: How could an investor use this information?

User Query: {question}
Documents: {documents}
```

#### 2.3 Backend: Modify Sources Event
- Currently yields: `{"type": "sources", "documents": [raw_metadata]}`
- New format: `{"type": "sources", "documents": [enhanced_metadata]}`
- Each document now includes `analysis: {summary, key_excerpt, thesis_signal, thesis_utility}`

#### 2.4 Frontend: Update SidebarSourceCard
**File: `web/components/thesis/SidebarSourceCard.tsx`**
- Display new structured fields
- Add visual indicator for thesis signal (green=bullish, red=bearish, gray=neutral)
- Show key excerpt in expandable section
- Show thesis utility text

#### 2.5 Performance Consideration
- Single batched LLM call for all docs (not per-doc) to minimize latency
- Could make this optional/toggleable if speed is concern
- Alternative: Stream the analysis after main response

### Files to Modify
1. `api/services/rag_chain.py` - Add document analysis chain
2. `web/lib/types.ts` - Add analysis fields to Document type
3. `web/components/thesis/SidebarSourceCard.tsx` - Enhanced display

---

## Execution Order

1. **Feature 1 first** (simpler, fewer files)
   - 1.1 Backend run_id tracking
   - 1.2 Feedback endpoint
   - 1.3 Frontend types + API
   - 1.4 Feedback buttons UI

2. **Feature 2 second** (more complex)
   - 2.1 DocumentAnalysis model
   - 2.2 Analysis chain + prompt
   - 2.3 Backend integration
   - 2.4 Frontend display updates

---

## Estimated Complexity

| Task | Files Changed | Complexity |
|------|--------------|------------|
| Feature 1: Run ID tracking | 1 | Low |
| Feature 1: Feedback endpoint | 1 | Low |
| Feature 1: Frontend feedback | 3 | Medium |
| Feature 2: Document analysis chain | 1 | Medium |
| Feature 2: Frontend display | 2 | Medium |

**Total: 5 files, ~200-300 lines of code**
