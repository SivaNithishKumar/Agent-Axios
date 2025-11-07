"""Test script for Azure Cohere service implementation."""
import os
import sys
import time
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import only what we need
from openai import OpenAI
from config.settings import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCohereEmbeddingService:
    """Standalone test for Azure Cohere embedding service using OpenAI SDK."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.COHERE_EMBED_ENDPOINT,
            api_key=Config.COHERE_EMBED_API_KEY
        )
        self.model = Config.COHERE_EMBED_MODEL
        self.dimensions = Config.COHERE_EMBED_DIMENSIONS
        logger.info(f"Initialized Azure Cohere Embedding Service: {self.model} ({self.dimensions}d)")
    
    def generate_embeddings(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Generate embeddings using OpenAI SDK."""
        start_time = time.time()
        
        # Use OpenAI SDK for Azure-hosted Cohere embeddings
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        latency = time.time() - start_time
        
        logger.info(f"Generated {len(embeddings)} embeddings in {latency:.2f}s")
        
        return embeddings


class TestCohereRerankService:
    """Standalone test for Azure Cohere reranking service."""
    
    def __init__(self):
        import requests
        self.requests = requests
        self.endpoint = Config.COHERE_RERANK_ENDPOINT
        self.api_key = Config.COHERE_RERANK_API_KEY
        self.model = Config.COHERE_RERANK_MODEL
        logger.info(f"Initialized Azure Cohere Rerank Service: {self.model}")
    
    def rerank(self, query: str, documents: List[str], top_n: int = 10) -> List[Dict]:
        """Rerank documents."""
        start_time = time.time()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": min(top_n, len(documents)),
            "return_documents": True
        }
        
        response = self.requests.post(
            self.endpoint,  # Don't append /rerank - endpoint already includes it
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        latency = time.time() - start_time
        
        results = []
        for result in data.get('results', []):
            results.append({
                'index': result.get('index'),
                'text': result.get('document', {}).get('text') if isinstance(result.get('document'), dict) else result.get('document'),
                'relevance_score': result.get('relevance_score')
            })
        
        logger.info(f"Reranked {len(documents)} documents to top {len(results)} in {latency:.2f}s")
        
        return results

def test_embeddings():
    """Test Azure Cohere embedding service."""
    print("\n" + "="*60)
    print("Testing Azure Cohere Embedding Service")
    print("="*60)
    
    try:
        service = TestCohereEmbeddingService()
        print(f"✓ Service initialized: {service.model}")
        
        # Test with sample texts
        texts = [
            "Azure AI provides powerful machine learning capabilities",
            "Python is a popular programming language for data science",
            "Cloud computing enables scalable applications"
        ]
        
        print(f"\nGenerating embeddings for {len(texts)} texts...")
        embeddings = service.generate_embeddings(
            texts=texts,
            input_type="search_document"
        )
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Embedding dimension: {len(embeddings[0])}")
        print(f"✓ Expected dimension: {service.dimensions}")
        
        assert len(embeddings) == len(texts), "Embedding count mismatch"
        assert len(embeddings[0]) == service.dimensions, "Dimension mismatch"
        
        print("\n✅ Embedding test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Embedding test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_reranking():
    """Test Azure Cohere reranking service."""
    print("\n" + "="*60)
    print("Testing Azure Cohere Reranking Service")
    print("="*60)
    
    try:
        service = TestCohereRerankService()
        print(f"✓ Service initialized: {service.model}")
        
        # Test with sample query and documents
        query = "What is artificial intelligence?"
        documents = [
            "Artificial intelligence is the simulation of human intelligence by machines",
            "Python is a programming language widely used in AI development",
            "Machine learning is a subset of AI that learns from data",
            "Cloud computing provides infrastructure for AI applications",
            "Neural networks are inspired by biological neural networks"
        ]
        
        print(f"\nReranking {len(documents)} documents for query: '{query}'")
        results = service.rerank(
            query=query,
            documents=documents,
            top_n=3
        )
        
        print(f"✓ Reranked to top {len(results)} results")
        print("\nTop results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['relevance_score']:.3f} - {result['text'][:60]}...")
        
        assert len(results) > 0, "No results returned"
        assert results[0]['relevance_score'] >= results[-1]['relevance_score'], "Results not sorted by relevance"
        
        print("\n✅ Reranking test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Reranking test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Azure Cohere Implementation Test Suite")
    print("="*60)
    print("\nNote: Ensure environment variables are set:")
    print("  - COHERE_EMBED_ENDPOINT")
    print("  - COHERE_EMBED_API_KEY")
    print("  - COHERE_RERANK_ENDPOINT")
    print("  - COHERE_RERANK_API_KEY")
    
    # Run tests
    embedding_passed = test_embeddings()
    reranking_passed = test_reranking()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Embedding Service: {'✅ PASSED' if embedding_passed else '❌ FAILED'}")
    print(f"Reranking Service: {'✅ PASSED' if reranking_passed else '❌ FAILED'}")
    
    if embedding_passed and reranking_passed:
        print("\n🎉 All tests passed! Implementation is correct.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check configuration and implementation.")
        sys.exit(1)
