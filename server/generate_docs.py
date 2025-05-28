"""
Generate API documentation from OpenAPI specification.
"""
import json
import os
import sys
from pathlib import Path
import requests

def generate_openapi_spec(api_url: str = "http://localhost:8000/openapi.json") -> dict:
    """
    Fetch the OpenAPI specification from the running API.
    
    Args:
        api_url: URL to the OpenAPI specification
        
    Returns:
        OpenAPI specification as a dictionary
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI spec: {e}", file=sys.stderr)
        sys.exit(1)

def save_openapi_spec(spec: dict, output_file: str = "openapi.json") -> None:
    """
    Save the OpenAPI specification to a file.
    
    Args:
        spec: OpenAPI specification dictionary
        output_file: Path to the output file
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print(f"OpenAPI spec saved to {output_file}")

def generate_redoc_html(spec: dict, output_file: str = "docs/index.html") -> None:
    """
    Generate ReDoc HTML documentation.
    
    Args:
        spec: OpenAPI specification dictionary
        output_file: Path to the output HTML file
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # ReDoc HTML template
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>RSS Feed Processor API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url='{}'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body>
</html>
"""
    
    # Save the spec to a temporary file
    spec_file = os.path.join(output_dir, "openapi.json")
    save_openapi_spec(spec, spec_file)
    
    # Generate HTML with relative path to the spec
    relative_spec_path = os.path.relpath(spec_file, os.path.dirname(output_file))
    html_content = html_template.format(relative_spec_path)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"ReDoc HTML documentation generated at {output_file}")

def main():
    """Main function to generate documentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate API documentation")
    parser.add_argument("--api-url", default="http://localhost:8000/openapi.json",
                       help="URL to the OpenAPI specification")
    parser.add_argument("--output-dir", default="docs",
                       help="Output directory for documentation")
    parser.add_argument("--format", choices=["json", "html", "all"], default="all",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate OpenAPI spec
    spec = generate_openapi_spec(args.api_url)
    
    # Generate requested output formats
    if args.format in ["json", "all"]:
        json_file = os.path.join(args.output_dir, "openapi.json")
        save_openapi_spec(spec, json_file)
    
    if args.format in ["html", "all"]:
        html_file = os.path.join(args.output_dir, "index.html")
        generate_redoc_html(spec, html_file)
    
    print("\nDocumentation generation complete!")

if __name__ == "__main__":
    main()
