from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.routes import router
from app.core.config import get_settings
from app.core.exceptions import BaseAppException, format_error_response
from app.core.tracing import configure_tracing
from app.data.db import Base, get_engine
from app.data.seed import seed_orders
from app.middleware.rate_limit import setup_rate_limiting


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    
    # Initialize LangSmith tracing
    configure_tracing()
    
    # Initialize database
    engine = get_engine()
    if settings.AUTO_SEED_DATA and settings.DATABASE_URL.startswith("sqlite:///./"):
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    if settings.AUTO_SEED_DATA:
        with Session(engine) as session:
            seed_orders(session)
            # Also seed demo orders
            from app.data.seed_demo import seed_demo_orders
            seed_demo_orders(session)
    yield


app = FastAPI(title="ResolveAI", lifespan=lifespan)

# Setup CORS middleware for frontend integration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Correlation-ID",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Correlation-ID",
        "X-RateLimit-Remaining",
    ],
)

# Setup Prometheus metrics middleware
from app.middleware.prometheus import PrometheusMiddleware
app.add_middleware(PrometheusMiddleware)

# Setup rate limiting
setup_rate_limiting(app, requests_per_minute=60, burst_size=10)

# Exception handlers
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=400,
        content=format_error_response(exc),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {"type": type(exc).__name__},
        },
    )

app.include_router(router)
