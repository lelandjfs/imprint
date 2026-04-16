-- Enable Row-Level Security on all tables
-- Uses service_role bypass for backend access (personal app)
-- This stops Supabase security warnings while keeping everything working

-- Documents table
ALTER TABLE imprint_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON imprint_documents FOR ALL TO service_role USING (true);

-- Ingestion log
ALTER TABLE ingestion_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON ingestion_log FOR ALL TO service_role USING (true);

-- Theses
ALTER TABLE theses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON theses FOR ALL TO service_role USING (true);

-- Thesis sections
ALTER TABLE thesis_sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON thesis_sections FOR ALL TO service_role USING (true);

-- Thesis citations
ALTER TABLE thesis_citations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON thesis_citations FOR ALL TO service_role USING (true);

-- Markets
ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON markets FOR ALL TO service_role USING (true);

-- Market price history
ALTER TABLE market_price_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON market_price_history FOR ALL TO service_role USING (true);

-- Market current prices
ALTER TABLE market_current_prices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON market_current_prices FOR ALL TO service_role USING (true);

-- Thesis market alignments
ALTER TABLE thesis_market_alignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON thesis_market_alignments FOR ALL TO service_role USING (true);

-- Market global relevance
ALTER TABLE market_global_relevance ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access" ON market_global_relevance FOR ALL TO service_role USING (true);
