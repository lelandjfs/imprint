"""Chat endpoint with streaming support."""

import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langsmith import trace, Client
from services.rag_chain import stream_rag_response
from services.memory import memory_store


router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""

    session_id: str
    message: str
    model: str = "claude-sonnet-4-5-20250929"
    filters: Optional[dict] = None


class ModelInfo(BaseModel):
    """Model information."""

    id: str
    name: str
    provider: str


class FeedbackRequest(BaseModel):
    """Feedback request model."""

    run_id: str
    score: int  # 1 for thumbs up, 0 for thumbs down
    comment: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Stream chat responses using RAG pipeline.

    Returns Server-Sent Events (SSE) stream with:
    - sources: Retrieved documents
    - token: Individual response tokens
    - done: Final complete response
    """
    try:
        # Get conversation history
        chat_history = memory_store.get_messages(request.session_id)

        # Add user message to history
        memory_store.add_user_message(request.session_id, request.message)

        # Extract filters
        filters = request.filters or {}
        filter_sector = filters.get("sector")
        filter_entities = filters.get("entities")
        filter_sentiment = filters.get("sentiment")
        filter_catalyst_window = filters.get("catalyst_window")
        filter_weighting = filters.get("weighting")
        filter_topic = filters.get("topic")

        # Stream response
        async def event_stream():
            full_response = ""
            run_id = None
            try:
                # Wrap entire RAG pipeline in a single trace
                with trace(name="Chat RAG Pipeline", run_type="chain",
                          inputs={"question": request.message, "model": request.model},
                          metadata={"session_id": request.session_id}) as run_tree:
                    async for chunk in stream_rag_response(
                        question=request.message,
                        chat_history=chat_history,
                        model=request.model,
                        filter_sector=filter_sector,
                        filter_entities=filter_entities,
                        filter_sentiment=filter_sentiment,
                        filter_catalyst_window=filter_catalyst_window,
                        filter_weighting=filter_weighting,
                        filter_topic=filter_topic,
                    ):
                        # Format as SSE
                        yield f"data: {json.dumps(chunk)}\n\n"

                        # Track full response
                        if chunk["type"] == "done":
                            full_response = chunk["full_response"]

                    # Capture run_id after trace completes
                    run_id = str(run_tree.id) if run_tree else None

                # Send run_id with done event for feedback
                if run_id:
                    done_with_id = {"type": "run_id", "run_id": run_id}
                    yield f"data: {json.dumps(done_with_id)}\n\n"

                # Add AI response to memory
                if full_response:
                    memory_store.add_ai_message(request.session_id, full_response)

            except Exception as e:
                error_data = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a LangSmith run.

    Score: 1 for thumbs up, 0 for thumbs down.
    """
    try:
        client = Client()
        client.create_feedback(
            run_id=request.run_id,
            key="user_rating",
            score=request.score,
            comment=request.comment
        )
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models():
    """Get available LLM models."""
    return {
        "models": [
            ModelInfo(
                id="claude-sonnet-4-6",
                name="Claude Sonnet 4.6",
                provider="anthropic",
            ),
            ModelInfo(
                id="claude-sonnet-4-5-20250929",
                name="Claude Sonnet 4.5 (Sep 2025)",
                provider="anthropic",
            ),
            ModelInfo(
                id="claude-opus-4-6",
                name="Claude Opus 4.6",
                provider="anthropic",
            ),
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
            ),
        ],
        "default": "claude-sonnet-4-5-20250929",
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    memory_store.clear_session(session_id)
    return {"message": "Session cleared"}
