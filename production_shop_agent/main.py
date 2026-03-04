"""
Production Shop - Site Generator API Server
Main FastAPI application entry point

Run with:
    uvicorn main:app --reload                    # Development
    uvicorn main:app --host 0.0.0.0 --port 8000  # Production
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.site_generator_router import router
from api.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 60)
    print("  PRODUCTION SHOP - SITE GENERATOR API")
    print("=" * 60)
    print(f"  Jobs Directory: {settings.jobs_dir}")
    print(f"  Max Concurrent Jobs: {settings.max_concurrent_jobs}")
    print(f"  Rate Limiting: {'Enabled' if settings.rate_limit_enabled else 'Disabled'}")
    if settings.rate_limit_enabled:
        print(f"  Rate Limit: {settings.rate_limit_per_hour} requests/hour")
    print(f"  Job Retention: {settings.job_retention_hours} hours")
    print(f"  Webhooks: {'Enabled' if settings.webhook_enabled else 'Disabled'}")
    print("=" * 60)
    print()

    yield

    print("\n[SHUTDOWN] Site Generator API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Production Shop - Site Generator API",
    description="Generate complete websites from JSON specifications using Claude AI",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# CORS middleware (configure allowed origins in settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit headers middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to responses"""
    response = await call_next(request)

    # Add rate limit info if available
    if hasattr(request.state, "rate_limit_remaining"):
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_hour)
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unexpected errors"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": str(request.url.path)
        }
    )


# Include site generator router
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """API information endpoint"""
    return {
        "name": "Production Shop - Site Generator API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/site-generator/health",
        "endpoints": {
            "generate": "POST /api/site-generator/generate",
            "status": "GET /api/site-generator/status/{job_id}",
            "download": "GET /api/site-generator/download/{job_id}",
            "preview": "GET /api/site-generator/preview/{job_id}",
            "list_jobs": "GET /api/site-generator/jobs",
            "cancel": "POST /api/site-generator/jobs/{job_id}/cancel",
            "delete": "DELETE /api/site-generator/jobs/{job_id}",
        },
        "authentication": "API key required (X-API-Key header or Bearer token)",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
