from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from agent_aichain.core.config import settings
from agent_aichain.core.database import init_db
from agent_aichain.core.neo4j_db import neo4j_conn
from agent_aichain.api.versioning import setup_versioning

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting AgentAichain application")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Neo4j connection
    success = await neo4j_conn.connect_async()
    if success:
        logger.info("Neo4j initialized")
        from agent_aichain.services.graph_service import GraphService
        await GraphService.initialize_schema()
    else:
        logger.error("Failed to initialize Neo4j")
        
    yield
    # Shutdown
    logger.info("Shutting down AgentAichain application")
    await neo4j_conn.close_async()
    logger.info("Neo4j connection closed")


app = FastAPI(
    title="AgentAichain API",
    description="Multi-tenant AI Agent orchestration platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware (S1)
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    return response

# API Versioning middleware (B9)
setup_versioning(app)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": type(exc).__name__}
    )


# Prometheus Metrics (O2)
from prometheus_client import make_asgi_app, Counter, Histogram
import time

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total HTTP Requests", 
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP Request Duration", 
    ["method", "endpoint"]
)

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    method = request.method
    # Use path, but avoid high cardinality for dynamic endpoints if possible. 
    # For now, we use the raw path.
    path = request.url.path
    
    # Don't track metrics for /metrics
    if path == "/metrics":
        return await call_next(request)
        
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency = time.time() - start_time
        REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(latency)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent-aichain", "version": "0.1.0"}


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to AgentAichain API",
        "docs": "/docs",
        "version": "0.1.0"
    }


# Include API routers
from agent_aichain.api import auth, agents, teams, runs, api_keys, settings, graph, dashboard

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1/dashboard")