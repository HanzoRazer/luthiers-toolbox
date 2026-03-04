"""
Configuration management for Site Generator API
Loads settings from environment variables with sensible defaults
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Security
    api_key: str = os.getenv("SITE_GENERATOR_API_KEY", "dev-key-change-in-production")
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Claude API - set ANTHROPIC_API_KEY environment variable
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Job Management
    jobs_dir: Path = Path(os.getenv("SITE_JOBS_DIR", "./site_jobs"))
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
    job_retention_hours: int = int(os.getenv("JOB_RETENTION_HOURS", "48"))

    # Rate Limiting
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "10"))

    # Webhooks
    webhook_enabled: bool = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
    webhook_secret: Optional[str] = os.getenv("WEBHOOK_SECRET")

    # File size limits
    max_spec_size_kb: int = int(os.getenv("MAX_SPEC_SIZE_KB", "100"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure jobs directory exists
settings.jobs_dir.mkdir(parents=True, exist_ok=True)
