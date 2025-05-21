# Medicare FAQ 语义搜索系统

这个项目实现了一个基于语义搜索的系统，可以查找与用户查询最相似的Medicare FAQ。系统使用Hugging Face的Sentence Transformers模型将文本转换为嵌入向量，然后使用余弦相似度查找最相似的FAQ。

## 功能特点

- 使用Hugging Face API获取文本嵌入
- 加载预先嵌入的Medicare FAQ数据集
- 执行语义搜索找到最相似的FAQ
- 提供交互式查询界面
- 包含完整的单元测试

## 安装依赖

```bash
pip install requests datasets torch sentence-transformers huggingface_hub python-dotenv
```

## 环境配置

1. 复制`.env.example`文件并重命名为`.env`
2. 在`.env`文件中设置你的Hugging Face API Token：

```
HF_TOKEN=your_huggingface_token_here
```

> 注意：`.env`文件包含敏感信息，已被添加到`.gitignore`中，不会被提交到代码仓库。

## 使用方法

### 运行演示脚本

```bash
python semantic_search_demo.py
```

这将启动一个交互式会话，您可以输入Medicare相关问题，系统会返回最相似的FAQ。

### 运行测试

```bash
python test_query.py
```

## 文件说明

- `test_query.py`: 包含查询函数、语义搜索功能和单元测试
- `semantic_search_demo.py`: 交互式演示脚本
- `main.py`: RSS解析和数据集创建工具

## 技术细节

系统使用以下技术：

- **Sentence Transformers**: 用于生成文本嵌入
- **PyTorch**: 用于处理嵌入向量
- **Hugging Face Datasets**: 用于加载和处理数据集
- **语义搜索**: 使用余弦相似度查找最相似的文本

## 示例

```python
from test_query import load_faq_embeddings, find_similar_faqs

# 加载数据集
faqs_dataset, dataset_embeddings = load_faq_embeddings()

# 执行语义搜索
query_text = "How can Medicare help me?"
similar_faqs = find_similar_faqs(query_text, dataset_embeddings, faqs_dataset)

# 打印结果
for i, faq in enumerate(similar_faqs):
    print(f"{i+1}. {faq['text']} (Score: {faq['score']:.4f})")
```