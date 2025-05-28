import pytest
from fastapi.testclient import TestClient
from main import app
from rss_processor.models import ProcessRSSRequest, FilterBySourceRequest, SemanticSearchRequest

client = TestClient(app)

def test_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()
    assert "docs" in response.json()
    assert "redoc" in response.json()

def test_process_rss():
    """Test the process-rss endpoint"""
    test_urls = ["https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"]
    request_data = {
        "rss_urls": test_urls,
        "batch_size": 32,
        "max_articles": 5
    }
    response = client.post("/api/v1/process-rss", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["pending", "processing", "completed"]
    assert "message" in data

# Add more test cases for other endpoints

def test_semantic_search():
    """Test the semantic search endpoint"""
    # First, process some RSS feeds
    test_urls = ["https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"]
    process_request = {
        "rss_urls": test_urls,
        "batch_size": 32,
        "max_articles": 5
    }
    process_response = client.post("/api/v1/process-rss", json=process_request)
    assert process_response.status_code == 200
    
    # Then perform a search
    search_request = {
        "query": "latest technology news",
        "source_url": test_urls[0],
        "top_k": 3
    }
    search_response = client.post("/api/v1/semantic-search", json=search_request)
    assert search_response.status_code == 200
    data = search_response.json()
    assert "status" in data
    assert data["status"] == "success"
    assert "results" in data
    assert isinstance(data["results"], list)

# Add more test cases for error scenarios and edge cases
