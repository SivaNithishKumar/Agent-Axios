"""CVE search service - finds vulnerabilities using Milvus + reranking."""
from typing import List, Callable, Optional, Dict, Any
import os
from langsmith import traceable
from app.models import CodeChunk, CVEFinding, db
from app.services.cohere_service import CohereEmbeddingService, CohereRerankService
from app.services.milvus_client import MilvusClient
import logging

logger = logging.getLogger(__name__)

class CVESearchService:
    """Handles CVE search with Milvus and reranking using consistent Cohere embeddings."""
    
    CONFIDENCE_THRESHOLD = 0.65  # Minimum confidence to save finding
    
    def __init__(self):
        self.cohere_embedding = CohereEmbeddingService()
        self.cohere_rerank = CohereRerankService()
        
        # Milvus configuration
        milvus_config = {
            "collection_name": "vuln",
            "endpoint": "https://in03-6ad99fbc2869a71.serverless.aws-eu-central-1.cloud.zilliz.com",
            "token": os.getenv("MILVUS_TOKEN", "0c10dc02af7b90a3313e75db42c20269b25f7a2926877466b51f29e037315e336cab32756d681c6c6c666ac5c5b8e26c2aa8aba6"),
        }
        
        # Initialize Milvus client
        self.milvus_client = MilvusClient(milvus_config)
        
        # Connect to Milvus
        if not self.milvus_client.connect():
            logger.error("Failed to connect to Milvus - CVE search will not work")
        else:
            logger.info("Successfully connected to Milvus CVE database")
            logger.warning("Note: Milvus uses 3072-dim Gemini embeddings, but we're using 1024-dim Cohere (padded)")
    
    @traceable(name="search_cves_by_queries", run_type="retriever")
    def search_by_queries(
        self,
        queries: List[str],
        top_k_per_query: int = 20,
        rerank_top_n: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search CVEs using multiple decomposed queries.
        
        This implements the correct flow:
        1. Take decomposed CVE queries
        2. Search Milvus for each query
        3. Rerank results
        4. Deduplicate and return top CVEs
        
        Args:
            queries: List of decomposed search queries
            top_k_per_query: Milvus candidates per query
            rerank_top_n: Final results per query after reranking
            progress_callback: Optional progress callback (current, total)
        
        Returns:
            List of CVE records with scores
        """
        total = len(queries)
        logger.info(f"Searching CVEs with {total} decomposed queries")
        
        all_cves = {}  # cve_id -> cve_data (keeping best score)
        
        for i, query in enumerate(queries):
            try:
                # Generate query embedding (1024-dim Cohere)
                query_embedding_1024 = self.cohere_embedding.generate_embeddings([query], input_type="search_query")[0]
                
                # Pad to 3072 dimensions for Milvus compatibility
                # Note: This is a workaround. Ideally, rebuild Milvus with Cohere embeddings
                query_embedding_3072 = query_embedding_1024 + [0.0] * (3072 - 1024)
                
                # Milvus similarity search
                milvus_results = self.milvus_client.search_similar(
                    query_vector=query_embedding_3072,
                    limit=top_k_per_query,
                    similarity_threshold=0.25,  # Lower threshold due to dimension mismatch
                    output_fields=["cve_id", "summary", "cvss_score"]
                )
                
                if not milvus_results:
                    logger.debug(f"Query {i + 1}/{total}: No Milvus results")
                    continue
                
                # Prepare documents for reranking
                documents = []
                cve_map = {}
                for result in milvus_results:
                    cve_id = result.get('cve_id', '')
                    summary = result.get('summary', '')
                    doc_text = f"{cve_id}: {summary}"
                    documents.append(doc_text)
                    cve_map[cve_id] = result
                
                if not documents:
                    continue
                
                # Rerank with Cohere
                rerank_results = self.cohere_rerank.rerank(
                    query,
                    documents,
                    top_n=rerank_top_n
                )
                
                # Store CVEs with best relevance scores
                for result in rerank_results:
                    doc_text = result.get('text') or result.get('document', '')
                    cve_id = doc_text.split(':')[0].strip() if ':' in doc_text else ''
                    
                    if cve_id in cve_map:
                        cve_data = cve_map[cve_id]
                        relevance_score = result['relevance_score']
                        
                        # Keep CVE with highest relevance score
                        if cve_id not in all_cves or relevance_score > all_cves[cve_id]['relevance_score']:
                            all_cves[cve_id] = {
                                'cve_id': cve_id,
                                'summary': cve_data.get('summary', ''),
                                'cvss_score': cve_data.get('cvss_score', 0.0),
                                'relevance_score': relevance_score,
                                'matched_query': query
                            }
                
                if progress_callback:
                    progress_callback(i + 1, total)
                
                logger.info(f"Query {i + 1}/{total}: Found {len(rerank_results)} relevant CVEs")
                
            except Exception as e:
                logger.warning(f"Query {i + 1}/{total} failed: {str(e)}")
                continue
        
        # Sort by relevance score and return
        sorted_cves = sorted(all_cves.values(), key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Total unique CVEs found: {len(sorted_cves)}")
        return sorted_cves
    
    @traceable(name="search_all_chunks", run_type="tool")
    def search_all_chunks(
        self,
        chunks: List[CodeChunk],
        milvus_top_k: int = 50,
        rerank_top_n: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[CVEFinding]:
        """
        Search for CVEs across all chunks using Milvus.
        
        Args:
            chunks: List of CodeChunk objects
            milvus_top_k: Number of candidates from Milvus
            rerank_top_n: Number of results after reranking
            progress_callback: Optional progress callback (current, total)
        
        Returns:
            List[CVEFinding]: Created findings
        """
        total = len(chunks)
        logger.info(f"Searching CVEs for {total} chunks (Milvus top-{milvus_top_k}, rerank top-{rerank_top_n})")
        
        all_findings = []
        
        for i, chunk in enumerate(chunks):
            try:
                findings = self._search_chunk(chunk, milvus_top_k, rerank_top_n)
                all_findings.extend(findings)
                
                if progress_callback:
                    progress_callback(i + 1, total)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Searched {i + 1}/{total} chunks, found {len(all_findings)} vulnerabilities")
                    
            except Exception as e:
                logger.warning(f"Failed to search chunk {chunk.chunk_id}: {str(e)}")
                continue
        
        logger.info(f"Total vulnerabilities found: {len(all_findings)}")
        return all_findings
    
    @traceable(name="search_single_chunk", run_type="tool")
    def _search_chunk(
        self,
        chunk: CodeChunk,
        milvus_top_k: int,
        rerank_top_n: int
    ) -> List[CVEFinding]:
        """Search CVEs for a single chunk using Milvus."""
        # Generate query text for the chunk
        query_text = (
            f"File: {chunk.file_path}\nLines {chunk.line_start}-{chunk.line_end}\n\n{chunk.chunk_text}"
        )
        
        # Generate query embedding using Azure Cohere (1024-dim)
        # Note: Milvus collection expects 3072-dim (Gemini), so we need to pad
        query_embedding_1024 = self.cohere_embedding.generate_embeddings([query_text])[0]
        
        # Pad embedding from 1024 to 3072 dimensions (zero-padding)
        query_embedding_3072 = query_embedding_1024 + [0.0] * (3072 - 1024)
        
        if not query_embedding_3072:
            logger.warning(f"Failed to generate embedding for chunk {chunk.chunk_id}")
            return []
        
        # Milvus similarity search
        milvus_results = self.milvus_client.search_similar(
            query_vector=query_embedding_3072,
            limit=milvus_top_k,
            similarity_threshold=0.3,  # Lower threshold due to dimension mismatch
            output_fields=["cve_id", "summary", "cvss_score"]
        )
        
        if not milvus_results:
            return []
        
        # Create documents for reranking
        documents = []
        cve_map = {}
        for result in milvus_results:
            cve_id = result.get('cve_id', '')
            summary = result.get('summary', '')
            doc_text = f"{cve_id}: {summary}"
            documents.append(doc_text)
            cve_map[cve_id] = result
        
        if not documents:
            return []

        # Rerank with Cohere
        rerank_results = self.cohere_rerank.rerank(
            query_text,
            documents,
            top_n=rerank_top_n
        )
        
        # Create findings above confidence threshold
        findings = []
        for result in rerank_results:
            if result['relevance_score'] >= self.CONFIDENCE_THRESHOLD:
                # Extract CVE ID from the document text
                doc_text = result.get('text') or result.get('document', '')
                cve_id = doc_text.split(':')[0].strip() if ':' in doc_text else ''
                
                cve_data = cve_map.get(cve_id)
                
                if cve_data:
                    finding = CVEFinding(
                        analysis_id=chunk.analysis_id,
                        chunk_id=chunk.chunk_id,
                        cve_id=cve_id,
                        file_path=chunk.file_path,
                        confidence_score=result['relevance_score'],
                        validation_status='pending',
                        cve_description=cve_data.get('summary', '')
                    )
                    db.session.add(finding)
                    findings.append(finding)
        
        if findings:
            db.session.flush()
            logger.debug(
                "Chunk %s: found %s potential vulnerabilities from Milvus",
                chunk.chunk_id,
                len(findings)
            )
        
        return findings
    
    @traceable(name="search_by_query", run_type="tool")
    def search_by_query(
        self,
        query: str,
        top_k: int = 20,
        top_n: int = 5
    ) -> List[dict]:
        """
        Direct CVE search by text query (for testing/debugging).
        
        Args:
            query: Search query
            top_k: Milvus candidates
            top_n: Reranked results
        
        Returns:
            List of CVE results with scores
        """
        # Generate embedding using Azure Cohere (1024-dim)
        query_embedding_1024 = self.cohere_embedding.generate_embeddings([query])[0]
        
        # Pad to 3072 dimensions
        query_embedding_3072 = query_embedding_1024 + [0.0] * (3072 - 1024)
        
        if not query_embedding_3072:
            logger.warning("Failed to generate embedding for query")
            return []
        
        # Milvus search
        milvus_results = self.milvus_client.search_similar(
            query_vector=query_embedding_3072,
            limit=top_k,
            similarity_threshold=0.3,  # Lower threshold due to dimension mismatch
            output_fields=["cve_id", "summary", "cvss_score"]
        )
        
        if not milvus_results:
            return []
        
        # Create CVE map for quick lookup
        cve_map = {r.get('cve_id', ''): r for r in milvus_results}
        
        # Rerank
        documents = [f"{r.get('cve_id', '')}: {r.get('summary', '')}" for r in milvus_results]
        if not documents:
            return []
        
        rerank_results = self.cohere_rerank.rerank(query, documents, top_n=top_n)
        
        # Format results
        results = []
        for result in rerank_results:
            doc_text = result.get('text') or result.get('document', '')
            cve_id = doc_text.split(':')[0].strip() if ':' in doc_text else ''
            cve_data = cve_map.get(cve_id)
            
            if cve_data:
                results.append({
                    'cve_id': cve_id,
                    'description': cve_data.get('summary', ''),
                    'cvss_score': cve_data.get('cvss_score', 0.0),
                    'relevance_score': result['relevance_score']
                })
        
        return results
