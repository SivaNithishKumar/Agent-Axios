"""Embedding generation service - creates embeddings for code chunks."""
from typing import List, Callable, Optional
import numpy as np
from langsmith import traceable
from app.models import CodeChunk, db
from app.services.cohere_service import CohereEmbeddingService
from app.services.faiss_manager import CodebaseIndexManager
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Handles embedding generation and storage."""
    
    BATCH_SIZE = 10  # Process 10 chunks at a time
    
    def __init__(self):
        self.cohere_service = CohereEmbeddingService()
        self.faiss_manager = CodebaseIndexManager()
    
    @traceable(name="embed_all_chunks", run_type="tool")
    def embed_chunks(
        self,
        chunks: List[CodeChunk],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Generate embeddings for all chunks and store in FAISS.
        
        Args:
            chunks: List of CodeChunk objects
            progress_callback: Optional progress callback (current, total)
        """
        total = len(chunks)
        logger.info(f"Generating embeddings for {total} chunks")

        if total == 0:
            logger.info("No chunks found for embedding stage, skipping")
            return
        
        # Process in batches
        for i in range(0, total, self.BATCH_SIZE):
            batch = chunks[i:i + self.BATCH_SIZE]
            
            try:
                # Prepare texts for embedding
                texts = []
                for chunk in batch:
                    # Include file path and code for better context
                    text = f"File: {chunk.file_path}\nLines {chunk.line_start}-{chunk.line_end}\n\n{chunk.chunk_text}"
                    texts.append(text)
                
                # Generate embeddings
                embeddings = self.cohere_service.generate_embeddings(texts)
                
                # Add to FAISS index
                embedding_array = np.array(embeddings, dtype='float32')
                metadata = [
                    {
                        'chunk_id': chunk.chunk_id,
                        'analysis_id': chunk.analysis_id,
                        'file_path': chunk.file_path,
                        'line_start': chunk.line_start,
                        'line_end': chunk.line_end,
                        'language': chunk.language
                    }
                    for chunk in batch
                ]
                vector_ids = self.faiss_manager.add_vectors(embedding_array, metadata)
                
                # Update chunks with embedding_id
                for chunk, vector_id in zip(batch, vector_ids):
                    chunk.embedding_id = vector_id
                
                db.session.flush()
                
                # Report progress
                processed = min(i + self.BATCH_SIZE, total)
                if progress_callback:
                    progress_callback(processed, total)
                
                logger.info(f"Embedded batch {i // self.BATCH_SIZE + 1}: {processed}/{total} chunks")
                
            except Exception as e:
                logger.error(f"Failed to embed batch {i // self.BATCH_SIZE + 1}: {str(e)}")
                # Continue with next batch instead of failing completely
                continue
        
        # Save FAISS index to disk
        self.faiss_manager.save_index()
        logger.info(f"Successfully embedded {total} chunks and saved FAISS index")
