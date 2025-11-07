"""
File Processor Module

Handles reading and processing files from the codebase directory.
Each file becomes a chunk with metadata.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes files from a codebase directory"""

    # File extensions to process
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".m",
        ".mm",
        ".sql",
        ".sh",
        ".bash",
        ".ps1",
        ".yaml",
        ".yml",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".scss",
        ".sass",
        ".md",
        ".txt",
        ".rst",
        ".vue",
        ".svelte",
    }

    # Directories to skip
    SKIP_DIRS = {
        "__pycache__",
        "node_modules",
        ".git",
        ".svn",
        ".hg",
        "venv",
        "env",
        ".env",
        "virtualenv",
        ".venv",
        "dist",
        "build",
        "target",
        "out",
        "bin",
        "obj",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "coverage",
        ".coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        ".DS_Store",
    }

    def __init__(
        self,
        max_file_size_mb: float = 5.0,
        encoding: str = "utf-8",
        skip_binary: bool = True,
    ):
        """
        Initialize the file processor

        Args:
            max_file_size_mb: Maximum file size to process in MB
            encoding: Default encoding for text files
            skip_binary: Skip binary files
        """
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.encoding = encoding
        self.skip_binary = skip_binary

    def scan_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Scan directory and return list of file chunks

        Args:
            directory_path: Path to the codebase directory

        Returns:
            List of dictionaries with file content and metadata
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory does not exist: {directory_path}")
            return []

        if not os.path.isdir(directory_path):
            logger.error(f"Path is not a directory: {directory_path}")
            return []

        chunks = []
        base_path = Path(directory_path).resolve()

        logger.info(f"Scanning directory: {directory_path}")

        for root, dirs, files in os.walk(directory_path):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for file_name in files:
                file_path = os.path.join(root, file_name)
                chunk = self._process_file(file_path, base_path)

                if chunk:
                    chunks.append(chunk)

        logger.info(f"Processed {len(chunks)} files from {directory_path}")
        return chunks

    def _process_file(
        self, file_path: str, base_path: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single file and return chunk data

        Args:
            file_path: Path to the file
            base_path: Base directory path for relative path calculation

        Returns:
            Dictionary with file content and metadata, or None if file should be skipped
        """
        try:
            # Get file extension
            file_ext = Path(file_path).suffix.lower()

            # Check if extension is supported
            if file_ext not in self.SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipping unsupported file type: {file_path}")
                return None

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size_bytes:
                logger.warning(
                    f"Skipping large file ({file_size / 1024 / 1024:.2f} MB): {file_path}"
                )
                return None

            if file_size == 0:
                logger.debug(f"Skipping empty file: {file_path}")
                return None

            # Read file content
            try:
                with open(file_path, "r", encoding=self.encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                if self.skip_binary:
                    logger.debug(f"Skipping binary file: {file_path}")
                    return None
                else:
                    # Try with latin-1 encoding as fallback
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()

            # Calculate relative path
            relative_path = Path(file_path).relative_to(base_path)

            # Get file metadata
            stat = os.stat(file_path)

            # Create chunk
            chunk = {
                "file_path": str(relative_path),
                "absolute_path": file_path,
                "content": content,
                "file_name": Path(file_path).name,
                "file_extension": file_ext,
                "file_size": file_size,
                "line_count": content.count("\n") + 1,
                "char_count": len(content),
                "modified_time": stat.st_mtime,
            }

            logger.debug(
                f"Processed: {relative_path} ({file_size} bytes, {chunk['line_count']} lines)"
            )
            return chunk

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None

    def get_file_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics of processed files

        Args:
            chunks: List of file chunks

        Returns:
            Dictionary with summary statistics
        """
        if not chunks:
            return {
                "total_files": 0,
                "total_size": 0,
                "total_lines": 0,
                "file_types": {},
            }

        total_size = sum(chunk["file_size"] for chunk in chunks)
        total_lines = sum(chunk["line_count"] for chunk in chunks)

        # Count file types
        file_types = {}
        for chunk in chunks:
            ext = chunk["file_extension"]
            if ext not in file_types:
                file_types[ext] = 0
            file_types[ext] += 1

        return {
            "total_files": len(chunks),
            "total_size": total_size,
            "total_size_mb": total_size / 1024 / 1024,
            "total_lines": total_lines,
            "file_types": file_types,
            "average_file_size": total_size / len(chunks),
            "average_lines_per_file": total_lines / len(chunks),
        }
