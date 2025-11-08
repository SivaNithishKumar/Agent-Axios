"""Dashboard and analytics routes."""
from flask import Blueprint, request, jsonify
from app.services.auth_service import require_auth, get_current_user
from app.models import Repository, Analysis, CVEFinding, Notification, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/overview', methods=['GET'])
@require_auth
def get_dashboard_overview():
    """Get dashboard overview statistics."""
    try:
        user = get_current_user()
        
        # Repository stats
        repos = db.session.query(Repository).filter_by(user_id=user.user_id).all()
        total_repos = len(repos)
        starred_repos = sum(1 for r in repos if getattr(r, 'is_starred', False))

        # Build list of repository URLs owned by user (avoid relying on a missing FK column)
        repo_urls = [r.url for r in repos]

        # Analysis stats - use repo_url matching since DB may lack analyses.repo_id column
        total_scans = db.session.query(Analysis).filter(Analysis.repo_url.in_(repo_urls)).count() if repo_urls else 0

        active_scans = db.session.query(Analysis).filter(
            Analysis.repo_url.in_(repo_urls),
            Analysis.status.in_(['pending', 'running'])
        ).count() if repo_urls else 0

        completed_scans = db.session.query(Analysis).filter(
            Analysis.repo_url.in_(repo_urls),
            Analysis.status == 'completed'
        ).count() if repo_urls else 0

        failed_scans = db.session.query(Analysis).filter(
            Analysis.repo_url.in_(repo_urls),
            Analysis.status == 'failed'
        ).count() if repo_urls else 0
        
        # Vulnerability stats
        total_vulnerabilities = db.session.query(db.func.sum(Repository.vulnerability_count)).filter(
            Repository.user_id == user.user_id
        ).scalar() or 0
        
        critical_count = db.session.query(db.func.sum(Repository.critical_count)).filter(
            Repository.user_id == user.user_id
        ).scalar() or 0
        
        high_count = db.session.query(db.func.sum(Repository.high_count)).filter(
            Repository.user_id == user.user_id
        ).scalar() or 0
        
        medium_count = db.session.query(db.func.sum(Repository.medium_count)).filter(
            Repository.user_id == user.user_id
        ).scalar() or 0
        
        low_count = db.session.query(db.func.sum(Repository.low_count)).filter(
            Repository.user_id == user.user_id
        ).scalar() or 0
        
        # Notification stats
        unread_notifications = db.session.query(Notification).filter_by(
            user_id=user.user_id, is_read=False
        ).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_scans = db.session.query(Analysis).filter(
            Analysis.repo_url.in_(repo_urls),
            Analysis.created_at >= week_ago
        ).count() if repo_urls else 0
        
        # Get recent repositories
        recent_repos = repos[:5]
        
        # Get recent analyses
        recent_analyses = db.session.query(Analysis).filter(
            Analysis.repo_url.in_(repo_urls)
        ).order_by(Analysis.created_at.desc()).limit(5).all() if repo_urls else []
        
        return jsonify({
            'repositories': {
                'total': total_repos,
                'starred': starred_repos,
                'recent': [r.to_dict() for r in recent_repos]
            },
            'scans': {
                'total': total_scans,
                'active': active_scans,
                'completed': completed_scans,
                'failed': failed_scans,
                'recent_count': recent_scans,
                'recent': [a.to_dict() for a in recent_analyses]
            },
            'vulnerabilities': {
                'total': int(total_vulnerabilities),
                'critical': int(critical_count),
                'high': int(high_count),
                'medium': int(medium_count),
                'low': int(low_count)
            },
            'notifications': {
                'unread': unread_notifications
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard overview'}), 500


@dashboard_bp.route('/analytics', methods=['GET'])
@require_auth
def get_analytics():
    """Get analytics data with time series.
    
    Query params:
    - days: Number of days to look back (default 30)
    """
    try:
        user = get_current_user()
        days = request.args.get('days', 30, type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Scan trends
        scan_history = db.session.query(
            db.func.date(Analysis.created_at).label('date'),
            db.func.count(Analysis.analysis_id).label('count'),
            Analysis.status
        ).join(Repository).filter(
            Repository.user_id == user.user_id,
            Analysis.created_at >= start_date
        ).group_by(
            db.func.date(Analysis.created_at),
            Analysis.status
        ).all()
        
        # Vulnerability trends
        vuln_history = db.session.query(
            db.func.date(Analysis.created_at).label('date'),
            db.func.sum(Analysis.total_findings).label('findings')
        ).join(Repository).filter(
            Repository.user_id == user.user_id,
            Analysis.created_at >= start_date,
            Analysis.status == 'completed'
        ).group_by(
            db.func.date(Analysis.created_at)
        ).all()
        
        # Language distribution
        language_dist = db.session.query(
            Repository.language,
            db.func.count(Repository.repo_id).label('count')
        ).filter(
            Repository.user_id == user.user_id,
            Repository.language.isnot(None)
        ).group_by(Repository.language).all()
        
        return jsonify({
            'scan_trends': [
                {
                    'date': str(s.date),
                    'count': s.count,
                    'status': s.status
                } for s in scan_history
            ],
            'vulnerability_trends': [
                {
                    'date': str(v.date),
                    'findings': int(v.findings) if v.findings else 0
                } for v in vuln_history
            ],
            'language_distribution': [
                {
                    'language': l.language,
                    'count': l.count
                } for l in language_dist
            ],
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500
