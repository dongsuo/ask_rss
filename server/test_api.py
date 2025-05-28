import pytest
import requests
import time
import json
from typing import List, Dict, Any

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test the health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data
    assert "timestamp" in data

def test_process_rss():
    """Test processing an RSS feed"""
    test_urls = ["https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"]
    payload = {
        "rss_urls": test_urls,
        "max_articles": 5
    }
    
    # Process the feed
    response = requests.post(f"{BASE_URL}/process-rss", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert data["status"] in ["success", "partial"]
    assert "message" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    
    # Check that we have at least one successful result
    assert any(r["status"] == "success" for r in data["results"])
    
    # Give some time for processing
    time.sleep(5)
    
    return test_urls[0]

def test_semantic_search(feed_url: str):
    """Test semantic search on processed articles"""
    if not feed_url:
        pytest.skip("No feed URL available from previous test")
    
    search_payload = {
        "query": "latest technology news",
        "source_url": feed_url,
        "top_k": 3
    }
    
    response = requests.post(f"{BASE_URL}/semantic-search", json=search_payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert data["status"] == "success"
    assert "query" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    
    # If we have results, check their structure
    if data["results"]:
        result = data["results"][0]
        assert "title" in result
        assert "link" in result
        assert "source_url" in result
        assert "score" in result

def test_invalid_search():
    """Test semantic search with invalid input"""
    # Test empty query
    response = requests.post(
        f"{BASE_URL}/semantic-search", 
        json={"query": ""}
    )
    assert response.status_code == 400
    
    # Test invalid URL
    response = requests.post(
        f"{BASE_URL}/process-rss",
        json={"rss_urls": ["not-a-valid-url"]}
    )
    assert response.status_code == 200  # Should still return 200 with error in response
    data = response.json()
    assert data["status"] in ["error", "partial"]

if __name__ == "__main__":
    # Run the process_rss test first to get the feed URL
    feed_url = test_process_rss()
    
    # Then run semantic search with the feed URL
    test_semantic_search(feed_url)
    
    # Run other tests
    test_health_check()
    test_invalid_search()
    
    print("All tests passed!")
