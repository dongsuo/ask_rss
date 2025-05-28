"""
API monitoring and health check script.
"""
import time
import requests
import psutil
import platform
import socket
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

class APIMonitor:
    """Monitor the health and performance of the RSS Feed Processor API."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """Initialize the monitor with the API URL."""
        self.api_url = api_url.rstrip("/")
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "hostname": socket.gethostname(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "virtual_memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used,
                    "free": psutil.virtual_memory().free
                },
                "disk_usage": {
                    "/": {
                        "total": psutil.disk_usage("/").total,
                        "used": psutil.disk_usage("/").used,
                        "free": psutil.disk_usage("/").free,
                        "percent": psutil.disk_usage("/").percent
                    }
                },
                "boot_time": psutil.boot_time(),
                "uptime": time.time() - psutil.boot_time()
            },
            "monitor": {
                "start_time": self.start_time,
                "uptime": time.time() - self.start_time,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0
            }
        }
    
    def check_health(self) -> Dict[str, Any]:
        """Check the health of the API."""
        health_url = f"{self.api_url}/health"
        start_time = time.time()
        
        try:
            response = requests.get(health_url, timeout=5)
            response_time = (time.time() - start_time) * 1000  # in milliseconds
            self.response_times.append(response_time)
            self.request_count += 1
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": response_time,
                **response.json()
            }
        except requests.exceptions.RequestException as e:
            self.error_count += 1
            return {
                "status": "error",
                "error": str(e)
            }
    
    def monitor_loop(self, interval: int = 60, max_checks: Optional[int] = None):
        """Run the monitor in a loop."""
        print(f"Starting API monitor for {self.api_url}")
        print("Press Ctrl+C to stop...\n")
        
        check_count = 0
        
        try:
            while True:
                if max_checks and check_count >= max_checks:
                    break
                    
                # Get system info
                system_info = self.get_system_info()
                
                # Check API health
                health = self.check_health()
                
                # Print status
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"[{timestamp}] API Status: {health.get('status', 'unknown').upper()}")
                print(f"  Response Time: {health.get('response_time_ms', 0):.2f} ms")
                print(f"  CPU Usage: {system_info['system']['cpu_percent']}%")
                print(f"  Memory Usage: {system_info['system']['virtual_memory']['percent']}%")
                print(f"  Disk Usage: {system_info['system']['disk_usage']['/']['percent']}%")
                print()
                
                # Save to log file
                log_entry = {
                    "timestamp": timestamp,
                    "system": system_info["system"],
                    "health": health
                }
                self._save_log(log_entry)
                
                check_count += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    def _save_log(self, log_entry: Dict[str, Any]):
        """Save log entry to a file."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "api_monitor.log"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

def main():
    """Main function to run the monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor the RSS Feed Processor API")
    parser.add_argument("--api-url", default="http://localhost:8000",
                       help="Base URL of the API")
    parser.add_argument("--interval", type=int, default=60,
                       help="Monitoring interval in seconds")
    parser.add_argument("--max-checks", type=int, default=None,
                       help="Maximum number of health checks to perform")
    
    args = parser.parse_args()
    
    monitor = APIMonitor(api_url=args.api_url)
    monitor.monitor_loop(interval=args.interval, max_checks=args.max_checks)

if __name__ == "__main__":
    main()
