# Azure Cohere Implementation Guide

## Overview
This document explains the correct implementation for using **Azure-hosted Cohere models** (deployed via Azure AI Model-as-a-Service) instead of the direct Cohere API.

## The Problem
The original implementation used the `cohere` Python SDK, which is designed for **direct Cohere API access**, not for Azure-hosted models. When you deploy Cohere models through Azure AI Foundry, they are accessed differently.

### Incorrect Implementation (Before)
```python
import cohere

client = cohere.Client(
    api_key=Config.COHERE_EMBED_API_KEY,
    api_url=Config.COHERE_EMBED_ENDPOINT  # This parameter doesn't work for Azure
)
```

**Problems:**
- The `cohere` SDK doesn't support Azure endpoints properly
- Even with `api_url` parameter, it's designed for Cohere's native API format
- Azure-hosted models use Azure AI Inference API format, not Cohere's format

## The Solution

### For Embeddings: Use Azure AI Inference SDK

#### Correct Implementation (After)
```python
from azure.ai.inference import EmbeddingsClient
from azure.ai.inference.models import EmbeddingInput, EmbeddingInputType
from azure.core.credentials import AzureKeyCredential

client = EmbeddingsClient(
    endpoint=Config.COHERE_EMBED_ENDPOINT,
    credential=AzureKeyCredential(Config.COHERE_EMBED_API_KEY)
)

# Generate embeddings
response = client.embed(
    input=texts,  # Use 'input' not 'texts'
    model=model_name,
    input_type=EmbeddingInputType.DOCUMENT  # or EmbeddingInputType.QUERY
)

# Extract embeddings
embeddings = [item.embedding for item in response.data]
```

#### Key Differences:
| Aspect | Cohere SDK | Azure AI Inference SDK |
|--------|-----------|----------------------|
| **Client Class** | `cohere.Client` | `EmbeddingsClient` |
| **Authentication** | `api_key` param | `AzureKeyCredential` |
| **Input Parameter** | `texts` | `input` |
| **Input Type** | `"search_document"` (string) | `EmbeddingInputType.DOCUMENT` (enum) |
| **Response Format** | `response.embeddings` (list) | `response.data` (list of objects) |
| **Embedding Access** | Direct list | `item.embedding` for each item |

### For Reranking: Use REST API

Azure AI Inference SDK doesn't have a dedicated reranking client, so we use direct REST API calls.

#### Correct Implementation (After)
```python
import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": model_name,
    "query": query,
    "documents": documents,
    "top_n": top_n,
    "return_documents": True
}

response = requests.post(
    f"{endpoint}/rerank",
    headers=headers,
    json=payload,
    timeout=30
)

data = response.json()
results = data.get('results', [])
```

## Environment Configuration

Your `.env` file should have:

```env
# Azure OpenAI (for GPT-4)
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com

# Azure Cohere Embeddings (deployed via Azure AI)
COHERE_EMBED_ENDPOINT=https://your-cohere-embed-endpoint.inference.ml.azure.com
COHERE_EMBED_API_KEY=your-cohere-embed-key
COHERE_EMBED_MODEL=Cohere-embed-v3-english

# Azure Cohere Reranker (deployed via Azure AI)
COHERE_RERANK_ENDPOINT=https://your-cohere-rerank-endpoint.inference.ml.azure.com
COHERE_RERANK_API_KEY=your-cohere-rerank-key
COHERE_RERANK_MODEL=Rerank-v3-5
```

## Updated Dependencies

### Before (requirements.txt)
```txt
cohere==4.37
```

### After (requirements.txt)
```txt
azure-ai-inference>=1.0.0
azure-core>=1.29.0
requests==2.31.0  # For reranking REST API
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│     Your Application                    │
│  (app/services/cohere_service.py)      │
└────────────┬────────────────────────────┘
             │
             │ Uses Azure AI Inference SDK
             ▼
┌─────────────────────────────────────────┐
│   Azure AI Inference Endpoint           │
│  (*.inference.ml.azure.com)            │
└────────────┬────────────────────────────┘
             │
             │ Routes to deployed models
             ▼
┌─────────────────────────────────────────┐
│   Cohere Models (Azure-hosted)          │
│   - embed-v3-english (embeddings)       │
│   - Rerank-v3-5 (reranking)            │
└─────────────────────────────────────────┘
```

## Why This Matters

1. **API Compatibility**: Azure-hosted models use Azure's API format, not Cohere's native format
2. **Authentication**: Azure uses Azure Key Credentials, not Cohere API keys directly
3. **Endpoint Structure**: Azure inference endpoints have different URL patterns and request/response formats
4. **Feature Support**: Some Cohere SDK features may not be available or work differently on Azure

## Testing the Implementation

### Test Embeddings
```python
from app.services.cohere_service import CohereEmbeddingService

service = CohereEmbeddingService()
embeddings = service.generate_embeddings(
    texts=["Hello world", "Azure AI is great"],
    input_type="search_document"
)
print(f"Generated {len(embeddings)} embeddings")
print(f"Embedding dimension: {len(embeddings[0])}")
```

### Test Reranking
```python
from app.services.cohere_service import CohereRerankService

service = CohereRerankService()
results = service.rerank(
    query="What is machine learning?",
    documents=[
        "ML is a subset of AI",
        "Python is a programming language",
        "Deep learning uses neural networks"
    ],
    top_n=2
)
print(f"Top result: {results[0]['text']} (score: {results[0]['relevance_score']})")
```

## Migration Checklist

- [x] Replace `cohere` SDK with `azure-ai-inference`
- [x] Update `CohereEmbeddingService` to use `EmbeddingsClient`
- [x] Update `CohereRerankService` to use REST API
- [x] Update `requirements.txt` with new dependencies
- [x] Install new packages: `pip install azure-ai-inference azure-core`
- [ ] Test embedding generation with sample texts
- [ ] Test reranking with sample queries and documents
- [ ] Verify environment variables are correctly configured
- [ ] Update any other code that imports or uses these services

## References

- [Azure AI Inference Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/how-to/use-embeddings)
- [Azure AI Model Inference API](https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/reference/reference-model-inference-api)
- [Cohere Models on Azure](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/endpoints)

## Summary

**Key Takeaway**: When using Cohere models deployed through Azure AI Foundry, you must use Azure's AI Inference SDK and REST APIs, NOT the native Cohere Python SDK. The models are accessed through Azure's infrastructure with Azure's API format and authentication.
