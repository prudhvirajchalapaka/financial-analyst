"""
Financial RAG Analyst - FastAPI Backend
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import upload, chat

# Load environment variables
load_dotenv()

# Validate API key
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("CRITICAL ERROR: GOOGLE_API_KEY not found. Please check your .env file.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Financial RAG Analyst API Starting...")
    yield
    print("👋 Shutting down... Cleaning up sessions...")
    # Cleanup all sessions on shutdown
    from routers.upload import sessions
    import shutil
    for session_id, session in list(sessions.items()):
        if "temp_dir" in session:
            shutil.rmtree(session["temp_dir"], ignore_errors=True)

# Create FastAPI app
app = FastAPI(
    title="Financial RAG Analyst API",
    description="Multi-modal RAG system for financial document analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - Allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "https://*.github.io",  # GitHub Pages
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(chat.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Financial RAG Analyst API",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Welcome to Financial RAG Analyst API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
