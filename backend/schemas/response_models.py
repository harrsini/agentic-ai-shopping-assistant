from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    model_config = {"protected_namespaces": ()}

    status: str
    timestamp: str
    environment: str
    model_loaded: bool


class PredictResponse(BaseModel):
    """Response model for prediction endpoint."""
    prediction: float = Field(..., description="Predicted price value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": 4.73
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ChatResponse(BaseModel):
    """
    Unified envelope returned by POST /chat for all intent types.

    Fields
    ------
    success : bool
        True when the pipeline completed without a fatal error.
    type : str
        Intent branch that handled the request.
        One of: ``"recommendation"`` | ``"comparison"`` | ``"information"`` | ``"error"``
    data : dict
        Branch-specific payload:
        - recommendation → ``{"products": [...]}``
        - comparison     → ``{"comparison": "...", "products": [...]}``
        - information    → ``{"message": "..."}``
        - error          → ``{}``
    error : str | None
        Human-readable error message; present only when ``success`` is False.
    """

    success: bool
    type: str
    data: Dict[str, Any]
    error: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "type": "recommendation",
                "data": {
                    "products": []
                },
                "error": None,
            }
        }
    }


class Product(BaseModel):
    """Product model."""

    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    average_rating: Optional[float] = None
    rating_number: Optional[int] = None
    description: Optional[list[str]] = None
    features: Optional[list[str]] = None
    images: Optional[list[dict]] = None


class RecommendResponse(BaseModel):
    """Response model for recommendation endpoint."""
    recommendations: List[Product]
    total: int


class ProductsResponse(BaseModel):
    """Response model for products list endpoint."""
    products: List[Product]
    total: int
    page: int
    page_size: int
