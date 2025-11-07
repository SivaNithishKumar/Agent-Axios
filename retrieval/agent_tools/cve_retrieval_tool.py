"""
CVE Retrieval Tool for AI Agents

This tool allows AI agents to search and retrieve vulnerability data from the CVE database.
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_tools.base_tool import BaseTool, ToolDefinition, ToolParameter
from retrieval_service import CVERetrievalService

logger = logging.getLogger(__name__)


class CVERetrievalTool(BaseTool):
    """
    Tool for searching and retrieving CVE vulnerability data.

    This tool provides AI agents with the ability to:
    - Search CVEs by text description
    - Find similar CVEs to a reference CVE
    - Filter CVEs by CVSS score
    - Retrieve specific CVE details
    - Analyze technical reports for vulnerabilities
    """

    def __init__(self):
        super().__init__()
        self.service = None

    def initialize(self) -> bool:
        """Initialize the CVE retrieval service"""
        try:
            self.service = CVERetrievalService()
            success = self.service.initialize()
            if success:
                self._initialized = True
                logger.info("CVE Retrieval Tool initialized successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to initialize CVE Retrieval Tool: {str(e)}")
            return False

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for AI agents"""
        return ToolDefinition(
            name="cve_retrieval",
            description="Search and retrieve vulnerability data from CVE database. Use this tool to find security vulnerabilities, analyze potential risks, and get detailed CVE information.",
            category="security",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform",
                    required=True,
                    enum=[
                        "search_by_text",
                        "search_similar",
                        "get_by_id",
                        "search_by_filters",
                        "get_high_severity",
                        "analyze_report",
                        "analyze_markdown",
                    ],
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query for text-based search (required for search_by_text)",
                    required=False,
                ),
                ToolParameter(
                    name="cve_id",
                    type="string",
                    description="CVE identifier (e.g., CVE-2021-1234) (required for get_by_id and search_similar)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Maximum number of results to return",
                    required=False,
                    default=10,
                ),
                ToolParameter(
                    name="similarity_threshold",
                    type="float",
                    description="Minimum similarity score (0.0-1.0)",
                    required=False,
                    default=0.7,
                ),
                ToolParameter(
                    name="min_cvss_score",
                    type="float",
                    description="Minimum CVSS score for filtering (0.0-10.0)",
                    required=False,
                ),
                ToolParameter(
                    name="max_cvss_score",
                    type="float",
                    description="Maximum CVSS score for filtering (0.0-10.0)",
                    required=False,
                ),
                ToolParameter(
                    name="expand_query",
                    type="boolean",
                    description="Expand search query with related terms",
                    required=False,
                    default=False,
                ),
                ToolParameter(
                    name="analysis_report",
                    type="object",
                    description="Technical analysis report for vulnerability analysis (required for analyze_report)",
                    required=False,
                ),
                ToolParameter(
                    name="markdown_report",
                    type="string",
                    description="Markdown security analysis report (required for analyze_markdown)",
                    required=False,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Number of top results to return (alias for limit)",
                    required=False,
                ),
                ToolParameter(
                    name="min_cvss",
                    type="float",
                    description="Minimum CVSS score filter (alias for min_cvss_score)",
                    required=False,
                ),
            ],
            examples=[
                {
                    "description": "Search for SQL injection vulnerabilities",
                    "parameters": {
                        "action": "search_by_text",
                        "query": "SQL injection in web applications",
                        "limit": 10,
                    },
                },
                {
                    "description": "Find CVEs similar to a known vulnerability",
                    "parameters": {
                        "action": "search_similar",
                        "cve_id": "CVE-2021-44228",
                        "limit": 5,
                    },
                },
                {
                    "description": "Get details of a specific CVE",
                    "parameters": {"action": "get_by_id", "cve_id": "CVE-2021-44228"},
                },
                {
                    "description": "Get high severity vulnerabilities",
                    "parameters": {
                        "action": "get_high_severity",
                        "min_cvss_score": 9.0,
                        "limit": 20,
                    },
                },
            ],
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the CVE retrieval tool

        Args:
            action: Action to perform (search_by_text, search_similar, etc.)
            **kwargs: Action-specific parameters

        Returns:
            Dictionary with results
        """
        if not self._initialized:
            return {"error": "Tool not initialized. Call initialize() first."}

        try:
            # Validate parameters
            validated = self.validate_parameters(kwargs)
            action = validated.get("action")

            # Route to appropriate action
            if action == "search_by_text":
                return self._search_by_text(validated)
            elif action == "search_similar":
                return self._search_similar(validated)
            elif action == "get_by_id":
                return self._get_by_id(validated)
            elif action == "search_by_filters":
                return self._search_by_filters(validated)
            elif action == "get_high_severity":
                return self._get_high_severity(validated)
            elif action == "analyze_report":
                return self._analyze_report(validated)
            elif action == "analyze_markdown":
                return self._analyze_markdown(validated)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Error executing CVE retrieval tool: {str(e)}")
            return {"error": str(e)}

    def _search_by_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search CVEs by text query"""
        query = params.get("query")
        if not query:
            return {"error": "query parameter is required for search_by_text action"}

        result = self.service.search_by_text(
            query=query,
            limit=params.get("limit", 10),
            similarity_threshold=params.get("similarity_threshold", 0.7),
            include_scores=True,
            expand_query=params.get("expand_query", False),
        )

        return {
            "tool": "cve_retrieval",
            "action": "search_by_text",
            "success": "error" not in result,
            "data": result,
        }

    def _search_similar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find similar CVEs to a reference CVE"""
        cve_id = params.get("cve_id")
        if not cve_id:
            return {
                "error": "cve_id parameter is required for search_similar action"
            }

        result = self.service.find_similar_cves(
            reference_cve_id=cve_id,
            limit=params.get("limit", 10),
            similarity_threshold=params.get("similarity_threshold", 0.7),
        )

        return {
            "tool": "cve_retrieval",
            "action": "search_similar",
            "success": "error" not in result,
            "data": result,
        }

    def _get_by_id(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific CVE by ID"""
        cve_id = params.get("cve_id")
        if not cve_id:
            return {"error": "cve_id parameter is required for get_by_id action"}

        result = self.service.search_by_cve_id(cve_id)

        return {
            "tool": "cve_retrieval",
            "action": "get_by_id",
            "success": "error" not in result,
            "data": result,
        }

    def _search_by_filters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search CVEs by filters"""
        filters = {}
        if "min_cvss_score" in params:
            filters["min_cvss_score"] = params["min_cvss_score"]
        if "max_cvss_score" in params:
            filters["max_cvss_score"] = params["max_cvss_score"]
        if "cve_id" in params:
            filters["cve_id"] = params["cve_id"]

        result = self.service.search_by_filters(
            filters=filters, limit=params.get("limit", 10)
        )

        return {
            "tool": "cve_retrieval",
            "action": "search_by_filters",
            "success": "error" not in result,
            "data": result,
        }

    def _get_high_severity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get high severity CVEs"""
        result = self.service.get_high_severity_cves(
            min_cvss_score=params.get("min_cvss_score", 7.0),
            limit=params.get("limit", 10),
        )

        return {
            "tool": "cve_retrieval",
            "action": "get_high_severity",
            "success": "error" not in result,
            "data": result,
        }

    def _analyze_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical report for vulnerabilities"""
        report = params.get("analysis_report")
        if not report:
            return {
                "error": "analysis_report parameter is required for analyze_report action"
            }

        result = self.service.analyze_report_vulnerabilities(
            analysis_report=report,
            limit=params.get("limit", 20),
            similarity_threshold=params.get("similarity_threshold", 0.5),
            include_scores=True,
        )

        return {
            "tool": "cve_retrieval",
            "action": "analyze_report",
            "success": "error" not in result,
            "data": result,
        }

    def _analyze_markdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze markdown security report and return vulnerabilities in specific format
        
        Expected response format:
        {
            "success": true,
            "count": 10,
            "message": "Successfully retrieved X vulnerabilities",
            "vulnerabilities": [
                {
                    "cve_id": "CVE-XXXX-XXXX",
                    "summary": "...",
                    "cvss_score": 7.5,
                    "cvss_vector": "...",
                    "severity": "HIGH",
                    "similarity_score": 0.85,
                    "rerank_score": -3.5,
                    "rank": 1
                }
            ]
        }
        """
        markdown_report = params.get("markdown_report")
        if not markdown_report:
            return {
                "success": False,
                "count": 0,
                "message": "markdown_report parameter is required",
                "vulnerabilities": []
            }

        # Handle parameter aliases
        limit = params.get("top_k") or params.get("limit", 10)
        min_cvss = params.get("min_cvss") or params.get("min_cvss_score", 0.0)
        
        # Extract vulnerability keywords from markdown
        import re
        
        # Extract text from markdown (remove headers, bullets, etc.)
        text = markdown_report.replace('#', '').replace('-', '').replace('*', '')
        
        # Extract potential vulnerability terms
        vulnerability_patterns = [
            r'SQL injection',
            r'buffer overflow',
            r'cross-site scripting|XSS',
            r'authentication bypass',
            r'remote code execution|RCE',
            r'privilege escalation',
            r'denial of service|DoS',
            r'information disclosure',
            r'command injection',
            r'path traversal',
            r'deserialization',
            r'CSRF',
            r'XXE',
            r'SSRF',
        ]
        
        # Find all vulnerability terms mentioned
        found_terms = []
        for pattern in vulnerability_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_terms.extend(matches)
        
        # If no specific terms found, use the entire text as query
        if not found_terms:
            found_terms = [text[:200]]  # Use first 200 chars
        
        # Search for vulnerabilities using extracted terms
        all_vulnerabilities = []
        seen_cve_ids = set()
        
        # Combine terms into a single search query
        search_query = " ".join(found_terms[:10])  # Use top 10 terms
        
        logger.info(f"Analyzing markdown with query: {search_query[:100]}...")
        
        try:
            # Use the service to search with very low threshold to get results
            # No CVSS filtering - just return based on text similarity
            result = self.service.search_by_text(
                query=search_query,
                limit=limit,  # Just get what we need
                similarity_threshold=0.01,  # Very low threshold for broad results
                include_scores=True,
                expand_query=False,  # Don't expand, use exact terms
            )
            
            if "error" in result:
                return {
                    "success": False,
                    "count": 0,
                    "message": f"Error: {result['error']}",
                    "vulnerabilities": []
                }
            
            # Extract and format vulnerabilities
            results = result.get("results", [])
            
            logger.info(f"Got {len(results)} results from search, returning top {limit}")
            if results:
                logger.info(f"First result sample: {results[0]}")
            
            # Format vulnerabilities (no CVSS filtering, just text-based)
            formatted_vulns = []
            
            for rank, vuln in enumerate(results[:limit], start=1):
                # Extract CVSS score and calculate severity
                cvss_score = vuln.get("cvss_score", 0.0)
                
                # Determine severity from CVSS score
                if cvss_score >= 9.0:
                    severity = "CRITICAL"
                elif cvss_score >= 7.0:
                    severity = "HIGH"
                elif cvss_score >= 4.0:
                    severity = "MEDIUM"
                elif cvss_score > 0:
                    severity = "LOW"
                else:
                    severity = "UNKNOWN"
                
                # Format vulnerability
                formatted_vuln = {
                    "cve_id": vuln.get("cve_id", ""),
                    "summary": vuln.get("summary", ""),
                    "cvss_score": cvss_score,
                    "cvss_vector": vuln.get("cvss_vector", ""),
                    "severity": severity,
                    "similarity_score": vuln.get("score", 0.0),  # 'score' is similarity
                    "rerank_score": vuln.get("rerank_score", 0.0),
                    "rank": rank
                }
                
                formatted_vulns.append(formatted_vuln)
            
            count = len(formatted_vulns)
            logger.info(f"Returning {count} vulnerabilities based on text search")
            
            return {
                "success": True,
                "count": count,
                "message": f"Successfully retrieved {count} vulnerabilities",
                "vulnerabilities": formatted_vulns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing markdown: {str(e)}")
            return {
                "success": False,
                "count": 0,
                "message": f"Error analyzing markdown: {str(e)}",
                "vulnerabilities": []
            }

    def cleanup(self):
        """Cleanup resources"""
        if self.service:
            self.service.close()
            logger.info("CVE Retrieval Tool cleaned up")
