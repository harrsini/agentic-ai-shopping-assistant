from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class PredictRequest(BaseModel):
    """Request model for price prediction endpoint."""
    features: Dict[str, Any] = Field(
        ...,
        description="Feature dictionary for prediction",
        example={
            "brand": "Apple",
            "category": "Electronics",
            "rating": 4.5,
            "reviews_count": 1200
        }
    )


class ChatRequest(BaseModel):
    """Request model for the unified chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's shopping query.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Compare Cetaphil and CeraVe moisturizers"
            }
        }
    }


class RecommendRequest(BaseModel):
    """Request model for product recommendation endpoint."""
    user_preferences: Dict[str, Any] = Field(
        ...,
        description="User preferences for recommendations"
    )
    limit: int = Field(default=10, ge=1, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_preferences": {
                    "category": "Electronics",
                    "price_range": [500, 1500],
                    "min_rating": 4.0
                },
                "limit": 10
            }
        }
