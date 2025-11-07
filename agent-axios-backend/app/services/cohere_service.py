"""Azure Cohere service for embeddings and reranking with LangSmith tracking."""
import time
import numpy as np
from typing import List, Dict
from config.settings import Config
from langsmith import traceable
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class CohereEmbeddingService:
    """Service for generating embeddings using Azure-hosted Cohere models via OpenAI SDK."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.COHERE_EMBED_ENDPOINT,
            api_key=Config.COHERE_EMBED_API_KEY
        )
        self.model = Config.COHERE_EMBED_MODEL
        self.dimensions = Config.COHERE_EMBED_DIMENSIONS
        logger.info(f"Initialized Azure Cohere Embedding Service: {self.model} ({self.dimensions}d)")
    
    @traceable(name="cohere_generate_embeddings", run_type="embedding")
    def generate_embeddings(
        self,
        texts: List[str],
        input_type: str = "search_document"
    ) -> List[List[float]]:
        """
        Generate embeddings with retry logic using OpenAI SDK for Azure-hosted Cohere.
        
        Args:
            texts: List of texts to embed
            input_type: Type of input (search_document or search_query) - not used with OpenAI SDK
            
        Returns:
            List of embedding vectors
        """
        for attempt in range(3):
            try:
                start_time = time.time()
                
                # Use OpenAI SDK for Azure-hosted Cohere embeddings
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model
                )
                
                # Extract embeddings from response
                embeddings = [item.embedding for item in response.data]
                latency = time.time() - start_time
                
                # Validate embeddings
                assert len(embeddings) == len(texts), "Embedding count mismatch"
                assert len(embeddings[0]) == self.dimensions, f"Dimension mismatch: {len(embeddings[0])} != {self.dimensions}"
                
                logger.info(
                    f"Generated {len(embeddings)} embeddings in {latency:.2f}s "
                    f"(avg {latency/len(embeddings)*1000:.1f}ms per text)"
                )
                
                return embeddings
                
            except Exception as e:
                logger.error(f"Embedding attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    raise Exception(f"Failed to generate embeddings after 3 attempts: {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return []


class CohereRerankService:
    """Service for reranking documents using Azure-hosted Cohere Rerank models via REST API."""
    
    def __init__(self):
        import requests
        self.requests = requests
        self.endpoint = Config.COHERE_RERANK_ENDPOINT
        self.api_key = Config.COHERE_RERANK_API_KEY
        self.model = Config.COHERE_RERANK_MODEL
        logger.info(f"Initialized Azure Cohere Rerank Service: {self.model}")
    
    @traceable(name="cohere_rerank_documents", run_type="retriever")
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10
    ) -> List[Dict]:
        """
        Rerank documents by relevance to query using Azure AI Inference REST API.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            top_n: Number of top results to return
            
        Returns:
            List of dicts with index, text, and relevance_score
        """
        try:
            start_time = time.time()
            
            # Azure AI Inference REST API for reranking
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
            
            # Parse response according to Cohere rerank API format
            results = []
            for result in data.get('results', []):
                results.append({
                    'index': result.get('index'),
                    'text': result.get('document', {}).get('text') if isinstance(result.get('document'), dict) else result.get('document'),
                    'relevance_score': result.get('relevance_score')
                })
            
            logger.info(
                f"Reranked {len(documents)} documents to top {len(results)} in {latency:.2f}s "
                f"(best score: {results[0]['relevance_score']:.3f})" if results else f"Reranked {len(documents)} documents in {latency:.2f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fallback: return original order with dummy scores
            return [
                {
                    'index': i,
                    'text': doc,
                    'relevance_score': 1.0 - (i * 0.1)
                }
                for i, doc in enumerate(documents[:top_n])
            ]
