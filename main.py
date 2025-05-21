import argparse
import feedparser
import requests
import os
from datasets import Dataset, Features, Value, Sequence
from huggingface_hub import HfFolder,InferenceClient
from bs4 import BeautifulSoup
from typing import List

MODEL_ID = "sentence-transformers/all-mpnet-base-v2"
HF_TOKEN = os.getenv("HF_TOKEN")  # 替换为你的 Hugging Face Token
API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

load_dotenv()

# 获取文本嵌入
def query(texts: List[str]) -> List[List[float]]:
    """获取文本的嵌入向量"""
    # 创建InferenceClient实例
    client = InferenceClient(
        provider="hf-inference",
        api_key=HF_TOKEN,
    )
    
    # 对每个文本进行特征提取
    results = []
    for text in texts:
        result = client.feature_extraction(
            text,
            model=MODEL_ID,
        )
        results.append(result)
    
    return results

def main():
    # Check if user is authenticated with Hugging Face
    if not HfFolder.get_token():
        print("Please log in using `huggingface-cli login` first.")
        exit(1)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert RSS feed articles to a Hugging Face Dataset")
    parser.add_argument('--rss_url', required=True, help='URL of the RSS feed to parse')
    parser.add_argument('--repo_id', required=True, help='Repository ID on Hugging Face Hub (e.g., "username/dataset_name")')
    args = parser.parse_args()

    # Parse the RSS feed
    print("Parsing RSS feed...")
    feed = feedparser.parse(args.rss_url)
    if feed.bozo:
        print(f"Error parsing RSS feed: {feed.bozo_exception}")
        exit(1)

    # Extract article data
    articles = []
    for entry in feed.entries:
        content = entry.get('description', '') or entry.get('summary', '')
        content = BeautifulSoup(content, 'html.parser').get_text()  # Remove HTML tags
        article = {
            'title': entry.get('title', ''),
            'content': content,
            'date': entry.get('published', '') or entry.get('updated', ''),
            'link': entry.get('link', '')
        }
        articles.append(article)

    if not articles:
        print("No articles found in the RSS feed.")
        exit(1)
    faq_texts = [f"{article['title']} {article['content']}" for article in articles]
    faq_embeddings = query(faq_texts)
    # Create the dataset
    print("Creating dataset...")
    data = {
        'title': [article['title'] for article in articles],
        'content': [article['content'] for article in articles],
        'date': [article['date'] for article in articles],
        'link': [article['link'] for article in articles],
        'embedding': faq_embeddings  # 添加嵌入向量
    }
    features = Features({
        'title': Value('string'),
        'content': Value('string'),
        'date': Value('string'),
        'link': Value('string'),
        'embedding': Sequence(Value('float32'))  # 存储嵌入向量
    })
    dataset = Dataset.from_dict(data, features=features)

    # Upload to Hugging Face Hub
    print("Uploading dataset to Hugging Face Hub...")
    dataset.push_to_hub(args.repo_id)
    print(f"Dataset successfully uploaded to https://huggingface.co/datasets/{args.repo_id}")

if __name__ == "__main__":
    main()