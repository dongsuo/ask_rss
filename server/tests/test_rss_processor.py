"""
Test script for the RSS Processor module.
"""
import asyncio
from rss_processor.processor import RSSProcessor
from rss_processor.models import ProcessRSSRequest

async def test_processor():
    """Test the RSS Processor functionality."""
    print("Testing RSS Processor...")
    
    # Initialize the processor
    processor = RSSProcessor()
    
    # Test feed URLs
    test_feeds = [
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://techcrunch.com/feed/",
        "https://feeds.bbci.co.uk/news/technology/rss.xml"
    ]
    
    # Process feeds
    print(f"\nProcessing {len(test_feeds)} feeds...")
    results = await processor.process_feeds(
        rss_urls=test_feeds,
        batch_size=32,
        max_articles=3  # Limit to 3 articles per feed for testing
    )
    
    # Print results
    print(f"\nProcessed {sum(len(articles) for articles in results.values())} articles from {len(results)} sources")
    for source, articles in results.items():
        print(f"\nSource: {source}")
        print(f"Articles: {len(articles)}")
        for i, article in enumerate(articles[:2], 1):  # Show first 2 articles per source
            print(f"  {i}. {article.title}")
            print(f"     Published: {article.published}")
            print(f"     Link: {article.link}")
    
    # Test semantic search
    if any(articles for articles in results.values()):
        print("\nTesting semantic search...")
        query = "latest technology news"
        search_results = processor.semantic_search(query, top_k=3)
        
        print(f"\nSearch results for '{query}':")
        for i, result in enumerate(search_results, 1):
            print(f"\n{i}. {result['title']} (Score: {result['score']:.4f})")
            print(f"   Source: {result['source_url']}")
            print(f"   Link: {result['link']}")
    
    # Test saving datasets
    print("\nSaving dataset shards...")
    saved_paths = processor.save_shards_by_source(output_dir="test_datasets")
    print(f"Saved {len(saved_paths)} dataset shards:")
    for source, path in saved_paths.items():
        print(f"- {source}: {path}")

if __name__ == "__main__":
    asyncio.run(test_processor())
