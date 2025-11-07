"""WebSocket event handlers for real-time communication."""
from flask_socketio import emit, join_room, leave_room, Namespace
from app import socketio
from app.models import Analysis, db
import logging

logger = logging.getLogger(__name__)

class AnalysisNamespace(Namespace):
    """Namespace for analysis-related WebSocket events."""
    
    def on_connect(self):
        """Handle client connection."""
        logger.info(f"Client connected to /analysis namespace")
        emit('connected', {'message': 'Connected to analysis namespace', 'status': 'ok'})
    
    def on_disconnect(self):
        """Handle client disconnection."""
        logger.info("Client disconnected from /analysis namespace")
    
    def on_start_analysis(self, data):
        """
        Start analysis in background.
        
        Expected data: {'analysis_id': int}
        """
        try:
            analysis_id = data.get('analysis_id')
            
            if not analysis_id:
                emit('error', {'message': 'analysis_id is required'})
                return
            
            # Verify analysis exists
            analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
            
            if not analysis:
                emit('error', {'message': f'Analysis {analysis_id} not found'})
                return
            
            if analysis.status != 'pending':
                emit('error', {'message': f'Analysis {analysis_id} is already {analysis.status}'})
                return
            
            # Join analysis room
            room = f"analysis_{analysis_id}"
            join_room(room)
            
            logger.info(f"Starting analysis {analysis_id} in background")
            
            # Start background analysis task
            from app.services.analysis_orchestrator import AnalysisOrchestrator
            orchestrator = AnalysisOrchestrator(analysis_id, socketio)
            socketio.start_background_task(target=orchestrator.run)
            
            emit('analysis_started', {
                'analysis_id': analysis_id,
                'room': room,
                'message': 'Analysis started'
            })
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {str(e)}")
            emit('error', {'message': str(e)})
    
    def on_get_progress(self, data):
        """
        Get current progress of analysis.
        
        Expected data: {'analysis_id': int}
        """
        try:
            analysis_id = data.get('analysis_id')
            analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
            
            if not analysis:
                emit('error', {'message': 'Analysis not found'})
                return
            
            emit('progress_response', {
                'analysis_id': analysis_id,
                'status': analysis.status,
                'total_files': analysis.total_files,
                'total_chunks': analysis.total_chunks,
                'total_findings': analysis.total_findings
            })
            
        except Exception as e:
            logger.error(f"Failed to get progress: {str(e)}")
            emit('error', {'message': str(e)})

# Register namespace
socketio.on_namespace(AnalysisNamespace('/analysis'))
