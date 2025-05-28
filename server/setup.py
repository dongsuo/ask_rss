from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rss_processor",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A FastAPI-based RSS feed processor with semantic search capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rss-processor",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "feedparser>=6.0.0",
        "beautifulsoup4>=4.9.0",
        "sentence-transformers>=2.2.0",
        "python-dotenv>=0.19.0",
        "datasets>=2.0.0",
        "pydantic>=1.8.0",
        "requests>=2.26.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0",
            "isort>=5.0.0",
            "mypy>=0.9.0",
            "flake8>=3.9.0",
        ],
    },
)
