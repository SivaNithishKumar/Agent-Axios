"""
Codebase Indexer

Main script to index a codebase into a local FAISS database.
Each file becomes a chunk with embeddings generated using Gemini API.
Overwrites existing database on each run.
"""

import os
import sys
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase_indexing.file_processor import FileProcessor
from codebase_indexing.faiss_manager import FAISSManager
from query_processor import QueryProcessor
from config import EMBEDDING_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CodebaseIndexer:
    """Index a codebase into FAISS database"""

    def __init__(
        self,
        db_path: str = "codebase_faiss_db",
        dimension: int = None,
        index_type: str = "flat",
        max_file_size_mb: float = 5.0,
    ):
        """
        Initialize the codebase indexer

        Args:
            db_path: Path to store FAISS database
            dimension: Embedding dimension (default from config)
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            max_file_size_mb: Maximum file size to process in MB
        """
        self.dimension = dimension or EMBEDDING_CONFIG["dimension"]
        self.db_path = db_path

        # Initialize components
        self.file_processor = FileProcessor(max_file_size_mb=max_file_size_mb)
        self.faiss_manager = FAISSManager(
            db_path=db_path, dimension=self.dimension, index_type=index_type
        )
        self.query_processor = QueryProcessor()

        logger.info(f"Initialized CodebaseIndexer with dimension {self.dimension}")

    def index_codebase(
        self, codebase_path: str, overwrite: bool = True, batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Index a codebase directory into FAISS database

        Args:
            codebase_path: Path to the codebase directory
            overwrite: If True, overwrite existing database
            batch_size: Number of files to process in each batch

        Returns:
            Dictionary with indexing results and statistics
        """
        start_time = time.time()

        try:
            # Step 1: Scan directory and extract file chunks
            logger.info(f"Scanning codebase directory: {codebase_path}")
            chunks = self.file_processor.scan_directory(codebase_path)

            if not chunks:
                logger.error("No files found to index")
                return {
                    "success": False,
                    "error": "No files found in the directory",
                    "total_files": 0,
                }

            logger.info(f"Found {len(chunks)} files to index")

            # Get file summary
            summary = self.file_processor.get_file_summary(chunks)
            logger.info(f"Codebase summary: {summary}")

            # Step 2: Create or clear FAISS index
            logger.info(f"Creating FAISS index (overwrite={overwrite})")
            if overwrite:
                self.faiss_manager.clear()

            success = self.faiss_manager.create_index(overwrite=True)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to create FAISS index",
                    "total_files": len(chunks),
                }

            # Step 3: Generate embeddings and add to index
            logger.info("Generating embeddings for code files...")
            successful_embeddings = 0
            failed_embeddings = 0

            # Process in batches
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(chunks) + batch_size - 1) // batch_size

                logger.info(
                    f"\n{'='*60}\nProcessing batch {batch_num}/{total_batches} "
                    f"({len(batch_chunks)} files)\n{'='*60}"
                )

                # Generate embeddings for batch
                batch_embeddings = []
                batch_metadata = []

                for chunk in batch_chunks:
                    # Create embedding text from file content and metadata
                    embedding_text = self._create_embedding_text(chunk)

                    logger.info(
                        f"Generating embedding for: {chunk['file_path']} "
                        f"({chunk['file_size']} bytes, {chunk['line_count']} lines)"
                    )

                    # Generate embedding
                    embedding = self.query_processor.generate_embedding(embedding_text)

                    if embedding:
                        batch_embeddings.append(embedding)
                        batch_metadata.append(
                            {
                                "file_path": chunk["file_path"],
                                "file_name": chunk["file_name"],
                                "file_extension": chunk["file_extension"],
                                "file_size": chunk["file_size"],
                                "line_count": chunk["line_count"],
                                "char_count": chunk["char_count"],
                                "content_preview": chunk["content"][
                                    :200
                                ],  # First 200 chars
                            }
                        )
                        successful_embeddings += 1
                        logger.info(f"✓ Successfully generated embedding")
                    else:
                        failed_embeddings += 1
                        logger.warning(
                            f"✗ Failed to generate embedding for {chunk['file_path']}"
                        )

                    # Small delay to avoid rate limiting
                    time.sleep(0.2)

                # Add batch to FAISS index
                if batch_embeddings:
                    embeddings_array = np.array(batch_embeddings, dtype=np.float32)
                    success = self.faiss_manager.add_embeddings(
                        embeddings_array, batch_metadata
                    )

                    if success:
                        logger.info(
                            f"✓ Added {len(batch_embeddings)} embeddings to FAISS index"
                        )
                    else:
                        logger.error(f"✗ Failed to add batch to FAISS index")

                logger.info(
                    f"Batch {batch_num} complete. "
                    f"Success: {successful_embeddings}, Failed: {failed_embeddings}"
                )

            # Step 4: Save FAISS index to disk
            logger.info("Saving FAISS index to disk...")
            save_success = self.faiss_manager.save()

            if not save_success:
                logger.error("Failed to save FAISS index")
                return {
                    "success": False,
                    "error": "Failed to save FAISS index",
                    "embeddings_generated": successful_embeddings,
                }

            # Step 5: Calculate statistics
            elapsed_time = time.time() - start_time
            stats = self.faiss_manager.get_stats()

            result = {
                "success": True,
                "codebase_path": codebase_path,
                "database_path": self.db_path,
                "file_summary": summary,
                "embedding_stats": {
                    "total_files": len(chunks),
                    "successful_embeddings": successful_embeddings,
                    "failed_embeddings": failed_embeddings,
                    "success_rate": (
                        successful_embeddings / len(chunks) * 100
                        if chunks
                        else 0
                    ),
                },
                "index_stats": stats,
                "processing_time": {
                    "total_seconds": elapsed_time,
                    "total_minutes": elapsed_time / 60,
                    "avg_time_per_file": elapsed_time / len(chunks) if chunks else 0,
                },
            }

            logger.info("\n" + "=" * 60)
            logger.info("INDEXING COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"Total files processed: {len(chunks)}")
            logger.info(f"Successful embeddings: {successful_embeddings}")
            logger.info(f"Failed embeddings: {failed_embeddings}")
            logger.info(f"Total time: {elapsed_time / 60:.2f} minutes")
            logger.info(f"Database saved to: {self.db_path}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    def _create_embedding_text(self, chunk: Dict[str, Any]) -> str:
        """
        Create text for embedding generation from file chunk

        Args:
            chunk: File chunk with content and metadata

        Returns:
            Text string optimized for embedding
        """
        # Include file path, extension, and content
        file_path = chunk["file_path"]
        file_ext = chunk["file_extension"]
        content = chunk["content"]

        # Truncate content if too long (to avoid API limits)
        max_content_length = 10000  # characters
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n... [truncated]"

        # Create structured text for embedding
        embedding_text = f"""File: {file_path}
Type: {file_ext}
Lines: {chunk['line_count']}

Content:
{content}
"""

        return embedding_text

    def search_codebase(
        self, query: str, k: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search the indexed codebase

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results with file information
        """
        try:
            # Load index if not already loaded
            if self.faiss_manager.index is None:
                logger.info("Loading FAISS index...")
                success = self.faiss_manager.load()
                if not success:
                    logger.error("Failed to load FAISS index")
                    return None

            # Generate query embedding
            logger.info(f"Searching for: {query}")
            query_embedding = self.query_processor.generate_embedding(query)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return None

            # Search FAISS index
            query_vector = np.array([query_embedding], dtype=np.float32)
            results = self.faiss_manager.search(query_vector[0], k=k)

            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error searching codebase: {str(e)}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the indexed codebase

        Returns:
            Dictionary with statistics
        """
        # Try to load index if not loaded
        if self.faiss_manager.index is None:
            self.faiss_manager.load()

        return self.faiss_manager.get_stats()


def main():
    """Main entry point for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Index a codebase into FAISS database"
    )
    parser.add_argument(
        "codebase_path", type=str, help="Path to the codebase directory to index"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="codebase_faiss_db",
        help="Path to store FAISS database (default: codebase_faiss_db)",
    )
    parser.add_argument(
        "--index-type",
        type=str,
        default="flat",
        choices=["flat", "ivf", "hnsw"],
        help="FAISS index type (default: flat)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing files (default: 10)",
    )
    parser.add_argument(
        "--max-file-size",
        type=float,
        default=5.0,
        help="Maximum file size in MB (default: 5.0)",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Don't overwrite existing database",
    )

    args = parser.parse_args()

    # Create indexer
    indexer = CodebaseIndexer(
        db_path=args.db_path,
        index_type=args.index_type,
        max_file_size_mb=args.max_file_size,
    )

    # Index codebase
    result = indexer.index_codebase(
        codebase_path=args.codebase_path,
        overwrite=not args.no_overwrite,
        batch_size=args.batch_size,
    )

    # Print result
    if result["success"]:
        print("\n✓ Indexing completed successfully!")
        print(f"  Database saved to: {args.db_path}")
        print(
            f"  Total files indexed: {result['embedding_stats']['successful_embeddings']}"
        )
        print(
            f"  Processing time: {result['processing_time']['total_minutes']:.2f} minutes"
        )
    else:
        print(f"\n✗ Indexing failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
