"""Delete the oil price document from Supabase."""

import os
import psycopg2

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("="*80)
print("🗑️  Deleting 'oil' documents from Supabase")
print("="*80)

# Find documents with 'oil' in title
cur.execute("""
    SELECT id, title, source_type, status
    FROM imprint_documents
    WHERE title ILIKE '%oil%'
""")

docs = cur.fetchall()

if docs:
    print(f"\nFound {len(docs)} document(s) containing 'oil':\n")
    for doc in docs:
        doc_id, title, source_type, status = doc
        print(f"📄 {title}")
        print(f"   ID: {doc_id}")
        print(f"   Type: {source_type}")
        print(f"   Status: {status}")
        print()

    # Delete
    confirm = input("Delete these documents? (yes/no): ")
    if confirm.lower() == 'yes':
        for doc in docs:
            doc_id = doc[0]
            # Delete from ingestion_log first
            cur.execute("DELETE FROM ingestion_log WHERE document_id = %s", (doc_id,))
            # Delete from documents
            cur.execute("DELETE FROM imprint_documents WHERE id = %s", (doc_id,))
            print(f"✓ Deleted {doc[1]}")

        conn.commit()
        print(f"\n✅ Successfully deleted {len(docs)} document(s)")
    else:
        print("\n❌ Cancelled")
else:
    print("\n✅ No documents containing 'oil' found in database")

cur.close()
conn.close()

print("="*80)
