"""Tests for database models."""
import pytest
from datetime import datetime
from app.models import Analysis, CodeChunk, CVEFinding, CVEDataset, db


class TestAnalysisModel:
    """Test Analysis model."""
    
    def test_create_analysis(self, app):
        """Test creating an analysis record."""
        with app.app_context():
            analysis = Analysis(
                repo_url='https://github.com/test/repo',
                analysis_type='SHORT',
                status='pending',
                config_json={'test': True}
            )
            db.session.add(analysis)
            db.session.commit()
            
            assert analysis.analysis_id is not None
            assert analysis.repo_url == 'https://github.com/test/repo'
            assert analysis.analysis_type == 'SHORT'
            assert analysis.status == 'pending'
            assert analysis.start_time is not None
    
    def test_analysis_to_dict(self, app):
        """Test Analysis.to_dict() method."""
        with app.app_context():
            analysis = Analysis(
                repo_url='https://github.com/test/repo',
                analysis_type='MEDIUM',
                status='completed'
            )
            db.session.add(analysis)
            db.session.commit()
            
            data = analysis.to_dict()
            assert 'analysis_id' in data
            assert data['repo_url'] == 'https://github.com/test/repo'
            assert data['analysis_type'] == 'MEDIUM'
            assert data['status'] == 'completed'


class TestCodeChunkModel:
    """Test CodeChunk model."""
    
    def test_create_code_chunk(self, app, sample_analysis):
        """Test creating a code chunk."""
        with app.app_context():
            chunk = CodeChunk(
                analysis_id=sample_analysis,
                file_path='test.py',
                chunk_text='def test(): pass',
                line_start=1,
                line_end=5,
                language='python'
            )
            db.session.add(chunk)
            db.session.commit()
            
            assert chunk.chunk_id is not None
            assert chunk.file_path == 'test.py'
            assert chunk.language == 'python'
            assert chunk.line_start == 1
            assert chunk.line_end == 5
    
    def test_code_chunk_relationship(self, app, sample_analysis):
        """Test CodeChunk relationship with Analysis."""
        with app.app_context():
            analysis = db.session.query(Analysis).filter_by(
                analysis_id=sample_analysis
            ).first()
            
            chunk = CodeChunk(
                analysis_id=sample_analysis,
                file_path='test.py',
                chunk_text='def test(): pass',
                line_start=1,
                line_end=5
            )
            db.session.add(chunk)
            db.session.commit()
            
            assert len(analysis.code_chunks) > 0
            assert analysis.code_chunks[0].file_path == 'test.py'


class TestCVEFindingModel:
    """Test CVEFinding model."""
    
    def test_create_cve_finding(self, app, sample_analysis):
        """Test creating a CVE finding."""
        with app.app_context():
            finding = CVEFinding(
                analysis_id=sample_analysis,
                cve_id='CVE-2021-44228',
                file_path='test.py',
                chunk_id=1,
                severity='CRITICAL',
                confidence_score=0.95
            )
            db.session.add(finding)
            db.session.commit()
            
            assert finding.finding_id is not None
            assert finding.cve_id == 'CVE-2021-44228'
            assert finding.severity == 'CRITICAL'
            assert finding.confidence_score == 0.95
    
    def test_cve_finding_to_dict(self, app, sample_analysis):
        """Test CVEFinding.to_dict() method."""
        with app.app_context():
            finding = CVEFinding(
                analysis_id=sample_analysis,
                cve_id='CVE-2021-44228',
                file_path='test.py',
                severity='HIGH',
                confidence_score=0.85
            )
            db.session.add(finding)
            db.session.commit()
            
            data = finding.to_dict()
            assert 'finding_id' in data
            assert data['cve_id'] == 'CVE-2021-44228'
            assert data['severity'] == 'HIGH'


class TestCVEDatasetModel:
    """Test CVEDataset model."""
    
    def test_create_cve_dataset(self, app):
        """Test creating a CVE dataset entry."""
        with app.app_context():
            from datetime import datetime
            import uuid
            # Use unique CVE ID to avoid conflicts
            unique_cve_id = f'CVE-TEST-{uuid.uuid4().hex[:8].upper()}'
            cve = CVEDataset(
                cve_id=unique_cve_id,
                cve_json=f'{{"id": "{unique_cve_id}"}}',
                description='Test vulnerability for dataset',
                severity='HIGH',
                cvss_score=8.5,
                last_updated=datetime.utcnow()
            )
            db.session.add(cve)
            db.session.commit()
            
            assert cve.cve_id == unique_cve_id
            assert cve.severity == 'HIGH'
            assert cve.cvss_score == 8.5
