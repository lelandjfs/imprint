"""
Imprint Vision Ingestion Pipeline
Extracts content from image-heavy PDFs using GPT-4o vision.
"""

import os
import re
import json
import base64
import fitz  # PyMuPDF
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
import anthropic
import psycopg2
from imprint_utils import log_ingestion, document_exists

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

# Folder IDs
IMPRINT_FOLDER_ID = '1o3RQOFx4WaFiENkFYRDaAJd5SZOYvDeJ'
VISION_FOLDER_ID = '1rysQYeZSqReScWxVq0T8cpfHHWNNi9LK'


def get_vision_files():
    """Fetch all files from the Vision folder."""
    results = drive.files().list(
        q=f"'{VISION_FOLDER_ID}' in parents",
        fields="files(id, name, mimeType, size)"
    ).execute()
    return results.get('files', [])


def download_file(file_id):
    """Download file content from Google Drive."""
    request = drive.files().get_media(fileId=file_id)
    return request.execute()


def pdf_pages_to_images(pdf_bytes, max_pages=20, dpi=150):
    """Convert PDF pages to base64-encoded images."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page_num in range(min(len(doc), max_pages)):
        page = doc[page_num]
        # Render page to image
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.standard_b64encode(img_bytes).decode('utf-8')
        images.append({
            'page': page_num + 1,
            'image_b64': img_b64
        })

    doc.close()
    return images


def extract_content_with_vision(images, filename):
    """Use GPT-4o to extract content from images."""
    print(f"  Analyzing {len(images)} pages with GPT-4o vision...")

    all_content = []

    # Process in batches of 5 pages to manage token limits
    batch_size = 5
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]

        messages_content = [{
            "type": "text",
            "text": f"""Analyze these pages from "{filename}". For each page:

1. Describe any charts, graphs, or diagrams in detail (axes, trends, key data points)
2. Extract all text content
3. Explain the key insights from visual elements

Be thorough - this will be used for search and retrieval later."""
        }]

        for img in batch:
            messages_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img['image_b64']}",
                    "detail": "high"
                }
            })

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": messages_content
            }]
        )

        batch_content = response.choices[0].message.content
        all_content.append(f"[Pages {i+1}-{min(i+batch_size, len(images))}]\n{batch_content}")
        print(f"    Processed pages {i+1}-{min(i+batch_size, len(images))}")

    return "\n\n".join(all_content)


def propose_tags(document):
    """Use Claude to propose tags for a document."""
    content_preview = document['content'][:10000]

    prompt = f"""You are a research librarian helping categorize investment research documents.

Given the document below (extracted from a visual/chart-heavy PDF), propose tags following the Imprint taxonomy. Return a JSON object with these fields:

- thesis: One primary thesis from: ai_cost_compression, capital_cycle, platform_consolidation, workflow_automation, regulatory_tailwind, distribution_shifts, pricing_power, security_as_default, data_gravity, verticalization (or propose a new one in snake_case if none fit)
- topic: One specific topic - be specific, not vague
- sector: One of: Infra, Security, Fintech, Healthcare, Consumer, Energy, Industrial, Macro
- entities: Array of companies/people mentioned. Use tickers for public companies, canonical names for private.
- document_type: One of: newsletter, article, whitepaper, research_report, earnings_call, tweet_thread, internal_note
- angle: One of: deep_dive, market_map, technical, earnings_notes, opinion, case_study, macro_view
- catalyst_window: One of: 0-3m, 3-12m, 12m+, structural
- summary: One sentence takeaway (what's the key insight?)

Reference taxonomy:
{TAG_DICTIONARY[:3000]}

Document title: {document['title']}
Document content (extracted via vision):
{content_preview}

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
            published_date, thesis, topic, sector, entities,
            document_type, angle, catalyst_window, summary, embedding, status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id
    """, (
        document['title'],
        document.get('author'),
        document['content'],
        'image',
        document.get('source'),
        document.get('source_url'),
        document.get('published_date'),
        tags.get('thesis'),
        tags.get('topic'),
        tags.get('sector'),
        tags.get('entities', []),
        tags.get('document_type'),
        tags.get('angle'),
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


def process_vision_file(file_info):
    """Process a single file through the vision pipeline."""
    file_id = file_info['id']
    filename = file_info['name']
    mime_type = file_info['mimeType']
    source_url = f"https://drive.google.com/file/d/{file_id}"

    # Parse title from filename for deduplication
    title = filename.replace('.pdf', '').replace('.png', '').replace('.jpg', '').replace('-', ' ')

    # Check for duplicate (by source_url AND title)
    if document_exists(source_url, title):
        print(f"  ⏭ Already ingested (same title or source): {filename}")
        return None

    print(f"  File: {filename}")
    print(f"  Size: {int(file_info.get('size', 0)) / 1024:.1f} KB")

    # Download file
    print(f"  Downloading from Drive...")
    file_bytes = download_file(file_id)

    # Convert to images
    if mime_type == 'application/pdf':
        print(f"  Converting PDF pages to images...")
        images = pdf_pages_to_images(file_bytes)
        print(f"  Pages: {len(images)}")
    else:
        # Handle direct image files
        img_b64 = base64.standard_b64encode(file_bytes).decode('utf-8')
        images = [{'page': 1, 'image_b64': img_b64}]

    if not images:
        print(f"  ✗ Could not extract images")
        log_ingestion('image', filename, 'failed', 'Could not extract images from file')
        return None

    # Extract content with vision
    content = extract_content_with_vision(images, filename)
    print(f"  Extracted content: {len(content)} chars")

    # Parse title from filename
    title = filename.replace('.pdf', '').replace('.png', '').replace('.jpg', '').replace('-', ' ')

    document = {
        'title': title,
        'content': content,
        'source': 'Google Drive (Vision)',
        'source_url': f"https://drive.google.com/file/d/{file_id}",
        'author': None,
        'published_date': None
    }

    # Propose tags
    print(f"  Proposing tags via Claude...")
    tags = propose_tags(document)
    print(f"  Thesis: {tags.get('thesis')}")
    print(f"  Topic: {tags.get('topic')}")
    print(f"  Sector: {tags.get('sector')}")
    print(f"  Entities: {tags.get('entities', [])}")

    # Generate embedding
    print(f"  Generating embedding...")
    embedding = generate_embedding(document['content'])

    # Store
    print(f"  Storing in Supabase...")
    doc_id = store_document(document, tags, embedding)
    print(f"  ✓ Stored with ID: {doc_id}")

    # Log success
    log_ingestion('image', filename, 'success', document_id=doc_id)

    return doc_id


def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("Imprint Vision Ingestion")
    print("=" * 60)

    files = get_vision_files()
    print(f"Found {len(files)} files in Vision folder")
    print()

    for i, file_info in enumerate(files):
        print(f"[{i+1}/{len(files)}] Processing file...")
        try:
            doc_id = process_vision_file(file_info)
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
