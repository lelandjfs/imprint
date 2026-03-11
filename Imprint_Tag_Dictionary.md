# Imprint – Tag Schema (V1)

This document defines the core tagging structure for documents ingested into **Imprint**.

Tags are designed to remain **simple, consistent, and market-linkable**.

The goal is not to perfectly structure every idea, but to provide enough metadata to connect research to **entities, sectors, and markets**.

---

## Core Tags

### 1. `topic`

**Definition**

The primary subject or mechanism the document discusses.

A topic describes **what the article is about**, not the investment opinion.

Topics should be **specific but reusable** across many documents.

**Format**

```
snake_case
```

**Examples**

```
ai_infrastructure
hyperscaler_capex
china_export_controls
trade_policy
consumer_credit
enterprise_ai_adoption
semiconductor_supply_chain
defense_spending
interest_rates
energy_grid_modernization
```

**Good topic rule**

Prefer **mechanism or domain-level descriptions** rather than broad labels.

Good:
```
gpu_supply_constraints
ai_inference_economics
```

Bad:
```
ai
technology
markets
```

---

### 2. `entities`

**Definition**

Companies, organizations, people, or products referenced in the document.

Entities create the main bridge between research and **markets**.

They are the most important tag for linking to:
- public equities
- private companies
- government actors
- prediction markets

**Format**

Array of values.

```json
["NVDA", "OpenAI", "Jerome Powell"]
```

**Entity formatting rules**

Public companies → ticker preferred
```
NVDA
AMZN
MSFT
TSLA
```

Private companies → canonical company name
```
OpenAI
Anthropic
Databricks
Anduril
```

People → full name
```
Sam Altman
Jerome Powell
Donald Trump
```

Organizations / institutions
```
Department of Defense
Federal Reserve
European Commission
```

---

### 3. `sector`

**Definition**

High-level classification describing the economic or industry area affected.

Sectors provide **broad filtering** across the research library.

Keep the list **tight and stable**.

**Recommended values** (examples, not exhaustive)

```
Infra
Software
Semiconductors
Security
Fintech
Healthcare
Energy
Industrial
Consumer
Macro
Government
Geopolitics
```

**Examples**

```
sector: Semiconductors
sector: Government
sector: Infra
sector: Fintech
```

---

### 4. `sentiment`

**Definition**

The overall directional tone of the document toward the topic or key entities.

Sentiment is **not truth** – it reflects the author's perspective.

Contradictory documents are expected and useful.

**Allowed values**

```
bullish
bearish
neutral
mixed
```

**Examples**

Article arguing hyperscaler spending will increase demand for GPUs:
```
sentiment: bullish
```

Article warning that Amazon is overspending on AI infrastructure:
```
sentiment: bearish
entities: ["AMZN"]
```

Article presenting both positive and negative arguments:
```
sentiment: mixed
```

---

### 5. `summary`

**Definition**

A short one-sentence explanation of the document's key takeaway.

This should capture **the core idea or signal** in the article.

The summary is written **after ingestion** and helps with:
- quick scanning
- search results
- digest generation
- pattern detection across documents

**Guidelines**

- One sentence
- Clear and direct
- Focus on the mechanism or implication

**Examples**

```
"Hyperscaler AI spending is accelerating faster than expected, creating near-term demand for Nvidia GPUs."

"Export controls on advanced chips could restrict Nvidia and AMD sales to China."

"Defense AI contracts are shifting toward private startups rather than traditional contractors."

"Enterprise AI adoption is being slowed by data governance and infrastructure constraints."
```

---

### 6. `document_type`

**Definition**

The format or style of the document.

This helps filter by content type when researching or building digests.

**Allowed values**

```
article
blog
whitepaper
transcript
presentation
earnings
report
image
other
```

**Examples**

```
document_type: article
document_type: blog
document_type: earnings
document_type: report
```

**Guidelines**

- `article` - News articles, magazine pieces, journalism
- `blog` - Blog posts, newsletters, personal commentary, Substack posts
- `whitepaper` - Technical whitepapers, research papers, academic publications
- `transcript` - Interview transcripts, podcast transcripts, conference talks
- `presentation` - Slide decks, investor presentations, pitch decks
- `earnings` - Earnings call transcripts, earnings releases, financial results
- `report` - Research reports from banks/analysts, industry reports, formal analyses
- `image` - Screenshots, charts, infographics, diagrams
- `other` - Everything else

---

### 7. `catalyst_window` (optional)

**Definition**

The expected time horizon for the idea or signal to materialize.

This is **optional** and only applies when the document implies a specific timing.

**Allowed values**

```
immediate
near_term
medium_term
long_term
structural
```

**Examples**

Article about upcoming earnings report:
```
catalyst_window: immediate
```

Article about AI regulation expected in 12-18 months:
```
catalyst_window: medium_term
```

Article about long-term shift in supply chains:
```
catalyst_window: structural
```

**Guidelines**

- `immediate` - Days to weeks (earnings, announcements, events)
- `near_term` - 1-6 months (upcoming policy changes, product launches)
- `medium_term` - 6-18 months (regulatory cycles, infrastructure buildouts)
- `long_term` - 18 months+ (demographic shifts, technology adoption)
- `structural` - No specific timeline, ongoing trend (deglobalization, AI transformation)

Leave blank if the document doesn't imply a specific timing.

---

## Example Document

Example document entry in Imprint:

```yaml
topic: ai_infrastructure
sector: Semiconductors

entities:
- NVDA
- AMZN
- MSFT

sentiment: bullish

document_type: article

catalyst_window: near_term

summary:
"Hyperscaler capital spending on AI data centers is accelerating, driving continued demand for Nvidia GPUs."

weighting: 4
```
