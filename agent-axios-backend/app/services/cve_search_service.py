"""CVE search service - finds vulnerabilities using FAISS + reranking."""
from typing import List, Callable, Optional
import numpy as np
from langsmith import traceable
from app.models import CodeChunk, CVEFinding, CVEDataset, db
from app.services.cohere_service import CohereEmbeddingService, CohereRerankService
from app.services.faiss_manager import CVEIndexManager
import logging

logger = logging.getLogger(__name__)

class CVESearchService:
    """Handles CVE search with FAISS and reranking."""
    
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to save finding
    
    def __init__(self):
        self.cohere_embedding = CohereEmbeddingService()
        self.cohere_rerank = CohereRerankService()
        self.cve_index = CVEIndexManager()
    
    @traceable(name="search_all_chunks", run_type="tool")
    def search_all_chunks(
        self,
        chunks: List[CodeChunk],
        faiss_top_k: int = 50,
        rerank_top_n: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[CVEFinding]:
        """
        Search for CVEs across all chunks.
        
        Args:
            chunks: List of CodeChunk objects
            faiss_top_k: Number of candidates from FAISS
            rerank_top_n: Number of results after reranking
            progress_callback: Optional progress callback (current, total)
        
        Returns:
            List[CVEFinding]: Created findings
        """
        total = len(chunks)
        logger.info(f"Searching CVEs for {total} chunks (FAISS top-{faiss_top_k}, rerank top-{rerank_top_n})")
        
        all_findings = []
        
        for i, chunk in enumerate(chunks):
            try:
                findings = self._search_chunk(chunk, faiss_top_k, rerank_top_n)
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
        faiss_top_k: int,
        rerank_top_n: int
    ) -> List[CVEFinding]:
        """Search CVEs for a single chunk."""
        # Generate query embedding for the chunk
        query_text = (
            f"File: {chunk.file_path}\nLines {chunk.line_start}-{chunk.line_end}\n\n{chunk.chunk_text}"
        )
        query_embedding = self.cohere_embedding.generate_embeddings([query_text])[0]
        
        # FAISS similarity search
        faiss_results = self.cve_index.search(np.array(query_embedding, dtype='float32'), top_k=faiss_top_k)
        
        if not faiss_results:
            return []
        
        # Get CVE data for reranking
        cve_ids = [result.get('cve_id') for result in faiss_results if result.get('cve_id')]
        cves = db.session.query(CVEDataset).filter(CVEDataset.cve_id.in_(cve_ids)).all()
        
        # Create documents for reranking
        documents = []
        cve_map = {}
        for cve in cves:
            doc_text = f"{cve.cve_id}: {cve.description}"
            documents.append(doc_text)
            cve_map[cve.cve_id] = cve
        
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
                cve_id = result['text'].split(':')[0] if 'text' in result else result['document'].split(':')[0]
                cve = cve_map.get(cve_id)
                
                if cve:
                    finding = CVEFinding(
                        analysis_id=chunk.analysis_id,
                        chunk_id=chunk.chunk_id,
                        cve_id=cve.cve_id,
                        file_path=chunk.file_path,
                        confidence_score=result['relevance_score'],
                        validation_status='pending',
                        cve_description=cve.description
                    )
                    db.session.add(finding)
                    findings.append(finding)
        
        if findings:
            db.session.flush()
            logger.debug(
                "Chunk %s: queued %s potential vulnerabilities",
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
            top_k: FAISS candidates
            top_n: Reranked results
        
        Returns:
            List of CVE results with scores
        """
        # Generate embedding
        query_embedding = self.cohere_embedding.generate_embeddings([query])[0]
        
        # FAISS search
        faiss_results = self.cve_index.search(np.array(query_embedding, dtype='float32'), top_k=top_k)
        
        if not faiss_results:
            return []
        
        # Get CVEs
        cve_ids = [result.get('cve_id') for result in faiss_results if result.get('cve_id')]
        cves = db.session.query(CVEDataset).filter(CVEDataset.cve_id.in_(cve_ids)).all()
        
        # Rerank
        documents = [f"{cve.cve_id}: {cve.description}" for cve in cves]
        if not documents:
            return []
        rerank_results = self.cohere_rerank.rerank(query, documents, top_n=top_n)
        
        # Format results
        results = []
        for result in rerank_results:
            cve_id = result['text'].split(':')[0] if 'text' in result else result['document'].split(':')[0]
            cve = next((c for c in cves if c.cve_id == cve_id), None)
            
            if cve:
                results.append({
                    'cve_id': cve.cve_id,
                    'description': cve.description,
                    'severity': cve.severity,
                    'relevance_score': result['relevance_score']
                })
        
        return results
