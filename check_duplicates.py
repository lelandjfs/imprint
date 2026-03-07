"""
Check for duplicate documents in Supabase.
Shows duplicates by title and provides cleanup options.
"""

import os
import psycopg2
from collections import defaultdict
from datetime import datetime

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
    SELECT id, title, source_url, source_type, ingested_date, published_date, status
    FROM imprint_documents
    ORDER BY ingested_date DESC
""")

docs = cur.fetchall()
print(f"\n{'='*80}")
print(f"IMPRINT DATABASE INSPECTION")
print(f"{'='*80}")
print(f"Total documents: {len(docs)}\n")

# Print all documents
print(f"{'ID':<6} {'Title':<50} {'Source Type':<12} {'Status':<15} {'Ingested':<20}")
print("-" * 120)
for doc in docs:
    doc_id, title, source_url, source_type, ingested, published, status = doc
    title_short = (title[:47] + '...') if len(title) > 50 else title
    ingested_str = ingested.strftime('%Y-%m-%d %H:%M') if ingested else 'N/A'
    print(f"{doc_id:<6} {title_short:<50} {source_type:<12} {status:<15} {ingested_str:<20}")

print("\n" + "="*80)
print("DUPLICATE ANALYSIS")
print("="*80)

# Group by title to find duplicates
title_groups = defaultdict(list)
for doc in docs:
    doc_id, title, source_url, source_type, ingested, published, status = doc
    title_groups[title].append({
        'id': doc_id,
        'title': title,
        'source_url': source_url,
        'source_type': source_type,
        'ingested_date': ingested,
        'published_date': published,
        'status': status
    })

# Find duplicates
duplicates = {title: docs for title, docs in title_groups.items() if len(docs) > 1}

if duplicates:
    print(f"\nFound {len(duplicates)} titles with duplicates:\n")

    for title, dup_docs in duplicates.items():
        print(f"Title: {title}")
        print(f"  Count: {len(dup_docs)} copies")
        for doc in dup_docs:
            print(f"    - ID {doc['id']}: {doc['source_type']} | "
                  f"Ingested: {doc['ingested_date'].strftime('%Y-%m-%d %H:%M') if doc['ingested_date'] else 'N/A'} | "
                  f"Status: {doc['status']}")
        print()
else:
    print("\nNo duplicates found!\n")

# Check for orphaned documents (source_url patterns that shouldn't exist)
print("="*80)
print("POTENTIAL ORPHANED DOCUMENTS")
print("="*80)

cur.execute("""
    SELECT id, title, source_url, source_type, status
    FROM imprint_documents
    WHERE status = 'active'
    ORDER BY title
""")

orphans = cur.fetchall()
print(f"\nActive documents (check if any shouldn't exist):")
for doc_id, title, source_url, source_type, status in orphans:
    print(f"  ID {doc_id}: {title[:60]}")
    print(f"    Source: {source_url}")
    print()

cur.close()
conn.close()

print("="*80)
print("\nTo delete a document, run:")
print("  psql $DATABASE_URL -c \"DELETE FROM imprint_documents WHERE id = <id>;\"")
print("\nOr use the cleanup script to remove all duplicates (keeps most recent).")
print("="*80)
