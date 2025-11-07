"""
Codebase Indexing Module

This module provides functionality to:
- Scan and process codebase directories
- Chunk code files (each file is a chunk)
- Generate embeddings using Gemini API
- Store embeddings in local FAISS database
- Overwrite existing data on each run
"""

from .codebase_indexer import CodebaseIndexer
from .faiss_manager import FAISSManager
from .file_processor import FileProcessor

__all__ = ["CodebaseIndexer", "FAISSManager", "FileProcessor"]
