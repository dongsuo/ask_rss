# RSS Feed Processor API

A simple and efficient API for processing RSS feeds and performing semantic searches on the content. This service automatically processes RSS feeds, generates embeddings for the content, and allows for semantic search across all processed articles. The service stores datasets in the Hugging Face Hub for easy access and sharing.

## Features

- Process RSS feeds with automatic embedding generation
- Store articles with their embeddings in the Hugging Face Hub
- Perform semantic search across all processed content
- Simple and intuitive REST API with just three endpoints
- Built with FastAPI for high performance
- Automatic caching of datasets for improved performance

## Project Structure

```
server/
├── rss_processor/           # Main package
│   ├── __init__.py          # Package initialization
│   ├── models.py            # Pydantic models
│   ├── processor.py         # Core processing and search logic
│   ├── utils.py             # Utility functions
│   └── api.py               # FastAPI routes
├── datasets/                # Directory for storing processed data
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your Hugging Face token in the `.env` file:
   ```bash
   # .env
   HF_TOKEN=your_huggingface_token_here
   ```

## Running the API

Start the server with auto-reload for development:

```bash
# The HF_TOKEN from .env will be automatically loaded
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Hugging Face Hub Integration

The service uses the Hugging Face Hub to store and retrieve datasets. Here's how it works:

1. **Dataset Naming**: Each feed URL is hashed to create a unique dataset name in the format `ask_rss_datasets_<hash>`
2. **Caching**: Datasets are cached locally in `~/.cache/huggingface/datasets` for faster access
3. **Authentication**: Uses your Hugging Face token for authentication (set via `HF_TOKEN` environment variable)

### Managing Datasets

You can view and manage your datasets on the [Hugging Face Hub](https://huggingface.co/datasets/ShawFay/ask_rss_datasets) (replace with your username/repo).

### Using a Custom Repository

To use a different Hugging Face repository, update the `hf_repo` parameter when initializing the `RSSProcessor`:

```python
processor = RSSProcessor(
    hf_repo="your-username/your-repo-name",
    hf_token="your-hf-token"
)
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Available Endpoints

1. **Health Check**
   - `GET /api/v1/health`: Check if the API is running

2. **Process RSS Feed**
   - `POST /api/v1/process-rss`: Process one or more RSS feeds and generate embeddings

3. **Semantic Search**
   - `POST /api/v1/semantic-search`: Search across all processed articles using natural language

## Example Usage

### 1. Check API Health

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Process an RSS Feed

```bash
curl -X POST "http://localhost:8000/api/v1/process-rss" \
  -H "Content-Type: application/json" \
  -d '{
    "rss_urls": [
      "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
      "https://techcrunch.com/feed/"
    ],
    "max_articles": 10
  }'
```

### 3. Perform Semantic Search

```bash
curl -X POST "http://localhost:8000/api/v1/semantic-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest technology news about artificial intelligence",
    "source_url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "top_k": 5
  }'
```

## How It Works

1. **Processing RSS Feeds**:
   - Fetches articles from the provided RSS feed URLs
   - Cleans and preprocesses the text content
   - Generates embeddings using a pre-trained sentence transformer model
   - Stores the articles with their embeddings in sharded datasets

2. **Semantic Search**:
   - Converts the search query into an embedding
   - Computes cosine similarity between the query and all article embeddings
   - Returns the most relevant articles based on semantic similarity

## Dependencies

- FastAPI - Modern, fast web framework
- Uvicorn - ASGI server
- Sentence Transformers - For generating embeddings
- Feedparser - For parsing RSS/Atom feeds
- BeautifulSoup - For HTML parsing
- Hugging Face Datasets - For efficient data storage and retrieval

## Performance Notes

- The first request to process a feed will be slower as it downloads the pre-trained model
- Subsequent requests will be faster as the model is cached
- Processing is done in batches for better performance
- Embeddings are stored on disk for persistence between server restarts


## License

MIT