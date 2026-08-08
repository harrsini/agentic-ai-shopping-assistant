"""
Predict Router
--------------
Exposes the POST /predict endpoint.
Delegates all business logic to ml_service.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from schemas.request_models import PredictRequest
from schemas.response_models import PredictResponse
from services import ml_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"],
)


@router.post(
    "",
    response_model=PredictResponse,
    summary="Predict product price",
    description=(
        "Accepts a feature dictionary, converts it to a pandas DataFrame, "
        "reindexes using the stored feature columns, and returns the "
        "XGBoost model prediction."
    ),
    responses={
        200: {"description": "Prediction returned successfully"},
        422: {"description": "Validation error – invalid request body"},
        503: {"description": "Model not loaded"},
        500: {"description": "Internal server error during prediction"},
    },
)
async def predict(request: PredictRequest) -> PredictResponse:
    """
    Run a price prediction using the loaded XGBoost model.

    - **features**: key-value pairs matching the model's training features.
    """
    if not ml_service.is_model_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not available. Please try again later.",
        )

    try:
        prediction_value = ml_service.predict(request.features)
        logger.info("Prediction successful: %.4f", prediction_value)
        return PredictResponse(prediction=prediction_value)

    except ValueError as exc:
        logger.warning("Prediction value error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.error("Unexpected prediction error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        ) from exc
