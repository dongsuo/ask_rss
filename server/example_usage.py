"""
Example script demonstrating how to use the RSS Feed Processor API.
"""
import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BASE_URL = "http://localhost:8000/api/v1"

# Test RSS feed URLs
TEST_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://techcrunch.com/feed/",
    "https://feeds.bbci.co.uk/news/technology/rss.xml"
]

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text.upper()} ".center(80, "="))
    print("=" * 80)

def test_process_rss():
    """Test the process-rss endpoint."""
    print_header("Testing RSS Feed Processing")
    
    payload = {
        "rss_urls": TEST_FEEDS,
        "batch_size": 32,
        "max_articles": 5
    }
    
    print(f"Processing RSS feeds: {', '.join(TEST_FEEDS)}")
    response = requests.post(f"{BASE_URL}/process-rss", json=payload)
    response.raise_for_status()
    
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"Message: {data['message']}")
    
    if "data" in data and "sources" in data["data"]:
        for source, articles in data["data"]["sources"].items():
            print(f"\nProcessed {len(articles)} articles from {source}")
    
    return data

def test_semantic_search(query: str, source_url: str = None, top_k: int = 3):
    """Test the semantic search endpoint."""
    print_header(f"Testing Semantic Search: '{query}'")
    
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    if source_url:
        payload["source_url"] = source_url
        print(f"Searching in source: {source_url}")
    else:
        print("Searching across all sources")
    
    response = requests.post(f"{BASE_URL}/semantic-search", json=payload)
    response.raise_for_status()
    
    data = response.json()
    print(f"Found {len(data['results'])} results:")
    
    for i, result in enumerate(data["results"], 1):
        print(f"\n{i}. {result['title']} (Score: {result['score']:.4f})")
        print(f"   Source: {result['source_url']}")
        print(f"   Link: {result['link']}")
        print(f"   Published: {result.get('published', 'N/A')}")
        print(f"   {result['summary'][:200]}..." if result.get('summary') else "")
    
    return data

def test_filter_by_source(source_url: str):
    """Test filtering articles by source."""
    print_header(f"Testing Filter by Source: {source_url}")
    
    payload = {"source_url": source_url}
    response = requests.post(f"{BASE_URL}/filter-by-source", json=payload)
    response.raise_for_status()
    
    data = response.json()
    print(f"Found {data['count']} articles from {source_url}")
    
    if data["count"] > 0:
        print("\nSample articles:")
        for i, article in enumerate(data["articles"][:3], 1):
            print(f"{i}. {article['title']}")
            print(f"   Link: {article['link']}")
    
    return data

def test_save_shards():
    """Test saving dataset shards by source."""
    print_header("Testing Save Shards")
    
    payload = {"output_dir": "datasets"}
    response = requests.post(f"{BASE_URL}/save-shards", json=payload)
    response.raise_for_status()
    
    data = response.json()
    print(f"Status: {data['status']}")
    print(f"Message: {data['message']}")
    
    if "saved_paths" in data:
        print("\nSaved shards:")
        for source, path in data["saved_paths"].items():
            print(f"- {source}: {path}")
    
    return data

if __name__ == "__main__":
    try:
        # Test processing RSS feeds
        process_result = test_process_rss()
        
        # Give some time for processing
        print("\nWaiting for processing to complete...")
        time.sleep(5)
        
        # Test semantic search across all sources
        test_semantic_search("latest technology news", top_k=3)
        
        # Test semantic search for a specific source
        if TEST_FEEDS:
            test_semantic_search("artificial intelligence", source_url=TEST_FEEDS[0], top_k=2)
        
        # Test filtering by source
        if TEST_FEEDS:
            test_filter_by_source(TEST_FEEDS[0])
        
        # Test saving shards
        test_save_shards()
        
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        print("Make sure the API server is running (run 'uvicorn main:app --reload')")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
