import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.db import check_db_connection, init_db
from app.auth import router as auth_router
from app.routes_users import router as users_router
from app.routes_orders import router as orders_router
from app.routes_wallet import router as wallet_router
from app.config import settings


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("payment-api")

app = FastAPI(
    title="Payment API",
    description="Production-ready API with JWT Authentication",
    version="1.0.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.on_event("startup")
def startup_event():
    logger.info("Starting Payment API")
    logger.info("Environment: %s", settings.app_env)
    logger.info("Configured log level: %s", settings.log_level.upper())
    logger.info("SQL query logging enabled: %s", settings.log_sql_queries)
    logger.info("Request logging enabled: %s", settings.log_requests)
    init_db()
    logger.info("Database initialized successfully")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = None
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        if settings.log_requests:
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = getattr(response, "status_code", "ERR")
            logger.info(
                "[%s] %s %s -> %s (%.2f ms)",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("[%s] HTTPException on %s %s: %s", request_id, request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("[%s] Unhandled exception on %s %s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": request_id},
    )


app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(wallet_router, prefix="/api")

@app.get("/", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "Payment API"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}


@app.get("/ready", tags=["health"])
def readiness_check():
    if not check_db_connection():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "database": "unavailable"},
        )
    return {"status": "ready", "database": "ok"}

@app.get("/api", tags=["info"])
def api_info():
    return {
        "docs": "/docs",
        "auth": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "protected_routes": "Add header: Authorization: Bearer <token>"
        }
    }
