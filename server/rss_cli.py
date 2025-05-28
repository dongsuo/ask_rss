"""
Command-line interface for the RSS Feed Processor API.
"""
import argparse
import json
import sys
import requests
from typing import List, Optional
from pathlib import Path

# Default API URL
DEFAULT_API_URL = "http://localhost:8000/api/v1"

class RSSClient:
    """Client for interacting with the RSS Feed Processor API."""
    
    def __init__(self, api_url: str = DEFAULT_API_URL):
        """Initialize the client with the API URL."""
        self.api_url = api_url
    
    def process_feeds(self, urls: List[str], batch_size: int = 32, max_articles: Optional[int] = None) -> dict:
        """Process one or more RSS feeds."""
        payload = {
            "rss_urls": urls,
            "batch_size": batch_size
        }
        if max_articles is not None:
            payload["max_articles"] = max_articles
            
        response = requests.post(f"{self.api_url}/process-rss", json=payload)
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, source_url: Optional[str] = None, top_k: int = 5) -> dict:
        """Perform a semantic search."""
        payload = {
            "query": query,
            "top_k": top_k
        }
        if source_url:
            payload["source_url"] = source_url
            
        response = requests.post(f"{self.api_url}/semantic-search", json=payload)
        response.raise_for_status()
        return response.json()
    
    def filter_by_source(self, source_url: str) -> dict:
        """Filter articles by source URL."""
        response = requests.post(
            f"{self.api_url}/filter-by-source",
            json={"source_url": source_url}
        )
        response.raise_for_status()
        return response.json()
    
    def save_shards(self, output_dir: str = "datasets") -> dict:
        """Save dataset shards by source."""
        response = requests.post(
            f"{self.api_url}/save-shards",
            json={"output_dir": output_dir}
        )
        response.raise_for_status()
        return response.json()

def print_json(data: dict):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="RSS Feed Processor CLI")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process RSS feeds")
    process_parser.add_argument("urls", nargs="+", help="RSS feed URLs to process")
    process_parser.add_argument("--batch-size", type=int, default=32, help="Batch size for processing")
    process_parser.add_argument("--max-articles", type=int, help="Maximum number of articles to process per feed")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search articles")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--source", help="Filter by source URL")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    
    # Filter command
    filter_parser = subparsers.add_parser("filter", help="Filter articles by source")
    filter_parser.add_argument("source_url", help="Source URL to filter by")
    
    # Save command
    save_parser = subparsers.add_parser("save", help="Save dataset shards")
    save_parser.add_argument("--output-dir", default="datasets", help="Output directory for shards")
    
    args = parser.parse_args()
    client = RSSClient(api_url=args.api_url)
    
    try:
        if args.command == "process":
            result = client.process_feeds(
                urls=args.urls,
                batch_size=args.batch_size,
                max_articles=args.max_articles
            )
        elif args.command == "search":
            result = client.search(
                query=args.query,
                source_url=args.source,
                top_k=args.top_k
            )
        elif args.command == "filter":
            result = client.filter_by_source(source_url=args.source_url)
        elif args.command == "save":
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            result = client.save_shards(output_dir=args.output_dir)
        else:
            parser.print_help()
            return
        
        print_json(result)
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
