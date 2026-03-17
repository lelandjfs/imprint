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
    filter_catalyst_window: Optional[List[str]] = None
    filter_weighting: Optional[List[int]] = None
    filter_topic: Optional[str] = None
    filter_status: str = "active"

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve documents relevant to query."""
        import logging

        # Generate embedding for query
        logging.info(f"Generating embedding for query: {query[:100]}")
        query_embedding = self.embeddings.embed_query(query)
        logging.info(f"Embedding generated, length: {len(query_embedding)}")

        # Call Supabase RPC function
        logging.info(f"Calling match_imprint_documents with k={self.k}, filters: sector={self.filter_sector}, entities={self.filter_entities}, topic={self.filter_topic}")
        try:
            response = self.supabase_client.rpc(
                "match_imprint_documents",
                {
                    "query_embedding": query_embedding,
                    "match_count": self.k,
                    "filter_sector": self.filter_sector,
                    "filter_entities": self.filter_entities,
                    "filter_sentiment": self.filter_sentiment,
                    "filter_catalyst_window": self.filter_catalyst_window,
                    "filter_weighting": self.filter_weighting,
                    "filter_topic": self.filter_topic,
                    "filter_status": self.filter_status,
                },
            ).execute()

            logging.info(f"Supabase returned {len(response.data) if response.data else 0} documents")
            if response.data:
                logging.info(f"First doc similarity: {response.data[0].get('similarity', 'N/A')}, title: {response.data[0].get('title', 'N/A')}")
                logging.info(f"First doc entities: {response.data[0].get('entities', 'N/A')}, sector: {response.data[0].get('sector', 'N/A')}")
        except Exception as e:
            logging.error(f"Error calling Supabase RPC: {str(e)}")
            raise

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
                "document_type": row["document_type"],
                "catalyst_window": row["catalyst_window"],
                "weighting": row["weighting"],
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
    filter_catalyst_window: Optional[List[str]] = None,
    filter_weighting: Optional[List[int]] = None,
    filter_topic: Optional[str] = None,
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
        api_key=settings.openai_api_key,
    )

    return ImprintRetriever(
        supabase_client=supabase_client,
        embeddings=embeddings,
        k=k,
        filter_sector=filter_sector,
        filter_entities=filter_entities,
        filter_sentiment=filter_sentiment,
        filter_catalyst_window=filter_catalyst_window,
        filter_weighting=filter_weighting,
        filter_topic=filter_topic,
    )
