"""
Script to start the RSS Feed Processor API server with logging configuration.
"""
import uvicorn
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting RSS Feed Processor API server...")
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Server will run on http://{host}:{port}")
    logger.info(f"Auto-reload: {'enabled' if reload_enabled else 'disabled'}")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level="info",
        workers=1
    )
