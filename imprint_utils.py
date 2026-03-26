"""
Imprint Shared Utilities
Logging, notifications, and common functions.
"""

import os
import base64
from email.mime.text import MIMEText
from datetime import datetime
import psycopg2
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v


def get_google_credentials():
    """
    Get Google OAuth credentials with automatic refresh.

    Returns:
        Credentials: Valid Google OAuth credentials

    Raises:
        Exception: If credentials are invalid and cannot be refreshed
    """
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')

    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"Token file not found at {token_path}. "
            "Run 'python refresh_google_auth.py' to authenticate."
        )

    # Scopes needed for Imprint
    scopes = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    creds = Credentials.from_authorized_user_file(token_path, scopes)

    # Check if credentials need refresh
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                print("Token expired. Refreshing...")
                creds.refresh(Request())

                # Save refreshed token
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())

                print("✓ Token refreshed successfully")
            except Exception as e:
                raise Exception(
                    f"Failed to refresh token: {e}\n"
                    "Run 'python refresh_google_auth.py' to re-authenticate."
                )
        else:
            raise Exception(
                "Token is invalid and cannot be refreshed.\n"
                "Run 'python refresh_google_auth.py' to re-authenticate."
            )

    return creds


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ['DATABASE_URL'])


def document_exists(source_url, title=None):
    """
    Check if a document already exists.

    Args:
        source_url: URL/identifier for this source (required)
        title: Document title (optional). If provided, checks both source_url AND title.
               This prevents the same article from being ingested from multiple sources.

    Returns:
        bool: True if document exists, False otherwise
    """
    if not source_url:
        return False

    conn = get_db_connection()
    cur = conn.cursor()

    # Check by source_url first (exact match)
    cur.execute("""
        SELECT id FROM imprint_documents WHERE source_url = %s LIMIT 1
    """, (source_url,))

    if cur.fetchone() is not None:
        cur.close()
        conn.close()
        return True

    # If title provided, also check for title matches
    # This prevents duplicates from different sources (e.g., PDF + image of same article)
    if title:
        cur.execute("""
            SELECT id FROM imprint_documents WHERE title = %s LIMIT 1
        """, (title,))

        if cur.fetchone() is not None:
            cur.close()
            conn.close()
            return True

    cur.close()
    conn.close()
    return False


def log_ingestion(source_type, source_identifier, status, error_message=None, document_id=None):
    """Log an ingestion attempt."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ingestion_log (source_type, source_identifier, status, error_message, document_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (source_type, source_identifier, status, error_message, document_id))

    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return log_id


def get_pending_documents():
    """Get all documents pending review."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, source_type, topic, sector, entities, sentiment, summary
        FROM imprint_documents
        WHERE status = 'pending_review'
        ORDER BY ingested_date DESC
    """)

    columns = ['id', 'title', 'source_type', 'topic', 'sector', 'entities', 'sentiment', 'summary']
    docs = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return docs


def get_recent_ingestion_log(since_minutes=60):
    """Get recent ingestion log entries."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT source_type, source_identifier, status, error_message, document_id, created_at
        FROM ingestion_log
        WHERE created_at > NOW() - INTERVAL '%s minutes'
        ORDER BY created_at DESC
    """, (since_minutes,))

    columns = ['source_type', 'source_identifier', 'status', 'error_message', 'document_id', 'created_at']
    logs = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return logs


def send_ingestion_summary_email(to_email="leland.speth@gmail.com"):
    """Send email summary of recent ingestion."""
    # Get Gmail credentials with auto-refresh
    creds = get_google_credentials()
    gmail = build('gmail', 'v1', credentials=creds)

    # Get recent logs and pending docs
    logs = get_recent_ingestion_log(since_minutes=60)
    pending_docs = get_pending_documents()

    if not logs and not pending_docs:
        print("No recent activity to report.")
        return

    # Build email body
    body_parts = []
    body_parts.append("=" * 50)
    body_parts.append("IMPRINT INGESTION SUMMARY")
    body_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    body_parts.append("=" * 50)
    body_parts.append("")

    # Recent ingestion results
    if logs:
        success = [l for l in logs if l['status'] == 'success']
        failed = [l for l in logs if l['status'] == 'failed']
        restricted = [l for l in logs if l['status'] == 'restricted']

        body_parts.append(f"INGESTION RESULTS ({len(logs)} items)")
        body_parts.append("-" * 40)

        if success:
            body_parts.append(f"\n✓ SUCCESS ({len(success)} items):")
            for log in success:
                body_parts.append(f"  • [{log['source_type']}] {log['source_identifier'][:50]}")

        if restricted:
            body_parts.append(f"\n⚠ RESTRICTED ({len(restricted)} items):")
            for log in restricted:
                body_parts.append(f"  • [{log['source_type']}] {log['source_identifier'][:50]}")
                if log['error_message']:
                    body_parts.append(f"    Reason: {log['error_message']}")

        if failed:
            body_parts.append(f"\n✗ FAILED ({len(failed)} items):")
            for log in failed:
                body_parts.append(f"  • [{log['source_type']}] {log['source_identifier'][:50]}")
                if log['error_message']:
                    body_parts.append(f"    Error: {log['error_message']}")

        body_parts.append("")

    # Pending documents for review
    if pending_docs:
        body_parts.append(f"PENDING REVIEW ({len(pending_docs)} documents)")
        body_parts.append("-" * 40)

        for i, doc in enumerate(pending_docs, 1):
            body_parts.append(f"\n[{i}] {doc['title'][:55]}")
            body_parts.append(f"    Type: {doc['source_type']}")
            body_parts.append(f"    Topic: {doc['topic']} | Sector: {doc['sector']} | Sentiment: {doc['sentiment']}")
            body_parts.append(f"    Entities: {', '.join(doc['entities'] or [])}")
            body_parts.append(f"    Summary: {doc['summary'][:100]}..." if doc['summary'] else "")

        body_parts.append("")
        body_parts.append("-" * 40)
        body_parts.append("Review in Supabase:")
        body_parts.append("https://supabase.com/dashboard/project/qvwqquyaxunxyiwtobsu/editor")

    body_parts.append("")
    body_parts.append("=" * 50)

    body = "\n".join(body_parts)

    # Create email
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = f"[Imprint] Ingestion Summary - {datetime.now().strftime('%m/%d %H:%M')}"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"✓ Summary email sent to {to_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False


def mark_document_reviewed(doc_id, status='active'):
    """Mark a document as reviewed."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE imprint_documents
        SET status = %s
        WHERE id = %s
    """, (status, doc_id))

    conn.commit()
    cur.close()
    conn.close()


def clean_ad_content(text, source_type='email'):
    """
    Remove ad content, tracking URLs, and newsletter chrome from text.
    Uses a combination of regex patterns and LLM for thorough cleaning.
    """
    import re
    import anthropic

    original_length = len(text)

    # Step 1: Remove tracking/CDN URLs (keep the link text if meaningful)
    # Mimecast protection URLs
    text = re.sub(r'<https?://url\.us\.m\.mimecastprotect\.com[^>]+>', '', text)
    # Substack CDN image URLs
    text = re.sub(r'\[https?://substackcdn\.com[^\]]+\]', '', text)
    # Generic long URLs (likely tracking)
    text = re.sub(r'<https?://[^>]{100,}>', '', text)
    # Empty link brackets
    text = re.sub(r'\[\s*\]', '', text)

    # Step 2: Remove common newsletter footer patterns
    footer_patterns = [
        r'©\s*\d{4}[^\n]*\n.*?(?=\n\n|\Z)',  # Copyright sections
        r'Unsubscribe\s*<[^>]+>',  # Unsubscribe links
        r'\d+\s+Market\s+Street[^\n]+',  # Address lines
        r'Forwarded this email\?[^\n]+',  # Forward prompts
        r'Subscribe here[^\n]*',  # Subscribe CTAs
        r'Get the app[^\n]*',  # App download CTAs
        r'READ IN APP[^\n]*',  # App CTAs
        r'View in browser[^\n]*',  # Browser view links
        r'Share this post[^\n]*',  # Share CTAs
    ]

    for pattern in footer_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Step 3: Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    # Step 4: Use LLM for aggressive cleaning
    if len(text) > 500 and source_type in ['email', 'url']:
        try:
            client = anthropic.Anthropic()

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"""Clean this content. Return ONLY the main article/newsletter.

REMOVE ALL:
- Sponsor sections ("This week's sponsor", "Brought to you by")
- Advertisement blocks
- Stock price widgets, market data headers
- "In this article:" ticker lists
- Site navigation, headers, footers
- "Related articles", "More from...", "You may also like"
- Subscribe/newsletter prompts
- Social sharing text
- Comments sections
- Cookie/privacy notices
- "Scroll back", "View details", UI instructions

KEEP ONLY:
- Title/headline
- Author/date
- The actual article paragraphs with substance, quotes, analysis

Return the cleaned text only, no preamble:

{text[:15000]}"""
                }]
            )

            cleaned = response.content[0].text.strip()

            # Remove any preamble the model might add
            if cleaned.startswith("Here is") or cleaned.startswith("Here's"):
                first_newline = cleaned.find('\n')
                if first_newline > 0:
                    cleaned = cleaned[first_newline:].strip()

            # Only use if substantial content remains
            if len(cleaned) > 200 and len(cleaned) < len(text):
                text = cleaned

        except Exception as e:
            # If LLM fails, continue with regex-cleaned version
            pass

    cleaned_length = len(text)
    reduction = ((original_length - cleaned_length) / original_length) * 100 if original_length > 0 else 0

    return text, reduction


def clean_pdf_content(text, is_web_saved=False):
    """
    Clean PDF content using LLM. Handles both traditional PDFs and web-pages-saved-as-PDF.
    """
    import re
    import anthropic

    original_length = len(text)

    # Step 1: Remove page markers we added during extraction
    text = re.sub(r'\[Page \d+\]\n', '', text)

    # Step 2: Use LLM for aggressive cleaning
    try:
        client = anthropic.Anthropic()

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""Clean this document. Return ONLY the main article/content.

REMOVE ALL:
- Stock price headers, market data widgets
- "In this article:" ticker symbol lists
- "Scroll back up" / "View Quote Details" / UI text
- "More from..." / "Related articles" sections
- Polymarket/prediction widgets
- "View Comments" sections
- Footer (Copyright, Terms, Privacy, What's trending)
- Search suggestions
- Navigation links
- Standalone ticker symbols (^TNX, CL=F, etc)

KEEP ONLY:
- Headline
- Author/date (one line)
- The actual article paragraphs with analysis, quotes, facts

Return the cleaned text only, no preamble:

{text[:15000]}"""
            }]
        )

        cleaned = response.content[0].text.strip()

        # Remove any preamble the model might add
        if cleaned.startswith("Here is") or cleaned.startswith("Here's"):
            first_newline = cleaned.find('\n')
            if first_newline > 0:
                cleaned = cleaned[first_newline:].strip()

        # Only use if substantial content remains
        if len(cleaned) > 200 and len(cleaned) < len(text):
            text = cleaned

    except Exception as e:
        # Fall back to basic cleaning
        pass

    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()

    cleaned_length = len(text)
    reduction = ((original_length - cleaned_length) / original_length) * 100 if original_length > 0 else 0

    return text, reduction


def _looks_like_web_content(text):
    """Detect if PDF content looks like a saved web page."""
    web_indicators = [
        'subscribe', 'newsletter', 'cookie', 'privacy policy',
        'share this', 'comments', 'related articles', 'advertisement'
    ]
    text_lower = text.lower()
    matches = sum(1 for indicator in web_indicators if indicator in text_lower)
    return matches >= 2
