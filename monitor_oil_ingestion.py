"""
Monitor for re-ingestion of deleted documents.
Run this after ingestion to ensure unwanted documents aren't coming back.
"""

import os
import psycopg2

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# List of unwanted keywords in titles
UNWANTED_KEYWORDS = ['oil', 'surging']

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("="*80)
print("🔍 Monitoring for unwanted document re-ingestion")
print("="*80)

for keyword in UNWANTED_KEYWORDS:
    cur.execute("""
        SELECT id, title, source_type, status, ingested_date
        FROM imprint_documents
        WHERE title ILIKE %s
        ORDER BY ingested_date DESC
    """, (f'%{keyword}%',))

    docs = cur.fetchall()

    if docs:
        print(f"\n❌ ALERT: Found {len(docs)} document(s) containing '{keyword}':")
        for doc in docs:
            doc_id, title, source_type, status, ingested_date = doc
            print(f"\n📄 {title}")
            print(f"   ID: {doc_id}")
            print(f"   Type: {source_type}")
            print(f"   Status: {status}")
            print(f"   Ingested: {ingested_date}")
            print(f"\n   ⚠️  THIS SHOULD NOT BE HERE!")
            print(f"   Run: python3 -c \"from imprint_utils import get_db_connection; conn = get_db_connection(); cur = conn.cursor(); cur.execute('DELETE FROM ingestion_log WHERE document_id = \\'{doc_id}\\''); cur.execute('DELETE FROM imprint_documents WHERE id = \\'{doc_id}\\''); conn.commit()\"")
    else:
        print(f"\n✅ No documents containing '{keyword}' found")

cur.close()
conn.close()

print("\n" + "="*80)
print("Monitoring complete")
print("="*80)
