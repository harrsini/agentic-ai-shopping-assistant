from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_uri: str
    
    # Groq API Configuration
    groq_api_key: str
    
    # Application Configuration
    environment: str = "development"
    debug: bool = True
    
    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:5173"]
    
    # Model Paths
    model_path: str = "models/model.joblib"
    feature_columns_path: str = "models/feature_columns.pkl"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": (),
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
