"""Quick script to get unique topics from Supabase."""

import os
from supabase import create_client

# Get env vars
supabase_url = os.getenv("SUPABASE_URL", "https://qvwqquyaxunxyiwtobsu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "sb_publishable_9ijcCdSAe65T5fNwE2aQog_YLBK6gvX")

# Create client
client = create_client(supabase_url, supabase_key)

# Query unique topics
response = client.table("imprint_documents").select("topic").execute()

# Get unique topics
topics = set()
for row in response.data:
    if row.get("topic"):
        topics.add(row["topic"])

# Print sorted
for topic in sorted(topics):
    print(topic)
