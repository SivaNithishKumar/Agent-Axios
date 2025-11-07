"""
Main retrieval service for CVE similarity search
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

# Handle imports for both direct execution and module import
try:
    from .milvus_client import MilvusClient
    from .query_processor import QueryProcessor
    from .config import RETRIEVAL_CONFIG, LOGGING_CONFIG
except ImportError:
    # Direct execution - add current directory to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from milvus_client import MilvusClient
    from query_processor import QueryProcessor
    from config import RETRIEVAL_CONFIG, LOGGING_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]), format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(__name__)


class CVERetrievalService:
    """Main service for CVE retrieval and similarity search"""

    def __init__(self):
        self.milvus_client = MilvusClient()
        self.query_processor = QueryProcessor()
        self.default_limit = RETRIEVAL_CONFIG["default_limit"]
        self.max_limit = RETRIEVAL_CONFIG["max_limit"]
        self.similarity_threshold = RETRIEVAL_CONFIG["similarity_threshold"]

    def initialize(self) -> bool:
        """
        Initialize the retrieval service

        Returns:
            bool: True if initialization successful
        """
        try:
            success = self.milvus_client.connect()
            if success:
                logger.info("CVE Retrieval Service initialized successfully")
            else:
                logger.error("Failed to initialize CVE Retrieval Service")
            return success
        except Exception as e:
            logger.error(f"Error initializing service: {str(e)}")
            return False

    def search_by_text(
        self,
        query: str,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        include_scores: bool = True,
        expand_query: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for similar CVEs using text query

        Args:
            query: Text query describing the vulnerability
            limit: Maximum number of results (default from config)
            similarity_threshold: Minimum similarity score (default: 0.7)
            include_scores: Whether to include similarity scores
            expand_query: Whether to expand query with related terms

        Returns:
            Dictionary with search results and metadata
        """
        # Validate inputs
        if not query or not query.strip():
            return {"error": "Query cannot be empty", "results": []}

        limit = min(limit or self.default_limit, self.max_limit)
        similarity_threshold = similarity_threshold or self.similarity_threshold

        try:
            # Process queries
            queries_to_search = [query]
            if expand_query:
                queries_to_search = self.query_processor.expand_query(query)

            all_results = []
            seen_cve_ids = set()

            for search_query in queries_to_search:
                logger.info(f"Searching for: '{search_query}'")

                # Generate embedding
                embedding = self.query_processor.generate_embedding(search_query)
                if not embedding:
                    logger.warning(
                        f"Failed to generate embedding for query: {search_query}"
                    )
                    continue

                # Validate embedding
                if not self.query_processor.validate_embedding(embedding):
                    logger.warning(
                        f"Invalid embedding generated for query: {search_query}"
                    )
                    continue

                # Search similar vectors
                search_limit = max(
                    limit * 3, 50
                )  # Increased multiplier for better results
                results = self.milvus_client.search_similar(
                    query_vector=embedding,
                    limit=search_limit,
                    similarity_threshold=similarity_threshold,
                    output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
                )

                logger.info(
                    f"Milvus returned {len(results)} results for query: '{search_query}'"
                )

                # Deduplicate and add to results
                for result in results:
                    cve_id = result.get("cve_id")
                    if cve_id not in seen_cve_ids:
                        seen_cve_ids.add(cve_id)
                        if not include_scores:
                            result.pop("score", None)
                        all_results.append(result)
                        logger.debug(
                            f"Added CVE: {cve_id} with score: {result.get('score', 'N/A')}"
                        )

                logger.info(f"Total unique results so far: {len(all_results)}")

                # Continue searching all expanded queries to get maximum results
                # Don't break early unless we have significantly more than needed
                if len(all_results) >= limit * 2:
                    break

            # Sort by score if available and limit results
            if include_scores and all_results:
                all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

            final_results = all_results[:limit]

            return {
                "query": query,
                "results": final_results,
                "total_found": len(final_results),
                "similarity_threshold": similarity_threshold,
                "expanded_query": expand_query,
                "queries_searched": queries_to_search if expand_query else [query],
            }

        except Exception as e:
            logger.error(f"Error in text search: {str(e)}")
            return {"error": str(e), "results": []}

    def search_by_filters(
        self, filters: Dict[str, Any], limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search CVEs by attribute filters

        Args:
            filters: Dictionary of filters (cve_id, min_cvss_score, max_cvss_score)
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        limit = min(limit or self.default_limit, self.max_limit)

        try:
            results = self.milvus_client.search_by_filters(
                filters=filters,
                limit=limit,
                output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
            )

            return {"filters": filters, "results": results, "total_found": len(results)}

        except Exception as e:
            logger.error(f"Error in filter search: {str(e)}")
            return {"error": str(e), "results": []}

    def search_by_cve_id(self, cve_id: str) -> Dict[str, Any]:
        """
        Search for a specific CVE by ID

        Args:
            cve_id: CVE identifier (e.g., "CVE-2021-1234")

        Returns:
            Dictionary with CVE data or error
        """
        try:
            results = self.milvus_client.search_by_filters(
                filters={"cve_id": cve_id},
                limit=1,
                output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
            )

            if results:
                return {"cve_id": cve_id, "found": True, "data": results[0]}
            else:
                return {
                    "cve_id": cve_id,
                    "found": False,
                    "message": f"CVE {cve_id} not found in database",
                }

        except Exception as e:
            logger.error(f"Error searching for CVE {cve_id}: {str(e)}")
            return {"error": str(e), "cve_id": cve_id}

    def find_similar_cves(
        self,
        reference_cve_id: str,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Find CVEs similar to a reference CVE

        Args:
            reference_cve_id: CVE ID to find similar ones for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score

        Returns:
            Dictionary with similar CVEs
        """
        limit = min(limit or self.default_limit, self.max_limit)
        similarity_threshold = similarity_threshold or self.similarity_threshold

        try:
            # First get the reference CVE
            reference_cve = self.search_by_cve_id(reference_cve_id)
            if not reference_cve.get("found"):
                return {
                    "error": f"Reference CVE {reference_cve_id} not found",
                    "results": [],
                }

            # Use the summary to find similar CVEs
            summary = reference_cve["data"]["summary"]
            search_results = self.search_by_text(
                query=summary,
                limit=limit + 1,  # +1 to account for the reference CVE itself
                similarity_threshold=similarity_threshold,
                include_scores=True,
            )

            # Filter out the reference CVE from results
            similar_cves = [
                result
                for result in search_results["results"]
                if result.get("cve_id") != reference_cve_id
            ][:limit]

            return {
                "reference_cve": reference_cve_id,
                "reference_summary": summary,
                "similar_cves": similar_cves,
                "total_found": len(similar_cves),
                "similarity_threshold": similarity_threshold,
            }

        except Exception as e:
            logger.error(f"Error finding similar CVEs for {reference_cve_id}: {str(e)}")
            return {"error": str(e), "results": []}

    def get_high_severity_cves(
        self, min_cvss_score: float = 7.0, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get high severity CVEs based on CVSS score

        Args:
            min_cvss_score: Minimum CVSS score (default: 7.0 for high)
            limit: Maximum number of results

        Returns:
            Dictionary with high severity CVEs
        """
        return self.search_by_filters(
            filters={"min_cvss_score": min_cvss_score}, limit=limit
        )

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics and health information

        Returns:
            Dictionary with service stats
        """
        try:
            milvus_stats = self.milvus_client.get_collection_stats()

            return {
                "service_status": "healthy",
                "milvus_connection": self.milvus_client._connection_established,
                "collection_stats": milvus_stats,
                "config": {
                    "default_limit": self.default_limit,
                    "max_limit": self.max_limit,
                    "similarity_threshold": self.similarity_threshold,
                    "embedding_dimension": self.query_processor.model_name,
                },
            }

        except Exception as e:
            logger.error(f"Error getting service stats: {str(e)}")
            return {"service_status": "error", "error": str(e)}

    def search_raw_similarity(
        self, query: str, limit: int = 20, include_scores: bool = True
    ) -> Dict[str, Any]:
        """
        Raw similarity search without threshold filtering - for debugging

        Args:
            query: Text query
            limit: Maximum results
            include_scores: Include similarity scores

        Returns:
            All results from Milvus without filtering
        """
        try:
            # Generate embedding
            embedding = self.query_processor.generate_embedding(query)
            if not embedding:
                return {"error": "Failed to generate embedding", "results": []}

            # Get raw results from Milvus with no threshold
            raw_results = self.milvus_client.search_similar(
                query_vector=embedding,
                limit=limit,
                similarity_threshold=0.0,  # No threshold
                output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
            )

            if not include_scores:
                for result in raw_results:
                    result.pop("score", None)

            return {
                "query": query,
                "results": raw_results,
                "total_found": len(raw_results),
                "raw_search": True,
                "note": "All results without threshold filtering",
            }

        except Exception as e:
            logger.error(f"Error in raw similarity search: {str(e)}")
            return {"error": str(e), "results": []}

    def analyze_report_vulnerabilities(
        self,
        analysis_report: dict,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        include_scores: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze a technical report and find relevant vulnerabilities

        Args:
            analysis_report: Dictionary containing the analysis report
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            include_scores: Include similarity scores in results

        Returns:
            Dictionary with vulnerability analysis results
        """
        limit = min(limit or 20, self.max_limit)
        similarity_threshold = similarity_threshold or 0.5

        try:
            # Extract search terms from the report
            search_queries = []
            all_vulnerabilities = []
            seen_cve_ids = set()

            # Get vulnerability search keywords if available
            vulnerability_keywords = analysis_report.get(
                "vulnerability_search_keywords", []
            )
            if vulnerability_keywords:
                search_queries.extend(
                    vulnerability_keywords[:10]
                )  # Limit to top 10 keywords

            # Extract technology stack information
            tech_stack = analysis_report.get("technology_stack", {})
            if tech_stack:
                primary_lang = tech_stack.get("primary_language")
                if primary_lang:
                    search_queries.append(f"{primary_lang} security vulnerability")

                technologies = tech_stack.get("inferred_technologies", [])
                for tech in technologies[:5]:  # Limit to top 5 technologies
                    search_queries.append(f"{tech} vulnerability")

            # Extract security concerns
            security_context = analysis_report.get("security_context", {})
            security_concerns = security_context.get("security_concerns", [])
            search_queries.extend(security_concerns[:8])  # Top 8 security concerns

            # Add general queries based on metadata
            metadata = analysis_report.get("metadata", {})
            repo_url = metadata.get("repository_url", "")
            if "flask" in repo_url.lower():
                search_queries.extend(
                    [
                        "Flask web framework vulnerability",
                        "Python web application security",
                        "WSGI security vulnerability",
                    ]
                )

            # Remove duplicates and limit total queries
            unique_queries = list(dict.fromkeys(search_queries))[:15]

            logger.info(f"Analyzing report with {len(unique_queries)} search queries")

            # Search for vulnerabilities using each query
            for i, query in enumerate(unique_queries):
                logger.info(
                    f"Searching query {i + 1}/{len(unique_queries)}: '{query[:50]}...'"
                )

                # Generate embedding and search
                embedding = self.query_processor.generate_embedding(query)
                if not embedding:
                    logger.warning(f"Failed to generate embedding for query: {query}")
                    continue

                # Search Milvus
                results = self.milvus_client.search_similar(
                    query_vector=embedding,
                    limit=max(
                        limit // 2, 10
                    ),  # Get fewer results per query to diversify
                    similarity_threshold=similarity_threshold,
                    output_fields=["cve_id", "summary", "cvss_score", "cvss_vector"],
                )

                # Add unique results
                for result in results:
                    cve_id = result.get("cve_id")
                    if cve_id not in seen_cve_ids:
                        seen_cve_ids.add(cve_id)
                        result["matched_query"] = query  # Track which query matched
                        if not include_scores:
                            result.pop("score", None)
                        all_vulnerabilities.append(result)

                # Stop if we have enough results
                if len(all_vulnerabilities) >= limit * 2:
                    break

            # Sort by score if available and limit results
            if include_scores and all_vulnerabilities:
                all_vulnerabilities.sort(key=lambda x: x.get("score", 0), reverse=True)

            final_results = all_vulnerabilities[:limit]

            # Categorize vulnerabilities by type
            vulnerability_categories = {}
            for vuln in final_results:
                summary = vuln.get("summary", "").lower()
                categories = []

                if any(term in summary for term in ["sql injection", "sqli"]):
                    categories.append("SQL Injection")
                if any(term in summary for term in ["xss", "cross-site scripting"]):
                    categories.append("Cross-Site Scripting")
                if any(
                    term in summary for term in ["buffer overflow", "buffer overrun"]
                ):
                    categories.append("Buffer Overflow")
                if any(term in summary for term in ["authentication", "auth bypass"]):
                    categories.append("Authentication")
                if any(
                    term in summary for term in ["privilege escalation", "elevation"]
                ):
                    categories.append("Privilege Escalation")
                if any(term in summary for term in ["denial of service", "dos"]):
                    categories.append("Denial of Service")
                if any(
                    term in summary
                    for term in ["directory traversal", "path traversal"]
                ):
                    categories.append("Directory Traversal")
                if any(
                    term in summary for term in ["information disclosure", "info leak"]
                ):
                    categories.append("Information Disclosure")

                if not categories:
                    categories.append("Other")

                for category in categories:
                    if category not in vulnerability_categories:
                        vulnerability_categories[category] = 0
                    vulnerability_categories[category] += 1

            return {
                "analysis_summary": {
                    "repository_url": metadata.get("repository_url", "Unknown"),
                    "primary_technology": tech_stack.get("primary_language", "Unknown"),
                    "analysis_date": metadata.get("analysis_timestamp", "Unknown"),
                },
                "search_metadata": {
                    "queries_used": len(unique_queries),
                    "sample_queries": unique_queries[:5],
                    "similarity_threshold": similarity_threshold,
                },
                "vulnerabilities": final_results,
                "vulnerability_summary": {
                    "total_found": len(final_results),
                    "categories": vulnerability_categories,
                    "severity_distribution": self._analyze_severity_distribution(
                        final_results
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing report vulnerabilities: {str(e)}")
            return {"error": str(e), "vulnerabilities": []}

    def _analyze_severity_distribution(self, vulnerabilities):
        """Analyze CVSS score distribution of vulnerabilities"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}

        for vuln in vulnerabilities:
            cvss_score = vuln.get("cvss_score")
            if cvss_score is None:
                distribution["unknown"] += 1
            elif cvss_score >= 9.0:
                distribution["critical"] += 1
            elif cvss_score >= 7.0:
                distribution["high"] += 1
            elif cvss_score >= 4.0:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1

        return distribution

    def close(self):
        """Close all connections and cleanup"""
        try:
            self.milvus_client.disconnect()
            logger.info("CVE Retrieval Service closed successfully")
        except Exception as e:
            logger.error(f"Error closing service: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
