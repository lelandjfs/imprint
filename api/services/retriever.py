"""Supabase pgvector retriever for Imprint documents."""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_openai import OpenAIEmbeddings
from supabase import create_client, Client
from config import get_settings


class ImprintRetriever(BaseRetriever):
    """Custom retriever for Imprint documents using Supabase pgvector."""

    supabase_client: Client
    embeddings: OpenAIEmbeddings
    k: int = 5
    filter_sector: Optional[List[str]] = None
    filter_entities: Optional[List[str]] = None
    filter_sentiment: Optional[List[str]] = None
    filter_status: str = "active"

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve documents relevant to query."""
        # Generate embedding for query
        query_embedding = self.embeddings.embed_query(query)

        # Call Supabase RPC function
        response = self.supabase_client.rpc(
            "match_imprint_documents",
            {
                "query_embedding": query_embedding,
                "match_count": self.k,
                "filter_sector": self.filter_sector,
                "filter_entities": self.filter_entities,
                "filter_sentiment": self.filter_sentiment,
                "filter_status": self.filter_status,
            },
        ).execute()

        # Convert to LangChain Documents
        documents = []
        for row in response.data:
            metadata = {
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "topic": row["topic"],
                "sector": row["sector"],
                "sentiment": row["sentiment"],
                "entities": row["entities"],
                "source_url": row["source_url"],
                "similarity": row["similarity"],
            }
            documents.append(
                Document(
                    page_content=row["content"],
                    metadata=metadata,
                )
            )

        return documents


def create_retriever(
    k: int = 5,
    filter_sector: Optional[List[str]] = None,
    filter_entities: Optional[List[str]] = None,
    filter_sentiment: Optional[List[str]] = None,
) -> ImprintRetriever:
    """Create a configured Imprint retriever."""
    settings = get_settings()

    supabase_client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        dimensions=1536,
    )

    return ImprintRetriever(
        supabase_client=supabase_client,
        embeddings=embeddings,
        k=k,
        filter_sector=filter_sector,
        filter_entities=filter_entities,
        filter_sentiment=filter_sentiment,
    )
