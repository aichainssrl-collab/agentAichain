from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from agent_aichain.core.config import settings
from agent_aichain.core.database import init_db
from agent_aichain.core.neo4j_db import neo4j_conn

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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": type(exc).__name__}
    )


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
from agent_aichain.api import auth, agents, teams, runs, api_keys, settings

app.include_router(auth.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(runs.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")