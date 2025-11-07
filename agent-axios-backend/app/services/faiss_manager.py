"""FAISS index manager with LangSmith tracking."""
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Sequence, Union
from config.settings import Config
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

class FAISSIndexManager:
    """Base FAISS index manager."""
    
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = f"{index_path}.metadata"
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.load_index()
        logger.info(f"Initialized FAISS index at {index_path} with {self.index.ntotal} vectors")
    
    @traceable(name="faiss_add_vectors", run_type="embedding")
    def add_vectors(self, vectors: Union[np.ndarray, Sequence[Sequence[float]]], metadata: List[Dict]) -> List[int]:
        """
        Add vectors to FAISS index.
        
        Args:
            vectors: numpy array or sequence of shape (n, dimension)
            metadata: List of metadata dicts for each vector
            
        Returns:
            List of FAISS vector IDs
        """
        if not metadata:
            raise ValueError("Metadata list cannot be empty when adding vectors")

        vector_array = np.array(vectors, dtype='float32')

        if vector_array.ndim != 2 or vector_array.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch: expected (?, {self.dimension}), got {vector_array.shape}"
            )

        if len(metadata) != len(vector_array):
            raise ValueError(
                f"Metadata length mismatch: {len(metadata)} metadata entries for {len(vector_array)} vectors"
            )
        
        start_id = self.index.ntotal
        self.index.add(vector_array)
        
        # Store metadata with FAISS vector IDs
        vector_ids = list(range(start_id, start_id + len(vectors)))
        for vid, meta in zip(vector_ids, metadata):
            self.metadata.append({'faiss_id': vid, **meta})
        
        logger.info(f"Added {len(vectors)} vectors to index (total: {self.index.ntotal})")
        
        # Auto-save every 100 additions
        if len(self.metadata) % 100 == 0:
            self.save_index()
        
        return vector_ids
    
    @traceable(name="faiss_search_vectors", run_type="retriever")
    def search(self, query_vector: Union[np.ndarray, Sequence[float]], top_k: int = 50) -> List[Dict]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector of shape (dimension,)
            top_k: Number of results to return
            
        Returns:
            List of results with metadata and distance
        """
        if self.index.ntotal == 0:
            logger.warning("Search called on empty index")
            return []
        
        query_array = np.array(query_vector, dtype='float32').reshape(1, -1)
        if query_array.shape[1] != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.dimension}, got {query_array.shape[1]}"
            )

        distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):  # Valid index
                results.append({
                    'faiss_id': int(idx),
                    'distance': float(dist),
                    **self.metadata[idx]
                })
        
        if results:
            logger.info(
                "Search returned %s results (best distance: %.4f)",
                len(results),
                results[0]['distance']
            )
        else:
            logger.info("Search returned no results")
        return results
    
    def save_index(self):
        """Persist index and metadata to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Saved index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
    
    def load_index(self):
        """Load existing index and metadata from disk."""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
            
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded {len(self.metadata)} metadata entries")
        except Exception as e:
            logger.warning(f"Failed to load index: {str(e)}, creating new index")


class CVEIndexManager(FAISSIndexManager):
    """FAISS index manager for CVE embeddings."""
    
    def __init__(self):
        super().__init__(Config.COHERE_EMBED_DIMENSIONS, Config.CVE_FAISS_INDEX_PATH)
        logger.info("CVE Index Manager initialized")


class CodebaseIndexManager(FAISSIndexManager):
    """FAISS index manager for codebase embeddings."""
    
    def __init__(self):
        super().__init__(Config.COHERE_EMBED_DIMENSIONS, Config.CODEBASE_FAISS_INDEX_PATH)
        logger.info("Codebase Index Manager initialized")
