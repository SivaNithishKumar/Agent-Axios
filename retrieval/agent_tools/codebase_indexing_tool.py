"""
Codebase Indexing Tool for AI Agents

This tool allows AI agents to index and search code repositories.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tools.base_tool import BaseTool, ToolDefinition, ToolParameter
from codebase_indexing.codebase_indexer import CodebaseIndexer
from config import CODEBASE_CONFIG

logger = logging.getLogger(__name__)


class CodebaseIndexingTool(BaseTool):
    """
    Tool for indexing and searching code repositories.

    This tool provides AI agents with the ability to:
    - Index entire codebases into searchable databases
    - Search code using natural language queries
    - Get statistics about indexed codebases
    - Manage multiple code databases
    """

    def __init__(self):
        super().__init__()
        self.indexers = {}  # Cache indexers by db_path

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for AI agents"""
        return ToolDefinition(
            name="codebase_indexing",
            description="Index and search code repositories using natural language. Use this tool to analyze codebases, find specific code patterns, or understand code structure.",
            category="code_analysis",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform",
                    required=True,
                    enum=["index", "search", "get_stats", "clear", "analyze_codebase", "auto_index"],
                ),
                ToolParameter(
                    name="codebase_path",
                    type="string",
                    description="Path to the codebase directory to index (required for index action)",
                    required=False,
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="Natural language search query (required for search action)",
                    required=False,
                ),
                ToolParameter(
                    name="db_path",
                    type="string",
                    description="Path to store/access FAISS database",
                    required=False,
                    default="codebase_faiss_db",
                ),
                ToolParameter(
                    name="index_type",
                    type="string",
                    description="Type of FAISS index to create",
                    required=False,
                    default="flat",
                    enum=["flat", "ivf", "hnsw"],
                ),
                ToolParameter(
                    name="batch_size",
                    type="integer",
                    description="Number of files to process in each batch",
                    required=False,
                    default=10,
                ),
                ToolParameter(
                    name="max_file_size_mb",
                    type="float",
                    description="Maximum file size in MB to process",
                    required=False,
                    default=5.0,
                ),
                ToolParameter(
                    name="overwrite",
                    type="boolean",
                    description="Overwrite existing database",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Number of search results to return",
                    required=False,
                    default=10,
                ),
            ],
            examples=[
                {
                    "description": "Index a codebase",
                    "parameters": {
                        "action": "index",
                        "codebase_path": "/path/to/repository",
                        "db_path": "my_codebase_db",
                        "overwrite": True,
                    },
                },
                {
                    "description": "Search for authentication code",
                    "parameters": {
                        "action": "search",
                        "query": "user authentication and login logic",
                        "db_path": "my_codebase_db",
                        "top_k": 5,
                    },
                },
                {
                    "description": "Get database statistics",
                    "parameters": {"action": "get_stats", "db_path": "my_codebase_db"},
                },
            ],
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the codebase indexing tool

        Args:
            action: Action to perform (index, search, get_stats)
            **kwargs: Action-specific parameters

        Returns:
            Dictionary with results
        """
        try:
            # Validate parameters
            validated = self.validate_parameters(kwargs)
            action = validated.get("action")

            # Route to appropriate action
            if action == "index":
                return self._index_codebase(validated)
            elif action == "search":
                return self._search_codebase(validated)
            elif action == "get_stats":
                return self._get_stats(validated)
            elif action == "clear":
                return self._clear_database(validated)
            elif action == "analyze_codebase":
                return self._analyze_codebase(validated)
            elif action == "auto_index":
                return self._auto_index(validated)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Error executing codebase indexing tool: {str(e)}")
            return {"error": str(e)}

    def _filter_indexer_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter parameters for indexer creation"""
        return {
            "index_type": params.get("index_type", "flat"),
            "max_file_size_mb": params.get("max_file_size_mb", 5.0),
        }

    def _get_or_create_indexer(self, db_path: str, index_type: str = "flat", max_file_size_mb: float = 5.0) -> CodebaseIndexer:
        """Get or create an indexer for the given database path"""
        if db_path not in self.indexers:
            self.indexers[db_path] = CodebaseIndexer(
                db_path=db_path,
                index_type=index_type,
                max_file_size_mb=max_file_size_mb,
            )
        return self.indexers[db_path]

    def _index_codebase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index a codebase"""
        codebase_path = params.get("codebase_path")
        if not codebase_path:
            return {
                "error": "codebase_path parameter is required for index action"
            }

        # Validate path
        if not os.path.exists(codebase_path):
            return {"error": f"Codebase path does not exist: {codebase_path}"}

        if not os.path.isdir(codebase_path):
            return {"error": f"Codebase path is not a directory: {codebase_path}"}

        db_path = params.get("db_path", "codebase_faiss_db")

        logger.info(f"Starting codebase indexing: {codebase_path} -> {db_path}")

        # Create indexer
        indexer_params = self._filter_indexer_params(params)
        indexer = self._get_or_create_indexer(db_path, **indexer_params)

        # Index codebase
        result = indexer.index_codebase(
            codebase_path=codebase_path,
            overwrite=params.get("overwrite", True),
            batch_size=params.get("batch_size", 10),
        )

        return {
            "tool": "codebase_indexing",
            "action": "index",
            "success": result.get("success", False),
            "data": result,
        }

    def _search_codebase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search the codebase"""
        query = params.get("query")
        if not query:
            return {"error": "query parameter is required for search action"}

        db_path = params.get("db_path", "codebase_faiss_db")

        # Check if database exists
        index_file = os.path.join(db_path, "faiss.index")
        if not os.path.exists(index_file):
            return {
                "error": f"Database not found at {db_path}. Please index your codebase first."
            }

        logger.info(f"Searching codebase: '{query}' in {db_path}")

        # Create indexer
        indexer_params = self._filter_indexer_params(params)
        indexer = self._get_or_create_indexer(db_path, **indexer_params)

        # Search
        results = indexer.search_codebase(
            query=query, k=params.get("top_k", 10)
        )

        if results is None:
            return {"error": "Search failed"}

        return {
            "tool": "codebase_indexing",
            "action": "search",
            "success": True,
            "data": {
                "query": query,
                "database": db_path,
                "total_results": len(results),
                "results": results,
            },
        }

    def _get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get database statistics"""
        db_path = params.get("db_path", "codebase_faiss_db")

        # Check if database exists
        index_file = os.path.join(db_path, "faiss.index")
        if not os.path.exists(index_file):
            return {
                "error": f"Database not found at {db_path}. Please index your codebase first."
            }

        logger.info(f"Getting stats for database: {db_path}")

        # Create indexer
        indexer_params = self._filter_indexer_params(params)
        indexer = self._get_or_create_indexer(db_path, **indexer_params)

        # Get stats
        stats = indexer.get_stats()

        return {
            "tool": "codebase_indexing",
            "action": "get_stats",
            "success": True,
            "data": stats,
        }

    def _clear_database(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear a database"""
        db_path = params.get("db_path", "codebase_faiss_db")

        logger.info(f"Clearing database: {db_path}")

        # Create indexer and clear
        indexer_params = self._filter_indexer_params(params)
        indexer = self._get_or_create_indexer(db_path, **indexer_params)
        success = indexer.faiss_manager.clear()

        # Remove from cache
        if db_path in self.indexers:
            del self.indexers[db_path]

        return {
            "tool": "codebase_indexing",
            "action": "clear",
            "success": success,
            "data": {"message": f"Database cleared: {db_path}"},
        }

    def _analyze_codebase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a codebase and search it with a query in one call
        
        Returns response in standardized format:
        {
            "success": true,
            "count": 5,
            "message": "Successfully found 5 code files",
            "results": [
                {
                    "file_path": "...",
                    "content": "...",
                    "similarity_score": 0.85,
                    "rank": 1
                }
            ]
        }
        """
        codebase_path = params.get("codebase_path")
        query = params.get("query")
        
        if not codebase_path:
            return {
                "success": False,
                "count": 0,
                "message": "codebase_path parameter is required",
                "results": []
            }
        
        if not query:
            return {
                "success": False,
                "count": 0,
                "message": "query parameter is required",
                "results": []
            }
        
        # Validate path
        if not os.path.exists(codebase_path):
            return {
                "success": False,
                "count": 0,
                "message": f"Codebase path does not exist: {codebase_path}",
                "results": []
            }
        
        db_path = params.get("db_path", "codebase_faiss_db")
        top_k = params.get("top_k", 10)
        
        logger.info(f"Analyzing codebase: {codebase_path} with query: '{query}'")
        
        try:
            # Step 1: Index the codebase
            index_type = params.get("index_type", "flat")
            max_file_size_mb = params.get("max_file_size_mb", 5.0)
            
            indexer = CodebaseIndexer(
                db_path=db_path,
                index_type=index_type,
                max_file_size_mb=max_file_size_mb,
            )
            
            # Cache it
            self.indexers[db_path] = indexer
            
            index_result = indexer.index_codebase(
                codebase_path=codebase_path,
                overwrite=params.get("overwrite", True),
                batch_size=params.get("batch_size", 10),
            )
            
            if not index_result.get("success"):
                return {
                    "success": False,
                    "count": 0,
                    "message": f"Indexing failed: {index_result.get('error', 'Unknown error')}",
                    "results": []
                }
            
            logger.info(f"Indexed {index_result.get('total_files', 0)} files")
            
            # Step 2: Search the indexed codebase
            search_result = indexer.search(query=query, top_k=top_k)
            
            if not search_result.get("success"):
                return {
                    "success": False,
                    "count": 0,
                    "message": f"Search failed: {search_result.get('error', 'Unknown error')}",
                    "results": []
                }
            
            # Step 3: Format results in standardized format
            search_results = search_result.get("results", [])
            formatted_results = []
            
            for rank, result in enumerate(search_results, start=1):
                formatted_result = {
                    "file_path": result.get("file_path", ""),
                    "content": result.get("content", ""),
                    "similarity_score": result.get("score", 0.0),
                    "rank": rank
                }
                formatted_results.append(formatted_result)
            
            count = len(formatted_results)
            
            return {
                "success": True,
                "count": count,
                "message": f"Successfully found {count} code files",
                "indexing_stats": {
                    "total_files_indexed": index_result.get("total_files", 0),
                    "files_processed": index_result.get("files_processed", 0),
                    "database_path": db_path
                },
                "results": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing codebase: {str(e)}")
            return {
                "success": False,
                "count": 0,
                "message": f"Error: {str(e)}",
                "results": []
            }

    def _auto_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically index the codebase from .env configuration
        Each file becomes one chunk in FAISS database
        
        Returns:
        {
            "success": true,
            "message": "Successfully indexed 150 files",
            "stats": {
                "total_files": 150,
                "codebase_path": "...",
                "database_path": "..."
            }
        }
        """
        # Get codebase path from .env config
        codebase_path = CODEBASE_CONFIG["codebase_path"]
        db_path = params.get("db_path") or CODEBASE_CONFIG["faiss_db_path"]
        
        logger.info(f"Auto-indexing codebase from .env: {codebase_path} -> {db_path}")
        
        # Validate path
        if not os.path.exists(codebase_path):
            return {
                "success": False,
                "message": f"Codebase path from .env does not exist: {codebase_path}",
                "stats": {}
            }
        
        try:
            # Create indexer
            index_type = params.get("index_type", "flat")
            max_file_size_mb = params.get("max_file_size_mb", 5.0)
            
            indexer = CodebaseIndexer(
                db_path=db_path,
                index_type=index_type,
                max_file_size_mb=max_file_size_mb,
            )
            
            # Cache it
            self.indexers[db_path] = indexer
            
            # Index codebase
            result = indexer.index_codebase(
                codebase_path=codebase_path,
                overwrite=params.get("overwrite", True),
                batch_size=params.get("batch_size", 10),
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "message": f"Indexing failed: {result.get('error', 'Unknown error')}",
                    "stats": {}
                }
            
            return {
                "success": True,
                "message": f"Successfully indexed {result.get('total_files', 0)} files from .env config",
                "stats": {
                    "total_files": result.get("total_files", 0),
                    "files_processed": result.get("files_processed", 0),
                    "codebase_path": codebase_path,
                    "database_path": db_path,
                    "time_taken": result.get("time_taken", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error auto-indexing codebase: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "stats": {}
            }

    def cleanup(self):
        """Cleanup resources"""
        self.indexers.clear()
        logger.info("Codebase Indexing Tool cleaned up")
