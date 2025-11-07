"""API routes for Agent Axios backend."""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models import Analysis, db
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app import socketio
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@api_bp.route('/analysis', methods=['POST'])
def create_analysis():
    """
    Create new analysis.
    
    Expected JSON:
    {
        "repo_url": "https://github.com/user/repo",
        "analysis_type": "SHORT|MEDIUM|HARD",
        "config": {...}
    }
    """
    try:
        data = request.json
        
        if not data or 'repo_url' not in data:
            return jsonify({'error': 'repo_url is required'}), 400
        
        if 'analysis_type' not in data:
            return jsonify({'error': 'analysis_type is required (SHORT/MEDIUM/HARD)'}), 400
        
        repo_url = data['repo_url']
        analysis_type = data['analysis_type'].upper()
        config_json = data.get('config', {})
        
        if analysis_type not in ['SHORT', 'MEDIUM', 'HARD']:
            return jsonify({'error': 'analysis_type must be SHORT, MEDIUM, or HARD'}), 400
        
        # Create analysis record
        analysis = Analysis(
            repo_url=repo_url,
            analysis_type=analysis_type,
            status='pending',
            config_json=config_json
        )
        db.session.add(analysis)
        db.session.commit()
        
        logger.info(f"Created analysis {analysis.analysis_id} for {repo_url} ({analysis_type})")
        
        return jsonify(analysis.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Failed to create analysis: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get analysis by ID."""
    try:
        analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        return jsonify(analysis.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to get analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analysis/<int:analysis_id>/results', methods=['GET'])
def get_analysis_results(analysis_id):
    """Get detailed analysis results."""
    try:
        from app.models import CVEFinding
        
        analysis = db.session.query(Analysis).filter_by(analysis_id=analysis_id).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if analysis.status != 'completed':
            return jsonify({'error': 'Analysis not completed yet'}), 400
        
        # Get findings
        findings = db.session.query(CVEFinding).filter_by(analysis_id=analysis_id).all()
        
        # Calculate summary
        confirmed = [f for f in findings if f.validation_status == 'confirmed']
        by_severity = {}
        for finding in confirmed:
            severity = finding.severity or 'unknown'
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        result = {
            'analysis': analysis.to_dict(),
            'summary': {
                'total_files': analysis.total_files,
                'total_chunks': analysis.total_chunks,
                'total_findings': len(findings),
                'confirmed_vulnerabilities': len(confirmed),
                'false_positives': len([f for f in findings if f.validation_status == 'false_positive']),
                'severity_breakdown': by_severity
            },
            'findings': [f.to_dict() for f in findings[:100]]  # Limit to first 100
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Failed to get results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyses', methods=['GET'])
def list_analyses():
    """List all analyses with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        query = db.session.query(Analysis)
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(Analysis.created_at.desc())
        
        # Pagination
        total = query.count()
        analyses = query.limit(per_page).offset((page - 1) * per_page).all()
        
        return jsonify({
            'analyses': [a.to_dict() for a in analyses],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}")
        return jsonify({'error': str(e)}), 500
