"""Analysis orchestrator - coordinates the CVE analysis pipeline with correct flow."""
import os
import shutil
import time
from datetime import datetime
from typing import List, Dict, Any
from langsmith import traceable
from app.models import Analysis, CVEFinding, CodeChunk, db
from app.services.repo_service import RepoService
from app.services.chunking_service import ChunkingService
from app.services.codebase_indexing_service import CodebaseIndexingService
from app.services.cve_search_service import CVESearchService
from app.services.query_decomposition_service import QueryDecompositionService
from app.services.validation_service import ValidationService
from app.services.report_service import ReportService
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """
    Orchestrates the full vulnerability analysis pipeline with correct flow:
    
    1. Clone repository
    2. Chunk code files
    3. Index codebase in FAISS (for semantic search)
    4. Search CVE database for relevant vulnerabilities
    5. Decompose CVE queries using Hype (Hypothetical Answer Generation)
    6. Search codebase for each decomposed query
    7. Match CVEs to code locations
    8. Validate findings with GPT-4.1
    9. Generate final report
    """
    
    def __init__(self, analysis_id: int, socketio_instance):
        self.analysis_id = analysis_id
        self.socketio = socketio_instance
        self.analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
        if not self.analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        self.room = f"analysis_{analysis_id}"
        
        # Initialize services
        self.repo_service = RepoService()
        self.chunking_service = ChunkingService()
        self.indexing_service = CodebaseIndexingService()
        self.cve_search_service = CVESearchService()
        self.query_decomposition_service = QueryDecompositionService()
        self.validation_service = ValidationService()
        self.report_service = ReportService()
        
        # Get analysis type config
        self.config = Config.ANALYSIS_CONFIGS.get(self.analysis.analysis_type, Config.ANALYSIS_CONFIGS['MEDIUM'])
        
        logger.info(f"Initialized orchestrator for analysis {analysis_id} ({self.analysis.analysis_type})")

    
    @traceable(name="full_analysis_pipeline", run_type="chain")
    def run(self):
        """Execute the full analysis pipeline with correct flow."""
        repo_path = None
        
        try:
            # Refresh session in background thread
            db.session.expire_all()
            self.analysis = db.session.query(Analysis).filter_by(analysis_id=self.analysis_id).first()
            if not self.analysis:
                raise ValueError(f"Analysis {self.analysis_id} not found in background task")
            
            self.analysis.status = 'running'
            self.analysis.start_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ Analysis {self.analysis_id} started")
            
            logger.info(f"Starting analysis {self.analysis_id}: {self.analysis.repo_url}")
            
            # ========== STEP 1: Clone Repository (0% → 10%) ==========
            self.emit_progress(0, 'cloning', 'Cloning repository...')
            repo_path = self.repo_service.clone(self.analysis.repo_url)
            self.emit_progress(10, 'cloning', 'Repository cloned successfully')
            time.sleep(0.5)
            
            # ========== STEP 2: Chunk Files (10% → 20%) ==========
            self.emit_progress(10, 'chunking', 'Parsing and chunking code files...')
            chunks = self.chunking_service.process_directory(
                repo_path,
                self.analysis_id,
                max_files=self.config['max_files'],
                max_chunks_per_file=self.config['max_chunks_per_file'],
                progress_callback=self._chunking_progress_callback
            )
            self.analysis.total_files = self.chunking_service.files_processed
            self.analysis.total_chunks = len(chunks)
            db.session.commit()
            self.emit_progress(20, 'chunking', f'Chunked {len(chunks)} code segments from {self.analysis.total_files} files')
            
            # Early exit if no code files
            if len(chunks) == 0:
                logger.warning(f"No code chunks found for analysis {self.analysis_id}")
                self._complete_analysis(0, 'No supported code files found in repository')
                return
            
            # ========== STEP 3: Index Codebase in FAISS (20% → 35%) ==========
            self.emit_progress(20, 'indexing', 'Creating searchable codebase index...')
            self.indexing_service.index_chunks(
                chunks,
                progress_callback=self._indexing_progress_callback
            )
            self.emit_progress(35, 'indexing', f'Indexed {len(chunks)} code chunks in FAISS')
            time.sleep(0.5)
            
            # ========== STEP 4: Search CVE Database (35% → 45%) ==========
            self.emit_progress(35, 'cve_search', 'Searching CVE database for relevant vulnerabilities...')
            
            # Generate initial query based on repo analysis
            # For now, use generic query; later can integrate with repo_analyzer
            initial_query = self._generate_initial_query(repo_path)
            
            # Search CVEs with initial query
            initial_cves = self.cve_search_service.search_by_queries(
                [initial_query],
                top_k_per_query=50,
                rerank_top_n=self.config.get('cve_top_k', 20)
            )
            
            if not initial_cves:
                logger.warning(f"No relevant CVEs found for analysis {self.analysis_id}")
                self._complete_analysis(0, 'No relevant vulnerabilities found for this repository')
                return
            
            self.emit_progress(45, 'cve_search', f'Found {len(initial_cves)} relevant CVEs')
            logger.info(f"Top CVEs: {[cve['cve_id'] for cve in initial_cves[:5]]}")
            time.sleep(0.5)
            
            # ========== STEP 5: Query Decomposition (45% → 50%) ==========
            self.emit_progress(45, 'decomposition', 'Decomposing CVE queries using Hype...')
            
            # Decompose top CVEs (limit based on analysis type)
            num_cves_to_analyze = self.config.get('cves_to_analyze', 10)
            top_cves = initial_cves[:num_cves_to_analyze]
            
            all_decomposed_queries = []
            cve_query_map = {}  # query -> cve_id mapping
            
            for cve in top_cves:
                queries = self.query_decomposition_service.decompose_cve(
                    cve['cve_id'],
                    cve['summary'],
                    num_queries=self.config.get('queries_per_cve', 3)
                )
                all_decomposed_queries.extend(queries)
                
                # Map queries back to CVE
                for query in queries:
                    cve_query_map[query] = cve
            
            self.emit_progress(50, 'decomposition', f'Generated {len(all_decomposed_queries)} search queries from {len(top_cves)} CVEs')
            logger.info(f"Decomposed {len(top_cves)} CVEs into {len(all_decomposed_queries)} queries")
            time.sleep(0.5)
            
            # ========== STEP 6: Search Codebase (50% → 70%) ==========
            self.emit_progress(50, 'code_search', 'Searching codebase for vulnerability patterns...')
            
            code_matches = self.indexing_service.search_multiple(
                all_decomposed_queries,
                top_k_per_query=self.config.get('code_matches_per_query', 5),
                similarity_threshold=0.5,
                progress_callback=self._code_search_progress_callback
            )
            
            self.emit_progress(70, 'code_search', f'Found {len(code_matches)} potential vulnerability locations')
            logger.info(f"Found {len(code_matches)} code matches across {len(all_decomposed_queries)} queries")
            time.sleep(0.5)
            
            # ========== STEP 7: Match CVEs to Code (70% → 75%) ==========
            self.emit_progress(70, 'matching', 'Matching CVEs to code locations...')
            
            findings = self._create_findings(code_matches, cve_query_map, chunks)
            self.analysis.total_findings = len(findings)
            db.session.commit()
            
            self.emit_progress(75, 'matching', f'Created {len(findings)} CVE findings')
            logger.info(f"Created {len(findings)} findings")
            time.sleep(0.5)
            
            # ========== STEP 8: Validate with GPT-4.1 (75% → 95%) ==========
            if self.config['validation_enabled'] and findings:
                self.emit_progress(75, 'validating', 'Validating findings with GPT-4.1...')
                self.validation_service.validate_all_findings(
                    findings,
                    chunks,
                    progress_callback=self._validation_progress_callback
                )
                self.emit_progress(95, 'validating', 'Validation complete')
            else:
                self.emit_progress(95, 'skipping_validation', 'Skipping validation (SHORT analysis)')
            
            # ========== STEP 9: Generate Reports (95% → 100%) ==========
            self.emit_progress(95, 'finalizing', 'Generating reports...')
            
            report_paths = self.report_service.generate_reports(self.analysis_id)
            config_snapshot = dict(self.analysis.config_json or {})
            config_snapshot['reports'] = report_paths
            self.analysis.config_json = config_snapshot
            
            self._complete_analysis(len(findings), 'Analysis completed successfully')
            
        except Exception as e:
            logger.error(f"Analysis {self.analysis_id} failed: {str(e)}", exc_info=True)
            self._handle_error(str(e))
            
        finally:
            # Cleanup temporary repository
            if repo_path and os.path.exists(repo_path):
                try:
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up temporary repo at {repo_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup repo: {str(e)}")
    
    def _generate_initial_query(self, repo_path: str) -> str:
        """Generate initial CVE search query based on repository."""
        # TODO: Integrate with react_agent for deeper repo analysis
        # For now, use generic query based on detected technologies
        
        # Simple heuristic: check for common frameworks/languages
        queries = []
        
        if os.path.exists(os.path.join(repo_path, 'package.json')):
            queries.append("JavaScript Node.js web application vulnerabilities")
        if os.path.exists(os.path.join(repo_path, 'requirements.txt')):
            queries.append("Python application security vulnerabilities")
        if os.path.exists(os.path.join(repo_path, 'pom.xml')):
            queries.append("Java application security vulnerabilities")
        if os.path.exists(os.path.join(repo_path, 'go.mod')):
            queries.append("Go application security vulnerabilities")
        
        if queries:
            return " ".join(queries)
        else:
            return "Common web application security vulnerabilities including injection attacks authentication issues and data exposure"
    
    def _create_findings(
        self,
        code_matches: List[Dict[str, Any]],
        cve_query_map: Dict[str, Dict[str, Any]],
        chunks: List[CodeChunk]
    ) -> List[CVEFinding]:
        """Create CVEFinding records from code matches and CVEs."""
        findings = []
        chunk_map = {chunk.chunk_id: chunk for chunk in chunks}
        
        # Group matches by chunk_id to avoid duplicate findings
        chunk_cve_pairs = set()
        
        for match in code_matches:
            chunk_id = match['chunk_id']
            chunk = chunk_map.get(chunk_id)
            
            if not chunk:
                continue
            
            # Find which query matched this code
            # For simplicity, we'll associate with the first CVE from the query map
            # In a more sophisticated implementation, we'd track query->match mapping
            for query, cve in cve_query_map.items():
                pair = (chunk_id, cve['cve_id'])
                if pair in chunk_cve_pairs:
                    continue
                
                chunk_cve_pairs.add(pair)
                
                finding = CVEFinding(
                    analysis_id=self.analysis_id,
                    chunk_id=chunk_id,
                    cve_id=cve['cve_id'],
                    file_path=chunk.file_path,
                    confidence_score=match['similarity_score'] * cve['relevance_score'],
                    validation_status='pending',
                    cve_description=cve['summary']
                )
                db.session.add(finding)
                findings.append(finding)
                
                # Limit findings per chunk
                if len([f for f in findings if f.chunk_id == chunk_id]) >= 3:
                    break
        
        if findings:
            db.session.flush()
        
        return findings
    
    def _complete_analysis(self, total_findings: int, message: str):
        """Complete the analysis successfully."""
        db.session.expire_all()
        self.analysis = db.session.query(Analysis).filter_by(analysis_id=self.analysis_id).first()
        
        self.analysis.status = 'completed'
        self.analysis.end_time = datetime.utcnow()
        self.analysis.total_findings = total_findings
        db.session.commit()
        
        duration = (self.analysis.end_time - self.analysis.start_time).total_seconds()
        logger.info(f"✅ Analysis {self.analysis_id} completed in {duration:.1f}s with {total_findings} findings")
        
        self.emit_progress(100, 'completed', message)
        self.socketio.emit('analysis_complete', {
            'analysis_id': self.analysis_id,
            'duration_seconds': int(duration),
            'total_findings': total_findings,
            'message': message
        }, room=self.room, namespace='/analysis')
    
    def _handle_error(self, error_message: str):
        """Handle analysis error."""
        db.session.rollback()
        db.session.expire_all()
        self.analysis = db.session.query(Analysis).filter_by(analysis_id=self.analysis_id).first()
        
        if self.analysis:
            self.analysis.status = 'failed'
            self.analysis.error_message = error_message
            self.analysis.end_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ COMMITTED STATUS='failed' for analysis {self.analysis_id}")
        
        self.socketio.emit('error', {
            'analysis_id': self.analysis_id,
            'error': error_message,
            'stage': 'analysis_pipeline'
        }, room=self.room, namespace='/analysis')
    
    def emit_progress(self, percentage: int, stage: str, message: str):
        """Emit progress update via SocketIO."""
        self.socketio.emit('progress_update', {
            'analysis_id': self.analysis_id,
            'progress': percentage,
            'stage': stage,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }, room=self.room, namespace='/analysis')
        
        logger.info(f"Analysis {self.analysis_id}: {percentage}% - {stage} - {message}")
    
    def _chunking_progress_callback(self, current: int, total: int):
        """Callback for chunking progress (10% → 20%)."""
        if total > 0:
            progress = 10 + int((current / total) * 10)
            self.emit_progress(progress, 'chunking', f'Processing file {current}/{total}')
    
    def _indexing_progress_callback(self, current: int, total: int):
        """Callback for indexing progress (20% → 35%)."""
        if total > 0:
            progress = 20 + int((current / total) * 15)
            self.emit_progress(progress, 'indexing', f'Indexed {current}/{total} chunks')
    
    def _code_search_progress_callback(self, current: int, total: int):
        """Callback for code search progress (50% → 70%)."""
        if total > 0:
            progress = 50 + int((current / total) * 20)
            self.emit_progress(progress, 'code_search', f'Searched {current}/{total} queries')
    
    def _validation_progress_callback(self, current: int, total: int):
        """Callback for validation progress (75% → 95%)."""
        if total > 0:
            progress = 75 + int((current / total) * 20)
            self.emit_progress(progress, 'validating', f'Validated {current}/{total} findings')    
    def _validation_progress_callback(self, current: int, total: int):
        """Callback for validation progress (75% → 95%)."""
        if total > 0:
            progress = 75 + int((current / total) * 20)
            self.emit_progress(progress, 'validating', f'Validated {current}/{total} findings')
