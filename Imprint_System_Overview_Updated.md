# Imprint -- System Overview

## Objective

Build a personal decision-support system that combines: - Long-form
research (articles, newsletters, whitepapers, PDFs) - Structured market
signals (prediction markets + stock prices) -- V2

The system should: - Organize information by thesis, topic, sector, and
entities - Surface relevant context quickly - Detect meaningful trend
shifts - Generate automated summaries - Remain architecturally clean and
scalable

------------------------------------------------------------------------

# V1 -- Research Knowledge Base

## Purpose

Create a centralized, searchable library of: - Newsletters - Articles -
Whitepapers - PDFs - Long-form research

This layer answers:

> What have I read about this topic, and how does it fit my thesis
> framework?

------------------------------------------------------------------------

## Inputs

### 1) Email newsletters (Gmail)

-   Source of truth: Gmail label (e.g., `Imprint`)
-   You forward or label newsletters you care about

### 2) Web articles (Safari bookmarks)

-   Source of truth: Safari bookmark folder (e.g., `Imprint`)
-   URLs saved on desktop sync to phone via iCloud Safari

### 3) PDFs + images (Google Drive)

-   Source of truth: Google Drive folder (e.g., `Imprint/Inbox`)
-   Includes PDFs (whitepapers, saved articles) and images
    (charts/screenshots)

All content flows into a single ingestion process.

------------------------------------------------------------------------

## Process (V1)

For each new item (email / URL / file):

1.  Extract text
2.  Extract metadata (best-effort):
    -   Title
    -   Author (nullable)
    -   Publisher / Source
3.  **LLM Tag Proposal (best-effort):** The parser attempts to infer
    tags directly from the document content, including:
    -   Entities mentioned (highest confidence)
    -   Topic (best guess)
    -   Sector (best guess)
    -   Thesis (suggested hypothesis)
    -   Optional: document type, angle, catalyst window, and published
        date (when inferable)
4.  **Human-in-the-loop tag review:**
    -   After ingestion, the system presents the proposed tags
    -   You approve, modify, or add additional tags
    -   The final approved tags are stored as canonical metadata
5.  Store raw text + metadata + approved tags
6.  Generate embeddings
7.  Enable hybrid search:
    -   Metadata filtering
    -   Semantic similarity

------------------------------------------------------------------------

## Tags (V1)

### Required

-   Thesis
-   Topic
-   Sector
-   Entities

### Dates

-   Published date (optional)
-   Ingested date (auto)

### Optional

-   Angle: deep_dive \| market_map \| technical \| earnings_notes \|
    opinion \| case_study \| macro_view
-   Conviction: 1--5 scale
-   Catalyst window: 0--3m \| 3--12m \| 12m+ \| structural
-   Notes

------------------------------------------------------------------------

## Core Table (High-Level)

### imprint_documents

-   id
-   title
-   author (nullable)
-   content
-   source_type (email \| url \| pdf \| image)
-   source
-   source_url
-   published_date
-   ingested_date
-   thesis
-   topic
-   sector
-   entities
-   angle
-   conviction
-   catalyst_window
-   notes
-   embedding

------------------------------------------------------------------------

## Retrieval Strategy

Imprint uses **metadata tags for pre-filtering** (thesis, topic, sector,
entities, and dates) before running vector similarity search over the
filtered subset.

Embeddings allow semantic retrieval across long-form research while
metadata ensures queries remain structured and precise.

A common implementation pattern is:

-   **Postgres + pgvector** for storing embeddings alongside metadata
-   An embedding model such as **OpenAI `text-embedding-3-large`**

This is a suggested baseline rather than a fixed requirement, and the
system architecture is designed to remain flexible regarding embedding
providers or vector storage solutions.

------------------------------------------------------------------------

# V2 -- Signals Layer

## Purpose

Add structured, live data to complement research.

This layer answers:

> What is changing in the real world that relates to my theses?

------------------------------------------------------------------------

## Data Source 1 -- Prediction Markets (Polymarket via the CLI tool)

### Objective

Track: - Implied probabilities - Volume spikes - Liquidity changes -
Rapid repricing events

Focus is on **deltas and momentum**, not archival completeness.

### Table: imprint_prediction_markets

-   market_id
-   question
-   probability
-   probability_change_24h
-   volume
-   liquidity
-   timestamp
-   mapped_topic
-   mapped_sector
-   mapped_entities

------------------------------------------------------------------------

## Data Source 2 -- Stock Price API

### Objective

Track: - Price momentum - Volatility spikes - Sector rotation - Relative
strength

This layer provides contextual awareness rather than trading automation.

### Table: imprint_market_prices

-   ticker
-   date
-   close
-   volume
-   7d_change
-   30d_change
-   volatility_metric
-   mapped_sector
-   mapped_topic
-   mapped_entities

------------------------------------------------------------------------

# System Architecture (High Level)

Layer 1 -- Research Library (V1)\
→ Tagged long-form content\
→ Embedded + searchable

Layer 2 -- Structured Signals (V2)\
→ Prediction markets\
→ Stock prices\
→ Trend computation

Layer 3 -- Trend Engine (V2)\
→ Daily data pull\
→ Delta computation\
→ Topic mapping\
→ Ranked summaries\
→ Digest output (email / Slack)

------------------------------------------------------------------------

# Design Principles

-   One ingestion pipeline
-   Tags are the backbone
-   Signals must map to taxonomy
-   Focus on change, not static values
-   Build modularly: V1 first, V2 second

------------------------------------------------------------------------

# Final Outcome

A unified personal investment system that combines:

-   Context (what you've studied)
-   Signals (what is moving)
-   Structure (how it maps to your theses)
-   Automation (trend detection + summaries)
