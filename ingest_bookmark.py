"""
Imprint Bookmark Ingestion Pipeline
Extracts articles from Safari bookmarks, proposes tags via Claude, embeds via OpenAI, stores in Supabase.
Handles both regular articles and Twitter/X content.
"""

import os
import re
import json
import plistlib
import requests
from openai import OpenAI
import anthropic
import psycopg2
from imprint_utils import log_ingestion, clean_ad_content, document_exists

# Load environment
with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

# Clients
openai_client = OpenAI()
anthropic_client = anthropic.Anthropic()

# Load tag dictionary
TAG_DICTIONARY_PATH = os.path.join(os.path.dirname(__file__), 'Imprint_Tag_Dictionary.md')
with open(TAG_DICTIONARY_PATH) as f:
    TAG_DICTIONARY = f.read()

BOOKMARKS_PATH = os.path.expanduser('~/Library/Safari/Bookmarks.plist')


def get_imprint_bookmarks():
    """Fetch all bookmarks from the Imprint folder."""
    with open(BOOKMARKS_PATH, 'rb') as f:
        plist = plistlib.load(f)

    def find_imprint_folder(node):
        if isinstance(node, dict):
            if node.get('Title') == 'Imprint':
                return node
            for v in node.values():
                result = find_imprint_folder(v)
                if result:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = find_imprint_folder(item)
                if result:
                    return result
        return None

    imprint = find_imprint_folder(plist)
    if not imprint:
        return []

    bookmarks = []
    for child in imprint.get('Children', []):
        if 'URLString' in child:
            uri_dict = child.get('URIDictionary', {})
            bookmarks.append({
                'title': uri_dict.get('title', 'Unknown'),
                'url': child.get('URLString')
            })

    return bookmarks


def detect_url_type(url):
    """Detect the type of URL for routing."""
    url_lower = url.lower()
    if 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    else:
        return 'article'


def fetch_with_jina(url):
    """Fetch content using Jina Reader API."""
    jina_url = f"https://r.jina.ai/{url}"

    try:
        response = requests.get(jina_url, timeout=45, headers={
            'Accept': 'text/plain',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        if response.status_code == 200 and len(response.text) > 100:
            return response.text
    except Exception as e:
        print(f"    Jina fetch failed: {e}")

    return None


def fetch_with_parallel(url):
    """Fetch content using Parallel Extract API - better at bypassing bot detection."""
    api_key = os.environ.get('PARALLEL_API_KEY')
    if not api_key:
        print(f"    Parallel API key not configured")
        return None

    try:
        response = requests.post(
            'https://api.parallel.ai/v1beta/extract',
            headers={
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'parallel-beta': 'search-extract-2025-10-10'
            },
            json={
                'urls': [url],
                'objective': 'Extract the full article content including title, author, and main text',
                'excerpts': True,
                'full_content': False
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            # Handle response format - results array with excerpts
            if isinstance(data, dict) and 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                # Combine excerpts into full content
                if 'excerpts' in result and result['excerpts']:
                    content = '\n\n'.join([exc for exc in result['excerpts'] if exc])
                    if len(content) > 100:
                        return content
                # Fallback to full_content if available
                if 'full_content' in result and result['full_content']:
                    return result['full_content']

        print(f"    Parallel returned status {response.status_code}")
        if response.status_code != 200:
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    Parallel fetch failed: {e}")

    return None


def fetch_with_requests(url):
    """Fallback: fetch with requests + BeautifulSoup."""
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Try to find main content
        article = soup.find('article') or soup.find('main') or soup.find('body')
        if article:
            return article.get_text(separator='\n', strip=True)

        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        print(f"    Direct fetch failed: {e}")

    return None


def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\t+', ' ', text)
    return text.strip()


def propose_tags(document):
    """Use Claude to propose tags for a document."""
    prompt = f"""You are a research librarian helping categorize investment research documents for market-linkable research.

Given the document below, propose tags following the Imprint taxonomy. Return a JSON object with these fields:

- topic: One specific topic (e.g., ai_inference_economics, gpu_supply_constraints) - be specific and mechanism-focused, not vague
- sector: One sector (e.g., Infra, Software, Semiconductors, Security, Fintech, Healthcare, Energy, Industrial, Consumer, Macro, Government, Geopolitics)
- entities: Array of companies/people/organizations. Use tickers for public companies (NVDA not Nvidia), canonical names for private (OpenAI not openai), full names for people (Jerome Powell)
- sentiment: One of: bullish, bearish, neutral, mixed (the author's directional tone toward the topic/entities)
- document_type: One of: memo, article, research_report, transcript, presentation, other
- catalyst_window: (optional, null if not applicable) One of: immediate, near_term, medium_term, long_term, structural (leave null if document doesn't imply specific timing)
- summary: One sentence takeaway capturing the core insight or signal

Reference taxonomy (examples, not exhaustive):
{TAG_DICTIONARY[:3000]}

Document title: {document['title']}
Document URL: {document.get('url', 'Unknown')}
Document content (first 8000 chars):
{document['content'][:8000]}

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
        'url',
        document.get('source'),
        document.get('url'),
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


def process_bookmark(bookmark):
    """Process a single bookmark through the full pipeline."""
    url = bookmark['url']
    title = bookmark['title']

    # Check for duplicate (by source_url AND title)
    if document_exists(url, title):
        print(f"  ⏭ Already ingested (same title or source): {url[:50]}...")
        return None

    url_type = detect_url_type(url)

    print(f"  URL: {url[:70]}...")
    print(f"  Title: {title[:50]}")
    print(f"  Type: {url_type}")

    # Fetch content - cascade through methods for best results
    print(f"  Fetching content via Jina...")
    content = fetch_with_jina(url)
    fetch_method = 'jina'

    # If Jina returns insufficient content, try Parallel (better at bot-protected sites)
    if not content or len(content) < 500:
        jina_len = len(content) if content else 0
        print(f"  Jina returned only {jina_len} chars, trying Parallel...")
        parallel_content = fetch_with_parallel(url)
        if parallel_content and len(parallel_content) > len(content or ''):
            content = parallel_content
            fetch_method = 'parallel'
            print(f"  Parallel returned {len(content)} chars")

    # Last resort: direct fetch
    if not content or len(content) < 100:
        print(f"  Trying direct fetch...")
        content = fetch_with_requests(url)
        if content:
            fetch_method = 'direct'

    if not content or len(content) < 50:
        print(f"  ✗ Could not fetch content")
        log_ingestion('url', url, 'failed', 'Could not fetch content')
        return None

    print(f"  Fetched via: {fetch_method}")

    content = clean_text(content)
    print(f"  Raw content length: {len(content)} chars")

    # Clean ad content
    print(f"  Cleaning ad/tracking content...")
    content, reduction = clean_ad_content(content, 'url')
    print(f"  Cleaned content length: {len(content)} chars ({reduction:.1f}% removed)")

    # Detect restricted/paywalled content (very short extracts)
    if len(content) < 500:
        print(f"  ⚠ Content appears restricted/paywalled")
        log_ingestion('url', url, 'restricted', f'Only {len(content)} chars extracted - likely paywalled')
        # Still proceed but flag it

    # Extract source domain
    source = url.split('/')[2] if '/' in url else url
    if url_type == 'twitter':
        source = 'Twitter/X'

    document = {
        'title': title,
        'url': url,
        'content': content,
        'source': source,
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

    # Log success (unless already logged as restricted)
    if len(content) >= 500:
        log_ingestion('url', url, 'success', document_id=doc_id)

    return doc_id


def main():
    """Main ingestion entry point."""
    print("=" * 60)
    print("Imprint Bookmark Ingestion")
    print("=" * 60)

    bookmarks = get_imprint_bookmarks()
    print(f"Found {len(bookmarks)} bookmarks in Imprint folder")
    print()

    for i, bookmark in enumerate(bookmarks):
        print(f"[{i+1}/{len(bookmarks)}] Processing bookmark...")
        try:
            doc_id = process_bookmark(bookmark)
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
