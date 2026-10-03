import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1.router import api_v1_router
from src.core.config import settings
from src.core.redis import close_redis, init_redis, redis_client
from src.domain.exceptions import (
    DomainException,
    EntityNotFoundException,
    InvalidCredentialsException,
    UnauthorizedAccessException,
    UserAlreadyExistsException,
)
from src.services.websocket_manager import start_redis_pubsub_listener, ws_manager

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("riskflow.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize Redis and PubSub background worker
    pubsub_task: asyncio.Task[None] | None = None
    try:
        r_client = await init_redis()
        pubsub_task = asyncio.create_task(start_redis_pubsub_listener(r_client, ws_manager))
        logger.info("RiskFlow API started successfully.")
    except Exception as e:
        logger.warning(
            "Redis initialization warning (will run in standalone mode if Redis is down): %s", e
        )

    yield

    # Shutdown
    if pubsub_task and not pubsub_task.done():
        pubsub_task.cancel()
        try:
            await pubsub_task
        except asyncio.CancelledError:
            pass
    await close_redis()
    logger.info("RiskFlow API shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Trading Journal & Portfolio Risk Analytics Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Process Timing Middleware
@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}s"
    return response


# Global Exception Handlers
@app.exception_handler(UserAlreadyExistsException)
async def user_already_exists_handler(
    request: Request, exc: UserAlreadyExistsException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "USER_ALREADY_EXISTS", "detail": exc.message},
    )


@app.exception_handler(InvalidCredentialsException)
async def invalid_credentials_handler(
    request: Request, exc: InvalidCredentialsException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "INVALID_CREDENTIALS", "detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(UnauthorizedAccessException)
async def unauthorized_access_handler(
    request: Request, exc: UnauthorizedAccessException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": "FORBIDDEN", "detail": exc.message},
    )


@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "NOT_FOUND", "detail": exc.message},
    )


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "BAD_REQUEST", "detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "VALIDATION_ERROR", "detail": exc.errors()},
    )


# Health check endpoint
@app.get("/health", tags=["Health"], summary="System health check")
async def health_check() -> dict[str, Any]:
    redis_alive = False
    if redis_client:
        try:
            redis_alive = bool(await redis_client.ping())
        except Exception:
            redis_alive = False

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "redis_connected": redis_alive,
    }


# Include V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
