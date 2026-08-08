"""
Products Router
---------------
Provides endpoints for searching products stored in MongoDB.
"""

from fastapi import APIRouter, HTTPException, Query
from services.mongodb_service import search_products
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("/search")
async def search_products_endpoint(
    keyword: str = Query(
        ...,
        min_length=2,
        description="Keyword to search for products",
    ),
):
    """
    Search products by keyword.

    The keyword is matched against:
    - Product title
    - Product description
    - Product features

    Results are sorted by highest average rating.
    """

    try:
        products = await search_products(keyword)

        return {
            "success": True,
            "count": len(products),
            "products": products,
        }

    except Exception as exc:
        logger.error("Product search failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to search products.",
        )