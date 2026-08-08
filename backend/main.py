"""
Agentic AI Shopping Assistant — FastAPI Application Entry Point
---------------------------------------------------------------
Configures the app, registers middleware, wires up the lifespan
(startup / shutdown) events, and mounts all routers.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from services import ml_service
from services.mongodb_service import connect_to_mongodb, close_mongodb_connection
from routers import chat, predict, products


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup & shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager that runs once at startup and once at shutdown.
    Loads the ML model and opens the MongoDB connection pool.
    """
    settings = get_settings()
    logger.info("Starting Agentic AI Shopping Assistant API (%s)...", settings.environment)

    # --- Startup ---
    # Load the XGBoost model (blocking, but runs only once).
    try:
        ml_service.load_model()
    except FileNotFoundError as exc:
        logger.warning(
            "Model files not found during startup: %s. "
            "The /predict endpoint will return 503 until the model is placed in models/.",
            exc,
        )

    # Open MongoDB connection pool.
    try:
        await connect_to_mongodb()
    except Exception as exc:
        logger.warning(
            "MongoDB connection failed during startup: %s. "
            "Database-backed endpoints will be unavailable.",
            exc,
        )

    logger.info("Startup complete.")
    yield  # Application is running.

    # --- Shutdown ---
    logger.info("Shutting down Agentic AI Shopping Assistant API...")
    await close_mongodb_connection()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title="Agentic AI Shopping Assistant API",
    description=(
        "Production-ready backend for the Agentic AI Shopping Assistant. "
        "Provides price prediction (XGBoost), product listings (MongoDB), "
        "and AI-powered chat/recommendations (Groq / Qwen)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(predict.router)
app.include_router(chat.router)
app.include_router(products.router)


# ---------------------------------------------------------------------------
# Root & health endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/",
    tags=["Root"],
    summary="API root",
    response_description="Welcome message",
)
async def root() -> dict:
    """Return a simple welcome message to confirm the API is reachable."""
    return {"message": "Agentic AI Shopping Assistant API"}


@app.get(
    "/health",
    tags=["Health"],
    summary="Application health check",
    response_description="Current health status",
)
async def health() -> dict:
    """
    Return the current health status of the application including:
    - Overall status
    - Timestamp
    - Active environment
    - Whether the ML model is loaded
    """
    return {
        "status": (
            "healthy"
            if ml_service.is_model_loaded()
            else "degraded"
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "model_loaded": ml_service.is_model_loaded(),
    }
