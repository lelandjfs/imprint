"""RAG chain for question answering with conversation memory."""

from typing import List, Optional, AsyncIterator
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from services.retriever import create_retriever
from config import get_settings


def get_llm(model: str, streaming: bool = False):
    """Get LLM instance based on model name."""
    settings = get_settings()

    if model.startswith("claude"):
        return ChatAnthropic(
            model=model,
            temperature=0,
            streaming=streaming,
            api_key=settings.anthropic_api_key,
        )
    else:
        return ChatOpenAI(
            model=model,
            temperature=0,
            streaming=streaming,
            api_key=settings.openai_api_key,
        )


# Query analysis model
class QueryAnalysis(BaseModel):
    """Structured analysis of user query for metadata extraction."""

    topic: Optional[str] = Field(
        None,
        description="Core topic keyword extracted from query that semantically matches database topics. Extract the most specific keyword that will match via ILIKE pattern (e.g., 'nuclear', 'ai', 'semiconductor'). Return null if no clear topic match."
    )
    entities: List[str] = Field(
        default_factory=list,
        description="List of entities mentioned (companies, people, technologies, e.g., ['NVDA', 'Jensen Huang', 'H100'])"
    )
    sectors: List[str] = Field(
        default_factory=list,
        description="Relevant sectors (e.g., ['Energy', 'Semiconductors', 'Software']). Match exactly: Energy, Semiconductors, Infra, Software"
    )
    sentiment_intent: Optional[str] = Field(
        None,
        description="What sentiment is user asking about? Options: 'bullish', 'bearish', 'neutral', 'mixed', or null if not sentiment-focused"
    )
    catalyst_window: Optional[str] = Field(
        None,
        description="Time horizon user cares about. Options: 'near_term', 'medium_term', 'long_term', or null if not time-specific"
    )
    search_intent: str = Field(
        description="What is user trying to find? Options: 'risks', 'opportunities', 'trends', 'comparison', 'facts', 'sentiment_analysis', 'general'"
    )


# Document analysis model
class DocumentAnalysis(BaseModel):
    """Structured analysis of a document for thesis development."""

    summary: str = Field(
        description="2-3 sentence summary of the key insight relevant to the user's query"
    )
    key_excerpt: str = Field(
        description="Most relevant direct quote from the document (50-100 words)"
    )
    thesis_signal: str = Field(
        description="Investment signal from this document. Options: 'bullish', 'bearish', 'neutral', 'mixed'"
    )
    thesis_utility: str = Field(
        description="How an investor could use this information in an investment thesis (1-2 sentences)"
    )


class DocumentAnalysisResponse(BaseModel):
    """Batch analysis response for multiple documents."""

    analyses: List[DocumentAnalysis] = Field(
        description="Analysis for each document in the same order as input"
    )


# Prompt for query analysis
query_analysis_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a query analyzer for an investment research system. "
        "Extract structured metadata from the user's question to enable precise document retrieval. "
        "Be strict and specific - only extract what is explicitly mentioned or clearly implied.\n\n"
        "Available sectors (use exact match): Energy, Semiconductors, Infra, Software\n"
        "Available sentiment values: bullish, bearish, neutral, mixed\n"
        "Available catalyst windows: near_term, medium_term, long_term\n\n"
        "Available topics in database: {available_topics}\n\n"
        "For topic extraction:\n"
        "1. Look at the user's query and identify the main theme/subject\n"
        "2. Find a keyword from the available topics that would semantically match the query\n"
        "3. Extract the core keyword (e.g., 'nuclear' from 'nuclear_energy_grid', 'ai' from 'ai_infrastructure')\n"
        "4. This keyword will be used with ILIKE pattern matching to find all related topics\n\n"
        "Examples:\n"
        "- Query: 'SMR buildout trends' → topic: 'nuclear' (matches nuclear_energy_grid, nuclear_defense_policy)\n"
        "- Query: 'GenAI training costs' → topic: 'ai' (matches ai_infrastructure, ai_data_training)\n"
        "- Query: 'TSMC margins' → topic: 'semiconductor' (matches semiconductor_design_economics)\n"
        "- Query: 'hyperscaler capex' → topic: 'data_center' (matches data_center_economics)\n\n"
        "If the user mentions company tickers, expand them to entities (e.g., 'NVDA' → 'NVIDIA', 'TSLA' → 'Tesla')."
    ),
    ("human", "{question}")
])


# Prompt for document analysis
document_analysis_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an investment research analyst analyzing documents to help build investment theses.\n\n"
        "For each document provided, you must:\n"
        "1. Summary: Extract the 2-3 sentence key insight most relevant to the user's query\n"
        "2. Key Excerpt: Find the most important direct quote (50-100 words)\n"
        "3. Thesis Signal: Determine if this is bullish, bearish, neutral, or mixed for the topic\n"
        "4. Thesis Utility: Explain how an investor could use this in an investment thesis\n\n"
        "User Query: {question}\n\n"
        "Documents to analyze:\n{documents}"
    )
])


# Prompt for condensing follow-up questions
condense_question_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given the conversation history and a follow-up question, "
            "rephrase the question as a standalone query that captures all necessary context. "
            "If it's already standalone, return it unchanged.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)


# Prompt for RAG answer generation
rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an investment research assistant helping analyze documents in the Imprint knowledge base. "
            "Answer the question using ONLY the provided context below. "
            "Be concise and specific. Cite document titles when referencing information. "
            "If the context doesn't contain enough information to answer fully, say so.\n\n"
            "Context:\n{context}",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)


async def stream_rag_response(
    question: str,
    chat_history: List[BaseMessage],
    model: str = "claude-sonnet-4-5-20250929",
    filter_sector: Optional[List[str]] = None,
    filter_entities: Optional[List[str]] = None,
    filter_sentiment: Optional[List[str]] = None,
    filter_catalyst_window: Optional[List[str]] = None,
    filter_weighting: Optional[List[int]] = None,
    filter_topic: Optional[str] = None,
) -> AsyncIterator[dict]:
    """Stream RAG response with sources."""
    import logging
    from supabase import create_client
    from config import get_settings

    # Condense question if there's chat history
    standalone_question = question
    if chat_history:
        llm_for_condensing = get_llm(model, streaming=False)
        condense_chain = condense_question_prompt | llm_for_condensing | StrOutputParser()
        standalone_question = await condense_chain.ainvoke({
            "input": question,
            "chat_history": chat_history
        })

    # Fetch available topics from database dynamically
    settings = get_settings()
    supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        response = supabase_client.table("imprint_documents").select("topic").execute()
        available_topics = sorted(set(row["topic"] for row in response.data if row.get("topic")))
        topics_str = ", ".join(available_topics)
    except Exception as e:
        logging.warning(f"Failed to fetch topics: {e}")
        available_topics = []
        topics_str = "nuclear_energy_grid, ai_infrastructure, semiconductor_design_economics, data_center_economics"

    # Analyze query to extract metadata filters
    llm_for_analysis = get_llm(model, streaming=False)
    analysis_chain = query_analysis_prompt | llm_for_analysis.with_structured_output(QueryAnalysis)

    query_metadata: QueryAnalysis = await analysis_chain.ainvoke({
        "question": standalone_question,
        "available_topics": topics_str
    })

    # Merge auto-extracted filters with manual filters (manual takes precedence)
    final_sector = filter_sector if filter_sector else (query_metadata.sectors if query_metadata.sectors else None)
    final_entities = filter_entities if filter_entities else (query_metadata.entities if query_metadata.entities else None)
    final_sentiment = filter_sentiment if filter_sentiment else ([query_metadata.sentiment_intent] if query_metadata.sentiment_intent else None)
    final_catalyst = filter_catalyst_window if filter_catalyst_window else ([query_metadata.catalyst_window] if query_metadata.catalyst_window else None)
    final_topic = filter_topic if filter_topic else query_metadata.topic

    # Log extracted metadata for debugging
    import logging
    logging.info(f"Query Analysis: {query_metadata.model_dump()}")
    logging.info(f"Applied Filters - sector: {final_sector}, entities: {final_entities}, sentiment: {final_sentiment}, catalyst: {final_catalyst}, topic: {final_topic}")

    # Yield query analysis for debugging/tracing
    yield {
        "type": "query_analysis",
        "analysis": {
            "topic": query_metadata.topic,
            "entities": query_metadata.entities,
            "sectors": query_metadata.sectors,
            "sentiment_intent": query_metadata.sentiment_intent,
            "catalyst_window": query_metadata.catalyst_window,
            "search_intent": query_metadata.search_intent,
        }
    }

    # HYBRID RETRIEVAL: Two-path approach
    # Path 1: Strict metadata filtering (if filters exist)
    # Path 2: Semantic search with high similarity threshold

    docs = []
    seen_ids = set()

    # Path 1: Metadata-filtered retrieval (strict match)
    if any([final_sector, final_entities, final_sentiment, final_catalyst, final_topic]):
        metadata_retriever = create_retriever(
            k=10,  # Get more candidates with metadata filters
            filter_sector=final_sector,
            filter_entities=final_entities,
            filter_sentiment=final_sentiment,
            filter_catalyst_window=final_catalyst,
            filter_weighting=filter_weighting,
            filter_topic=final_topic,
        )
        metadata_docs = await metadata_retriever.ainvoke(standalone_question)
        for doc in metadata_docs:
            if doc.metadata["id"] not in seen_ids:
                docs.append(doc)
                seen_ids.add(doc.metadata["id"])
        logging.info(f"Metadata retrieval returned {len(metadata_docs)} docs")

    # Path 2: Pure semantic search (no filters, high similarity threshold)
    semantic_retriever = create_retriever(
        k=10,
        filter_sector=None,
        filter_entities=None,
        filter_sentiment=None,
        filter_catalyst_window=None,
        filter_weighting=None,
    )
    semantic_docs = await semantic_retriever.ainvoke(standalone_question)

    # Only add semantic results with similarity > 0.4 (good semantic match)
    # Note: 0.7 was way too strict - real queries get 0.3-0.6 similarity
    for doc in semantic_docs:
        if doc.metadata["id"] not in seen_ids and doc.metadata.get("similarity", 0) > 0.4:
            docs.append(doc)
            seen_ids.add(doc.metadata["id"])
    logging.info(f"Semantic retrieval added {len([d for d in semantic_docs if d.metadata.get('similarity', 0) > 0.4])} docs (filtered by similarity > 0.4)")

    # Take top 5 results (combined from both paths)
    docs = sorted(docs, key=lambda x: x.metadata.get("similarity", 0), reverse=True)[:5]
    logging.info(f"Final result count: {len(docs)}")

    # Analyze documents for thesis utility
    analyses = []
    if docs:
        try:
            # Format documents for analysis
            docs_text = "\n\n---\n\n".join([
                f"Document {i+1}: {doc.metadata['title']}\n"
                f"Topic: {doc.metadata['topic']} | Sector: {doc.metadata['sector']}\n"
                f"Summary: {doc.metadata['summary']}\n\n"
                f"Content excerpt:\n{doc.page_content[:1000]}"
                for i, doc in enumerate(docs)
            ])

            # Run analysis chain
            llm_for_analysis = get_llm(model, streaming=False)
            analysis_chain = document_analysis_prompt | llm_for_analysis.with_structured_output(DocumentAnalysisResponse)

            analysis_response: DocumentAnalysisResponse = await analysis_chain.ainvoke({
                "question": standalone_question,
                "documents": docs_text
            })

            analyses = [
                {
                    "summary": analysis.summary,
                    "key_excerpt": analysis.key_excerpt,
                    "thesis_signal": analysis.thesis_signal,
                    "thesis_utility": analysis.thesis_utility
                }
                for analysis in analysis_response.analyses
            ]
            logging.info(f"Generated {len(analyses)} document analyses")
        except Exception as e:
            logging.error(f"Error analyzing documents: {str(e)}")
            # Continue without analysis if it fails

    # Yield sources with analysis
    sources = [
        {
            "id": doc.metadata["id"],
            "title": doc.metadata["title"],
            "summary": doc.metadata["summary"],
            "topic": doc.metadata["topic"],
            "sector": doc.metadata["sector"],
            "sentiment": doc.metadata["sentiment"],
            "document_type": doc.metadata["document_type"],
            "catalyst_window": doc.metadata["catalyst_window"],
            "weighting": doc.metadata["weighting"],
            "entities": doc.metadata["entities"],
            "source_url": doc.metadata["source_url"],
            "similarity": doc.metadata["similarity"],
            "analysis": analyses[i] if i < len(analyses) else None,
        }
        for i, doc in enumerate(docs)
    ]
    yield {"type": "sources", "documents": sources}

    # Format context from retrieved docs
    context = "\n\n---\n\n".join(
        [
            f"Document: {doc.metadata['title']}\n"
            f"Topic: {doc.metadata['topic']} | Sector: {doc.metadata['sector']} | Sentiment: {doc.metadata['sentiment']}\n"
            f"Summary: {doc.metadata['summary']}\n\n"
            f"{doc.page_content[:2000]}"  # Limit context per doc
            for doc in docs
        ]
    )

    # Create streaming LLM
    llm = get_llm(model, streaming=True)

    # Format prompt
    formatted_prompt = rag_prompt.format_messages(
        context=context,
        chat_history=chat_history,
        input=question,
    )

    # Stream response
    full_response = ""
    async for chunk in llm.astream(formatted_prompt):
        content = chunk.content
        if content:
            full_response += content
            yield {"type": "token", "content": content}

    # Yield final response
    yield {"type": "done", "full_response": full_response}
