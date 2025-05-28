"""
Health check script for the RSS Feed Processor API.
"""
import sys
import requests
from typing import Dict, Any, Optional

class HealthCheck:
    """Health check for the RSS Feed Processor API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the health check with the base URL of the API."""
        self.base_url = base_url.rstrip("/")
        self.endpoints = [
            "/health",
            "/api/v1/process-rss",
            "/api/v1/semantic-search",
            "/api/v1/filter-by-source",
            "/api/v1/save-shards"
        ]
    
    def check_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Check the health of a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if endpoint == "/api/v1/process-rss":
                # For POST endpoints, send a minimal valid request
                response = requests.post(
                    url,
                    json={"rss_urls": ["https://example.com/feed"]},
                    timeout=5
                )
            elif endpoint == "/api/v1/semantic-search":
                response = requests.post(
                    url,
                    json={"query": "test"},
                    timeout=5
                )
            elif endpoint == "/api/v1/filter-by-source":
                response = requests.post(
                    url,
                    json={"source_url": "https://example.com"},
                    timeout=5
                )
            elif endpoint == "/api/v1/save-shards":
                response = requests.post(
                    url,
                    json={"output_dir": "/tmp"},
                    timeout=5
                )
            else:
                # For GET endpoints
                response = requests.get(url, timeout=5)
            
            return {
                "endpoint": endpoint,
                "status": "healthy" if response.status_code < 500 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint,
                "status": "error",
                "error": str(e)
            }
    
    def run_checks(self) -> Dict[str, Any]:
        """Run health checks for all endpoints."""
        results = []
        all_healthy = True
        
        for endpoint in self.endpoints:
            result = self.check_endpoint(endpoint)
            results.append(result)
            
            if result.get("status") != "healthy":
                all_healthy = False
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": self._get_timestamp(),
            "endpoints": results
        }
    
    def _get_timestamp(self) -> str:
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def print_results(results: Dict[str, Any]):
    """Print the health check results in a human-readable format."""
    print(f"\n{' RSS Feed Processor API Health Check ':=^80}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['status'].upper()}\n")
    
    for endpoint in results["endpoints"]:
        status = endpoint.get("status", "unknown").upper()
        status_code = endpoint.get("status_code", "N/A")
        response_time = f"{endpoint.get('response_time_ms', 0):.2f} ms"
        
        if status == "HEALTHY":
            status_display = f"\033[92m{status}\033[0m"  # Green
        elif status == "UNHEALTHY":
            status_display = f"\033[91m{status}\033[0m"  # Red
        else:
            status_display = f"\033[93m{status}\033[0m"  # Yellow
        
        print(f"{endpoint['endpoint']}:")
        print(f"  Status:     {status_display}")
        print(f"  Status Code: {status_code}")
        print(f"  Response:   {response_time}")
        
        if "error" in endpoint:
            print(f"  Error:      {endpoint['error']}")
    
    print("\n" + "=" * 80)

def main():
    """Main function to run the health check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Health check for RSS Feed Processor API")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL of the API")
    
    args = parser.parse_args()
    
    health_check = HealthCheck(base_url=args.url)
    results = health_check.run_checks()
    print_results(results)
    
    # Exit with non-zero status if any check failed
    if results["status"] != "healthy":
        sys.exit(1)

if __name__ == "__main__":
    main()
