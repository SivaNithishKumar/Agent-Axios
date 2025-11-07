"""
Milvus client for CVE retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility

logger = logging.getLogger(__name__)


class MilvusClient:
    """Milvus client for vector similarity search"""

    def __init__(self, config: Dict[str, Any]):
        self.collection_name = config["collection_name"]
        self.endpoint = config["endpoint"]
        self.token = config["token"]
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
                uri=self.endpoint,
                token=self.token,
            )
            self._connection_established = True
            logger.info("Successfully connected to Milvus")

            # Initialize collection
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Collection '{self.collection_name}' loaded successfully")
                return True
            else:
                logger.error(f"Collection '{self.collection_name}' does not exist")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            self._connection_established = False
            return False

    def disconnect(self):
        """Disconnect from Milvus"""
        try:
            if self._connection_established:
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
            }

            logger.info(f"Searching Milvus with limit={limit}, threshold={similarity_threshold}")

            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=output_fields,
            )

            # Process results
            similar_cves = []

            for hits in results:
                logger.info(f"Milvus returned {len(hits)} raw hits")

                for hit in hits:
                    # Filter by similarity threshold
                    if hit.score >= similarity_threshold:
                        # Extract entity fields
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

            logger.info(f"Found {len(similar_cves)} CVEs above threshold {similarity_threshold}")
            return similar_cves

        except Exception as e:
            logger.error(f"Error searching Milvus: {str(e)}")
            return []

    def get_by_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific CVE by ID

        Args:
            cve_id: CVE identifier

        Returns:
            CVE record or None if not found
        """
        if not self._connection_established or not self.collection:
            logger.error("Not connected to Milvus or collection not loaded")
            return None

        try:
            # Query by CVE ID
            expr = f'cve_id == "{cve_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
                limit=1,
            )

            if results:
                return results[0]
            else:
                logger.warning(f"CVE not found: {cve_id}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving CVE {cve_id}: {str(e)}")
            return None
