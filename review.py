"""
Imprint Document Review Interface
Review and approve/edit tags proposed by LLM.
"""

import os
import json
import psycopg2

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v


def get_documents(status_filter=None):
    """Fetch documents, optionally filtered by status."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    if status_filter:
        cur.execute("""
            SELECT id, title, author, source_type, source_url, thesis, topic, sector,
                   entities, document_type, angle, catalyst_window, summary, status,
                   content
            FROM imprint_documents
            WHERE status = %s
            ORDER BY ingested_date DESC
        """, (status_filter,))
    else:
        cur.execute("""
            SELECT id, title, author, source_type, source_url, thesis, topic, sector,
                   entities, document_type, angle, catalyst_window, summary, status,
                   content
            FROM imprint_documents
            ORDER BY ingested_date DESC
        """)

    columns = ['id', 'title', 'author', 'source_type', 'source_url', 'thesis',
               'topic', 'sector', 'entities', 'document_type', 'angle',
               'catalyst_window', 'summary', 'status', 'content']

    docs = []
    for row in cur.fetchall():
        docs.append(dict(zip(columns, row)))

    cur.close()
    conn.close()

    return docs


def update_document(doc_id, updates):
    """Update document fields."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    set_clauses = []
    values = []
    for key, value in updates.items():
        set_clauses.append(f"{key} = %s")
        values.append(value)

    values.append(doc_id)

    cur.execute(f"""
        UPDATE imprint_documents
        SET {', '.join(set_clauses)}
        WHERE id = %s
    """, values)

    conn.commit()
    cur.close()
    conn.close()


def print_document(doc, index, total):
    """Display a document for review."""
    print()
    print("=" * 70)
    print(f"Document {index}/{total}")
    print("=" * 70)
    print(f"Title:    {doc['title'][:65]}")
    print(f"Type:     {doc['source_type']}")
    print(f"Author:   {doc['author'] or 'Unknown'}")
    print(f"Source:   {doc['source_url'][:60] if doc['source_url'] else 'N/A'}...")
    print()
    print("--- Proposed Tags ---")
    print(f"Thesis:         {doc['thesis']}")
    print(f"Topic:          {doc['topic']}")
    print(f"Sector:         {doc['sector']}")
    print(f"Entities:       {doc['entities']}")
    print(f"Document Type:  {doc['document_type']}")
    print(f"Angle:          {doc['angle']}")
    print(f"Catalyst:       {doc['catalyst_window']}")
    print()
    print(f"Summary: {doc['summary']}")
    print()
    print(f"Content preview: {doc['content'][:300]}...")
    print()


def edit_field(doc, field_name, current_value):
    """Prompt user to edit a field."""
    print(f"\nCurrent {field_name}: {current_value}")
    new_value = input(f"New {field_name} (or Enter to keep): ").strip()

    if new_value:
        if field_name == 'entities':
            # Parse as list
            new_value = [e.strip() for e in new_value.split(',')]
        return new_value
    return current_value


def review_document(doc, index, total):
    """Interactive review of a single document."""
    print_document(doc, index, total)

    while True:
        print("Actions:")
        print("  [a] Approve as-is")
        print("  [e] Edit tags")
        print("  [s] Skip (review later)")
        print("  [v] View full content")
        print("  [q] Quit review")

        action = input("\nChoice: ").strip().lower()

        if action == 'a':
            update_document(doc['id'], {'status': 'active'})
            print("✓ Approved")
            return 'next'

        elif action == 'e':
            updates = {}
            print("\nEdit fields (Enter to keep current value):")

            # Editable fields
            fields = [
                ('thesis', doc['thesis']),
                ('topic', doc['topic']),
                ('sector', doc['sector']),
                ('entities', doc['entities']),
                ('document_type', doc['document_type']),
                ('angle', doc['angle']),
                ('catalyst_window', doc['catalyst_window']),
                ('summary', doc['summary'])
            ]

            for field_name, current_value in fields:
                new_value = edit_field(doc, field_name, current_value)
                if new_value != current_value:
                    updates[field_name] = new_value
                    doc[field_name] = new_value  # Update local copy

            if updates:
                updates['status'] = 'active'
                update_document(doc['id'], updates)
                print(f"✓ Updated {len(updates)} fields")
            else:
                update_document(doc['id'], {'status': 'active'})
                print("✓ Approved (no changes)")

            return 'next'

        elif action == 's':
            print("Skipped")
            return 'next'

        elif action == 'v':
            print("\n" + "=" * 70)
            print("FULL CONTENT")
            print("=" * 70)
            print(doc['content'][:5000])
            if len(doc['content']) > 5000:
                print(f"\n... [{len(doc['content']) - 5000} more chars]")
            print("=" * 70)

        elif action == 'q':
            return 'quit'

        else:
            print("Invalid choice")


def main():
    """Main review entry point."""
    print("=" * 70)
    print("Imprint Document Review")
    print("=" * 70)
    print()
    print("Filter by status:")
    print("  [1] All documents")
    print("  [2] Active only")
    print("  [3] Pending review only")

    choice = input("\nChoice (default: 1): ").strip()

    status_filter = None
    if choice == '2':
        status_filter = 'active'
    elif choice == '3':
        status_filter = 'pending_review'

    docs = get_documents(status_filter)

    if not docs:
        print("\nNo documents found.")
        return

    print(f"\nFound {len(docs)} documents.")

    for i, doc in enumerate(docs, 1):
        result = review_document(doc, i, len(docs))
        if result == 'quit':
            break

    print("\n" + "=" * 70)
    print("Review session complete")


if __name__ == '__main__':
    main()
