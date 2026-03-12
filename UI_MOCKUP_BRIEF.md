# Imprint UI Overview for Mockups

## What is Imprint?

Imprint is a personal research knowledge base for investment research. Users ingest documents (emails, bookmarks, PDFs) which get auto-tagged with metadata (topic, sector, entities, sentiment, etc.). They can then chat with their research library using AI.

---

## Current App Structure

The app has **2 main tabs:**

### 1. Chat Tab (Main Page)
**Layout:** 3-column layout
- **Left:** Filter Sidebar (320px wide)
- **Center:** Chat Interface (flexible width)
- **Right:** Sources Panel (shows when sources are available)

### 2. Tag Approval Tab
**Layout:** 2-column layout
- **Left:** Document List (384px wide) - scrollable list of pending documents
- **Right:** Document Detail - shows selected document with editable tags

---

## Chat Tab - Detailed Breakdown

### Left Sidebar: Filters (320px)
**Sticky header:**
- "Filters" title with active count badge
- "Clear all" button

**Collapsible sections** (each can expand/collapse):
1. **Sector** - Checkboxes for: Infra, Software, Semiconductors, Security, Fintech, Healthcare, Energy, Industrial, Consumer, Macro, Government, Geopolitics
2. **Sentiment** - Checkboxes for: bullish, bearish, neutral, mixed
3. **Entities** - Search input + scrollable checkbox list (companies/people like "NVDA", "OpenAI", "Jerome Powell")
4. **Catalyst Window** - Checkboxes for: immediate, near_term, medium_term, long_term, structural
5. **Weighting** - Checkboxes for: ⭐ 1, ⭐ 2, ⭐ 3, ⭐ 4, ⭐ 5

**Visual style:**
- White background on gray-50 sidebar
- Each section is white card with rounded corners
- Blue-100 badges show active filter count
- Hover states on checkboxes

### Center: Chat Interface
**Top bar (sticky):**
- "Imprint" logo/title
- Model selector dropdown (Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Opus 4.6, GPT-4o)
- Session actions (clear conversation)

**Chat area:**
- Message history (scrollable)
- User messages: right-aligned, blue background
- Assistant messages: left-aligned, white background with border
- Source citations shown inline with message (small cards showing document title + similarity score)

**Bottom input bar (sticky):**
- Large text input with placeholder "Ask about your research..."
- Send button (blue, right side)
- Character count or status indicators

### Right: Sources Panel (shows conditionally)
**Appears when:** Assistant responds with sources

**Content:**
- "Sources" header
- List of document cards showing:
  - Document title
  - Summary (1 sentence)
  - Metadata badges: Sector, Sentiment, Document Type
  - Similarity score (percentage)
  - Click to open full document

---

## Tag Approval Tab - Detailed Breakdown

### Left: Document List (384px)
**Header (sticky):**
- "Pending Review (N)" count

**Document cards:**
- Title (2 line clamp)
- Source type + date (small gray text)
- Tag preview badges: Sector, Sentiment
- Selected state: blue-50 background

### Right: Document Detail
**Header:**
- Document title (large, bold)
- Save status indicator (Saving.../✓ Saved/✗ Error)

**Tag editor (ultra-compact 3-column grid):**
Row 1: Topic | Sector | Sentiment
Row 2: Type | Catalyst | Weighting (1-5 buttons)

**Full width sections:**
- Entities (tag chips with × remove, + add input)
- Summary (2-row textarea)

**Content preview:**
- Collapsed view showing first 2000 chars

**Action buttons (sticky bottom):**
- Green "✓ Approve" button (full width left)
- Red "✗ Reject & Delete Source" button (full width right)

---

## Proposed: Thesis Tab (New)

### Purpose
A place to define and manage investment theses. Each thesis acts as a high-level organizing concept that documents can be tagged with.

### Layout Ideas

**Option A: List + Detail (like Tag Approval)**
- Left: List of theses
- Right: Thesis detail/editor

**Option B: Kanban Board**
- Columns for thesis stages (Developing, Active, Archived)
- Cards for each thesis

**Option C: Table View**
- Sortable table with columns: Name, Description, Document Count, Last Updated

### Thesis Data Model (Proposed)
```
Thesis:
- Name (e.g., "AI Infrastructure Build-out")
- Description (2-3 sentences)
- Key Entities (array)
- Related Sectors (array)
- Status (developing, active, archived)
- Document Count (auto-calculated)
- Created Date
- Last Updated
```

### Key Features Needed
1. **Create thesis** - Modal or inline form
2. **Tag documents with thesis** - Dropdown in Tag Approval
3. **View thesis documents** - Click thesis → see all related docs
4. **Thesis analytics** - Sentiment breakdown, entity frequency, timeline

### Integration with Chat
- Filter by thesis in sidebar
- Ask questions scoped to specific thesis
- "Show me bearish takes on AI Infrastructure thesis"

---

## Visual Design System

**Colors:**
- Primary Blue: #2563eb (blue-600)
- Light Blue: #dbeafe (blue-100)
- Gray Background: #f9fafb (gray-50)
- White: #ffffff
- Green (approve): #16a34a (green-600)
- Red (reject): #dc2626 (red-600)

**Typography:**
- Headers: font-semibold, text-lg or text-2xl
- Body: text-sm or text-base
- Small labels: text-xs, text-gray-600

**Spacing:**
- Compact padding: p-2, p-3
- Standard padding: p-4
- Section gaps: space-y-4
- Inline gaps: gap-2

**Components:**
- Rounded corners: rounded-lg (8px)
- Borders: border-gray-200
- Shadows: minimal (border-based design, not heavy shadows)
- Badges: rounded-full, small padding, colored backgrounds

---

## User Flows

### Flow 1: Ingest → Review → Chat
1. User saves bookmark to Safari "Imprint" folder
2. Cron ingests document at 9pm, auto-tags it
3. User opens Tag Approval tab
4. User edits/approves tags
5. Document becomes searchable in Chat
6. User asks questions, gets answers with citations

### Flow 2: Filtered Research
1. User opens Chat tab
2. User selects filters (e.g., Sector: Semiconductors, Sentiment: bullish)
3. User asks "What are the growth drivers?"
4. System only searches documents matching filters
5. User gets focused, relevant answers

### Flow 3: Thesis Management (Proposed)
1. User creates thesis "AI Infrastructure Build-out"
2. User adds key entities (NVDA, AMZN, MSFT)
3. User tags relevant documents with this thesis in Tag Approval
4. User opens Thesis tab → sees all documents, sentiment breakdown
5. User asks thesis-scoped questions in Chat

---

## Technical Notes for Mockups

**Responsive behavior:**
- Desktop: 3-column chat layout
- Tablet: Filters collapse to hamburger menu
- Mobile: Full-width chat, filters as modal

**Interactive states:**
- Hover: slight background change (gray-50)
- Active/Selected: blue-50 background
- Disabled: gray-300 text, cursor-not-allowed
- Loading: spinner or skeleton UI

**Empty states:**
- No documents: "No documents pending review"
- No sources: Sources panel hidden
- No filters active: "Select filters to narrow results"
- No search results: "No entities match 'search term'"

**Data display:**
- Truncate long text with ellipsis
- Show first N items with "Show more" expand
- Format dates as "Mar 10, 2026"
- Show counts in badges

---

## Key Questions for Thesis Tab Mockup

1. **Layout preference:** List+Detail vs Kanban vs Table?
2. **Thesis creation:** Modal popup vs inline form vs dedicated page?
3. **Document tagging:** Add thesis dropdown to Tag Approval? Or bulk tag from Thesis view?
4. **Analytics view:** What metrics matter most? (sentiment breakdown, entity frequency, timeline, document count)
5. **Integration placement:** New top-level tab? Or nested under Chat/Tag Approval?

---

## Mockup Deliverables Needed

**For Thesis Tab:**
1. **Thesis List View** - How theses are displayed
2. **Thesis Detail/Editor** - Creating/editing a thesis
3. **Thesis Analytics Dashboard** - Metrics and insights for a thesis
4. **Document Tagging UI** - How to assign documents to thesis (in Tag Approval)
5. **Thesis Filter** - How thesis appears in Chat sidebar filters

**Visual consistency:**
- Match existing color scheme (blue/gray)
- Use same spacing/typography
- Maintain compact, information-dense design
- Keep collapsible sections pattern
