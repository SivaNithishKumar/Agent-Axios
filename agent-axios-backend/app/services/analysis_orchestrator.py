"""Analysis orchestrator - coordinates the entire analysis pipeline with LangSmith tracking."""
import os
import shutil
import time
from datetime import datetime
from langsmith import traceable
from app.models import Analysis, CVEFinding, db
from app.services.repo_service import RepoService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.cve_search_service import CVESearchService
from app.services.validation_service import ValidationService
from app.services.report_service import ReportService
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """Orchestrates the full vulnerability analysis pipeline."""
    
    def __init__(self, analysis_id: int, socketio_instance):
        self.analysis_id = analysis_id
        self.socketio = socketio_instance
        self.analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
        if not self.analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        self.room = f"analysis_{analysis_id}"
        self.repo_service = RepoService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.cve_search_service = CVESearchService()
        self.validation_service = ValidationService()
        self.report_service = ReportService()
        
        # Get analysis type config
        self.config = Config.ANALYSIS_CONFIGS.get(self.analysis.analysis_type, Config.ANALYSIS_CONFIGS['MEDIUM'])
        
        logger.info(f"Initialized orchestrator for analysis {analysis_id} ({self.analysis.analysis_type})")
    
    @traceable(name="full_analysis_pipeline", run_type="chain")
    def run(self):
        """Execute the full analysis pipeline."""
        repo_path = None
        
        try:
            self.analysis.status = 'running'
            self.analysis.start_time = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Starting analysis {self.analysis_id}: {self.analysis.repo_url}")
            
            # Step 1: Clone repository (0% → 20%)
            self.emit_progress(0, 'cloning', 'Cloning repository...')
            repo_path = self.repo_service.clone(self.analysis.repo_url)
            self.emit_progress(20, 'cloning', 'Repository cloned successfully')
            time.sleep(1)  # Brief pause for user to see status
            
            # Step 2: Chunk files (20% → 35%)
            self.emit_progress(20, 'chunking', 'Parsing and chunking code files...')
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
            self.emit_progress(35, 'chunking', f'Chunked {len(chunks)} code segments')
            
            # Step 3: Generate embeddings (35% → 55%)
            self.emit_progress(35, 'embedding', 'Generating code embeddings...')
            self.embedding_service.embed_chunks(
                chunks,
                progress_callback=self._embedding_progress_callback
            )
            db.session.commit()
            self.emit_progress(55, 'embedding', 'Embeddings generated successfully')
            
            # Step 4: Search CVEs (55% → 75%)
            self.emit_progress(55, 'searching', 'Searching for vulnerabilities...')
            findings = self.cve_search_service.search_all_chunks(
                chunks,
                faiss_top_k=self.config['faiss_top_k'],
                rerank_top_n=self.config['rerank_top_n'],
                progress_callback=self._search_progress_callback
            )
            db.session.flush()
            findings = db.session.query(CVEFinding).filter_by(analysis_id=self.analysis_id).all()
            self.analysis.total_findings = len(findings)
            db.session.commit()
            self.emit_progress(75, 'searching', f'Found {self.analysis.total_findings} potential vulnerabilities')
            
            # Step 5: Validate with GPT-4.1 (75% → 95%)
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
            
            # Step 6: Finalize (95% → 100%)
            self.emit_progress(95, 'finalizing', 'Generating reports and finalizing results...')

            report_paths = self.report_service.generate_reports(self.analysis_id)
            config_snapshot = dict(self.analysis.config_json or {})
            config_snapshot['reports'] = report_paths
            self.analysis.config_json = config_snapshot
            self.analysis.status = 'completed'
            self.analysis.end_time = datetime.utcnow()
            db.session.commit()
            
            duration = (self.analysis.end_time - self.analysis.start_time).total_seconds()
            logger.info(f"Analysis {self.analysis_id} completed in {duration:.1f}s")
            
            self.emit_progress(100, 'completed', 'Analysis complete!')
            self.socketio.emit('analysis_complete', {
                'analysis_id': self.analysis_id,
                'duration_seconds': int(duration),
                'total_findings': self.analysis.total_findings
            }, room=self.room, namespace='/analysis')
            
        except Exception as e:
            logger.error(f"Analysis {self.analysis_id} failed: {str(e)}", exc_info=True)
            db.session.rollback()
            self.analysis.status = 'failed'
            self.analysis.error_message = str(e)
            self.analysis.end_time = datetime.utcnow()
            db.session.commit()
            
            self.socketio.emit('error', {
                'analysis_id': self.analysis_id,
                'error': str(e),
                'stage': 'analysis_pipeline'
            }, room=self.room, namespace='/analysis')
            
        finally:
            # Cleanup temporary repository
            if repo_path and os.path.exists(repo_path):
                try:
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up temporary repo at {repo_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup repo: {str(e)}")
    
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
        """Callback for chunking progress (20% → 35%)."""
        if total > 0:
            progress = 20 + int((current / total) * 15)
            self.emit_progress(progress, 'chunking', f'Processing file {current}/{total}')
    
    def _embedding_progress_callback(self, current: int, total: int):
        """Callback for embedding progress (35% → 55%)."""
        if total > 0:
            progress = 35 + int((current / total) * 20)
            self.emit_progress(progress, 'embedding', f'Embedded {current}/{total} chunks')
    
    def _search_progress_callback(self, current: int, total: int):
        """Callback for search progress (55% → 75%)."""
        if total > 0:
            progress = 55 + int((current / total) * 20)
            self.emit_progress(progress, 'searching', f'Searched {current}/{total} chunks')
    
    def _validation_progress_callback(self, current: int, total: int):
        """Callback for validation progress (75% → 95%)."""
        if total > 0:
            progress = 75 + int((current / total) * 20)
            self.emit_progress(progress, 'validating', f'Validated {current}/{total} findings')
