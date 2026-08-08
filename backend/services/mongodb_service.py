"""
MongoDB Service
---------------
Handles the MongoDB Atlas connection and exposes a reusable database client.
Business logic (queries, inserts, etc.) will be added here in future iterations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import get_settings
import logging
from typing import List
import re

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_to_mongodb() -> None:
    """Open the MongoDB connection pool at application startup."""
    global _client
    settings = get_settings()
    try:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        # Verify the connection is reachable
        await _client.admin.command("ping")
        logger.info("Successfully connected to MongoDB Atlas.")
    except Exception as exc:
        logger.error("Failed to connect to MongoDB Atlas: %s", exc)
        raise


async def close_mongodb_connection() -> None:
    """Close the MongoDB connection pool at application shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the application database.
    """
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialised. "
            "Ensure connect_to_mongodb() was called during startup."
        )

    return _client["shopping_assistant"]


# ---------------------------------------------------------------------------
# Product Search Functions
# ---------------------------------------------------------------------------

async def search_products(keyword: str, limit: int = 20):
    """
    Search products across multiple fields.
    """

    db = get_database()

    query = {
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
            {"features": {"$regex": keyword, "$options": "i"}},
            {"brand": {"$regex": keyword, "$options": "i"}},
            {"category": {"$regex": keyword, "$options": "i"}},
        ]
    }

    cursor = (
        db.products
        .find(query)
        .sort([
            ("average_rating", -1),
            ("rating_number", -1),
        ])
        .limit(limit)
    )

    products = await cursor.to_list(length=limit)

    for product in products:
        product["_id"] = str(product["_id"])

    return products

async def search_products_with_filters(
    keyword: str,
    brand: str | None = None,
    category: str | None = None,
    min_rating: float = 0,
    limit: int = 20,
):
    db = get_database()

    query = {
        "$and": [
            {
                "$or": [
                    {"title": {"$regex": keyword, "$options": "i"}},
                    {"description": {"$regex": keyword, "$options": "i"}},
                    {"features": {"$regex": keyword, "$options": "i"}},
                    {"brand": {"$regex": keyword, "$options": "i"}},
                    {"category": {"$regex": keyword, "$options": "i"}},
                ]
            },
            {
                "average_rating": {
                    "$gte": min_rating
                }
            }
        ]
    }

    if brand:
        query["$and"].append(
            {"brand": {"$regex": brand, "$options": "i"}}
        )

    if category:
        query["$and"].append(
            {"category": {"$regex": category, "$options": "i"}}
        )

    cursor = (
        db.products
        .find(query)
        .sort([
            ("average_rating", -1),
            ("rating_number", -1),
        ])
        .limit(limit)
    )

    products = await cursor.to_list(length=limit)

    for product in products:
        product["_id"] = str(product["_id"])

    return products


async def get_candidate_products(
    product_type: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    min_rating: float = 3.5,
    limit: int = 100,
) -> list[dict]:
    """
    Broad candidate retrieval for the agentic recommendation pipeline.

    ``product_type`` is the primary relevance filter: it runs a case-
    insensitive regex across title, category, features, and description so
    that a query like "shampoo" matches products regardless of how the
    category field is labelled in the database.

    Remaining parameters (brand, category, max_price, min_rating) narrow
    the pool further after the product-type filter is satisfied.

    Sort order: average_rating DESC, rating_number DESC.

    Parameters
    ----------
    product_type : str | None
        The extracted product noun (e.g. "shampoo", "moisturizer",
        "serum"). Applied as a multi-field regex — no exact match required.
    brand : str | None
        Optional brand filter (case-insensitive regex).
    category : str | None
        Optional MongoDB category field filter (case-insensitive regex).
    max_price : float | None
        Optional upper price bound (inclusive).
    min_rating : float
        Minimum average_rating threshold. Defaults to 3.5.
    limit : int
        Maximum number of candidates to return. Defaults to 100.

    Returns
    -------
    list[dict]
        List of product dicts with ``_id`` cast to str.
    """
    db = get_database()

    # Always apply the rating floor.
    filters: list[dict] = [{"average_rating": {"$gte": min_rating}}]

    # ── Product-type filter (multi-field soft match) ────────────────────────
    # This is the primary type constraint — matches "shampoo" in title,
    # category, features list, or description regardless of exact labelling.
    if product_type:
        filters.append({
            "$or": [
                {"title":       {"$regex": product_type, "$options": "i"}},
                {"category":    {"$regex": product_type, "$options": "i"}},
                {"features":    {"$regex": product_type, "$options": "i"}},
                {"description": {"$regex": product_type, "$options": "i"}},
            ]
        })

    # ── Optional narrowing filters ──────────────────────────────────────────
    if brand:
        filters.append({"brand": {"$regex": brand, "$options": "i"}})

    if category:
        filters.append({"category": {"$regex": category, "$options": "i"}})

    if max_price is not None:
        filters.append({"price": {"$lte": max_price}})

    query = {"$and": filters} if len(filters) > 1 else filters[0]

    cursor = (
        db.products
        .find(query)
        .sort([
            ("average_rating", -1),
            ("rating_number", -1),
        ])
        .limit(limit)
    )

    products = await cursor.to_list(length=limit)

    for product in products:
        product["_id"] = str(product["_id"])

    logger.info(
        "get_candidate_products: %d result(s). "
        "product_type=%s, brand=%s, category=%s, max_price=%s, min_rating=%s",
        len(products),
        product_type,
        brand,
        category,
        max_price,
        min_rating,
    )

    return products
