"""Tests for API routes."""
import json
import pytest
from app.models import Analysis, db


class TestHealthEndpoint:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test GET /health endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        print(f"✓ Health check passed: {data}")
    
    def test_api_health_check(self, client):
        """Test GET /api/health endpoint."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        print(f"✓ API health check passed: {data}")


class TestAnalysisCreation:
    """Test analysis creation endpoints."""
    
    def test_create_analysis_success(self, client, app):
        """Test POST /api/analysis with valid data."""
        payload = {
            'repo_url': 'https://github.com/test/repo',
            'analysis_type': 'SHORT',
            'config': {'test': True}
        }
        
        response = client.post(
            '/api/analysis',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'analysis_id' in data
        assert data['repo_url'] == payload['repo_url']
        assert data['analysis_type'] == 'SHORT'
        assert data['status'] == 'pending'
        
        # Verify database record
        with app.app_context():
            analysis = db.session.query(Analysis).filter_by(
                analysis_id=data['analysis_id']
            ).first()
            assert analysis is not None
            assert analysis.repo_url == payload['repo_url']
    
    def test_create_analysis_missing_repo_url(self, client):
        """Test POST /api/analysis without repo_url."""
        payload = {
            'analysis_type': 'SHORT'
        }
        
        response = client.post(
            '/api/analysis',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'repo_url' in data['error']
    
    def test_create_analysis_missing_type(self, client):
        """Test POST /api/analysis without analysis_type."""
        payload = {
            'repo_url': 'https://github.com/test/repo'
        }
        
        response = client.post(
            '/api/analysis',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'analysis_type' in data['error']
    
    def test_create_analysis_invalid_type(self, client):
        """Test POST /api/analysis with invalid analysis_type."""
        payload = {
            'repo_url': 'https://github.com/test/repo',
            'analysis_type': 'INVALID'
        }
        
        response = client.post(
            '/api/analysis',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'SHORT, MEDIUM, or HARD' in data['error']
    
    def test_create_analysis_all_types(self, client, app):
        """Test creating analyses with all three types."""
        for analysis_type in ['SHORT', 'MEDIUM', 'HARD']:
            payload = {
                'repo_url': f'https://github.com/test/{analysis_type.lower()}',
                'analysis_type': analysis_type
            }
            
            response = client.post(
                '/api/analysis',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['analysis_type'] == analysis_type


class TestAnalysisRetrieval:
    """Test analysis retrieval endpoints."""
    
    def test_get_analysis_by_id(self, client, sample_analysis):
        """Test GET /api/analysis/<id>."""
        response = client.get(f'/api/analysis/{sample_analysis}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['analysis_id'] == sample_analysis
        assert data['repo_url'] == 'https://github.com/test/repo'
        assert data['analysis_type'] == 'SHORT'
        assert data['status'] == 'pending'
    
    def test_get_analysis_not_found(self, client):
        """Test GET /api/analysis/<id> with non-existent ID."""
        response = client.get('/api/analysis/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_get_analysis_results_success(self, client, completed_analysis):
        """Test GET /api/analysis/<id>/results for completed analysis."""
        response = client.get(f'/api/analysis/{completed_analysis}/results')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'analysis' in data
        assert 'findings' in data
        assert 'summary' in data
        assert len(data['findings']) > 0
        assert data['findings'][0]['cve_id'] == 'CVE-2021-44228'
    
    def test_get_analysis_results_not_completed(self, client, sample_analysis):
        """Test GET /api/analysis/<id>/results for pending analysis."""
        response = client.get(f'/api/analysis/{sample_analysis}/results')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not completed' in data['error'].lower()
    
    def test_get_analysis_results_not_found(self, client):
        """Test GET /api/analysis/<id>/results with non-existent ID."""
        response = client.get('/api/analysis/99999/results')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestAnalysisList:
    """Test analysis listing endpoints."""
    
    def test_list_analyses(self, client, app):
        """Test GET /api/analyses to list all analyses."""
        # Create multiple analyses
        with app.app_context():
            for i in range(3):
                analysis = Analysis(
                    repo_url=f'https://github.com/test/repo{i}',
                    analysis_type='SHORT',
                    status='pending'
                )
                db.session.add(analysis)
            db.session.commit()
        
        response = client.get('/api/analyses')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'analyses' in data
        assert len(data['analyses']) >= 3
    
    def test_list_analyses_empty(self, client):
        """Test GET /api/analyses with no analyses."""
        response = client.get('/api/analyses')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'analyses' in data
        assert isinstance(data['analyses'], list)


class TestAnalysisReport:
    """Test analysis report endpoints."""
    
    def test_get_report_success(self, client, completed_analysis):
        """Test GET /api/analysis/<id>/report."""
        response = client.get(f'/api/analysis/{completed_analysis}/report')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'report' in data
        assert 'analysis_id' in data['report']
        assert 'findings' in data['report']
    
    def test_get_report_not_completed(self, client, sample_analysis):
        """Test GET /api/analysis/<id>/report for pending analysis."""
        response = client.get(f'/api/analysis/{sample_analysis}/report')
        
        # Should return 400 or 404 depending on implementation
        assert response.status_code in [400, 404]
