"""
Milvus client for CVE retrieval microservice
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility

# Handle imports for both direct execution and module import
try:
    from .config import MILVUS_CONFIG, LOGGING_CONFIG
except ImportError:
    # Direct execution - add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import MILVUS_CONFIG, LOGGING_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]), format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)


class MilvusClient:
    """Milvus client for vector similarity search"""

    def __init__(self):
        self.collection_name = MILVUS_CONFIG["collection_name"]
        self.collection = None
        self._connection_established = False

    def connect(self) -> bool:
        """
        Establish connection to Milvus

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            connections.connect(
                alias="default",
                uri=MILVUS_CONFIG["endpoint"],
                token=MILVUS_CONFIG["token"],
            )
            self._connection_established = True
            logger.info("Successfully connected to Milvus")

            # Initialize collection
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Collection '{self.collection_name}' loaded successfully")
            else:
                logger.error(f"Collection '{self.collection_name}' does not exist")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            self._connection_established = False
            return False

    def disconnect(self):
        """Disconnect from Milvus"""
        try:
            connections.disconnect("default")
            self._connection_established = False
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error disconnecting from Milvus: {str(e)}")

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar CVE vectors

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score threshold
            output_fields: Fields to include in results

        Returns:
            List of similar CVE records with scores
        """
        if not self._connection_established or not self.collection:
            logger.error("Not connected to Milvus or collection not loaded")
            return []

        if output_fields is None:
            output_fields = ["cve_id", "summary", "cvss_score", "cvss_vector"]

        try:
            # Perform vector similarity search
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16},
            }  # Increased nprobe for better recall

            logger.info(
                f"Searching Milvus with limit={limit}, threshold={similarity_threshold}"
            )

            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=output_fields,
            )

            # Process results
            similar_cves = []
            total_hits = 0

            for hits in results:
                total_hits = len(hits)
                logger.info(f"Milvus returned {total_hits} raw hits")

                for i, hit in enumerate(hits):
                    logger.debug(f"Hit {i + 1}: ID={hit.id}, Score={hit.score:.4f}")

                    # Filter by similarity threshold
                    if hit.score >= similarity_threshold:
                        # Extract entity fields properly
                        cve_data = {
                            "id": hit.id,
                            "score": float(hit.score),
                        }
                        
                        # Add output fields from hit.entity
                        for field in output_fields:
                            if hasattr(hit.entity, field):
                                cve_data[field] = getattr(hit.entity, field)
                            elif isinstance(hit.entity, dict):
                                cve_data[field] = hit.entity.get(field, "")
                        
                        similar_cves.append(cve_data)
                    else:
                        logger.debug(
                            f"Filtered out hit with score {hit.score:.4f} (below threshold {similarity_threshold})"
                        )

            logger.info(
                f"Found {len(similar_cves)} CVEs above threshold {similarity_threshold} out of {total_hits} total hits"
            )
            return similar_cves

        except Exception as e:
            logger.error(f"Error searching Milvus: {str(e)}")
            return []

    def search_by_filters(
        self,
        filters: Dict[str, Any],
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search CVEs by attribute filters

        Args:
            filters: Dictionary of field filters
            limit: Maximum number of results
            output_fields: Fields to include in results

        Returns:
            List of matching CVE records
        """
        if not self._connection_established or not self.collection:
            logger.error("Not connected to Milvus or collection not loaded")
            return []

        if output_fields is None:
            output_fields = ["cve_id", "summary", "cvss_score", "cvss_vector"]

        try:
            # Build filter expression
            filter_expressions = []

            if "cve_id" in filters:
                filter_expressions.append(f'cve_id == "{filters["cve_id"]}"')

            if "min_cvss_score" in filters:
                filter_expressions.append(f"cvss_score >= {filters['min_cvss_score']}")

            if "max_cvss_score" in filters:
                filter_expressions.append(f"cvss_score <= {filters['max_cvss_score']}")

            # Combine filters with AND
            expression = " and ".join(filter_expressions) if filter_expressions else ""

            # Query collection
            results = self.collection.query(
                expr=expression, output_fields=output_fields, limit=limit
            )

            logger.info(f"Found {len(results)} CVEs matching filters")
            return results

        except Exception as e:
            logger.error(f"Error querying Milvus: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Dictionary with collection statistics
        """
        if not self._connection_established or not self.collection:
            return {"error": "Not connected to Milvus"}

        try:
            stats = {
                "collection_name": self.collection_name,
                "num_entities": self.collection.num_entities,
                "loaded": self.collection.has_index(),
            }

            # Get schema info
            schema_info = []
            for field in self.collection.schema.fields:
                field_info = {
                    "name": field.name,
                    "type": str(field.dtype),
                    "is_primary": field.is_primary,
                }
                if hasattr(field, "dim"):
                    field_info["dimension"] = field.dim
                schema_info.append(field_info)

            stats["schema"] = schema_info
            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
