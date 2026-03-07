"""
Remove duplicate documents from Supabase.
Keeps the most recently ingested version of each title.
"""

import os
import psycopg2
from collections import defaultdict

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all documents
cur.execute("""
    SELECT id, title, ingested_date
    FROM imprint_documents
    ORDER BY title, ingested_date DESC
""")

docs = cur.fetchall()

# Group by title
title_groups = defaultdict(list)
for doc_id, title, ingested in docs:
    title_groups[title].append({
        'id': doc_id,
        'ingested_date': ingested
    })

# Find duplicates
duplicates = {title: docs for title, docs in title_groups.items() if len(docs) > 1}

if not duplicates:
    print("No duplicates found!")
    cur.close()
    conn.close()
    exit()

print(f"\nFound {len(duplicates)} titles with duplicates")
print("="*80)

deleted_count = 0

for title, dup_docs in duplicates.items():
    # Sort by ingested_date (most recent first)
    dup_docs.sort(key=lambda x: x['ingested_date'] if x['ingested_date'] else '', reverse=True)

    # Keep the first (most recent), delete the rest
    keep = dup_docs[0]
    delete = dup_docs[1:]

    print(f"\nTitle: {title[:70]}...")
    print(f"  Keeping: ID {keep['id']} (ingested {keep['ingested_date']})")

    for doc in delete:
        print(f"  Deleting: ID {doc['id']} (ingested {doc['ingested_date']})")
        # First delete related ingestion_log entries
        cur.execute("DELETE FROM ingestion_log WHERE document_id = %s", (doc['id'],))
        # Then delete the document
        cur.execute("DELETE FROM imprint_documents WHERE id = %s", (doc['id'],))
        deleted_count += 1

# Commit deletions
conn.commit()
cur.close()
conn.close()

print("\n" + "="*80)
print(f"✓ Deleted {deleted_count} duplicate documents")
print(f"✓ Kept {len(duplicates)} unique documents (most recent versions)")
print("="*80)
