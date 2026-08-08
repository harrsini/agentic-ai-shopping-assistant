"""
ML Service
----------
Handles loading the XGBoost model and feature columns once at startup,
then exposes a predict() function for use by the prediction router.
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from config import get_settings

logger = logging.getLogger(__name__)

# Module-level singletons — loaded once during startup, reused on every request.
_model: Any = None
_feature_columns: list[str] = []


def load_model() -> None:
    """
    Load model.joblib and feature_columns.pkl from the paths defined in settings.
    Called once during FastAPI's lifespan startup event.
    Raises FileNotFoundError if either artefact is missing.
    """
    global _model, _feature_columns
    settings = get_settings()

    model_path = Path(settings.model_path)
    feature_columns_path = Path(settings.feature_columns_path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}. "
            "Place model.joblib inside the backend/models/ directory."
        )
    if not feature_columns_path.exists():
        raise FileNotFoundError(
            f"Feature columns file not found: {feature_columns_path}. "
            "Place feature_columns.pkl inside the backend/models/ directory."
        )

    logger.info("Loading XGBoost model from '%s'...", model_path)
    _model = joblib.load(model_path)

    logger.info("Loading feature columns from '%s'...", feature_columns_path)
    _feature_columns = joblib.load(feature_columns_path)

    logger.info(
        "Model loaded successfully. Expecting %d feature(s).",
        len(_feature_columns),
    )


def is_model_loaded() -> bool:
    """Return True if the model has been loaded successfully."""
    return _model is not None and len(_feature_columns) > 0


def predict(features: dict[str, Any]) -> float:
    """
    Run a prediction using the loaded XGBoost model.

    Parameters
    ----------
    features : dict
        Raw feature dictionary from the incoming request.

    Returns
    -------
    float
        The predicted value (e.g. price, rating).

    Raises
    ------
    RuntimeError
        If the model has not been loaded yet.
    ValueError
        If prediction returns no results.
    """
    if not is_model_loaded():
        raise RuntimeError(
            "Model is not loaded. "
            "Ensure load_model() was called during application startup."
        )

    # Build a single-row DataFrame from the incoming feature dict.
    df = pd.DataFrame([features])

    # Reindex to exactly match the columns the model was trained on.
    # Missing columns are filled with 0; extra columns are dropped.
    df = df.reindex(columns=_feature_columns, fill_value=0)

    result = _model.predict(df)

    if len(result) == 0:
        raise ValueError("Model returned an empty prediction array.")

    # Return a plain Python float for JSON serialisation.
    return float(result[0])

def create_product_features(product: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a MongoDB product document into the feature dictionary
    expected by the trained XGBoost model.
    """

    return {
        "review_length": 0,
        "title_length": len(product.get("title") or ""),
        "feature_count": len(product.get("features") or []),
        "description_length": len(" ".join(product.get("description") or [])),
        "product_review_count": 0,
        "verified_purchase": 0,
        "helpful_vote": 0,
        "price": product.get("price") or 0,
        "average_rating": product.get("average_rating") or 0,
        "rating_number": product.get("rating_number") or 0,
    }


def predict_product(product: dict[str, Any]) -> float:
    """
    Predict a score for a MongoDB product.
    """

    features = create_product_features(product)

    return predict(features)
