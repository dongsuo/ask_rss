#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
语义搜索演示脚本

这个脚本演示如何使用语义搜索来查找与用户查询最相似的Google Blog RSS FAQ。
"""

try:
    import torch
    import os
    from dotenv import load_dotenv
    from datasets import load_dataset
    from sentence_transformers.util import semantic_search
    from huggingface_hub import InferenceClient
    from typing import List
    DEPENDENCIES_INSTALLED = True
except ImportError as e:
    print(f"错误: 缺少必要的依赖包 - {e}")
    print("\n请安装所需的依赖包:")
    print("pip install --user torch datasets sentence-transformers huggingface_hub python-dotenv")
    print("\n如果您使用的是虚拟环境，请先激活虚拟环境，然后运行:")
    print("pip install torch datasets sentence-transformers huggingface_hub python-dotenv")
    DEPENDENCIES_INSTALLED = False
    # 导入基本模块以允许脚本继续运行
    from typing import List

# 加载环境变量
load_dotenv()

# 配置 Hugging Face API
MODEL_ID = "sentence-transformers/all-mpnet-base-v2"  # 更新为新的模型
HF_TOKEN = os.getenv("HF_TOKEN")  # 从.env文件加载Token

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

# 加载 FAQ 数据集并转换为 PyTorch 张量
def load_faq_embeddings(dataset_name: str = "ShawFay/google_blog_dataset"):
    """加载 FAQ 嵌入数据集并转换为 PyTorch 张量"""
    print(f"正在加载数据集 {dataset_name}...")
    faqs_embeddings = load_dataset(dataset_name)
    
    # 获取数据集的列名
    column_names = faqs_embeddings["train"].column_names
    print(f"数据集列名: {column_names}")
    
    # 检查数据集的第一个样本，了解其结构
    first_sample = faqs_embeddings["train"][0]
    print("数据集第一个样本的键:", list(first_sample.keys()))
    
    # 提取嵌入向量字段，如果存在的话
    if "embedding" in column_names:
        # 如果数据集中有embedding字段，直接使用
        print("使用数据集中的embedding字段...")
        # 检查embedding的类型和形状
        first_embedding = first_sample["embedding"]
        print(f"第一个embedding的类型: {type(first_embedding)}, 长度: {len(first_embedding) if hasattr(first_embedding, '__len__') else '未知'}")
        
        # 将所有embedding转换为张量并堆叠
        embeddings_list = []
        for item in faqs_embeddings["train"]:
            # 确保embedding是浮点数列表
            if isinstance(item["embedding"], list):
                embeddings_list.append(torch.tensor(item["embedding"], dtype=torch.float))
            else:
                # 如果不是列表，尝试转换
                try:
                    embeddings_list.append(torch.tensor(item["embedding"], dtype=torch.float))
                except Exception as e:
                    print(f"无法转换embedding: {e}")
                    # 使用零向量替代
                    if embeddings_list:
                        embeddings_list.append(torch.zeros_like(embeddings_list[0]))
                    else:
                        # 如果还没有任何向量，创建一个默认大小的零向量
                        embeddings_list.append(torch.zeros(384, dtype=torch.float))
        
        dataset_embeddings = torch.stack(embeddings_list)
    elif "text" in column_names:
        # 如果只有文本字段，需要先获取嵌入向量
        print("数据集只包含文本字段，需要生成嵌入向量...")
        # 为了演示，只处理前5个文本
        texts = [item["text"] for item in faqs_embeddings["train"][:5]]
        print(f"处理的文本示例: {texts[0][:50]}...")
        
        try:
            embeddings = query(texts)
            dataset_embeddings = torch.FloatTensor(embeddings)
        except Exception as e:
            print(f"获取嵌入向量时出错: {e}")
            # 创建一些随机嵌入向量用于演示
            print("使用随机嵌入向量进行演示...")
            dataset_embeddings = torch.randn(5, 384)  # 假设嵌入维度为384
    else:
        # 如果没有可识别的字段，使用默认方法
        print("使用默认方法处理数据集...")
        # 创建一些随机嵌入向量用于演示
        dataset_embeddings = torch.randn(len(faqs_embeddings["train"]), 384)  # 假设嵌入维度为384
    
    print(f"数据集加载完成，包含 {len(faqs_embeddings['train'])} 个FAQ条目")
    print(f"嵌入向量形状: {dataset_embeddings.shape}")
    return faqs_embeddings, dataset_embeddings

# 执行语义搜索并返回最相关的 FAQ
def find_similar_faqs(query_text: str, dataset_embeddings, faqs_dataset, top_k: int = 5):
    """查找与查询最相似的 FAQ"""
    print(f"\n查询: '{query_text}'")
    print("正在获取查询的嵌入向量...")
    try:
        # 获取查询的嵌入向量
        query_output = query([query_text])
        query_embeddings = torch.FloatTensor(query_output)
        
        print("正在执行语义搜索...")
        # 执行语义搜索
        hits = semantic_search(query_embeddings, dataset_embeddings, top_k=min(top_k, len(dataset_embeddings)))
        
        # 获取最相似的 FAQ
        similar_faqs = []
        for i in range(len(hits[0])):
            corpus_id = hits[0][i]['corpus_id']
            score = hits[0][i]['score']
            faq = faqs_dataset["train"][corpus_id]
            # print(f"找到相似FAQ: {faq}")
            # 检查FAQ是否包含text字段
            if "text" in faq:
                text = faq["text"]
            else:
                # 如果没有text字段，尝试使用第一个可用的字符串字段
                text = "未找到文本"
                for key, value in faq.items():
                    if isinstance(value, str) and len(value) > 0:
                        text = f"{key}: {value}"
                        break
            
            # 获取链接信息（如果存在）
            link = ""
            if "link" in faq:
                link = faq["link"]
            
            similar_faqs.append({
                "text": text,
                "score": score,
                "link": link  # 添加链接字段
            })
        
        return similar_faqs
    except Exception as e:
        print(f"执行语义搜索时出错: {e}")
        # 返回一个空列表作为后备
        return []

def main():
    """主函数"""
    print("Google Blog RSS FAQ 语义搜索演示")
    print("-" * 50)
    
    # 检查依赖包是否已安装
    if not DEPENDENCIES_INSTALLED:
        print("\n无法继续执行，请先安装所需的依赖包。")
        return
    
    try:
        # 加载数据集
        faqs_dataset, dataset_embeddings = load_faq_embeddings()
        
        # 示例查询 - 使用与Google Blog RSS相关的查询
        query_text = "Google I/O?"
        print(f"\n执行示例查询: '{query_text}'")
        similar_faqs = find_similar_faqs(query_text, dataset_embeddings, faqs_dataset)
        
        # 打印结果
        print("\n找到的最相似FAQ:")
        if similar_faqs:
            for i, faq in enumerate(similar_faqs):
                print(f"{i+1}. {faq['text']} {faq['link']} (相似度: {faq['score']:.4f})")
        else:
            print("未找到相关FAQ，请尝试其他查询。")
        
        # 交互式查询
        while True:
            print("\n" + "-" * 50)
            user_query = input("\n请输入您的Google Blog RSS相关问题 (输入'q'退出): ")
            if user_query.lower() == 'q':
                break
            
            similar_faqs = find_similar_faqs(user_query, dataset_embeddings, faqs_dataset)
            
            print("\n找到的最相似FAQ:")
            if similar_faqs:
                for i, faq in enumerate(similar_faqs):
                    link_info = f"链接: {faq['link']}" if faq['link'] else ""
                    print(f"{i+1}. {faq['text']} (相似度: {faq['score']:.4f}){' - ' + link_info if link_info else ''}")
            else:
                print("未找到相关FAQ，请尝试其他查询。")
    except Exception as e:
        print(f"\n运行过程中出现错误: {e}")
        print("请确保已安装所有必要的依赖包: torch, datasets, sentence-transformers, huggingface_hub")
        print("可以使用以下命令安装: pip install --user torch datasets sentence-transformers huggingface_hub")
        print("\n如果您使用的是虚拟环境，请先激活虚拟环境，然后运行:")
        print("pip install torch datasets sentence-transformers huggingface_hub")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n程序执行过程中出现未处理的错误: {e}")
        print("\n如果您遇到依赖包相关的问题，请安装所需的依赖包:")
        print("pip install --user torch datasets sentence-transformers huggingface_hub")
        print("\n如果您使用的是虚拟环境，请先激活虚拟环境，然后运行:")
        print("pip install torch datasets sentence-transformers huggingface_hub")