-- Migration 009: Create Markets Schema
-- Purpose: Add prediction markets from Kalshi and Polymarket with thesis alignment

-- Core market metadata (cached from APIs)
CREATE TABLE IF NOT EXISTS markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- External identifiers
    platform TEXT NOT NULL CHECK (platform IN ('kalshi', 'polymarket')),
    external_id TEXT NOT NULL,

    -- Market metadata
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    end_date TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('active', 'closed', 'resolved')),

    -- Resolution info
    outcome TEXT,
    resolved_at TIMESTAMPTZ,

    -- For vector search (market title + description embedding)
    embedding VECTOR(1536),

    -- URLs
    market_url TEXT NOT NULL,

    -- Metadata
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(platform, external_id)
);

-- Price history: OHLC data for charts
CREATE TABLE IF NOT EXISTS market_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,

    timestamp TIMESTAMPTZ NOT NULL,
    price DECIMAL(5,4) NOT NULL,  -- 0.0000 to 1.0000 (probability)
    volume DECIMAL(20,2),  -- In dollars

    UNIQUE(market_id, timestamp)
);

-- Current prices: Latest prices (fetched on page load, short TTL)
CREATE TABLE IF NOT EXISTS market_current_prices (
    market_id UUID PRIMARY KEY REFERENCES markets(id) ON DELETE CASCADE,

    yes_price DECIMAL(5,4) NOT NULL,
    no_price DECIMAL(5,4),
    volume_24h DECIMAL(20,2),
    open_interest DECIMAL(20,2),

    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- Thesis-market alignments: Pre-computed LLM scores
CREATE TABLE IF NOT EXISTS thesis_market_alignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    market_id UUID NOT NULL REFERENCES markets(id) ON DELETE CASCADE,

    -- LLM-generated alignment data
    alignment_score DECIMAL(3,2) NOT NULL,  -- 0.00 to 1.00
    alignment_direction TEXT CHECK (alignment_direction IN ('supports', 'contradicts', 'neutral')),
    reasoning TEXT NOT NULL,

    -- Metadata
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    model_used TEXT DEFAULT 'claude-sonnet-4-5-20250929',

    UNIQUE(thesis_id, market_id)
);

-- Global relevance scores: For "Explore" tab (all theses combined)
CREATE TABLE IF NOT EXISTS market_global_relevance (
    market_id UUID PRIMARY KEY REFERENCES markets(id) ON DELETE CASCADE,

    relevance_score DECIMAL(3,2) NOT NULL,  -- 0.00 to 1.00
    top_thesis_ids UUID[],  -- Top 3 related theses
    summary TEXT,  -- Why this market is relevant across theses

    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_markets_platform ON markets(platform);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);
CREATE INDEX IF NOT EXISTS idx_markets_embedding ON markets USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_price_history_market_time ON market_price_history(market_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_current_prices_fetched ON market_current_prices(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_alignments_thesis ON thesis_market_alignments(thesis_id, alignment_score DESC);
CREATE INDEX IF NOT EXISTS idx_alignments_market ON thesis_market_alignments(market_id);
CREATE INDEX IF NOT EXISTS idx_global_relevance_score ON market_global_relevance(relevance_score DESC);
