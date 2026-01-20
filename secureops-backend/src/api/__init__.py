"""API routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .video_routes import router as video_router
from .results_routes import router as results_router
from .analytics_routes import router as analytics_router
from .chat_routes import router as chat_router
from .document_routes import router as document_router
from .auth import router as auth_router
from .health_routes import router as health_router

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="SecureOps Safety API",
        description="AI-Powered Construction Site Monitoring Platform (Read-Only)",
        version="1.0.0"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(video_router)
    app.include_router(results_router, prefix="/api/v1/results")
    app.include_router(analytics_router)
    app.include_router(chat_router)
    app.include_router(document_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(health_router)
    # Note: video_router (Uploads) already has prefix defined in the file

    return app

app = create_app()

