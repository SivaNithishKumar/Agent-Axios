"""Pytest configuration and fixtures."""
import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, socketio, db
from app.models import Analysis, CodeChunk, CVEFinding, CVEDataset


@pytest.fixture
def app():
    """Create application for testing."""
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    # Create app
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Database tables are already created in create_app
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client."""
    return socketio.test_client(app, namespace='/analysis')


@pytest.fixture
def sample_analysis(app):
    """Create a sample analysis record."""
    with app.app_context():
        analysis = Analysis(
            repo_url='https://github.com/test/repo',
            analysis_type='SHORT',
            status='pending',
            config_json={'test': True}
        )
        db.session.add(analysis)
        db.session.commit()
        return analysis.analysis_id


@pytest.fixture
def completed_analysis(app):
    """Create a completed analysis with findings."""
    with app.app_context():
        # Create analysis
        analysis = Analysis(
            repo_url='https://github.com/test/repo',
            analysis_type='MEDIUM',
            status='completed',
            config_json={'test': True}
        )
        db.session.add(analysis)
        db.session.flush()
        
        # Create code chunk
        chunk = CodeChunk(
            analysis_id=analysis.analysis_id,
            file_path='test.py',
            chunk_text='def test(): pass',
            line_start=1,
            line_end=1,
            language='python'
        )
        db.session.add(chunk)
        db.session.flush()
        
        # Create CVE finding
        finding = CVEFinding(
            analysis_id=analysis.analysis_id,
            cve_id='CVE-2021-44228',
            file_path='test.py',
            chunk_id=chunk.chunk_id,
            severity='CRITICAL',
            confidence_score=0.95,
            validation_status='confirmed',
            cve_description='Log4j vulnerability detected'
        )
        db.session.add(finding)
        db.session.commit()
        
        return analysis.analysis_id


@pytest.fixture
def mock_cohere_embed():
    """Mock Cohere embedding service."""
    with patch('app.services.cohere_service.CohereEmbeddingService.generate_embeddings') as mock:
        mock.return_value = [[0.1] * 1024]  # Mock 1024-dim embedding
        yield mock


@pytest.fixture
def mock_cohere_rerank():
    """Mock Cohere reranking service."""
    with patch('app.services.cohere_service.CohereRerankService.rerank') as mock:
        mock.return_value = [
            {
                'index': 0,
                'relevance_score': 0.95,
                'document': {'text': 'test document'}
            }
        ]
        yield mock


@pytest.fixture
def mock_repo_clone():
    """Mock repository cloning."""
    with patch('app.services.repo_service.RepoService.clone') as mock:
        temp_dir = tempfile.mkdtemp()
        mock.return_value = temp_dir
        yield mock
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@pytest.fixture
def mock_gpt4_validation():
    """Mock GPT-4 validation."""
    with patch('app.services.validation_service.ValidationService._validate_finding') as mock:
        mock.return_value = {
            'is_valid': True,
            'confidence': 0.9,
            'severity': 'HIGH',
            'reasoning': 'Test validation'
        }
        yield mock
