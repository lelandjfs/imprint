"""RAG chain for question answering with conversation memory."""

from typing import List, Optional, AsyncIterator
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from services.retriever import create_retriever


def get_llm(model: str, streaming: bool = False):
    """Get LLM instance based on model name."""
    if model.startswith("claude"):
        return ChatAnthropic(
            model=model,
            temperature=0,
            streaming=streaming,
        )
    else:
        return ChatOpenAI(
            model=model,
            temperature=0,
            streaming=streaming,
        )


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
    model: str = "claude-3-5-sonnet-20250107",
    filter_sector: Optional[List[str]] = None,
    filter_entities: Optional[List[str]] = None,
    filter_sentiment: Optional[List[str]] = None,
) -> AsyncIterator[dict]:
    """Stream RAG response with sources."""

    # Create retriever with filters
    retriever = create_retriever(
        k=5,
        filter_sector=filter_sector,
        filter_entities=filter_entities,
        filter_sentiment=filter_sentiment,
    )

    # Condense question if there's chat history
    standalone_question = question
    if chat_history:
        llm_for_condensing = get_llm(model, streaming=False)
        condense_chain = condense_question_prompt | llm_for_condensing | StrOutputParser()
        standalone_question = await condense_chain.ainvoke({
            "input": question,
            "chat_history": chat_history
        })

    # Retrieve documents using standalone question
    docs = await retriever.ainvoke(standalone_question)

    # Yield sources first
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
        }
        for doc in docs
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
