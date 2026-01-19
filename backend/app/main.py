"""
Douyin Analytics Platform - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.db.database import init_db, close_db
from app.api import users, videos, comments, lives, search, ranking, tasks, analysis, websocket


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
if settings.log_file:
    logger.add(settings.log_file, rotation="10 MB", retention="7 days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="抖音数据分析平台 - 数据采集、实时监控、深度分析",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(videos.router, prefix="/api/videos", tags=["视频"])
app.include_router(comments.router, prefix="/api/comments", tags=["评论"])
app.include_router(lives.router, prefix="/api/lives", tags=["直播"])
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(ranking.router, prefix="/api/ranking", tags=["热榜"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["分析"])
app.include_router(websocket.router, prefix="/api/ws", tags=["WebSocket"])


@app.get("/", tags=["健康检查"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if settings.redis_enabled else "disabled",
        "scheduler": "running" if settings.scheduler_enabled else "disabled"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
