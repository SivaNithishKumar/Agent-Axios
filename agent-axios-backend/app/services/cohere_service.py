"""Cohere service for embeddings and reranking with LangSmith tracking."""
import time
import cohere
import numpy as np
from typing import List, Dict
from config.settings import Config
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

class CohereEmbeddingService:
    """Service for generating embeddings using Azure Cohere."""
    
    def __init__(self):
        self.client = cohere.Client(
            api_key=Config.COHERE_EMBED_API_KEY,
            base_url=Config.COHERE_EMBED_ENDPOINT
        )
        self.model = Config.COHERE_EMBED_MODEL
        self.dimensions = Config.COHERE_EMBED_DIMENSIONS
        logger.info(f"Initialized Cohere Embedding Service: {self.model} ({self.dimensions}d)")
    
    @traceable(name="cohere_generate_embeddings", run_type="embedding")
    def generate_embeddings(
        self,
        texts: List[str],
        input_type: str = "search_document"
    ) -> List[List[float]]:
        """
        Generate embeddings with retry logic.
        
        Args:
            texts: List of texts to embed
            input_type: Type of input (search_document or search_query)
            
        Returns:
            List of embedding vectors
        """
        for attempt in range(3):
            try:
                start_time = time.time()
                
                response = self.client.embed(
                    texts=texts,
                    model=self.model,
                    input_type=input_type,
                    embedding_types=["float"],
                    truncate="END"
                )
                
                embeddings = response.embeddings
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
    """Service for reranking documents using Azure Cohere."""
    
    def __init__(self):
        self.client = cohere.Client(
            api_key=Config.COHERE_RERANK_API_KEY,
            base_url=Config.COHERE_RERANK_ENDPOINT
        )
        self.model = Config.COHERE_RERANK_MODEL
        logger.info(f"Initialized Cohere Rerank Service: {self.model}")
    
    @traceable(name="cohere_rerank_documents", run_type="retriever")
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10
    ) -> List[Dict]:
        """
        Rerank documents by relevance to query.
        
        Args:
            query: Search query
            documents: List of document texts to rerank
            top_n: Number of top results to return
            
        Returns:
            List of dicts with index, text, and relevance_score
        """
        try:
            start_time = time.time()
            
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=True
            )
            
            latency = time.time() - start_time
            
            results = [
                {
                    'index': result.index,
                    'text': result.document['text'] if isinstance(result.document, dict) else result.document,
                    'relevance_score': result.relevance_score
                }
                for result in response
            ]
            
            logger.info(
                f"Reranked {len(documents)} documents to top {len(results)} in {latency:.2f}s "
                f"(best score: {results[0]['relevance_score']:.3f})"
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
