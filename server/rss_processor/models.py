from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum, auto

class ProcessingStatus(str, Enum):
    """Represents the status of a feed processing operation."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Article(BaseModel):
    """Represents an article from an RSS feed."""
    title: str
    link: str
    published: Optional[str] = None
    summary: Optional[str] = None
    source_url: str
    embedding: Optional[List[float]] = None

    class Config:
        json_encoders = {
            'datetime': lambda v: v.isoformat() if v else None
        }
        from_attributes = True

class SearchResult(BaseModel):
    """Represents a search result with similarity score and feed information."""
    title: str = Field(..., description="Title of the article")
    link: str = Field(..., description="URL of the article")
    source_url: str = Field(..., description="URL of the source website")
    feed_url: str = Field(..., description="URL of the RSS feed")
    feed_title: str = Field(..., description="Title of the RSS feed")
    published: Optional[str] = Field(None, description="Publication date in ISO format")
    summary: Optional[str] = Field(None, description="Summary/description of the article")
    score: float = Field(..., description="Similarity score (0-1)")

    class Config:
        json_encoders = {
            'datetime': lambda v: v.isoformat() if v else None
        }
        from_attributes = True

class ProcessRSSRequest(BaseModel):
    """Request model for processing RSS feeds."""
    rss_urls: List[str]
    max_articles: Optional[int] = 100  # Default to 100 articles per feed

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str
    source_url: Optional[str] = None
    top_k: Optional[int] = 5
