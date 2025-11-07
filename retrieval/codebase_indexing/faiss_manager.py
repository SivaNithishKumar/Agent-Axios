"""
FAISS Manager Module

Manages local FAISS database for storing and retrieving code embeddings.
Supports overwriting existing data.
"""

import os
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss

logger = logging.getLogger(__name__)


class FAISSManager:
    """Manages FAISS vector database for code embeddings"""

    def __init__(
        self,
        db_path: str = "codebase_faiss_db",
        dimension: int = 768,
        index_type: str = "flat",
    ):
        """
        Initialize FAISS manager

        Args:
            db_path: Directory to store FAISS database files
            dimension: Embedding dimension (768 for most models, 3072 for Gemini)
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')
        """
        self.db_path = db_path
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.metadata = []  # Store file metadata

        # File paths
        self.index_file = os.path.join(db_path, "faiss.index")
        self.metadata_file = os.path.join(db_path, "metadata.pkl")

        # Ensure directory exists
        os.makedirs(db_path, exist_ok=True)

    def create_index(self, overwrite: bool = True) -> bool:
        """
        Create a new FAISS index

        Args:
            overwrite: If True, overwrite existing index

        Returns:
            True if successful
        """
        try:
            if not overwrite and os.path.exists(self.index_file):
                logger.info("Index already exists. Use overwrite=True to replace it.")
                return False

            # Create index based on type
            if self.index_type == "flat":
                # Flat index (exact search, no training needed)
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info(f"Created Flat L2 index with dimension {self.dimension}")

            elif self.index_type == "ivf":
                # IVF index (faster but approximate search)
                nlist = 100  # Number of clusters
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                logger.info(f"Created IVF index with dimension {self.dimension}")

            elif self.index_type == "hnsw":
                # HNSW index (fast and accurate)
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                logger.info(f"Created HNSW index with dimension {self.dimension}")

            else:
                logger.error(f"Unsupported index type: {self.index_type}")
                return False

            # Clear metadata
            self.metadata = []

            logger.info("FAISS index created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False

    def add_embeddings(
        self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]
    ) -> bool:
        """
        Add embeddings to the index

        Args:
            embeddings: Numpy array of embeddings (N x dimension)
            metadata: List of metadata dictionaries for each embedding

        Returns:
            True if successful
        """
        try:
            if self.index is None:
                logger.error("Index not initialized. Call create_index() first.")
                return False

            if len(embeddings) != len(metadata):
                logger.error("Number of embeddings and metadata items must match")
                return False

            # Ensure embeddings are in correct format
            embeddings = embeddings.astype("float32")

            # Normalize embeddings for cosine similarity (optional)
            # faiss.normalize_L2(embeddings)

            # Train index if needed (for IVF)
            if self.index_type == "ivf" and not self.index.is_trained:
                logger.info("Training IVF index...")
                self.index.train(embeddings)
                logger.info("Training completed")

            # Add embeddings
            start_id = self.index.ntotal
            self.index.add(embeddings)

            # Store metadata
            self.metadata.extend(metadata)

            logger.info(
                f"Added {len(embeddings)} embeddings to index. Total: {self.index.ntotal}"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding embeddings: {str(e)}")
            return False

    def search(
        self, query_embedding: np.ndarray, k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return

        Returns:
            List of results with metadata and distances
        """
        try:
            if self.index is None:
                logger.error("Index not initialized. Load or create an index first.")
                return []

            if self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []

            # Ensure query is in correct format
            query_embedding = query_embedding.astype("float32")
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Normalize if needed
            # faiss.normalize_L2(query_embedding)

            # Search
            k = min(k, self.index.ntotal)  # Don't search for more than available
            distances, indices = self.index.search(query_embedding, k)

            # Prepare results
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    result = {
                        "rank": i + 1,
                        "distance": float(dist),
                        "similarity": float(
                            1 / (1 + dist)
                        ),  # Convert distance to similarity
                        **self.metadata[idx],
                    }
                    results.append(result)

            logger.info(f"Found {len(results)} results for query")
            return results

        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []

    def save(self) -> bool:
        """
        Save index and metadata to disk

        Returns:
            True if successful
        """
        try:
            if self.index is None:
                logger.error("No index to save")
                return False

            # Save FAISS index
            faiss.write_index(self.index, self.index_file)
            logger.info(f"Saved FAISS index to {self.index_file}")

            # Save metadata
            with open(self.metadata_file, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Saved metadata to {self.metadata_file}")

            return True

        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False

    def load(self) -> bool:
        """
        Load index and metadata from disk

        Returns:
            True if successful
        """
        try:
            if not os.path.exists(self.index_file):
                logger.error(f"Index file not found: {self.index_file}")
                return False

            if not os.path.exists(self.metadata_file):
                logger.error(f"Metadata file not found: {self.metadata_file}")
                return False

            # Load FAISS index
            self.index = faiss.read_index(self.index_file)
            logger.info(
                f"Loaded FAISS index from {self.index_file} ({self.index.ntotal} vectors)"
            )

            # Load metadata
            with open(self.metadata_file, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded {len(self.metadata)} metadata entries")

            return True

        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index

        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {
                "initialized": False,
                "total_vectors": 0,
                "dimension": self.dimension,
            }

        return {
            "initialized": True,
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metadata_count": len(self.metadata),
            "db_path": self.db_path,
            "is_trained": (
                self.index.is_trained if hasattr(self.index, "is_trained") else True
            ),
        }

    def clear(self) -> bool:
        """
        Clear the index and metadata

        Returns:
            True if successful
        """
        try:
            # Remove files if they exist
            if os.path.exists(self.index_file):
                os.remove(self.index_file)
                logger.info(f"Removed index file: {self.index_file}")

            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
                logger.info(f"Removed metadata file: {self.metadata_file}")

            # Reset index and metadata
            self.index = None
            self.metadata = []

            logger.info("Cleared FAISS database")
            return True

        except Exception as e:
            logger.error(f"Error clearing index: {str(e)}")
            return False

    def __len__(self) -> int:
        """Return number of vectors in the index"""
        if self.index is None:
            return 0
        return self.index.ntotal
