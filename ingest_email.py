"""
Imprint Email Ingestion Pipeline
Extracts newsletters from Gmail, proposes tags via Claude, embeds via OpenAI, stores in Supabase.
"""

import os
import re
import base64
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
import anthropic
import psycopg2
from imprint_utils import log_ingestion, clean_ad_content, document_exists, get_google_credentials

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# Clients
gmail_creds = get_google_credentials()
gmail = build('gmail', 'v1', credentials=gmail_creds)
openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()

# Load tag dictionary for prompts
TAG_DICTIONARY_PATH = os.path.join(os.path.dirname(__file__), 'Imprint_Tag_Dictionary.md')
with open(TAG_DICTIONARY_PATH) as f:
    TAG_DICTIONARY = f.read()


def get_imprint_emails():
    """Fetch all emails with the Imprint label."""
    labels = gmail.users().labels().list(userId='me').execute()
    imprint_label = next((l for l in labels['labels'] if l['name'] == 'Imprint'), None)
    if not imprint_label:
        raise ValueError("Imprint label not found in Gmail")

    messages = []
    result = gmail.users().messages().list(userId='me', labelIds=[imprint_label['id']]).execute()
    messages.extend(result.get('messages', []))

    return messages


def extract_email_body(payload):
    """Extract plain text body from email payload."""
    if 'body' in payload and payload['body'].get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    if 'parts' in payload:
        # Prefer text/plain
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        # Check nested multipart
        for part in payload['parts']:
            if part.get('mimeType', '').startswith('multipart/'):
                result = extract_email_body(part)
                if result:
                    return result
        # Fallback to any text part
        for part in payload['parts']:
            result = extract_email_body(part)
            if result:
                return result
    return None


def clean_text(text):
    """Clean invisible characters and normalize whitespace."""
    # Remove invisible formatting characters
    text = re.sub(r'[\u034f\u00ad\u200b-\u200f\u2028-\u202f\u205f-\u206f]', '', text)
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def parse_forwarded_email(body, headers):
    """
    Parse forwarded email to extract original metadata.
    Returns dict with: title, author, source, published_date, content
    """
    result = {
        'title': headers.get('Subject', ''),
        'author': None,
        'source': None,
        'source_url': None,
        'published_date': None,
        'content': body
    }

    # Check for Outlook forward pattern
    outlook_pattern = r'From:\s*(.+?)\s*<([^>]+)>\s*\nSent:\s*(.+?)\s*\nTo:.+?\nSubject:\s*(.+?)(?:\n|$)'
    match = re.search(outlook_pattern, body, re.IGNORECASE)

    if match:
        result['author'] = match.group(1).strip()
        result['source'] = match.group(2).strip()
        result['title'] = match.group(4).strip()

        # Parse date
        date_str = match.group(3).strip()
        try:
            # Try common formats
            for fmt in ['%A, %B %d, %Y %I:%M:%S %p', '%B %d, %Y %I:%M:%S %p', '%m/%d/%Y %I:%M %p']:
                try:
                    result['published_date'] = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
        except:
            pass

        # Extract content after the forward header
        content_start = match.end()
        result['content'] = body[content_start:]

    # Check for Gmail forward pattern
    gmail_pattern = r'-+ Forwarded message -+\s*\nFrom:\s*(.+?)\s*<([^>]+)>\s*\nDate:\s*(.+?)\s*\nSubject:\s*(.+?)\s*\nTo:'
    match = re.search(gmail_pattern, body, re.IGNORECASE)

    if match:
        result['author'] = match.group(1).strip()
        result['source'] = match.group(2).strip()
        result['title'] = match.group(4).strip()
        content_start = match.end()
        result['content'] = body[content_start:]

    # Clean the content
    result['content'] = clean_text(result['content'])

    # Remove forward preamble like "Get Outlook for iOS"
    result['content'] = re.sub(r'^.*?Get Outlook for iOS.*?\n', '', result['content'], flags=re.IGNORECASE)
    result['content'] = re.sub(r'^\[EXT\]\s*', '', result['content'])

    return result


class DocumentTags(BaseModel):
    """Structured tags for a document."""
    topic: str = Field(
        description="One specific topic (e.g., ai_inference_economics, gpu_supply_constraints) - be specific and mechanism-focused, not vague"
    )
    sector: str = Field(
        description="One sector: Infra, Software, Semiconductors, Security, Fintech, Healthcare, Energy, Industrial, Consumer, Macro, Government, or Geopolitics"
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Array of companies/people/organizations. Use tickers for public companies (NVDA not Nvidia), canonical names for private (OpenAI not openai), full names for people (Jerome Powell)"
    )
    sentiment: str = Field(
        description="One of: bullish, bearish, neutral, mixed (the author's directional tone toward the topic/entities)"
    )
    document_type: str = Field(
        description="One of: article, blog, whitepaper, transcript, presentation, earnings, report, image, x_post, other"
    )
    catalyst_window: Optional[str] = Field(
        None,
        description="One of: immediate, near_term, medium_term, long_term, structural (leave null if document doesn't imply specific timing)"
    )
    summary: str = Field(
        description="One sentence takeaway capturing the core insight or signal"
    )


def propose_tags(document):
    """Use Claude to propose tags for a document using structured output."""
    prompt = f"""You are a research librarian helping categorize investment research documents for market-linkable research.

Given the document below, propose tags following the Imprint taxonomy.

Reference taxonomy (examples, not exhaustive):
{TAG_DICTIONARY[:3000]}

Document title: {document['title']}
Document author: {document.get('author', 'Unknown')}
Document content (first 8000 chars):
{document['content'][:8000]}"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "document_tags",
            "description": "Tags for categorizing an investment research document",
            "input_schema": DocumentTags.model_json_schema()
        }],
        tool_choice={"type": "tool", "name": "document_tags"}
    )

    # Extract structured output from tool use
    for block in response.content:
        if block.type == "tool_use" and block.name == "document_tags":
            return block.input

    # Fallback (should not happen with tool_choice)
    raise ValueError("No structured output returned from Claude")


def generate_embedding(text):
    """Generate embedding using OpenAI text-embedding-3-large at 1536 dimensions."""
    # Truncate to ~8000 tokens worth of text (roughly 32000 chars)
    text = text[:32000]

    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
        dimensions=1536
    )

    return response.data[0].embedding


def store_document(document, tags, embedding):
    """Store document in Supabase with pending_review status."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO imprint_documents (
            title, author, content, source_type, source, source_url,
            published_date, topic, sector, entities, sentiment, document_type, catalyst_window, summary,
            embedding, status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id
    """, (
        document['title'],
        document.get('author'),
        document['content'],
        'email',
        document.get('source'),
        document.get('source_url'),
        document.get('published_date'),
        tags.get('topic'),
        tags.get('sector'),
        tags.get('entities', []),
        tags.get('sentiment'),
        tags.get('document_type'),
        tags.get('catalyst_window'),
        tags.get('summary'),
        embedding,
        'pending_review'
    ))

    doc_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return doc_id


def process_email(msg_id):
    """Process a single email through the full pipeline."""
    print(f"  Fetching email {msg_id}...")
    msg = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()

    # Extract headers
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    subject = headers.get('Subject', 'Unknown')

    # Extract body
    body = extract_email_body(msg['payload'])
    if not body:
        print(f"  ✗ Could not extract body")
        log_ingestion('email', subject, 'failed', 'Could not extract email body')
        return None

    # Parse forwarded email
    print(f"  Parsing email content...")
    document = parse_forwarded_email(body, headers)
    document['source_url'] = f"gmail://{msg_id}"
    print(f"  Title: {document['title'][:60]}...")
    print(f"  Author: {document.get('author', 'Unknown')}")

    # Check for duplicate (by source_url AND title)
    if document_exists(document['source_url'], document['title']):
        print(f"  ⏭ Already ingested (same title or source), skipping")
        return None
    print(f"  Raw content length: {len(document['content'])} chars")

    # Clean ad content
    print(f"  Cleaning ad/tracking content...")
    document['content'], reduction = clean_ad_content(document['content'], 'email')
    print(f"  Cleaned content length: {len(document['content'])} chars ({reduction:.1f}% removed)")

    # Propose tags
    print(f"  Proposing tags via Claude...")
    tags = propose_tags(document)
    print(f"  Topic: {tags.get('topic')}")
    print(f"  Sector: {tags.get('sector')}")
    print(f"  Sentiment: {tags.get('sentiment')}")
    print(f"  Document Type: {tags.get('document_type')}")
    print(f"  Catalyst Window: {tags.get('catalyst_window') or 'None'}")
    print(f"  Entities: {tags.get('entities', [])}")

    # Generate embedding
    print(f"  Generating embedding...")
    embedding = generate_embedding(document['content'])

    # Store
    print(f"  Storing in Supabase...")
    doc_id = store_document(document, tags, embedding)
    print(f"  ✓ Stored with ID: {doc_id}")

    # Log success
    log_ingestion('email', document['title'], 'success', document_id=doc_id)

    return doc_id


def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("Imprint Email Ingestion")
    print("=" * 60)

    emails = get_imprint_emails()
    print(f"Found {len(emails)} emails with Imprint label")
    print()

    for i, email_meta in enumerate(emails):
        print(f"[{i+1}/{len(emails)}] Processing email...")
        try:
            doc_id = process_email(email_meta['id'])
            if doc_id:
                print()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            print()

    print("=" * 60)
    print("Ingestion complete")


if __name__ == '__main__':
    main()
