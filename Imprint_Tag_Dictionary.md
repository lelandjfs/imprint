# Imprint – Tag Dictionary (V1)

This document defines the tagging conventions for Imprint so retrieval stays consistent as the library scales.

---

## Core Principles

- **Tag once, reuse everywhere.** Prefer a smaller, stable set of tags over many bespoke ones.
- **Entities are the join key.** Use consistent entity naming so V2 (prices/markets) can map cleanly.
- **Thesis ≠ Topic.** Thesis is the *lens*. Topic is the *subject*.
- **LLM proposes; you approve.** Treat suggested tags as drafts.

---

## Required Fields

### 1) `thesis`
**Definition:** Your investment lens / structural belief the document supports or challenges.

**Format:** `snake_case` (lowercase, no punctuation).  
**Cardinality:** Prefer **one primary thesis** per doc (you can add a secondary in notes if needed).

**Recommended starter set (edit freely):**
- `ai_cost_compression`
- `capital_cycle`
- `platform_consolidation`
- `workflow_automation`
- `regulatory_tailwind`
- `distribution_shifts`
- `pricing_power`
- `security_as_default`
- `data_gravity`
- `verticalization`

**Examples:**
- A GPU supply chain note supporting overbuild cycles → `capital_cycle`
- A piece on AI reducing software labor cost → `ai_cost_compression`

---

### 2) `topic`
**Definition:** What the piece is concretely about (narrower than thesis).

**Format:** `snake_case` (lowercase).  
**Cardinality:** One primary topic; add additional topics only if truly necessary.

**Topic conventions (recommended):**
- Prefer *mechanism- or domain-specific* topics:
  - `ai_inference_economics` (good)
  - `gpu_supply_constraints` (good)
  - `hyperscaler_capex` (good)
  - `vertical_saas_pricing` (good)
- Avoid vague topics:
  - `ai` (too broad)
  - `software` (too broad)

**Example topics (seed list):**
- `ai_inference_economics`
- `ai_agents_enterprise`
- `hyperscaler_capex`
- `gpu_supply_constraints`
- `semiconductor_supply_chain`
- `enterprise_procurement`
- `security_platforms`
- `devtools_adoption`
- `fintech_risk_models`
- `payments_networks`
- `healthcare_admin_workflows`
- `energy_grid_modernization`
- `industrial_automation`

---

### 3) `sector`
**Definition:** Broad bucket for quick filtering.

**Format:** Title Case (stable names).  
**Allowed values (keep tight):**
- `Infra`
- `Security`
- `Fintech`
- `Healthcare`
- `Consumer`
- `Energy`
- `Industrial`
- `Macro`

**Rule:** If you’re unsure, pick the closest primary sector and note the nuance in `notes`.

---

### 4) `entities`
**Definition:** Companies / tickers / people / products referenced.

**Format:** Array of strings.  
**Cardinality:** 0+ (but aim to include at least the key one).

#### Entity formatting rules
- **Public companies:** use **ticker** when clear (`NVDA`, `MSFT`, `AMZN`).  
- **Private companies:** use canonical brand name (`OpenAI`, `Anthropic`, `Databricks`).  
- **People:** `First Last` (`Sam Altman`).  
- **Products:** `Company:Product` (`Meta:Ray-Ban`, `OpenAI:ChatGPT`).

#### Canonicalization guidance
- Avoid duplicates: don’t include both `Nvidia` and `NVDA`. Pick one (prefer ticker for public).
- No `$` prefix in canonical entities (use `NVDA`, not `$NVDA`).

---

## Dates

### `published_date` (optional)
- Use when known (especially for older pieces).
- If unknown, leave blank.

### `ingested_date` (auto)
- Set by the system at ingestion time.
- Not manually edited.

---

## Optional Fields (High Leverage)

### `document_type` (optional but recommended)
**Definition:** What the artifact is structurally.

**Allowed values:**
- `newsletter`
- `article`
- `whitepaper`
- `research_report`
- `earnings_call`
- `tweet_thread`
- `internal_note`

---

### `angle` (optional)
**Definition:** What kind of analysis/thinking it represents.

**Allowed values:**
- `deep_dive`
- `market_map`
- `technical`
- `earnings_notes`
- `opinion`
- `case_study`
- `macro_view`

---

### `conviction` (optional)
**Definition:** Your confidence that the content is decision-relevant.

**Scale:** 1–5  
- 1 = weak / speculative
- 3 = solid / plausible
- 5 = high conviction / repeatedly validated

---

### `catalyst_window` (optional)
**Definition:** When you expect the idea to matter.

**Allowed values:**
- `0-3m`
- `3-12m`
- `12m+`
- `structural`

**Rule of thumb:**
- If it’s an event → `0-3m`
- If it’s an adoption curve → `3-12m` or `12m+`
- If it’s a regime shift → `structural`

---

### `source_quality` (optional, recommended)
**Definition:** How trustworthy / rigorous the source is (not your conviction in the thesis).

**Scale:** 1–5

---

### `status` (optional, recommended)
**Definition:** Lifecycle of the idea in your system.

**Allowed values:**
- `active`
- `watching`
- `invalidated`
- `archived`

---

### `summary` (optional, strongly recommended)
**Definition:** One-sentence takeaway (forced clarity).

**Guideline:** If you can’t write it, you probably don’t understand the point yet.

---

### `notes` (optional)
Free text: why you saved it, what you believe, what you disagree with, follow-ups.

---

## Suggested Review Flow (Post-Ingestion)

1. Ingest extracts text + metadata.
2. LLM proposes: thesis/topic/sector/entities + optional fields.
3. You:
   - **Approve**
   - **Edit**
   - **Add missing entities**
   - Add `summary` + `conviction` when useful

---

## Examples

### Example A: AI infra capex note
- thesis: `capital_cycle`
- topic: `hyperscaler_capex`
- sector: `Infra`
- entities: [`MSFT`, `AMZN`, `GOOGL`, `NVDA`]
- angle: `deep_dive`
- catalyst_window: `3-12m`
- conviction: 4
- summary: “Hyperscaler capex is accelerating, but second-order supply constraints may flip margins across the stack.”

### Example B: Security consolidation
- thesis: `platform_consolidation`
- topic: `security_platforms`
- sector: `Security`
- entities: [`CRWD`, `PANW`, `SentinelOne`]
- angle: `market_map`
- catalyst_window: `12m+`
- conviction: 3
- summary: “Security buyers are consolidating vendors; platform suites are winning budget share.”

---
