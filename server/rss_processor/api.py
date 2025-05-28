from fastapi import APIRouter, HTTPException, Depends
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import ProcessRSSRequest, SemanticSearchRequest, SearchResult
from .processor import RSSProcessor

router = APIRouter()
processor = RSSProcessor()

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "RSS Feed Processor API is running"
    }

@router.post("/process-rss")
async def process_rss(request: ProcessRSSRequest):
    """
    Process one or more RSS feeds.
    
    This endpoint will:
    1. Fetch articles from the provided RSS feed URLs
    2. Generate embeddings for each article
    3. Save the articles with embeddings as dataset shards
    """
    if not request.rss_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one RSS URL is required"
        )
    
    results = []
    for feed_url in request.rss_urls:
        try:
            result = await processor.process_feed(
                feed_url=feed_url,
                max_articles=request.max_articles
            )
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "message": f"Error processing {feed_url}: {str(e)}",
                "source_url": feed_url,
                "articles_processed": 0
            })
    
    # Calculate summary
    successful = sum(1 for r in results if r["status"] == "success")
    total_articles = sum(r.get("articles_processed", 0) for r in results)
    
    return {
        "status": "success" if successful > 0 else "partial" if results else "error",
        "message": f"Processed {total_articles} articles from {successful}/{len(results)} feeds",
        "results": results,
        "total_feeds": len(request.rss_urls),
        "successful_feeds": successful,
        "total_articles": total_articles
    }

@router.post("/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Perform semantic search on processed articles.
    
    This endpoint will:
    1. Generate an embedding for the query
    2. Find the most similar articles using cosine similarity
    3. Return the top matching articles with scores
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    try:
        results = await processor.search(
            query=request.query,
            source_url=request.source_url,
            top_k=request.top_k or 5
        )
        
        return {
            "status": "success",
            "query": request.query,
            "source_url": request.source_url,
            "results": [result.dict() for result in results]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing semantic search: {str(e)}"
        )

@router.get("/sources", response_model=List[Dict[str, Any]])
async def list_sources() -> List[Dict[str, Any]]:
    """
    List all available RSS feed sources with their metadata.
    
    Returns:
        List of sources with metadata including name, article count, last modified time, etc.
    """
    try:
        sources = await processor.list_sources()
        return sources
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sources: {str(e)}"
        )

# Add CORS middleware in the main FastAPI app, not here
# This is just a note that CORS should be enabled in the main app
