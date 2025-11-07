"""
Query processor for generating embeddings from text queries using Google Gemini
"""

import logging
import time
import random
from typing import List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process text queries and generate embeddings using Gemini"""

    def __init__(self, api_keys: List[str], model_name: str = "models/embedding-001"):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.model_name = model_name
        self.max_retries = 3
        self.retry_delay = 2

        # Configure initial API key
        if self.api_keys:
            genai.configure(api_key=self.api_keys[0])
        else:
            raise ValueError("No Gemini API keys provided")

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

        # Add context for CVE-related queries if not already present
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
                logger.info(f"Successfully generated embedding (dimension: {len(embedding)})")
                return embedding

            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {str(e)}")

                # Try rotating API key on failure
                if attempt < self.max_retries - 1:
                    self._rotate_api_key()
                    time.sleep(self.retry_delay + random.uniform(0, 1))
                else:
                    logger.error(f"Failed to generate embedding after {self.max_retries} attempts")

        return None

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 50) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch

        Returns:
            List of embeddings (some may be None if failed)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            batch_embeddings = []
            for text in batch:
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)
                time.sleep(0.1)  # Small delay to avoid rate limiting

            embeddings.extend(batch_embeddings)

        logger.info(f"Generated {sum(1 for e in embeddings if e is not None)} embeddings out of {len(texts)} texts")
        return embeddings
