from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import os
import logging
from pathlib import Path
import hashlib
from datasets import Dataset, load_dataset, Features, Value, Sequence
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from huggingface_hub import HfApi, HfFolder, login

from .models import Article, ProcessingStatus, SearchResult
from .utils import parse_feed, get_embeddings, get_source_name, clean_text

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RSSProcessor:
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2", 
                 device: str = None,
                 hf_token: str = None,
                 hf_repo: str = "ShawFay/ask_rss_datasets",
                 local_cache_dir: str = None,
                 cache_dir: str = "datasets"):
        """Initialize the RSS processor with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to use
            device: Device to run the model on (cuda, mps, or cpu)
            hf_token: Hugging Face authentication token
            hf_repo: Hugging Face repository to store datasets (format: username/repo)
            local_cache_dir: Local directory to cache datasets (default: ~/.cache/huggingface/datasets)
            cache_dir: Local directory to cache processed articles (default: datasets)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model = None
        self.logger = logging.getLogger(__name__)
        HF_TOKEN = os.getenv("HF_TOKEN")  # 从.env文件加载Token

        # Set up Hugging Face
        self.hf_token = hf_token or HF_TOKEN
        if not self.hf_token:
            raise ValueError("Hugging Face token is required. Set HF_TOKEN environment variable or pass hf_token parameter.")
            
        self.hf_repo = hf_repo
        self.hf_api = HfApi()
        self.hf_folder = HfFolder()
        
        # Login to Hugging Face
        login(token=self.hf_token)
        
        # Set up local cache
        self.local_cache_dir = Path(local_cache_dir) if local_cache_dir else Path.home() / ".cache" / "huggingface" / "datasets"
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up cache for processed articles
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_cache: Dict[str, List[float]] = {}
        self.articles_cache: Dict[str, Article] = {}
    
    def _get_dataset_name(self, feed_url: str) -> str:
        """Generate a unique dataset name based on the feed URL."""
        # Create a unique identifier for the feed
        feed_id = hashlib.md5(feed_url.encode()).hexdigest()
        return f"{self.hf_repo.split('/')[-1]}_{feed_id}"
        
    def _get_local_cache_path(self, dataset_name: str) -> Path:
        """Get local cache path for a dataset."""
        return self.local_cache_dir / dataset_name
    
    def _get_dataset_path(self, source_url: str) -> Path:
        """Get the path to save/load the dataset for a source."""
        source_hash = hashlib.md5(source_url.encode()).hexdigest()
        return self.cache_dir / f"{source_hash}"
    
    async def process_feed(self, feed_url: str, max_articles: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a single RSS feed, generate embeddings, and save as a dataset shard.
        
        Args:
            feed_url: URL of the RSS feed to process
            max_articles: Maximum number of articles to process
            
        Returns:
            Dict containing processing status and metadata
        """
        print(f"Processing feed: {feed_url}")
        try:
            # Parse feed and get articles
            articles = parse_feed(feed_url, max_articles)
            if not articles:
                return {
                    "status": "error",
                    "message": f"No articles found in feed: {feed_url}",
                    "source_url": feed_url,
                    "articles_processed": 0
                }
            
            # Generate embeddings for article content
            texts = [f"{a.title} {clean_text(a.summary or '')}" for a in articles]
            embeddings = await get_embeddings(texts)
            
            # Update articles with embeddings
            for article, embedding in zip(articles, embeddings):
                article.embedding = embedding
                self.articles_cache[article.link] = article
            
            # Create dataset with feed metadata
            dataset_dict = {
                'title': [a.title for a in articles],
                'link': [a.link for a in articles],
                'published': [a.published for a in articles],
                'source_url': [a.source_url for a in articles],
                'summary': [a.summary for a in articles],
                'embedding': [a.embedding for a in articles],
                'feed_url': [feed_url] * len(articles),  # Add feed URL to each article
                'feed_title': [get_source_name(feed_url)] * len(articles)  # Add feed title to each article
            }
            
            # Define features with feed metadata
            features = Features({
                'title': Value('string'),
                'link': Value('string'),
                'published': Value('string'),
                'source_url': Value('string'),
                'summary': Value('string'),
                'embedding': Sequence(Value('float32'), length=len(articles[0].embedding) if articles and hasattr(articles[0], 'embedding') else 0),
                'feed_url': Value('string'),
                'feed_title': Value('string')
            })
            
            dataset = Dataset.from_dict(dataset_dict, features=features)
            
            # Push dataset to Hugging Face Hub
            dataset_name = self._get_dataset_name(feed_url)
            
            # Set dataset info with source URL
            dataset.info.description = f"RSS feed dataset for {feed_url}"
            dataset.info.homepage = feed_url
            dataset.info.license = "MIT"
            
            # Add source URL to dataset features
            if not hasattr(dataset.info, 'features'):
                dataset.info.features = {}
            
            # Push to Hub with metadata
            dataset.push_to_hub(
                repo_id=f"{self.hf_repo}",
                config_name=dataset_name,
                split='train',
                token=self.hf_token,
                commit_message=f"Add dataset for {feed_url}",
                private=True
            )
            
            # Save metadata to a JSON file
            try:
                metadata = {
                    "name": dataset_name,
                    "feed_url": feed_url,
                    "feed_title": get_source_name(feed_url),
                    "source_url": feed_url,
                    "article_count": len(dataset),
                    "created_at": datetime.utcnow().isoformat(),
                    "features": [
                        {"name": "title", "dtype": "string"},
                        {"name": "link", "dtype": "string"},
                        {"name": "published", "dtype": "string"},
                        {"name": "source_url", "dtype": "string"},
                        {"name": "summary", "dtype": "string"},
                        {"name": "embedding", "dtype": "float32", "shape": [384]},
                        {"name": "feed_url", "dtype": "string"},
                        {"name": "feed_title", "dtype": "string"}
                    ]
                }
                
                # Save metadata to a JSON file
                import json
                metadata_json = json.dumps(metadata, indent=2)
                
                # Upload metadata file to the dataset
                self.hf_api.upload_file(
                    path_or_fileobj=metadata_json.encode('utf-8'),
                    path_in_repo=f"{dataset_name}/metadata.json",
                    repo_id=self.hf_repo,
                    repo_type="dataset",
                    token=self.hf_token,
                    commit_message=f"Add metadata for {dataset_name}"
                )
                
                # Also create a simple README
                readme_content = f"""# {dataset_name}

This dataset contains articles from the RSS feed: {feed_url}

## Metadata
- Feed URL: {feed_url}
- Feed Title: {get_source_name(feed_url)}
- Articles: {len(dataset)}
- Created: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

See `metadata.json` for complete dataset information."""
                
                self.hf_api.upload_file(
                    path_or_fileobj=readme_content.encode('utf-8'),
                    path_in_repo=f"{dataset_name}/README.md",
                    repo_id=self.hf_repo,
                    repo_type="dataset",
                    token=self.hf_token,
                    commit_message=f"Update README for {dataset_name}"
                )
                
            except Exception as e:
                self.logger.warning(f"Failed to save dataset metadata: {str(e)}")
            
            return {
                "status": "success",
                "message": f"Processed {len(articles)} articles from {feed_url}",
                "source_url": feed_url,
                "articles_processed": len(articles),
                "dataset_name": dataset_name,
                "hf_repo": self.hf_repo
            }
            
        except Exception as e:
            self.logger.error(f"Error processing feed {feed_url}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing feed {feed_url}: {str(e)}",
                "source_url": feed_url,
                "articles_processed": 0
            }

    async def list_sources(self) -> List[Dict[str, Any]]:
        """
        List all sources in the Hugging Face dataset repo: each source is a subdirectory with a metadata.json file.
        Returns a list of metadata dicts for each source.
        """
        import requests
        from huggingface_hub import list_repo_files

        self.logger.info(f"Listing sources from Hugging Face repo: {self.hf_repo}")
        sources = []
        try:
            # 1. 获取所有文件列表
            files = list_repo_files(self.hf_repo, repo_type="dataset")
            # 2. 找到所有形如 <source_id>/metadata.json 的文件
            source_meta_files = [f for f in files if f.count('/') == 1 and f.endswith('metadata.json')]
            for meta_file in source_meta_files:
                source_dir = meta_file.split('/')[0]
                meta_url = f"https://huggingface.co/datasets/{self.hf_repo}/resolve/main/{source_dir}/metadata.json"
                try:
                    resp = requests.get(meta_url, timeout=10)
                    if resp.status_code == 200:
                        meta = resp.json()
                        sources.append(meta)
                        self.logger.debug(f"Loaded metadata for source {source_dir}")
                    else:
                        self.logger.warning(f"Failed to fetch metadata.json for {source_dir}: {resp.status_code}")
                except Exception as e:
                    self.logger.warning(f"Error fetching metadata for {source_dir}: {str(e)}")
            self.logger.info(f"Found {len(sources)} sources in Hugging Face repo")
            return sources
        except Exception as e:
            self.logger.error(f"Error listing sources from Hugging Face: {str(e)}", exc_info=True)
            return []
            
    async def _list_local_sources(self) -> List[Dict[str, Any]]:
        """List sources from local cache with feed metadata."""
        sources = []
        # 使用实例的 cache_dir 属性，而不是硬编码路径
        cache_dir = self.cache_dir
        self.logger.info(f"Looking for datasets in local cache directory: {cache_dir.absolute()}")

        if not cache_dir.exists():
            self.logger.warning(f"Local cache directory {cache_dir.absolute()} does not exist")
            return []

        # Look for all parquet files in the cache directory
        parquet_files = list(cache_dir.glob("**/*.parquet"))
        self.logger.info(f"Found {len(parquet_files)} parquet files in {cache_dir}")
        
        for file_path in parquet_files:
            try:
                # Try to read the parquet file
                self.logger.info(f"Loading dataset from {file_path}")
                try:
                    dataset = datasets.load_dataset("parquet", data_files=str(file_path))["train"]
                except Exception as e:
                    self.logger.error(f"Failed to load dataset from {file_path}: {str(e)}")
                    raise
                
                # Get feed metadata from the first row if available
                if len(dataset) > 0:
                    feed_url = dataset[0].get('feed_url', '')
                    feed_title = dataset[0].get('feed_title', file_path.stem)
                    article_count = len(dataset)
                    
                    # Get file modification time
                    mtime = file_path.stat().st_mtime
                    last_modified = datetime.fromtimestamp(mtime).isoformat()
                    
                    sources.append({
                        "name": file_path.stem,
                        "path": str(file_path),
                        "source_url": feed_url,
                        "feed_url": feed_url,
                        "feed_title": feed_title,
                        "article_count": article_count,
                        "last_modified": last_modified,
                        "size_mb": file_path.stat().st_size / (1024 * 1024)  # Convert to MB
                    })
                    
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {str(e)}")
                continue
                
        return sources
        
    async def search(self, query: str, top_k: int = 5, source_url: Optional[str] = None, feed_url: Optional[str] = None) -> List[SearchResult]:
        """Search for relevant articles across all datasets.
        
        Args:
            query: Search query string
            top_k: Maximum number of results to return
            source_url: Optional source URL to filter results by
            feed_url: Optional feed URL to filter results by
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        try:
            # Get the model if not loaded
            if self.model is None:
                self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Generate query embedding using the model directly since we already have it loaded
            query_embedding = self.model.encode(
                [query],
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True
            )[0]
            results: List[SearchResult] = []
            
            # If source_url is provided, only search that source
            if source_url:
                try:
                    # Check if source_url is a local path or a dataset name
                    if os.path.exists(source_url):
                        dataset_path = Path(source_url)
                    else:
                        # Try to find the dataset in the cache
                        dataset_path = self._get_dataset_path(source_url)
                    
                    if not dataset_path.exists():
                        raise ValueError(f"Source not found: {source_url}")
                        
                    # Load and filter dataset
                    dataset = load_dataset("parquet", data_files=str(dataset_path), split="train")
                    
                    # Apply feed_url filter if provided
                    if feed_url:
                        dataset = dataset.filter(lambda x: x['feed_url'] == feed_url)
                    
                    if len(dataset) > 0:  # Only process if there are results after filtering
                        await self._process_dataset(dataset, query_embedding, results, top_k)
                        
                except Exception as e:
                    self.logger.error(f"Error processing source {source_url}: {str(e)}")
                    raise
            else:
                # Search all available sources
                sources = await self.list_sources()
                
                # First try to get from Hugging Face Hub
                try:
                    # Get dataset list from Hugging Face Hub
                    api = HfApi()
                    datasets_list = api.list_datasets(author=self.hf_repo.split('/')[0])
                    
                    # Filter datasets that match our repo
                    dataset_names = [
                        d.id for d in datasets_list 
                        if d.id.startswith(f"{self.hf_repo.split('/')[0]}/") and d.id != self.hf_repo
                    ]
                    
                    # Process each dataset
                    for dataset_name in dataset_names:
                        try:
                            # Load dataset from Hugging Face Hub
                            dataset = load_dataset(dataset_name, split="train")
                            
                            # Apply feed_url filter if provided
                            if feed_url:
                                dataset = dataset.filter(lambda x: x['feed_url'] == feed_url)
                            
                            if len(dataset) > 0:  # Only process if there are results after filtering
                                await self._process_dataset(dataset, query_embedding, results, top_k)
                            
                        except Exception as e:
                            self.logger.error(f"Error processing dataset {dataset_name}: {e}")
                            continue
                            
                except Exception as e:
                    self.logger.error(f"Error listing datasets from Hugging Face Hub: {e}")
                    # Fall back to local cache if remote listing fails
                    for source in sources:
                        try:
                            dataset = load_dataset("parquet", data_files=source['path'], split="train")
                            
                            # Apply feed_url filter if provided
                            if feed_url:
                                dataset = dataset.filter(lambda x: x['feed_url'] == feed_url)
                            
                            if len(dataset) > 0:  # Only process if there are results after filtering
                                await self._process_dataset(dataset, query_embedding, results, top_k)
                                
                        except Exception as e:
                            self.logger.error(f"Error processing local dataset {source['path']}: {e}")
                            continue
            
            # Sort all results by score and return top k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in search: {e}")
            raise
    
    async def _process_dataset(self, dataset, query_embedding, results, top_k):
        """Process a dataset and add search results to the results list."""
        try:
            import numpy as np
            from numpy.linalg import norm
            
            # Convert to list for processing
            dataset_list = [item for item in dataset]
            
            # Calculate similarities in batches
            similarities = []
            for item in dataset_list:
                try:
                    emb = np.array(item['embedding'])
                    similarity = float(np.dot(emb, query_embedding) / (norm(emb) * norm(query_embedding)))
                    similarities.append((similarity, item))
                except Exception as e:
                    self.logger.warning(f"Error calculating similarity: {str(e)}")
                    continue
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Add top k results
            for similarity, item in similarities[:top_k]:
                try:
                    # Get source URL with fallbacks
                    source_url = item.get('source_url', '')
                    if not source_url and hasattr(dataset, 'info'):
                        source_url = getattr(dataset.info, 'homepage', '')
                    if not source_url and hasattr(dataset, 'info') and hasattr(dataset.info, 'dataset_name'):
                        source_url = f"{self.hf_repo.split('/')[0]}/{dataset.info.dataset_name}"
                    
                    # Get feed information
                    feed_url = item.get('feed_url', '')
                    feed_title = item.get('feed_title', '')
                    
                    results.append(SearchResult(
                        title=item.get('title', 'No title'),
                        link=item.get('link', ''),
                        source_url=source_url,
                        feed_url=feed_url,
                        feed_title=feed_title,
                        published=item.get('published', ''),
                        summary=item.get('summary', ''),
                        score=similarity
                    ))
                except Exception as e:
                    self.logger.warning(f"Error creating search result: {str(e)}")
                    continue
                
        except Exception as e:
            self.logger.error(f"Error processing dataset: {e}")
            raise
    
    async def process_feeds(
        self, 
        rss_urls: List[str], 
        batch_size: int = 32, 
        max_articles: Optional[int] = None
    ) -> Dict[str, List[Article]]:
        """Process multiple RSS feeds and return a dictionary of source to articles."""
        results = {}
        
        for url in rss_urls:
            try:
                articles = await self.process_feed(url, max_articles)
                if articles:
                    source_name = get_source_name(url)
                    results[source_name] = articles
                    self.articles.extend(articles)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue
                
        return results

    def filter_by_source(self, source_url: str) -> List[Article]:
        """Filter articles by source URL."""
        return [article for article in self.articles if article.source_url == source_url]

    def to_dataset(self, articles: Optional[List[Article]] = None) -> Dataset:
        """Convert articles to a Hugging Face dataset with proper features and metadata."""
        if articles is None:
            articles = self.articles
            
        if not articles:
            return Dataset.from_dict({})
            
        # Get source URL from the first article
        source_url = articles[0].source_url if articles else ""
        
        # Convert to dict format
        data = {
            'title': [a.title for a in articles],
            'link': [a.link for a in articles],
            'published': [a.published.isoformat() if a.published else "" for a in articles],
            'summary': [a.summary for a in articles],
            'content': [a.content for a in articles],
            'source_url': [a.source_url for a in articles],
            'embedding': [a.embedding for a in articles]
        }
        
        # Create dataset with features
        features = Features({
            'title': Value('string'),
            'link': Value('string'),
            'published': Value('string'),
            'summary': Value('string'),
            'content': Value('string'),
            'source_url': Value('string'),
            'embedding': Sequence(Value('float32'), length=len(articles[0].embedding) if articles and hasattr(articles[0], 'embedding') else 0)
        })
        
        dataset = Dataset.from_dict(data, features=features)
        
        # Set dataset info
        dataset.info.description = f"RSS feed dataset for {source_url}"
        dataset.info.homepage = source_url
        dataset.info.license = "MIT"
        dataset.info.version = "1.0.0"
        
        # Add source URL to config
        if not hasattr(dataset.info, 'features'):
            dataset.info.features = features
            
        return dataset

    def save_dataset(self, dataset: Dataset, output_dir: str = "datasets") -> str:
        """Save dataset to disk."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"rss_dataset_{timestamp}")
        dataset.save_to_disk(output_path)
        return output_path

    def save_shards_by_source(self, output_dir: str = "datasets") -> Dict[str, str]:
        """Save separate dataset shards for each source."""
        sources = set(article.source_url for article in self.articles)
        saved_paths = {}
        
        for source in sources:
            source_articles = self.filter_by_source(source)
            if not source_articles:
                continue
                
            source_name = get_source_name(source)
            dataset = self.to_dataset(source_articles)
            
            # Create output directory
            source_dir = os.path.join(output_dir, source_name)
            os.makedirs(source_dir, exist_ok=True)
            
            # Save dataset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(source_dir, f"{source_name}_{timestamp}")
            dataset.save_to_disk(output_path)
            saved_paths[source] = output_path
            
        return saved_paths

    def semantic_search(
        self, 
        query: str, 
        source_url: Optional[str] = None, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on the articles."""
        from sentence_transformers import util
        import torch
        
        # Filter articles by source if specified
        articles = self.filter_by_source(source_url) if source_url else self.articles
        if not articles:
            return []
        
        # Get query embedding
        query_embedding = get_embeddings([query])[0]
        
        # Prepare article embeddings
        article_embeddings = [a.embedding for a in articles if a.embedding]
        if not article_embeddings:
            return []
            
        # Convert to tensors
        query_tensor = torch.tensor(query_embedding).unsqueeze(0)
        article_tensors = torch.tensor(article_embeddings)
        
        # Calculate similarities
        similarities = util.pytorch_cos_sim(query_tensor, article_tensors)[0]
        
        # Get top-k results
        top_indices = torch.topk(similarities, k=min(top_k, len(similarities))).indices.tolist()
        
        # Prepare results
        results = []
        for idx in top_indices:
            article = articles[idx]
            results.append({
                'title': article.title,
                'link': article.link,
                'published': article.published.isoformat() if article.published else None,
                'summary': article.summary,
                'source_url': article.source_url,
                'score': float(similarities[idx])
            })
            
        return results
