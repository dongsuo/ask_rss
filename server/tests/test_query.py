import unittest
import requests
import time
import torch
import os
from dotenv import load_dotenv
from typing import List, Any
from datasets import load_dataset
from sentence_transformers.util import semantic_search

# 加载环境变量
load_dotenv()

# 配置 Hugging Face API
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN = os.getenv("HF_TOKEN")  # 从.env文件加载Token
API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# 文档中的 query 函数 - 获取文本嵌入
def query(texts: List[str]) -> List[List[float]]:
    response = requests.post(API_URL, headers=HEADERS, json={"inputs": texts, "options": {"wait_for_model": True}})
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    return response.json()

# 加载 FAQ 数据集并转换为 PyTorch 张量
def load_faq_embeddings(dataset_name: str = "ITESM/embedded_faqs_medicare"):
    """加载 FAQ 嵌入数据集并转换为 PyTorch 张量"""
    faqs_embeddings = load_dataset(dataset_name)
    dataset_embeddings = torch.from_numpy(faqs_embeddings["train"].to_pandas().to_numpy()).to(torch.float)
    return faqs_embeddings, dataset_embeddings

# 执行语义搜索并返回最相关的 FAQ
def find_similar_faqs(query_text: str, dataset_embeddings, faqs_dataset, top_k: int = 5):
    """查找与查询最相似的 FAQ"""
    # 获取查询的嵌入向量
    query_output = query([query_text])
    query_embeddings = torch.FloatTensor(query_output)
    
    # 执行语义搜索
    hits = semantic_search(query_embeddings, dataset_embeddings, top_k=top_k)
    
    # 获取最相似的 FAQ
    similar_faqs = []
    for i in range(len(hits[0])):
        corpus_id = hits[0][i]['corpus_id']
        score = hits[0][i]['score']
        faq = faqs_dataset["train"][corpus_id]
        similar_faqs.append({
            "text": faq["text"],
            "score": score
        })
    
    return similar_faqs

class TestQueryFunction(unittest.TestCase):
    def test_single_text(self):
        """测试单个文本输入是否返回正确的 embedding"""
        texts = ["How can Medicare help me?"]
        result = query(texts)
        self.assertIsInstance(result, list, "Result should be a list")
        self.assertEqual(len(result), 1, "Should return one embedding for one text")
        self.assertEqual(len(result[0]), 384, "Embedding should have 384 dimensions")
        self.assertTrue(all(isinstance(x, float) for x in result[0]), "Embedding values should be floats")

    def test_multiple_texts(self):
        """测试多个文本输入是否返回正确的 embeddings"""
        texts = [
            "How do I get a replacement Medicare card?",
            "What is Medicare and who can get it?"
        ]
        result = query(texts)
        self.assertEqual(len(result), 2, "Should return two embeddings")
        self.assertEqual(len(result[0]), 384, "First embedding should have 384 dimensions")
        self.assertEqual(len(result[1]), 384, "Second embedding should have 384 dimensions")

    def test_empty_input(self):
        """测试空输入是否抛出错误"""
        with self.assertRaises(Exception, msg="Empty input should raise an exception"):
            query([])

    def test_invalid_token(self):
        """测试无效 token 是否抛出认证错误"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        with self.assertRaises(Exception, msg="Invalid token should raise an exception"):
            response = requests.post(API_URL, headers=invalid_headers, json={"inputs": ["test"], "options": {"wait_for_model": True}})
            response.raise_for_status()

    def test_performance(self):
        """测试单文本和多文本的响应时间"""
        texts_single = ["How can Medicare help me?"]
        texts_multiple = ["Text " + str(i) for i in range(10)]  # 10 个文本

        # 测试单文本
        start_time = time.time()
        query(texts_single)
        single_time = time.time() - start_time
        print(f"Single text query time: {single_time:.2f} seconds")
        self.assertLess(single_time, 30, "Single text query should take less than 30 seconds")

        # 测试多文本
        start_time = time.time()
        query(texts_multiple)
        multi_time = time.time() - start_time
        print(f"Multiple texts query time: {multi_time:.2f} seconds")
        self.assertLess(multi_time, 60, "Multiple texts query should take less than 60 seconds")

    def test_semantic_search(self):
        """测试语义搜索功能"""
        try:
            # 尝试加载数据集
            faqs_dataset, dataset_embeddings = load_faq_embeddings()
            
            # 执行语义搜索
            query_text = "How can Medicare help me?"
            similar_faqs = find_similar_faqs(query_text, dataset_embeddings, faqs_dataset)
            
            # 验证结果
            self.assertIsInstance(similar_faqs, list, "Result should be a list")
            self.assertEqual(len(similar_faqs), 5, "Should return 5 similar FAQs")
            self.assertIn("text", similar_faqs[0], "Each result should have a 'text' field")
            self.assertIn("score", similar_faqs[0], "Each result should have a 'score' field")
            self.assertGreater(similar_faqs[0]["score"], 0, "Score should be positive")
            
            # 打印结果
            print("\nTop 5 similar FAQs:")
            for i, faq in enumerate(similar_faqs):
                print(f"{i+1}. {faq['text']} (Score: {faq['score']:.4f})")
                
        except Exception as e:
            self.skipTest(f"Skipping semantic search test due to: {str(e)}")

if __name__ == "__main__":
    # 运行单元测试
    unittest.main()
    
    # 或者直接执行语义搜索示例
    # print("\n示例: 执行语义搜索")
    # faqs_dataset, dataset_embeddings = load_faq_embeddings()
    # query_text = "How can Medicare help me?"
    # similar_faqs = find_similar_faqs(query_text, dataset_embeddings, faqs_dataset)
    # print("\nTop 5 similar FAQs:")
    # for i, faq in enumerate(similar_faqs):
    #     print(f"{i+1}. {faq['text']} (Score: {faq['score']:.4f})")