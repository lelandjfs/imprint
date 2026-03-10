"""Delete all pending documents for re-ingestion with new schema."""

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

print("=" * 80)
print("🗑️  Deleting ALL pending documents")
print("=" * 80)

# Get count of pending documents
cur.execute("SELECT COUNT(*) FROM imprint_documents WHERE status = 'pending_review'")
count = cur.fetchone()[0]

if count == 0:
    print("\n✅ No pending documents found")
else:
    print(f"\n📄 Found {count} pending document(s)\n")

    # Show titles
    cur.execute("""
        SELECT id, title, source_type, ingested_date
        FROM imprint_documents
        WHERE status = 'pending_review'
        ORDER BY ingested_date DESC
    """)

    docs = cur.fetchall()
    for doc_id, title, source_type, ingested_date in docs:
        print(f"  • {title[:60]}")
        print(f"    ({source_type} - {ingested_date})")

    # Confirm deletion
    confirm = input(f"\n⚠️  Delete all {count} pending document(s)? (yes/no): ")

    if confirm.lower() == 'yes':
        # Delete ingestion logs for pending documents
        cur.execute("""
            DELETE FROM ingestion_log
            WHERE document_id IN (
                SELECT id FROM imprint_documents WHERE status = 'pending_review'
            )
        """)
        logs_deleted = cur.rowcount

        # Delete pending documents
        cur.execute("DELETE FROM imprint_documents WHERE status = 'pending_review'")
        docs_deleted = cur.rowcount

        conn.commit()

        print(f"\n✅ Deleted {docs_deleted} document(s) and {logs_deleted} log(s)")
        print("\nNow run: python3 ingest_all.py")
    else:
        print("\n❌ Cancelled")

cur.close()
conn.close()

print("\n" + "=" * 80)
