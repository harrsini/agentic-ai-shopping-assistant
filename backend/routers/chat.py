"""
Chat Router
-----------
POST /chat  — unified entry point for all shopping queries.

The endpoint delegates entirely to ``process_query()``, which routes
internally based on detected intent:
  - recommend   → recommendation pipeline (MongoDB + XGBoost + Groq)
  - compare     → side-by-side product comparison (MongoDB + Groq)
  - information → conversational Groq response

POST /chat/recommend is kept for backwards-compatibility with any existing
callers that pass explicit ``user_preferences``.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from schemas.request_models import ChatRequest, RecommendRequest
from schemas.response_models import ChatResponse, RecommendResponse, Product
from services import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat & Recommendations"],
)


# ---------------------------------------------------------------------------
# POST /chat  — unified query endpoint
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a shopping query to the AI assistant",
    description=(
        "Accepts a plain-text message and routes it through the full "
        "Agentic AI pipeline. The intent is detected automatically and "
        "the response ``type`` field tells the frontend which branch ran:\n\n"
        "- **recommendation** — ranked product list from MongoDB + XGBoost\n"
        "- **comparison** — side-by-side AI comparison of two products\n"
        "- **information** — conversational answer from Groq Llama\n"
        "- **error** — something went wrong (``success: false``)"
    ),
    responses={
        200: {"description": "Query processed — check ``success`` and ``type`` fields"},
        422: {"description": "Validation error — message is empty or too long"},
        500: {"description": "Unexpected server error"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Route the user's message through ``process_query()`` and return a
    standardised envelope response.

    The handler never raises a 503 for LLM/DB failures — those are caught
    inside the service layer and surfaced as ``{"success": false, "type":
    "error", ...}`` so the frontend always receives a parseable JSON body.
    """
    logger.info(
        "POST /chat received. message_preview='%s'",
        request.message[:80],
    )

    try:
        result: dict = await llm_service.process_query(request.message)

        response_type: str = result.get("type", "error")
        is_error: bool = response_type == "error"

        # Build branch-specific data payload — strip the "type" key.
        data: dict = {k: v for k, v in result.items() if k != "type"}

        logger.info(
            "POST /chat completed. type='%s', success=%s",
            response_type,
            not is_error,
        )

        return ChatResponse(
            success=not is_error,
            type=response_type,
            data=data,
            error=data.get("message") if is_error else None,
        )

    except Exception:
        logger.exception("Unhandled exception in POST /chat.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


# ---------------------------------------------------------------------------
# POST /chat/recommend  — explicit recommendation endpoint (kept for compat)
# ---------------------------------------------------------------------------

@router.post(
    "/recommend",
    response_model=ChatResponse,
    summary="Generate product recommendations from explicit preferences",
    description=(
        "Accepts structured ``user_preferences`` and runs the recommendation "
        "pipeline directly, bypassing intent detection. Kept for "
        "backwards-compatibility — prefer ``POST /chat`` for new integrations."
    ),
    responses={
        200: {"description": "Recommendations generated successfully"},
        503: {"description": "Recommendation service unavailable"},
    },
)
async def recommend(request: RecommendRequest) -> ChatResponse:
    """
    Run the recommendation pipeline from explicit user preferences.

    Constructs a synthetic query from the preferences dict so it can be
    passed to ``get_product_recommendations()`` without going through intent
    extraction again.
    """
    logger.info("POST /chat/recommend received. preferences=%s", request.user_preferences)

    try:
        products = await llm_service.get_product_recommendations(
            user_preferences=request.user_preferences,
        )

        top = products[: request.limit]

        logger.info(
            "POST /chat/recommend complete. returning %d product(s).", len(top)
        )

        return ChatResponse(
            success=True,
            type="recommendation",
            data={"products": top},
        )

    except Exception:
        logger.exception("Recommendation pipeline failed in POST /chat/recommend.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation service is temporarily unavailable.",
        )
