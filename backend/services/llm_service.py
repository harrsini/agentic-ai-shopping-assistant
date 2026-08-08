"""
LLM Service
-----------
Groq Llama-powered service for:
  - Conversational responses   (generate_response)
  - Intent extraction          (extract_user_intent)
  - Recommendation explanation (generate_recommendation_explanation)
  - Full recommendation pipeline (get_product_recommendations)
"""

# ---------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------
import json
import logging
import re

# ---------------------------------------------------------------------------
# Third-party
# ---------------------------------------------------------------------------
from groq import Groq

# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------
from config import get_settings
from services.ml_service import predict_product
from services.mongodb_service import get_candidate_products, search_products_with_filters

# ---------------------------------------------------------------------------
# Module-level setup
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
settings = get_settings()

client = Groq(api_key=settings.groq_api_key)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_NAME = "llama-3.3-70b-versatile"
MAX_TOKENS = 1024
TEMPERATURE = 0.7

SYSTEM_PROMPT = (
    "You are an intelligent AI Shopping Assistant. "
    "Help users choose products based on their needs, budget and preferences. "
    "Be concise, friendly and accurate."
)

INTENT_SCHEMA = {
    "intent": "",
    "product": "",
    "brand": "",
    "budget": None,
    "category": "",
    "keywords": [],
}

_DEFAULT_INTENT: dict = {
    "intent": "recommend",
    "product": "",
    "brand": "",
    "budget": None,
    "category": "",
    "keywords": [],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_response(
    message: str,
    conversation_id: str | None = None,
) -> str:
    """
    Generate a conversational response using the Groq Llama model.

    Parameters
    ----------
    message : str
        The user's shopping query.
    conversation_id : str | None
        Optional identifier for conversation continuity (not yet persisted).

    Returns
    -------
    str
        The assistant's reply, or a safe fallback message on failure.
    """
    logger.info(
        "Generating response. conversation_id=%s, message_preview='%s'",
        conversation_id,
        message[:80],
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        response = completion.choices[0].message.content
        logger.info("Groq response generated successfully.")
        return response

    except Exception:
        logger.exception("Groq API call failed in generate_response.")
        return (
            "Sorry, I couldn't generate a response at the moment. "
            "Please try again."
        )


async def extract_user_intent(message: str) -> dict:
    """
    Extract structured shopping intent from a natural-language query.

    Calls the Groq model and requests a strict JSON response.
    Strips any markdown code fences the model may add.
    Returns a validated dict; falls back to ``_DEFAULT_INTENT`` on failure.

    Parameters
    ----------
    message : str
        Raw user message.

    Returns
    -------
    dict
        Keys: intent, product, brand, budget, category, keywords.
    """
    prompt = f"""You are an AI shopping assistant.

Extract the user's shopping intent from the query below.

Return ONLY valid JSON — no explanation, no markdown fences.

Schema:
{{
    "intent": "",
    "product": "",
    "brand": "",
    "budget": null,
    "category": "",
    "keywords": []
}}

Possible intent values: recommend | compare | information

Examples:

User: Show me a moisturizer for dry skin
Output: {{"intent":"recommend","product":"moisturizer","brand":"","budget":null,"category":"skincare","keywords":["dry skin"]}}

User: Compare Cetaphil and CeraVe moisturizers
Output: {{"intent":"compare","product":"moisturizer","brand":"","budget":null,"category":"skincare","keywords":["Cetaphil","CeraVe"]}}

User: What is niacinamide?
Output: {{"intent":"information","product":"niacinamide","brand":"","budget":null,"category":"skincare","keywords":[]}}

User Query: {message}"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=200,
        )
        raw = completion.choices[0].message.content or ""

        # Strip markdown code fences that models sometimes add.
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()

        intent = json.loads(raw)
        logger.info("Intent extracted successfully: intent=%s", intent.get("intent"))
        return intent

    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse intent JSON from Groq response. "
            "Returning default intent."
        )
        return _DEFAULT_INTENT.copy()

    except Exception:
        logger.exception("Unexpected error in extract_user_intent.")
        return _DEFAULT_INTENT.copy()


async def generate_recommendation_explanation(
    query: str,
    product: dict,
) -> str:
    """
    Generate a concise 2–3 sentence explanation of why a product suits the query.

    Parameters
    ----------
    query : str
        The original user search query.
    product : dict
        MongoDB product document (must contain title, brand, price, etc.).

    Returns
    -------
    str
        AI-generated explanation, or a safe fallback string on failure.
    """
    prompt = f"""You are an AI shopping assistant.

A user searched for: "{query}"

Recommended Product:
  Title:          {product.get("title")}
  Brand:          {product.get("brand")}
  Price:          {product.get("price")}
  Average Rating: {product.get("average_rating")}
  Features:       {product.get("features")}

Explain in 2-3 sentences why this product is a good match.
Be concise and helpful."""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=200,
        )
        return completion.choices[0].message.content.strip()

    except Exception:
        logger.exception(
            "Groq API call failed in generate_recommendation_explanation "
            "for product '%s'.",
            product.get("title", "Unknown"),
        )
        return "Recommended based on your preferences."


async def get_product_recommendations(
    user_preferences: dict,
) -> list[dict]:
    """
    Agentic recommendation pipeline: intent → broad retrieval → XGBoost → LLM.

    The LLM is the decision-maker. MongoDB provides a broad candidate pool;
    XGBoost ranks by predicted quality; Groq selects and explains the best 5.
    The pipeline never returns an empty list solely because a keyword has no
    exact match in the database.

    Workflow
    --------
    1. Extract structured intent from the user query.
    2. Retrieve up to 100 candidate products using broad filters only
       (rating floor, optional brand, optional category, optional budget).
    3. Score every candidate with ``predict_product()``; failed predictions
       default to 0.0 and are kept in the pool.
    4. Sort candidates by ML score descending; send top 20 to Groq.
    5. Groq selects the best 5 products and writes a personalised explanation
       for each — one API call for all 5.
    6. Format and return the final list.

    Parameters
    ----------
    user_preferences : dict
        Must contain ``query`` (str).
        Optional: ``brand``, ``category``, ``min_rating``, ``budget``.

    Returns
    -------
    list[dict]
        Up to 5 ranked and explained product dicts, each containing:
        id, asin, title, brand, category, price, average_rating,
        rating_number, image, features, ml_score, ai_explanation.
    """
    raw_query: str = user_preferences.get("query", "")

    if not raw_query:
        logger.warning("get_product_recommendations called with no query.")
        return []

    logger.info("Recommendation pipeline started. query='%s'", raw_query)

    # ── Step 1: Intent extraction ───────────────────────────────────────────
    intent = await extract_user_intent(raw_query)

    # product_type is the core type constraint (e.g. "shampoo", "moisturizer").
    # Prefer intent["product"] as it's the most specific noun extracted.
    # Fall back to the first keyword, then to nothing (broad retrieval).
    product_type: str | None = (
        intent.get("product")
        or (intent.get("keywords") or [None])[0]
        or None
    )

    brand: str | None = (
        intent.get("brand") or user_preferences.get("brand") or None
    )
    category: str | None = (
        intent.get("category") or user_preferences.get("category") or None
    )
    min_rating: float = float(user_preferences.get("min_rating", 3.5))

    # Budget: prefer caller's value, fall back to LLM-extracted budget.
    budget = user_preferences.get("budget") or intent.get("budget")
    max_price: float | None = float(budget) if budget else None

    logger.info(
        "Intent: product_type=%s, brand=%s, category=%s, max_price=%s, min_rating=%s",
        product_type, brand, category, max_price, min_rating,
    )

    # ── Step 2: Candidate retrieval with product-type filter ───────────────
    # product_type enforces relevance (multi-field regex across title,
    # category, features, description). brand/category/price narrow further.
    try:
        candidates = await get_candidate_products(
            product_type=product_type,
            brand=brand,
            category=category,
            max_price=max_price,
            min_rating=min_rating,
            limit=100,
        )
        logger.info(
            "Candidate pool: %d product(s) for product_type='%s'.",
            len(candidates),
            product_type,
        )
    except Exception:
        logger.exception("Candidate retrieval failed.")
        return []

    if not candidates and product_type:
        # Relax price and rating constraints but keep the type filter.
        logger.warning(
            "No candidates with full filters. Relaxing price/rating for type='%s'.",
            product_type,
        )
        try:
            candidates = await get_candidate_products(
                product_type=product_type,
                brand=brand,
                min_rating=0,
                limit=100,
            )
            logger.info(
                "Relaxed retry returned %d candidate(s) for type='%s'.",
                len(candidates),
                product_type,
            )
        except Exception:
            logger.exception("Relaxed candidate retrieval failed.")

    if not candidates:
        # Last resort: drop the type filter entirely — broad pool.
        logger.warning(
            "Still no candidates. Falling back to unfiltered retrieval."
        )
        try:
            candidates = await get_candidate_products(
                min_rating=3.5,
                limit=100,
            )
            logger.info(
                "Unfiltered fallback returned %d candidate(s).", len(candidates)
            )
        except Exception:
            logger.exception("Unfiltered candidate retrieval failed.")
            return []

    if not candidates:
        logger.error("Candidate pool is empty after all retries.")
        return []

    # ── Step 3: XGBoost scoring ────────────────────────────────────────────
    for product in candidates:
        try:
            product["ml_score"] = predict_product(product)
        except Exception:
            logger.warning(
                "ML prediction failed for '%s'. Defaulting to 0.0.",
                product.get("title", "Unknown"),
            )
            product["ml_score"] = 0.0

    # ── Step 4: Sort by ML score ────────────────────────────────────────────
    candidates.sort(key=lambda p: p["ml_score"], reverse=True)
    logger.info(
        "Top ML score: %.4f | Bottom of top-20: %.4f",
        candidates[0]["ml_score"],
        candidates[min(19, len(candidates) - 1)]["ml_score"],
    )

    # ── Step 5: LLM selection and explanation (single Groq call) ───────────
    selected = await _llm_select_and_explain(
        query=raw_query,
        candidates=candidates,
    )
    logger.info(
        "Recommendation pipeline complete. Returning %d product(s).", len(selected)
    )

    # ── Step 6: Format and return ───────────────────────────────────────────
    return [_format_product(p) for p in selected]


async def compare_products(query: str, intent: dict) -> dict:
    """
    Compare products using the LLM's own knowledge — no MongoDB, no XGBoost.

    Workflow
    --------
    1. Extract product/brand names from ``intent["keywords"]``.
    2. Validate at least two names are present.
    3. Build a structured comparison prompt and call Groq.
    4. If Groq indicates the products are unknown or obscure, surface that
       message rather than fabricating information.
    5. Return ``{"type": "comparison", "comparison": str, "products": []}``.

    The ``products`` list is intentionally empty — this workflow uses LLM
    knowledge rather than database records, so there are no product dicts
    to attach.

    Parameters
    ----------
    query : str
        Original natural-language query from the user.
    intent : dict
        Extracted intent dict — must contain a ``keywords`` list with the
        names of the products or brands to compare.

    Returns
    -------
    dict
        ``{"type": "comparison", "comparison": str, "products": []}``
    """
    keywords: list[str] = intent.get("keywords") or []

    logger.info(
        "compare_products called (LLM-only). keywords=%s, query_preview='%s'",
        keywords,
        query[:80],
    )

    # ── Step 1: Validate we have at least two names to compare ─────────────
    if len(keywords) < 2:
        logger.warning(
            "Comparison requires at least 2 keywords; received %d.", len(keywords)
        )
        return {
            "type": "comparison",
            "comparison": (
                "I need at least two product or brand names to compare. "
                "Try something like: *'Compare CeraVe and Cetaphil moisturizers'*."
            ),
            "products": [],
        }

    product_a, product_b = keywords[0], keywords[1]
    logger.info("Comparing '%s' vs '%s'.", product_a, product_b)

    # ── Step 2: Build prompt and call Groq ─────────────────────────────────
    prompt = _build_llm_comparison_prompt(query, product_a, product_b)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=900,
        )
        comparison_text = completion.choices[0].message.content.strip()
        logger.info("Groq LLM comparison generated successfully.")

    except Exception:
        logger.exception("Groq API call failed in compare_products.")
        comparison_text = (
            "I wasn't able to generate a comparison right now. "
            "Please try again."
        )

    return {
        "type": "comparison",
        "comparison": comparison_text,
        "products": [],
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _llm_select_and_explain(
    query: str,
    candidates: list[dict],
) -> list[dict]:
    """
    Ask Groq to choose the best 5 products from the ML-ranked candidate list
    and write a personalised explanation for each selection.

    A single API call handles both selection and explanation, keeping latency
    low regardless of candidate pool size.

    The model receives a numbered catalogue of up to 20 products (title, brand,
    price, average_rating, rating_number, features, ml_score) plus the original
    user query. It is instructed to return a JSON array of exactly 5 objects,
    each with ``index`` (1-based position in the catalogue) and
    ``ai_explanation``.

    If the Groq call fails or returns unparseable JSON, the function falls back
    to the top 5 candidates by ML score with a generic explanation.

    Parameters
    ----------
    query : str
        Original user query — gives the LLM context for relevance reasoning.
    candidates : list[dict]
        ML-scored and sorted product dicts (highest score first).
        Only the first 20 are sent to the LLM.

    Returns
    -------
    list[dict]
        Up to 5 product dicts, each with ``ai_explanation`` populated.
    """
    pool = candidates[:20]

    # Build a compact catalogue string for the prompt.
    catalogue_lines: list[str] = []
    for i, p in enumerate(pool, start=1):
        features = (p.get("features") or [])[:3]
        feature_text = "; ".join(features) if features else "N/A"
        catalogue_lines.append(
            f"{i}. Title: {p.get('title', 'N/A')} | "
            f"Brand: {p.get('brand', 'N/A')} | "
            f"Price: {p.get('price', 'N/A')} | "
            f"Rating: {p.get('average_rating', 'N/A')} "
            f"({p.get('rating_number', 0)} reviews) | "
            f"ML Score: {round(p.get('ml_score', 0.0), 4)} | "
            f"Features: {feature_text}"
        )
    catalogue = "\n".join(catalogue_lines)

    prompt = f"""You are an expert AI Shopping Assistant.

A user asked: "{query}"

Below is a ranked catalogue of products retrieved from the database.
ML Score reflects predicted product quality (higher is better).

{catalogue}

Your task:
1. Reason about the user's needs based on their query.
2. Consider ML score, average rating, review count, price, and features.
3. Select the 5 products that best satisfy the user's request.
4. For each selected product, write a concise 2-sentence explanation of why it suits the user.

Return ONLY a valid JSON array — no markdown, no extra text.

Schema:
[
  {{
    "index": <1-based position from the catalogue above>,
    "ai_explanation": "<2-sentence explanation>"
  }},
  ...
]

Select exactly 5 products."""

    # --- Groq call ----------------------------------------------------------
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Return only a JSON array."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        raw = completion.choices[0].message.content or ""
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        selections: list[dict] = json.loads(raw)
        logger.info("LLM selected %d product(s) from catalogue.", len(selections))

    except json.JSONDecodeError:
        logger.warning(
            "LLM returned unparseable JSON in _llm_select_and_explain. "
            "Falling back to top-5 by ML score."
        )
        selections = []

    except Exception:
        logger.exception(
            "Groq call failed in _llm_select_and_explain. "
            "Falling back to top-5 by ML score."
        )
        selections = []

    # --- Map selections back to product dicts --------------------------------
    results: list[dict] = []

    if selections:
        for sel in selections[:5]:
            idx = sel.get("index")
            explanation = sel.get("ai_explanation", "Recommended based on your preferences.")
            if isinstance(idx, int) and 1 <= idx <= len(pool):
                product = pool[idx - 1].copy()
                product["ai_explanation"] = explanation
                results.append(product)

    # Fallback: top-5 by ML score with a generic explanation.
    if len(results) < 5:
        logger.warning(
            "LLM selection produced %d result(s); padding with ML-ranked fallbacks.",
            len(results),
        )
        used_ids = {p.get("_id") for p in results}
        for p in pool:
            if len(results) >= 5:
                break
            if p.get("_id") not in used_ids:
                fallback = p.copy()
                fallback["ai_explanation"] = "Recommended based on your preferences."
                results.append(fallback)

    return results


def _build_llm_comparison_prompt(
    query: str,
    product_a: str,
    product_b: str,
) -> str:
    """
    Build a structured prompt asking Groq to compare two named products
    using its own knowledge — no database data required.

    The prompt instructs the model to cover eight dimensions and to
    explicitly flag unknown or obscure products rather than guessing.

    Parameters
    ----------
    query : str
        Original user query for suitability context.
    product_a : str
        Name of the first product or brand.
    product_b : str
        Name of the second product or brand.

    Returns
    -------
    str
        Formatted prompt string ready to send to the Groq API.
    """
    return f"""You are an expert AI Shopping Assistant specialising in beauty and skincare.

A user asked: "{query}"

They want a detailed comparison between **{product_a}** and **{product_b}**.

IMPORTANT RULES:
- Use only your own knowledge about these products.
- Do NOT mention any database, search results, or external lookup.
- If either product is obscure, fictional, or you cannot confidently discuss it,
  clearly say so and explain what you do know — do not fabricate information.

If you can discuss both products, structure your response in this exact markdown format:

## {product_a} vs {product_b}

**Ingredients & Key Actives**
Compare the notable ingredients or active components of each product.

**Benefits**
What skin concerns or needs does each product address?

**Skin Types**
Which skin types is each product best suited for?

**Texture & Application**
Describe the feel, consistency, and how each is applied.

**Price Range**
Give a general price range for each (e.g. budget / mid-range / premium).

**Pros & Cons**
| | {product_a} | {product_b} |
|---|---|---|
| Pros | ... | ... |
| Cons | ... | ... |

**Recommendation**
Based on the user's query ("{query}"), which product do you recommend and why?
Keep this to 2–3 sentences.

---
If you cannot confidently compare one or both products, respond with:
"I don't have reliable information about [product name]. [Brief explanation of what you do or don't know]."
Do not attempt a comparison for products you are uncertain about."""


def _extract_image_url(product: dict) -> str | None:
    """
    Return the best available image URL from a product document.

    Resolution order: hi_res → large → thumb.

    Parameters
    ----------
    product : dict
        MongoDB product document containing an ``images`` list.

    Returns
    -------
    str | None
        First available image URL, or None if no images are present.
    """
    images = product.get("images")
    if not images or not isinstance(images, list):
        return None

    first = images[0]
    return first.get("hi_res") or first.get("large") or first.get("thumb")


def _format_product(product: dict) -> dict:
    """
    Serialise a MongoDB product document into the API response shape.

    Parameters
    ----------
    product : dict
        Scored and explained product document.

    Returns
    -------
    dict
        Flat dict matching the frontend contract.
    """
    return {
        "id": product.get("_id"),
        "asin": product.get("asin"),
        "title": product.get("title"),
        "brand": product.get("brand"),
        "category": product.get("category"),
        "price": product.get("price"),
        "average_rating": product.get("average_rating"),
        "rating_number": product.get("rating_number"),
        "image": _extract_image_url(product),
        "features": product.get("features"),
        "ml_score": round(product.get("ml_score", 0.0), 4),
        "ai_explanation": product.get("ai_explanation"),
    }


async def process_query(query: str) -> dict:
    """
    Route a user query to the appropriate handler based on detected intent.

    Workflow
    --------
    1. Call ``extract_user_intent()`` to classify the query.
    2. Route based on the ``intent`` field:
       - ``recommend``   → full recommendation pipeline
       - ``compare``     → placeholder (comparison not yet implemented)
       - ``information`` → conversational Groq response
    3. Return a consistent dict with a ``type`` field so callers always
       receive a predictable shape regardless of which branch ran.

    Parameters
    ----------
    query : str
        Raw natural-language query from the user.

    Returns
    -------
    dict
        Always contains ``"type"`` plus branch-specific payload keys:
        - recommendation: ``{"type": "recommendation", "products": [...]}``
        - comparison:     ``{"type": "comparison", "message": "..."}``
        - information:    ``{"type": "information", "message": "..."}``
        - error:          ``{"type": "error", "message": "..."}``
    """
    logger.info("process_query called. query_preview='%s'", query[:80])

    try:
        intent_data = await extract_user_intent(query)
        intent = intent_data.get("intent", "recommend")
        logger.info("Detected intent: '%s'", intent)

        if intent == "recommend":
            return await _handle_recommend(query)

        if intent == "compare":
            return await _handle_compare(query, intent_data)

        # "information" and any unrecognised intent both fall through here.
        return await _handle_information(query)

    except Exception:
        logger.exception("Unhandled exception in process_query.")
        return {
            "type": "error",
            "message": (
                "Something went wrong while processing your request. "
                "Please try again."
            ),
        }


# ---------------------------------------------------------------------------
# Private routing helpers
# ---------------------------------------------------------------------------

async def _handle_recommend(query: str) -> dict:
    """Call the recommendation pipeline and wrap the result."""
    logger.info("Routing to recommendation pipeline.")
    products = await get_product_recommendations({"query": query})
    return {
        "type": "recommendation",
        "products": products,
    }


async def _handle_compare(query: str, intent: dict) -> dict:
    """Delegate to the real comparison pipeline."""
    logger.info("Routing to comparison handler.")
    return await compare_products(query, intent)


async def _handle_information(query: str) -> dict:
    """Call the conversational Groq response and wrap the result."""
    logger.info("Routing to information/conversational handler.")
    response_text = await generate_response(query)
    return {
        "type": "information",
        "message": response_text,
    }
