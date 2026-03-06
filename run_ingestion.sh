#!/bin/bash
# Imprint Daily Ingestion Runner
# Runs all ingestion pipelines and logs output

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/ingestion_$(date +%Y%m%d_%H%M%S).log"

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Run ingestion with logging
echo "=== Imprint Ingestion Started: $(date) ===" >> "$LOG_FILE"
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 "$SCRIPT_DIR/ingest_all.py" >> "$LOG_FILE" 2>&1
echo "=== Imprint Ingestion Finished: $(date) ===" >> "$LOG_FILE"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "ingestion_*.log" -mtime +30 -delete
