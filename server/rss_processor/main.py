import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict
import uvicorn
import logging
from pathlib import Path

from .api import router as rss_router

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="RSS Feed Processor API",
    description="Simple API for processing and searching RSS feeds with semantic search",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the RSS processor router
app.include_router(
    rss_router,
    prefix="/api/v1",
    tags=["RSS Feed Processing"]
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail)},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "message": "Validation error", "detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal server error"},
    )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RSS Feed Processor API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint (moved to the router)

if __name__ == "__main__":
    # Create datasets directory if it doesn't exist
    datasets_dir = Path("datasets")
    datasets_dir.mkdir(exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "rss_processor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
