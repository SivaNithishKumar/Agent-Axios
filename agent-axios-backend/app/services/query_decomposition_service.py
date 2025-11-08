"""Query decomposition service using GPT-4.1 for generating multiple search angles."""
from typing import List
from langchain_openai import AzureChatOpenAI
from langsmith import traceable
from config.settings import Config
import logging

logger = logging.getLogger(__name__)


class QueryDecompositionService:
    """Handles query decomposition using Hypothetical Answer Generation (Hype)."""
    
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            deployment_name=Config.AZURE_OPENAI_MODEL,
            temperature=0.3
        )
        logger.info("Initialized QueryDecompositionService with GPT-4.1")
    
    @traceable(name="decompose_cve_query", run_type="llm")
    def decompose_cve(self, cve_id: str, cve_description: str, num_queries: int = 5) -> List[str]:
        """
        Decompose a CVE into multiple search queries using Hypothetical Answer Generation.
        
        Args:
            cve_id: CVE identifier
            cve_description: CVE description/summary
            num_queries: Number of queries to generate
        
        Returns:
            List of decomposed search queries
        """
        prompt = f"""You are a security expert analyzing code vulnerabilities.

CVE: {cve_id}
Description: {cve_description}

Generate {num_queries} diverse search queries to find code patterns related to this vulnerability.
Each query should focus on different aspects:
1. Code patterns that might exhibit this vulnerability
2. Specific functions or methods involved
3. Data structures or variables related to the issue
4. Library/framework usage patterns
5. Security-sensitive operations

For each query, describe what vulnerable code would look like.

Return ONLY the queries, one per line, without numbering or explanation.
"""
        
        try:
            response = self.llm.invoke(prompt)
            queries = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            
            # Ensure we have at least the original description
            if not queries:
                queries = [cve_description]
            
            # Limit to requested number
            queries = queries[:num_queries]
            
            logger.info(f"Decomposed {cve_id} into {len(queries)} queries")
            return queries
            
        except Exception as e:
            logger.error(f"Failed to decompose CVE query: {str(e)}")
            # Fallback to original description
            return [cve_description]
    
    @traceable(name="expand_query", run_type="llm")
    def expand_query(self, query: str, num_expansions: int = 3) -> List[str]:
        """
        Expand a single query into multiple related queries.
        
        Args:
            query: Original search query
            num_expansions: Number of expanded queries
        
        Returns:
            List including original and expanded queries
        """
        prompt = f"""Given this vulnerability search query:
"{query}"

Generate {num_expansions - 1} alternative ways to describe the same vulnerability or related code patterns.
Focus on:
- Alternative technical terminology
- Related security issues
- Different manifestations of the same vulnerability

Return ONLY the alternative queries, one per line."""

        try:
            response = self.llm.invoke(prompt)
            expanded = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            
            # Include original query first
            all_queries = [query] + expanded[:num_expansions - 1]
            
            logger.info(f"Expanded query into {len(all_queries)} variations")
            return all_queries
            
        except Exception as e:
            logger.error(f"Failed to expand query: {str(e)}")
            return [query]
