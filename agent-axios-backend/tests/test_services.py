"""Tests for service layer."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestCohereEmbeddingService:
    """Test CohereEmbeddingService."""
    
    @patch('app.services.cohere_service.cohere.Client')
    def test_generate_embeddings(self, mock_client):
        """Test embedding generation."""
        from app.services.cohere_service import CohereEmbeddingService
        
        # Mock response
        mock_response = Mock()
        mock_response.embeddings.float = [[0.1] * 1024, [0.2] * 1024]
        mock_client.return_value.embed.return_value = mock_response
        
        service = CohereEmbeddingService()
        embeddings = service.generate_embeddings(['text1', 'text2'])
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1024
    
    @patch('app.services.cohere_service.cohere.Client')
    def test_generate_embeddings_retry(self, mock_client):
        """Test embedding generation with retry logic."""
        from app.services.cohere_service import CohereEmbeddingService
        
        # Mock to fail twice then succeed
        mock_response = Mock()
        mock_response.embeddings.float = [[0.1] * 1024]
        mock_client.return_value.embed.side_effect = [
            Exception("API Error"),
            Exception("API Error"),
            mock_response
        ]
        
        service = CohereEmbeddingService()
        embeddings = service.generate_embeddings(['text1'])
        
        assert len(embeddings) == 1
        assert mock_client.return_value.embed.call_count == 3


class TestCohereRerankService:
    """Test CohereRerankService."""
    
    @patch('app.services.cohere_service.cohere.Client')
    def test_rerank(self, mock_client):
        """Test reranking."""
        from app.services.cohere_service import CohereRerankService
        
        # Mock response
        mock_result = Mock()
        mock_result.index = 0
        mock_result.relevance_score = 0.95
        mock_result.document = Mock(text='test doc')
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        mock_client.return_value.rerank.return_value = mock_response
        
        service = CohereRerankService()
        results = service.rerank('query', ['doc1', 'doc2'], top_n=1)
        
        assert len(results) == 1
        assert results[0]['relevance_score'] == 0.95


class TestFAISSManager:
    """Test FAISS index manager."""
    
    def test_add_vectors(self, app, tmp_path):
        """Test adding vectors to FAISS index."""
        from app.services.faiss_manager import FAISSIndexManager
        import os
        
        # Use temporary path
        index_path = str(tmp_path / 'test.faiss')
        
        manager = FAISSIndexManager(dimension=128, index_path=index_path)
        
        vectors = np.random.rand(5, 128).astype('float32')
        metadata = [{'id': i} for i in range(5)]
        
        ids = manager.add_vectors(vectors, metadata)
        
        assert len(ids) == 5
        assert manager.index.ntotal == 5
    
    def test_search_vectors(self, app, tmp_path):
        """Test searching FAISS index."""
        from app.services.faiss_manager import FAISSIndexManager
        
        index_path = str(tmp_path / 'test.faiss')
        manager = FAISSIndexManager(dimension=128, index_path=index_path)
        
        # Add vectors
        vectors = np.random.rand(10, 128).astype('float32')
        metadata = [{'id': i} for i in range(10)]
        manager.add_vectors(vectors, metadata)
        
        # Search
        query = np.random.rand(1, 128).astype('float32')
        results = manager.search(query, k=3)
        
        assert len(results) == 3
        assert all('distance' in r for r in results)
        assert all('metadata' in r for r in results)


class TestRepoService:
    """Test RepoService."""
    
    @patch('app.services.repo_service.git.Repo.clone_from')
    def test_clone_repository(self, mock_clone):
        """Test repository cloning."""
        from app.services.repo_service import RepoService
        import tempfile
        
        temp_dir = tempfile.mkdtemp()
        mock_clone.return_value = Mock()
        
        service = RepoService()
        result = service.clone('https://github.com/test/repo')
        
        assert result is not None
        mock_clone.assert_called_once()
    
    def test_get_metadata(self, tmp_path):
        """Test getting repository metadata."""
        from app.services.repo_service import RepoService
        
        # Create dummy files
        (tmp_path / 'test.py').write_text('print("hello")')
        (tmp_path / 'test.js').write_text('console.log("hello")')
        
        service = RepoService()
        metadata = service.get_metadata(str(tmp_path))
        
        assert 'file_count' in metadata
        assert 'languages' in metadata
        assert metadata['file_count'] >= 2


class TestChunkingService:
    """Test ChunkingService."""
    
    def test_chunk_python_file(self, tmp_path):
        """Test chunking a Python file."""
        from app.services.chunking_service import ChunkingService
        
        # Create test file
        test_file = tmp_path / 'test.py'
        test_file.write_text('''
def function1():
    pass

def function2():
    pass

class TestClass:
    def method1(self):
        pass
''')
        
        service = ChunkingService()
        chunks = service.chunk_file(str(test_file), 'python')
        
        assert len(chunks) > 0
        assert all('text' in chunk for chunk in chunks)
        assert all('line_start' in chunk for chunk in chunks)


class TestEmbeddingService:
    """Test EmbeddingService."""
    
    @patch('app.services.embedding_service.CohereEmbeddingService')
    @patch('app.services.embedding_service.CodebaseIndexManager')
    def test_embed_chunks(self, mock_faiss, mock_cohere, app, sample_analysis):
        """Test embedding generation for chunks."""
        from app.services.embedding_service import EmbeddingService
        from app.models import CodeChunk, db
        
        # Setup mocks
        mock_cohere.return_value.generate_embeddings.return_value = [[0.1] * 1024]
        mock_faiss.return_value.add_vectors.return_value = [0]
        
        with app.app_context():
            # Create test chunk
            chunk = CodeChunk(
                analysis_id=sample_analysis,
                file_path='test.py',
                chunk_text='def test(): pass',
                line_start=1,
                line_end=1
            )
            db.session.add(chunk)
            db.session.commit()
            
            chunks = [chunk]
            
            service = EmbeddingService()
            service.embed_chunks(chunks)
            
            # Verify embedding was called
            assert mock_cohere.return_value.generate_embeddings.called


class TestValidationService:
    """Test ValidationService."""
    
    @patch('app.services.validation_service.AzureChatOpenAI')
    def test_validate_finding(self, mock_llm, app, sample_analysis):
        """Test CVE finding validation."""
        from app.services.validation_service import ValidationService
        from app.models import CVEFinding, db
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = '{"is_valid": true, "confidence": 0.9, "severity": "HIGH", "reasoning": "Test"}'
        mock_llm.return_value.invoke.return_value = mock_response
        
        with app.app_context():
            finding = CVEFinding(
                analysis_id=sample_analysis,
                cve_id='CVE-2021-44228',
                file_path='test.py',
                severity='CRITICAL',
                confidence_score=0.85
            )
            db.session.add(finding)
            db.session.commit()
            
            service = ValidationService()
            result = service.validate_finding_by_id(finding.finding_id)
            
            assert result is True or isinstance(result, bool)
