"""
Imprint PDF Ingestion Pipeline
Extracts PDFs from Google Drive Imprint folder, proposes tags via Claude, embeds via OpenAI, stores in Supabase.
"""

import os
import re
import json
import io
import fitz  # PyMuPDF
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
import anthropic
import psycopg2
from imprint_utils import log_ingestion, clean_pdf_content, document_exists

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# Clients
drive_creds = Credentials.from_authorized_user_file(
    os.path.join(os.path.dirname(__file__), 'token.json')
)
drive = build('drive', 'v3', credentials=drive_creds)
openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()

# Load tag dictionary
TAG_DICTIONARY_PATH = os.path.join(os.path.dirname(__file__), 'Imprint_Tag_Dictionary.md')
with open(TAG_DICTIONARY_PATH) as f:
    TAG_DICTIONARY = f.read()

# Imprint folder ID (from earlier discovery)
IMPRINT_FOLDER_ID = '1o3RQOFx4WaFiENkFYRDaAJd5SZOYvDeJ'


def get_imprint_pdfs():
    """Fetch all PDFs from the Imprint folder (not subfolders)."""
    # Get files directly in Imprint folder (not in Vision subfolder)
    results = drive.files().list(
        q=f"'{IMPRINT_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name, size, createdTime)"
    ).execute()

    return results.get('files', [])


def download_pdf(file_id):
    """Download PDF content from Google Drive."""
    request = drive.files().get_media(fileId=file_id)
    content = request.execute()
    return content


def extract_pdf_text(pdf_bytes):
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_parts.append(f"[Page {page_num + 1}]\n{text}")

    doc.close()

    return '\n\n'.join(text_parts)


def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def summarize_for_classification(content):
    """For long documents, create a summary for better classification."""
    if len(content) <= 10000:
        return content

    # For long docs, take beginning, middle, and end
    chunk_size = 3000
    beginning = content[:chunk_size]
    middle_start = len(content) // 2 - chunk_size // 2
    middle = content[middle_start:middle_start + chunk_size]
    end = content[-chunk_size:]

    return f"""[BEGINNING OF DOCUMENT]
{beginning}

[MIDDLE OF DOCUMENT]
{middle}

[END OF DOCUMENT]
{end}"""


def propose_tags(document):
    """Use Claude to propose tags for a document."""
    # Use condensed content for classification
    content_for_classification = summarize_for_classification(document['content'])

    prompt = f"""You are a research librarian helping categorize investment research documents for market-linkable research.

Given the document below, propose tags following the Imprint taxonomy. Return a JSON object with these fields:

- topic: One specific topic (e.g., ai_inference_economics, gpu_supply_constraints) - be specific and mechanism-focused, not vague
- sector: One sector (e.g., Infra, Software, Semiconductors, Security, Fintech, Healthcare, Energy, Industrial, Consumer, Macro, Government, Geopolitics)
- entities: Array of companies/people/organizations. Use tickers for public companies (NVDA not Nvidia), canonical names for private (OpenAI not openai), full names for people (Jerome Powell)
- sentiment: One of: bullish, bearish, neutral, mixed (the author's directional tone toward the topic/entities)
- document_type: One of: blog, whitepaper, transcript, presentation, earnings, report, image, other
- catalyst_window: (optional, null if not applicable) One of: immediate, near_term, medium_term, long_term, structural (leave null if document doesn't imply specific timing)
- summary: One sentence takeaway capturing the core insight or signal

Reference taxonomy (examples, not exhaustive):
{TAG_DICTIONARY[:3000]}

Document title: {document['title']}
Document content (condensed for long documents):
{content_for_classification[:12000]}

Return ONLY valid JSON, no other text."""

    response = anthropic_client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text
    if '```json' in response_text:
        response_text = response_text.split('```json')[1].split('```')[0]
    elif '```' in response_text:
        response_text = response_text.split('```')[1].split('```')[0]

    return json.loads(response_text.strip())


def generate_embedding(text):
    """Generate embedding using OpenAI text-embedding-3-large at 1536 dimensions."""
    # For long docs, embed a summary rather than full content
    if len(text) > 32000:
        text = summarize_for_classification(text)

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
        'pdf',
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


def process_pdf(file_info):
    """Process a single PDF through the full pipeline."""
    file_id = file_info['id']
    filename = file_info['name']
    source_url = f"https://drive.google.com/file/d/{file_id}"

    # Parse title from filename for deduplication
    title = filename.replace('.pdf', '').replace('-', ' ')

    # Check for duplicate (by source_url AND title)
    if document_exists(source_url, title):
        print(f"  ⏭ Already ingested (same title or source): {filename}")
        return None

    print(f"  File: {filename}")
    print(f"  Size: {int(file_info.get('size', 0)) / 1024:.1f} KB")

    # Download PDF
    print(f"  Downloading from Drive...")
    pdf_bytes = download_pdf(file_id)

    # Extract text
    print(f"  Extracting text...")
    content = extract_pdf_text(pdf_bytes)
    content = clean_text(content)

    if not content or len(content) < 100:
        print(f"  ✗ Could not extract text (possibly image-only PDF)")
        log_ingestion('pdf', filename, 'failed', 'Could not extract text - possibly image-only PDF')
        return None

    # Count pages
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    doc.close()

    print(f"  Pages: {page_count}")
    print(f"  Raw content length: {len(content)} chars")

    # Clean content (handles both traditional PDFs and web-saved PDFs)
    print(f"  Cleaning content...")
    content, reduction = clean_pdf_content(content)
    print(f"  Cleaned content length: {len(content)} chars ({reduction:.1f}% removed)")

    # Parse title from filename
    title = filename.replace('.pdf', '').replace('-', ' ')

    document = {
        'title': title,
        'content': content,
        'source': 'Google Drive',
        'source_url': f"https://drive.google.com/file/d/{file_id}",
        'author': None,
        'published_date': None
    }

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
    log_ingestion('pdf', filename, 'success', document_id=doc_id)

    return doc_id


def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("Imprint PDF Ingestion")
    print("=" * 60)

    pdfs = get_imprint_pdfs()
    print(f"Found {len(pdfs)} PDFs in Imprint folder")
    print()

    for i, pdf in enumerate(pdfs):
        print(f"[{i+1}/{len(pdfs)}] Processing PDF...")
        try:
            doc_id = process_pdf(pdf)
            print()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 60)
    print("Ingestion complete")


if __name__ == '__main__':
    main()
