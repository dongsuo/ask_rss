import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import html
from urllib.parse import urlparse

from .models import Article

def clean_text(text: str) -> str:
    """Clean and normalize text by removing HTML tags and extra whitespace."""
    if not text:
        return ""
    
    # Convert HTML entities to text
    text = html.unescape(text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def parse_feed(feed_url: str, max_articles: Optional[int] = None) -> List[Article]:
    """
    Parse an RSS/Atom feed and return a list of Article objects.
    
    Args:
        feed_url: URL of the RSS/Atom feed
        max_articles: Maximum number of articles to return
        
    Returns:
        List of Article objects
    """
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            print(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
            return []
            
        articles = []
        for i, entry in enumerate(feed.entries):
            if max_articles is not None and i >= max_articles:
                break
                
            # Extract title
            title = clean_text(getattr(entry, 'title', 'Untitled'))
            
            # Extract link
            link = getattr(entry, 'link', '')
            if not link and hasattr(entry, 'links') and len(entry.links) > 0:
                link = entry.links[0].get('href', '')
            
            # Extract published date
            published = None
            for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                if hasattr(entry, date_field) and getattr(entry, date_field):
                    published = datetime(*getattr(entry, date_field)[:6]).isoformat()
                    break
            
            # Extract summary/content
            summary = None
            for content_field in ['summary', 'description', 'content']:
                if hasattr(entry, content_field):
                    content = getattr(entry, content_field)
                    if isinstance(content, list) and content:
                        content = content[0].get('value', '')
                    summary = clean_text(str(content) if content else '')
                    if summary:
                        break
            
            articles.append(Article(
                title=title,
                link=link,
                published=published,
                summary=summary,
                source_url=feed_url
            ))
        
        return articles
        
    except Exception as e:
        print(f"Error parsing feed {feed_url}: {e}")
        return []

async def get_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Get embeddings for a list of texts using a pre-trained sentence transformer model.
    
    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to process in each batch
        
    Returns:
        List of embedding vectors (lists of floats)
    """
    if not texts:
        return []
        
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        
        # Use GPU if available, otherwise CPU
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Load the model (cache it for better performance)
        model = SentenceTransformer('all-mpnet-base-v2', device=device)
        
        # Generate embeddings in batches to handle large inputs
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(
                batch,
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            all_embeddings.extend(batch_embeddings.tolist())
        
        return all_embeddings
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return zero vectors in case of error
        return [[0.0] * 768 for _ in range(len(texts))]

def get_source_name(url: str) -> str:
    """
    Extract a clean source name from a URL.
    
    Args:
        url: Input URL
        
    Returns:
        Cleaned source name
    """
    try:
        # Parse the URL
        parsed = urlparse(url)
        if not parsed.netloc:
            return "unknown_source"
            
        # Remove common subdomains
        domain = parsed.netloc.lower()
        for prefix in ['www.', 'm.', 'mobile.']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
                break
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Remove TLD and split by dots
        parts = domain.split('.')
        if len(parts) > 2:
            # Get the last two parts (e.g., 'example.co.uk' -> 'example')
            domain = parts[-3] if parts[-2] in ['co', 'com', 'org', 'net'] else parts[-2]
        else:
            domain = parts[0] if len(parts) == 1 else parts[-2]
        
        # Remove any non-alphanumeric characters
        domain = re.sub(r'[^a-z0-9]', '_', domain)
        
        return domain or "unknown_source"
        
    except Exception:
        return "unknown_source"
