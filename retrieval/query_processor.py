"""
Query processor for generating embeddings from text queries
"""

import logging
import os
import sys
import time
import random
from typing import List, Optional
import google.generativeai as genai

# Handle imports for both direct execution and module import
try:
    from .config import GEMINI_API_KEYS, EMBEDDING_CONFIG, LOGGING_CONFIG
except ImportError:
    # Direct execution - add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import GEMINI_API_KEYS, EMBEDDING_CONFIG, LOGGING_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]), format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process text queries and generate embeddings"""

    def __init__(self):
        self.api_keys = GEMINI_API_KEYS
        self.current_key_index = 0
        self.model_name = EMBEDDING_CONFIG["model_name"]
        self.max_retries = EMBEDDING_CONFIG["max_retries"]
        self.retry_delay = EMBEDDING_CONFIG["retry_delay"]

        # Configure initial API key
        if self.api_keys:
            genai.configure(api_key=self.api_keys[0])
        else:
            raise ValueError("No Gemini API keys provided in configuration")

    def _rotate_api_key(self):
        """Rotate to the next API key"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            genai.configure(api_key=self.api_keys[self.current_key_index])
            logger.info(f"Rotated to API key index: {self.current_key_index}")

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess the input query for better embedding generation

        Args:
            query: Raw text query

        Returns:
            Preprocessed query string
        """
        # Basic preprocessing
        processed_query = query.strip()

        # Add context for CVE-related queries
        if not any(
            keyword in processed_query.lower()
            for keyword in ["cve", "vulnerability", "security", "exploit", "attack"]
        ):
            processed_query = f"cybersecurity vulnerability: {processed_query}"

        return processed_query

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text query

        Args:
            text: Input text to embed

        Returns:
            Embedding vector or None if failed
        """
        processed_text = self.preprocess_query(text)

        for attempt in range(self.max_retries):
            try:
                # Generate embedding using Gemini
                response = genai.embed_content(
                    model=self.model_name,
                    content=processed_text,
                    task_type="retrieval_query",
                )

                embedding = response["embedding"]
                logger.info(
                    f"Successfully generated embedding (dimension: {len(embedding)})"
                )
                return embedding

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                # Try rotating API key on failure
                if attempt < self.max_retries - 1:
                    self._rotate_api_key()
                    time.sleep(self.retry_delay + random.uniform(0, 1))
                else:
                    logger.error(
                        f"Failed to generate embedding after {self.max_retries} attempts"
                    )

        return None

    def generate_embeddings_batch(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embeddings (some may be None if failed)
        """
        embeddings = []
        batch_size = EMBEDDING_CONFIG["batch_size"]

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
            )

            batch_embeddings = []
            for text in batch:
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)

                # Add small delay between requests to avoid rate limiting
                time.sleep(0.1)

            embeddings.extend(batch_embeddings)

        logger.info(
            f"Generated {sum(1 for e in embeddings if e is not None)} embeddings out of {len(texts)} texts"
        )
        return embeddings

    def expand_query(self, query: str) -> List[str]:
        """
        Expand a query with related terms for better retrieval

        Args:
            query: Original query

        Returns:
            List of expanded query variations
        """
        expanded_queries = [query]

        # Add technical variations
        query_lower = query.lower()

        # Security-related expansions
        security_terms = {
            "buffer overflow": ["buffer overrun", "stack overflow", "heap overflow"],
            "sql injection": ["sqli", "database injection", "sql attack"],
            "xss": ["cross-site scripting", "script injection"],
            "csrf": ["cross-site request forgery", "session riding"],
            "rce": ["remote code execution", "code injection"],
            "privilege escalation": ["privilege elevation", "permission bypass"],
        }

        for term, variations in security_terms.items():
            if term in query_lower:
                for variation in variations:
                    expanded_queries.append(query.replace(term, variation))

        # Add generic security context
        if len(expanded_queries) == 1:  # No specific expansions found
            expanded_queries.append(f"security vulnerability {query}")
            expanded_queries.append(f"{query} exploit")

        return expanded_queries[:3]  # Limit to 3 variations to avoid too many requests

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate if an embedding is properly formatted

        Args:
            embedding: Embedding vector to validate

        Returns:
            True if valid, False otherwise
        """
        if not embedding:
            return False

        if len(embedding) != EMBEDDING_CONFIG["dimension"]:
            logger.warning(
                f"Embedding dimension mismatch: expected {EMBEDDING_CONFIG['dimension']}, got {len(embedding)}"
            )
            return False

        # Check for valid float values
        try:
            for value in embedding:
                if not isinstance(value, (int, float)) or not (-1 <= value <= 1):
                    return False
        except (TypeError, ValueError):
            return False

        return True
