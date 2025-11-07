# Agent Axios Backend - Strategic Implementation Todo List

**Project Goal:** Build production-ready backend with Azure Cohere embeddings/reranker + Flask-SocketIO + FAISS + SQLite

**Timeline:** 6 weeks (150-180 hours total effort)

**Current Phase:** Research & Planning ✅ → Setup & Infrastructure (Next)

---

## Phase 1: Foundation Setup (Week 1) - 25 hours

### 1.1 Project Initialization ⏳ NEXT
**Priority:** CRITICAL | **Time Estimate:** 2 hours | **Dependencies:** None

**Tasks:**
- [ ] Create `agent-axios-backend/` directory structure
  ```
  agent-axios-backend/
  ├── app/
  │   ├── __init__.py
  │   ├── routes/
  │   ├── services/
  │   ├── models/
  │   └── utils/
  ├── config/
  │   ├── __init__.py
  │   └── settings.py
  ├── tests/
  ├── migrations/
  ├── .env.example
  ├── .gitignore
  ├── requirements.txt
  └── README.md
  ```
- [ ] Initialize git repository (separate from Agent-Axios main repo)
- [ ] Create `.env.example` with all required environment variables
- [ ] Setup Python 3.10 virtual environment

**Acceptance Criteria:**
- Directory structure matches above schema
- Virtual environment activates without errors
- `.gitignore` excludes `.env`, `__pycache__`, `*.pyc`, `venv/`

**Code Snippet:**
```bash
mkdir -p agent-axios-backend/{app/{routes,services,models,utils},config,tests,migrations}
cd agent-axios-backend
python3.10 -m venv venv
source venv/bin/activate
git init
```

---

### 1.2 Dependency Installation ⏳
**Priority:** CRITICAL | **Time Estimate:** 1.5 hours | **Dependencies:** 1.1

**Tasks:**
- [ ] Create `requirements.txt` with pinned versions:
  ```
  flask==3.0.0
  flask-socketio==5.3.5
  eventlet==0.35.2
  flask-cors==4.0.0
  sqlalchemy==2.0.23
  alembic==1.13.1
  faiss-cpu==1.7.4
  cohere==4.37
  python-dotenv==1.0.0
  pydantic==2.5.3
  pandas==2.1.4
  numpy==1.24.4
  requests==2.31.0
  pytest==7.4.3
  pytest-cov==4.1.0
  black==23.12.1
  flake8==6.1.0
  ```
- [ ] Install all dependencies: `pip install -r requirements.txt`
- [ ] Create `requirements-dev.txt` for development tools
- [ ] Verify imports work: `python -c "import flask, flask_socketio, faiss, cohere, sqlalchemy"`

**Acceptance Criteria:**
- All packages install without conflicts
- Import verification passes
- `pip list` shows all packages with correct versions

---

### 1.3 Configuration Management ⏳
**Priority:** HIGH | **Time Estimate:** 2 hours | **Dependencies:** 1.2

**Tasks:**
- [ ] Create `config/settings.py` with environment-based configuration
- [ ] Implement `Config`, `DevelopmentConfig`, `ProductionConfig` classes
- [ ] Add Azure Cohere credentials loading from `.env`
- [ ] Add database URL configuration (SQLite path)
- [ ] Add FAISS index paths configuration
- [ ] Add Flask-SocketIO settings (CORS, async_mode)

**Code Template:**
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///agent_axios.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Azure Cohere
    COHERE_EMBED_ENDPOINT = os.getenv('COHERE_EMBED_ENDPOINT')
    COHERE_EMBED_API_KEY = os.getenv('COHERE_EMBED_API_KEY')
    COHERE_EMBED_MODEL = "Cohere-embed-v3-english"
    COHERE_EMBED_DIMENSIONS = 1024
    
    COHERE_RERANK_ENDPOINT = os.getenv('COHERE_RERANK_ENDPOINT')
    COHERE_RERANK_API_KEY = os.getenv('COHERE_RERANK_API_KEY')
    COHERE_RERANK_MODEL = "Rerank-v3-5"
    
    # FAISS
    CVE_FAISS_INDEX_PATH = "data/cve_index.faiss"
    CODEBASE_FAISS_INDEX_PATH = "data/codebase_index.faiss"
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'eventlet'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"  # Restrict in production

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv('FRONTEND_URL', 'http://localhost:3000')
```

**Acceptance Criteria:**
- Configuration loads without errors
- All Azure credentials are retrieved from environment
- Development/Production configs can be switched via `FLASK_ENV`

---

### 1.4 Database Models Setup ⏳
**Priority:** HIGH | **Time Estimate:** 3 hours | **Dependencies:** 1.3

**Tasks:**
- [ ] Create SQLAlchemy models in `app/models/`
- [ ] Implement `Analysis` model with status tracking
- [ ] Implement `CodeChunk` model with file path and line numbers
- [ ] Implement `CVEFinding` model with severity and confidence
- [ ] Implement `CVEDataset` model with FAISS vector ID reference
- [ ] Add model relationships (foreign keys)
- [ ] Create Alembic migration scripts

**Code Template:**
```python
# app/models/analysis.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class Analysis(Base):
    __tablename__ = 'analyses'
    
    analysis_id = Column(Integer, primary_key=True)
    repo_url = Column(String(500), nullable=False)
    analysis_type = Column(String(20), nullable=False)  # SHORT, MEDIUM, HARD
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    config_json = Column(JSON, nullable=True)
    
    # Relationships
    code_chunks = relationship('CodeChunk', back_populates='analysis', cascade='all, delete-orphan')
    cve_findings = relationship('CVEFinding', back_populates='analysis', cascade='all, delete-orphan')
```

**Acceptance Criteria:**
- All 4 models defined with proper types
- Relationships work correctly (test with `analysis.code_chunks`)
- Alembic migration runs: `alembic upgrade head`
- Database file created: `agent_axios.db`

---

### 1.5 Flask Application Bootstrap ⏳
**Priority:** CRITICAL | **Time Estimate:** 2 hours | **Dependencies:** 1.4

**Tasks:**
- [ ] Create `app/__init__.py` with Flask app factory
- [ ] Initialize Flask-SocketIO with eventlet async mode
- [ ] Configure CORS for frontend communication
- [ ] Initialize SQLAlchemy database connection
- [ ] Register blueprints for API routes
- [ ] Add health check endpoint: `GET /health`

**Code Template:**
```python
# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from app.models.base import db
from config.settings import DevelopmentConfig

socketio = SocketIO()

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/*": {"origins": app.config['SOCKETIO_CORS_ALLOWED_ORIGINS']}})
    socketio.init_app(app, 
                     cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
                     async_mode=app.config['SOCKETIO_ASYNC_MODE'])
    
    # Register blueprints
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    
    return app
```

**Acceptance Criteria:**
- Flask app starts without errors: `flask run`
- Health check endpoint returns 200: `curl http://localhost:5000/health`
- SocketIO server initializes with eventlet async mode

---

### 1.6 Cohere Service Implementation 🔴 CRITICAL
**Priority:** CRITICAL | **Time Estimate:** 4 hours | **Dependencies:** 1.3

**Tasks:**
- [ ] Create `app/services/cohere_service.py`
- [ ] Implement `CohereEmbeddingService` class
  - `generate_embeddings(texts: List[str], input_type: str) -> List[List[float]]`
  - Add error handling and retry logic (3 retries with exponential backoff)
  - Add rate limiting (10 requests/second)
  - Log embedding dimensions and API latency
- [ ] Implement `CohereRerankService` class
  - `rerank(query: str, documents: List[str], top_n: int) -> List[Dict]`
  - Add error handling for API failures
  - Log reranking scores and processing time
- [ ] Write unit tests with mocked API responses

**Code Template:**
```python
# app/services/cohere_service.py
import cohere
import time
from typing import List, Dict
from config.settings import Config

class CohereEmbeddingService:
    def __init__(self):
        self.client = cohere.Client(
            api_key=Config.COHERE_EMBED_API_KEY,
            base_url=Config.COHERE_EMBED_ENDPOINT
        )
        self.model = Config.COHERE_EMBED_MODEL
        self.dimensions = Config.COHERE_EMBED_DIMENSIONS
    
    def generate_embeddings(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """Generate embeddings with retry logic."""
        for attempt in range(3):
            try:
                response = self.client.v2.embed(
                    texts=texts,
                    model=self.model,
                    input_type=input_type,
                    embedding_types=["float"],
                    truncate="END"
                )
                embeddings = response.embeddings.float
                assert len(embeddings) == len(texts), "Embedding count mismatch"
                assert len(embeddings[0]) == self.dimensions, "Dimension mismatch"
                return embeddings
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

class CohereRerankService:
    def __init__(self):
        self.client = cohere.Client(
            api_key=Config.COHERE_RERANK_API_KEY,
            base_url=Config.COHERE_RERANK_ENDPOINT
        )
        self.model = Config.COHERE_RERANK_MODEL
    
    def rerank(self, query: str, documents: List[str], top_n: int = 10) -> List[Dict]:
        """Rerank documents by relevance."""
        response = self.client.v2.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n,
            return_documents=True
        )
        return [
            {
                'index': result.index,
                'text': result.document.text,
                'relevance_score': result.relevance_score
            }
            for result in response.results
        ]
```

**Acceptance Criteria:**
- Embedding generation returns correct dimensions (1024)
- Retry logic works (mock API failure scenarios)
- Reranker returns top N documents with scores
- Unit tests achieve >90% coverage

---

### 1.7 FAISS Index Manager Implementation 🔴 CRITICAL
**Priority:** CRITICAL | **Time Estimate:** 4 hours | **Dependencies:** 1.6

**Tasks:**
- [ ] Create `app/services/faiss_manager.py`
- [ ] Implement `FAISSIndexManager` base class
- [ ] Implement `CVEIndexManager` (inherits from base)
  - `add_vectors(vectors: np.ndarray, metadata: List[Dict]) -> List[int]`
  - `search(query_vector: np.ndarray, top_k: int) -> List[Dict]`
  - `save_index(path: str)` and `load_index(path: str)`
- [ ] Implement `CodebaseIndexManager` (inherits from base)
- [ ] Add index persistence logic (auto-save every 100 additions)
- [ ] Write unit tests with sample vectors

**Code Template:**
```python
# app/services/faiss_manager.py
import faiss
import numpy as np
import pickle
from typing import List, Dict
from config.settings import Config

class FAISSIndexManager:
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []  # Store metadata separately
        self.load_index()
    
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict]) -> List[int]:
        """Add vectors to FAISS index."""
        assert vectors.shape[1] == self.dimension, f"Vector dimension mismatch: {vectors.shape[1]} != {self.dimension}"
        
        start_id = self.index.ntotal
        self.index.add(vectors.astype('float32'))
        
        # Store metadata with FAISS vector IDs
        vector_ids = list(range(start_id, start_id + len(vectors)))
        for vid, meta in zip(vector_ids, metadata):
            self.metadata.append({'faiss_id': vid, **meta})
        
        # Auto-save every 100 additions
        if len(self.metadata) % 100 == 0:
            self.save_index()
        
        return vector_ids
    
    def search(self, query_vector: np.ndarray, top_k: int = 50) -> List[Dict]:
        """Search for similar vectors."""
        query_vector = query_vector.astype('float32').reshape(1, -1)
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):  # Valid index
                results.append({
                    'faiss_id': int(idx),
                    'distance': float(dist),
                    **self.metadata[idx]
                })
        return results
    
    def save_index(self):
        """Persist index and metadata."""
        faiss.write_index(self.index, self.index_path)
        with open(f"{self.index_path}.metadata", 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load_index(self):
        """Load existing index and metadata."""
        try:
            self.index = faiss.read_index(self.index_path)
            with open(f"{self.index_path}.metadata", 'rb') as f:
                self.metadata = pickle.load(f)
        except FileNotFoundError:
            pass  # New index

class CVEIndexManager(FAISSIndexManager):
    def __init__(self):
        super().__init__(Config.COHERE_EMBED_DIMENSIONS, Config.CVE_FAISS_INDEX_PATH)
```

**Acceptance Criteria:**
- Index adds vectors correctly (test with 100 random vectors)
- Search returns top K results with distances
- Index persists to disk and loads correctly
- Metadata correctly maps to FAISS vector IDs

---

### 1.8 Flask-SocketIO Event Handlers 🔴 CRITICAL
**Priority:** HIGH | **Time Estimate:** 3 hours | **Dependencies:** 1.5

**Tasks:**
- [ ] Create `app/routes/socketio_events.py`
- [ ] Implement `/analysis` namespace
- [ ] Add event handlers:
  - `connect`: Client connection handling
  - `disconnect`: Cleanup resources
  - `start_analysis`: Trigger analysis and return analysis_id
  - `get_progress`: Fetch current progress
- [ ] Implement room management (one room per analysis)
- [ ] Add background task wrapper for long-running analysis

**Code Template:**
```python
# app/routes/socketio_events.py
from flask_socketio import emit, join_room, leave_room, Namespace
from app import socketio
from app.services.analysis_service import AnalysisService

class AnalysisNamespace(Namespace):
    def on_connect(self):
        emit('connected', {'message': 'Connected to analysis namespace'})
    
    def on_disconnect(self):
        print('Client disconnected')
    
    def on_start_analysis(self, data):
        """Start a new analysis in background."""
        analysis_id = data.get('analysis_id')
        room = f"analysis_{analysis_id}"
        join_room(room)
        
        # Start background task
        socketio.start_background_task(
            target=self._run_analysis,
            analysis_id=analysis_id,
            room=room
        )
        
        emit('analysis_started', {'analysis_id': analysis_id, 'room': room})
    
    def _run_analysis(self, analysis_id, room):
        """Background analysis worker."""
        try:
            # Emit progress updates
            socketio.emit('progress_update', {'progress': 10, 'stage': 'cloning'}, room=room, namespace='/analysis')
            
            # Run analysis (placeholder for now)
            # analysis_service = AnalysisService()
            # result = analysis_service.run_analysis(analysis_id)
            
            socketio.emit('analysis_complete', {'analysis_id': analysis_id}, room=room, namespace='/analysis')
        except Exception as e:
            socketio.emit('error', {'message': str(e)}, room=room, namespace='/analysis')

socketio.on_namespace(AnalysisNamespace('/analysis'))
```

**Acceptance Criteria:**
- Client can connect to `/analysis` namespace
- `start_analysis` event triggers background task
- Progress updates emit correctly to specific room
- Multiple concurrent analyses work independently

---

### 1.9 API Endpoints with Pydantic Schemas ⏳
**Priority:** HIGH | **Time Estimate:** 3 hours | **Dependencies:** 1.4, 1.8

**Tasks:**
- [ ] Create `app/routes/api.py` with Flask blueprint
- [ ] Define Pydantic request/response schemas
- [ ] Implement endpoints:
  - `POST /api/analysis` - Create new analysis
  - `GET /api/analysis/<id>` - Get analysis status
  - `GET /api/analysis/<id>/results` - Get analysis results
  - `GET /api/analyses` - List all analyses
- [ ] Add request validation using Pydantic
- [ ] Add error handling middleware

**Code Template:**
```python
# app/schemas.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime

class AnalysisCreateRequest(BaseModel):
    repo_url: HttpUrl
    analysis_type: Literal['SHORT', 'MEDIUM', 'HARD']
    config: Optional[dict] = Field(default_factory=dict)

class AnalysisResponse(BaseModel):
    analysis_id: int
    repo_url: str
    analysis_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    config: Optional[dict]

# app/routes/api.py
from flask import Blueprint, request, jsonify
from app.schemas import AnalysisCreateRequest, AnalysisResponse
from app.models.analysis import Analysis
from app.models.base import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/analysis', methods=['POST'])
def create_analysis():
    """Create new analysis."""
    data = AnalysisCreateRequest(**request.json)
    
    analysis = Analysis(
        repo_url=str(data.repo_url),
        analysis_type=data.analysis_type,
        config_json=data.config
    )
    db.session.add(analysis)
    db.session.commit()
    
    response = AnalysisResponse.from_orm(analysis)
    return jsonify(response.dict()), 201

@api_bp.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Get analysis by ID."""
    analysis = db.session.get(Analysis, analysis_id)
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    
    response = AnalysisResponse.from_orm(analysis)
    return jsonify(response.dict())
```

**Acceptance Criteria:**
- `POST /api/analysis` creates analysis and returns ID
- `GET /api/analysis/<id>` returns analysis details
- Pydantic validates requests (test with invalid data)
- Error responses follow consistent format

---

## Phase 2: Core Analysis Pipeline (Week 2-3) - 40 hours

### 2.1 Repository Cloning Service ⏳
**Priority:** HIGH | **Time Estimate:** 3 hours | **Dependencies:** 1.6

**Tasks:**
- [ ] Integrate existing `src/tools/repo_loader.py` into backend
- [ ] Create `app/services/repo_service.py` wrapper
- [ ] Add temporary directory management
- [ ] Implement cleanup after analysis
- [ ] Add progress callback for SocketIO updates
- [ ] Handle git errors (invalid URL, auth failures)

**Acceptance Criteria:**
- Repository clones successfully to temp directory
- Progress updates emit during cloning (0% → 25%)
- Cleanup removes temp directory after analysis
- Handles private repos with credentials

---

### 2.2 Code Chunking Service ⏳
**Priority:** HIGH | **Time Estimate:** 4 hours | **Dependencies:** 2.1

**Tasks:**
- [ ] Integrate existing `retrieval/codebase_indexing/file_processor.py`
- [ ] Create `app/services/chunking_service.py`
- [ ] Implement chunking strategy:
  - Python: Function-level chunking with AST parsing
  - JavaScript: Function-level chunking with regex
  - Generic: 100-line overlapping chunks (20 lines overlap)
- [ ] Store chunks in `code_chunks` table with metadata
- [ ] Add progress tracking (25% → 40%)

**Code Template:**
```python
# app/services/chunking_service.py
from app.models.code_chunk import CodeChunk
from app.models.base import db

class ChunkingService:
    def chunk_file(self, file_path: str, content: str, analysis_id: int) -> List[CodeChunk]:
        """Chunk file based on extension."""
        chunks = []
        
        if file_path.endswith('.py'):
            # Use AST-based chunking
            chunks = self._chunk_python(content)
        elif file_path.endswith(('.js', '.ts')):
            chunks = self._chunk_javascript(content)
        else:
            # Generic line-based chunking
            chunks = self._chunk_generic(content)
        
        # Create CodeChunk objects
        chunk_objects = []
        for chunk in chunks:
            chunk_obj = CodeChunk(
                analysis_id=analysis_id,
                file_path=file_path,
                chunk_text=chunk['text'],
                line_start=chunk['line_start'],
                line_end=chunk['line_end']
            )
            chunk_objects.append(chunk_obj)
        
        db.session.bulk_save_objects(chunk_objects)
        db.session.commit()
        
        return chunk_objects
```

**Acceptance Criteria:**
- Python files chunked by function (test with Flask repo)
- Chunks stored in database with correct line numbers
- Progress updates emit every 10 files processed

---

### 2.3 Embedding Generation Pipeline ⏳
**Priority:** CRITICAL | **Time Estimate:** 5 hours | **Dependencies:** 2.2, 1.6

**Tasks:**
- [ ] Create `app/services/embedding_service.py`
- [ ] Implement batch embedding generation (batch size: 10 chunks)
- [ ] Add retry logic for failed embeddings
- [ ] Store embeddings in FAISS index with code chunk metadata
- [ ] Update `code_chunks` table with `embedding_id` (FAISS vector ID)
- [ ] Add progress tracking (40% → 60%)

**Code Template:**
```python
# app/services/embedding_service.py
from app.services.cohere_service import CohereEmbeddingService
from app.services.faiss_manager import CodebaseIndexManager
from app.models.code_chunk import CodeChunk
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.cohere = CohereEmbeddingService()
        self.faiss_manager = CodebaseIndexManager()
    
    def embed_chunks(self, chunks: List[CodeChunk], progress_callback=None):
        """Generate and store embeddings for code chunks."""
        batch_size = 10
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk.chunk_text for chunk in batch]
            
            # Generate embeddings
            embeddings = self.cohere.generate_embeddings(texts, input_type="search_document")
            embeddings_array = np.array(embeddings)
            
            # Store in FAISS
            metadata = [{'chunk_id': chunk.chunk_id, 'file_path': chunk.file_path} for chunk in batch]
            vector_ids = self.faiss_manager.add_vectors(embeddings_array, metadata)
            
            # Update chunks with FAISS IDs
            for chunk, vid in zip(batch, vector_ids):
                chunk.embedding_id = vid
            db.session.commit()
            
            # Progress update
            if progress_callback:
                progress = 40 + (i / len(chunks)) * 20  # 40% → 60%
                progress_callback(progress, f"Embedded {i+len(batch)}/{len(chunks)} chunks")
```

**Acceptance Criteria:**
- Embeddings generated for all chunks (test with 100 sample chunks)
- FAISS index contains correct number of vectors
- `code_chunks.embedding_id` correctly references FAISS vectors
- Progress updates emit during embedding

---

### 2.4 CVE Search and Reranking Service ⏳
**Priority:** CRITICAL | **Time Estimate:** 6 hours | **Dependencies:** 2.3, 1.7

**Tasks:**
- [ ] Create `app/services/cve_search_service.py`
- [ ] Implement CVE search pipeline:
  1. Generate embedding for code chunk
  2. FAISS search: retrieve top 50 CVE candidates
  3. Cohere reranker: refine to top 10
  4. Score threshold filtering (>0.7 relevance)
- [ ] Store findings in `cve_findings` table
- [ ] Add progress tracking (60% → 75%)
- [ ] Implement parallel processing (ThreadPoolExecutor for 5 chunks at a time)

**Code Template:**
```python
# app/services/cve_search_service.py
from app.services.cohere_service import CohereEmbeddingService, CohereRerankService
from app.services.faiss_manager import CVEIndexManager
from app.models.cve_finding import CVEFinding
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class CVESearchService:
    def __init__(self):
        self.cohere_embed = CohereEmbeddingService()
        self.cohere_rerank = CohereRerankService()
        self.cve_index = CVEIndexManager()
    
    def search_cves_for_chunk(self, chunk: CodeChunk) -> List[CVEFinding]:
        """Search CVEs for a single code chunk."""
        # Step 1: Generate embedding
        embedding = self.cohere_embed.generate_embeddings([chunk.chunk_text], input_type="search_query")[0]
        embedding_array = np.array(embedding)
        
        # Step 2: FAISS search (top 50 candidates)
        candidates = self.cve_index.search(embedding_array, top_k=50)
        
        # Step 3: Rerank with Cohere (top 10)
        cve_texts = [c['description'] for c in candidates]
        reranked = self.cohere_rerank.rerank(chunk.chunk_text, cve_texts, top_n=10)
        
        # Step 4: Filter by relevance threshold
        findings = []
        for result in reranked:
            if result['relevance_score'] > 0.7:
                cve_id = candidates[result['index']]['cve_id']
                finding = CVEFinding(
                    analysis_id=chunk.analysis_id,
                    cve_id=cve_id,
                    file_path=chunk.file_path,
                    confidence_score=result['relevance_score'],
                    validation_status='pending'
                )
                findings.append(finding)
        
        return findings
    
    def search_all_chunks(self, chunks: List[CodeChunk], progress_callback=None):
        """Parallel CVE search for all chunks."""
        all_findings = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.search_cves_for_chunk, chunk) for chunk in chunks]
            
            for i, future in enumerate(futures):
                findings = future.result()
                all_findings.extend(findings)
                
                if progress_callback:
                    progress = 60 + (i / len(chunks)) * 15  # 60% → 75%
                    progress_callback(progress, f"Searched {i+1}/{len(chunks)} chunks")
        
        db.session.bulk_save_objects(all_findings)
        db.session.commit()
        
        return all_findings
```

**Acceptance Criteria:**
- FAISS retrieves top 50 CVE candidates (<50ms)
- Reranker refines to top 10 with scores (<150ms)
- Findings stored with confidence scores
- Parallel processing reduces total time by 60%

---

### 2.5 GPT-4 Validation Service ⏳
**Priority:** HIGH | **Time Estimate:** 5 hours | **Dependencies:** 2.4

**Tasks:**
- [ ] Create `app/services/validation_service.py`
- [ ] Integrate Azure OpenAI GPT-4.1 for validation
- [ ] Implement validation prompt template
- [ ] Classify findings as: `confirmed`, `false_positive`, `needs_review`
- [ ] Update `cve_findings.validation_status` and `severity`
- [ ] Add progress tracking (75% → 90%)

**Code Template:**
```python
# app/services/validation_service.py
import openai
from app.models.cve_finding import CVEFinding

class ValidationService:
    def __init__(self):
        openai.api_key = Config.AZURE_OPENAI_API_KEY
        openai.api_base = Config.AZURE_OPENAI_ENDPOINT
        openai.api_type = "azure"
        openai.api_version = "2024-02-15-preview"
    
    def validate_finding(self, finding: CVEFinding, code_chunk: str, cve_description: str) -> Dict:
        """Validate CVE finding with GPT-4.1."""
        prompt = f"""
You are a security expert. Analyze if the following code is vulnerable to the CVE described.

**Code:**
```
{code_chunk}
```

**CVE Description:**
{cve_description}

**Analysis:**
1. Does the code exhibit the vulnerability pattern? (yes/no/uncertain)
2. Severity if confirmed? (critical/high/medium/low)
3. Explanation (1-2 sentences)

Respond in JSON format:
{{"vulnerable": true/false, "severity": "...", "explanation": "..."}}
"""
        
        response = openai.ChatCompletion.create(
            engine="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Update finding
        finding.validation_status = 'confirmed' if result['vulnerable'] else 'false_positive'
        finding.severity = result['severity'] if result['vulnerable'] else None
        
        return result
```

**Acceptance Criteria:**
- GPT-4.1 validation works with Azure endpoint
- Validation classifies findings correctly (test with known CVEs)
- Updates stored in database
- Progress updates emit during validation

---

### 2.6 Report Generation Service ⏳
**Priority:** MEDIUM | **Time Estimate:** 4 hours | **Dependencies:** 2.5

**Tasks:**
- [ ] Integrate existing `retrieval/agent_tools/pdf_report_generator.py`
- [ ] Create `app/services/report_service.py`
- [ ] Generate JSON report with all findings
- [ ] Generate PDF report with visualizations
- [ ] Store reports in `data/reports/<analysis_id>/`
- [ ] Add progress tracking (90% → 100%)

**Acceptance Criteria:**
- JSON report includes all findings with metadata
- PDF report formatted correctly (test with sample data)
- Reports accessible via API endpoint
- Progress reaches 100% on completion

---

### 2.7 Analysis Orchestrator ⏳
**Priority:** CRITICAL | **Time Estimate:** 6 hours | **Dependencies:** 2.1-2.6

**Tasks:**
- [ ] Create `app/services/analysis_service.py`
- [ ] Implement `AnalysisOrchestrator` class
- [ ] Wire together: clone → chunk → embed → search → validate → report
- [ ] Add analysis type configs (SHORT/MEDIUM/HARD)
- [ ] Implement error recovery and cleanup
- [ ] Emit progress updates via SocketIO

**Code Template:**
```python
# app/services/analysis_service.py
from app import socketio
from app.services.repo_service import RepoService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.cve_search_service import CVESearchService
from app.services.validation_service import ValidationService
from app.services.report_service import ReportService

class AnalysisOrchestrator:
    def __init__(self, analysis_id: int):
        self.analysis_id = analysis_id
        self.analysis = db.session.get(Analysis, analysis_id)
        self.room = f"analysis_{analysis_id}"
    
    def run(self):
        """Execute full analysis pipeline."""
        try:
            self.analysis.status = 'running'
            db.session.commit()
            
            # Step 1: Clone repository
            self.emit_progress(0, 'Cloning repository')
            repo_path = RepoService().clone(self.analysis.repo_url)
            
            # Step 2: Chunk files
            self.emit_progress(25, 'Chunking code files')
            chunks = ChunkingService().process_directory(repo_path, self.analysis_id)
            
            # Step 3: Generate embeddings
            self.emit_progress(40, 'Generating embeddings')
            EmbeddingService().embed_chunks(chunks, progress_callback=self.emit_progress)
            
            # Step 4: Search CVEs
            self.emit_progress(60, 'Searching for vulnerabilities')
            findings = CVESearchService().search_all_chunks(chunks, progress_callback=self.emit_progress)
            
            # Step 5: Validate with GPT-4
            self.emit_progress(75, 'Validating findings')
            ValidationService().validate_all_findings(findings, progress_callback=self.emit_progress)
            
            # Step 6: Generate reports
            self.emit_progress(90, 'Generating reports')
            ReportService().generate_reports(self.analysis_id)
            
            # Complete
            self.analysis.status = 'completed'
            self.analysis.end_time = datetime.utcnow()
            db.session.commit()
            
            self.emit_progress(100, 'Analysis complete')
            socketio.emit('analysis_complete', {'analysis_id': self.analysis_id}, room=self.room, namespace='/analysis')
        
        except Exception as e:
            self.analysis.status = 'failed'
            db.session.commit()
            socketio.emit('error', {'message': str(e)}, room=self.room, namespace='/analysis')
    
    def emit_progress(self, percentage: int, stage: str):
        """Emit progress update via SocketIO."""
        socketio.emit('progress_update', {
            'progress': percentage,
            'stage': stage
        }, room=self.room, namespace='/analysis')
```

**Acceptance Criteria:**
- Full pipeline runs end-to-end without errors
- Progress updates emit at each stage
- Analysis completes in <5 minutes for 1000-file repo (SHORT)
- Error handling gracefully fails and cleans up resources

---

## Phase 3: Testing & Optimization (Week 4) - 30 hours

### 3.1 Unit Tests for Services ⏳
**Priority:** HIGH | **Time Estimate:** 8 hours | **Dependencies:** Phase 2 completion

**Tasks:**
- [ ] Write tests for `cohere_service.py` (mock API calls)
- [ ] Write tests for `faiss_manager.py` (sample vectors)
- [ ] Write tests for `cve_search_service.py` (end-to-end search)
- [ ] Write tests for `validation_service.py` (GPT-4 responses)
- [ ] Write tests for `analysis_service.py` (orchestrator logic)
- [ ] Achieve >80% code coverage

**Acceptance Criteria:**
- All tests pass: `pytest tests/`
- Coverage report: `pytest --cov=app tests/`
- No critical issues flagged by flake8

---

### 3.2 Integration Tests ⏳
**Priority:** HIGH | **Time Estimate:** 6 hours | **Dependencies:** 3.1

**Tasks:**
- [ ] Test full analysis pipeline with sample repository
- [ ] Test concurrent analyses (5 simultaneous analyses)
- [ ] Test error scenarios (invalid repo URL, API failures)
- [ ] Test SocketIO events with test client
- [ ] Test API endpoints with Postman/curl

**Acceptance Criteria:**
- Full pipeline test completes successfully
- Concurrent analyses don't interfere
- Error handling works for all failure scenarios

---

### 3.3 Performance Optimization ⏳
**Priority:** MEDIUM | **Time Estimate:** 8 hours | **Dependencies:** 3.2

**Tasks:**
- [ ] Profile embedding generation (target: <100ms per chunk)
- [ ] Optimize FAISS search (target: <50ms for 50K vectors)
- [ ] Optimize reranking (batch multiple queries)
- [ ] Add caching for repeated CVE searches
- [ ] Optimize database queries (add indexes)

**Acceptance Criteria:**
- Embedding generation: <100ms per chunk
- FAISS search: <50ms average
- Total analysis time: <5 minutes for 1000-file repo

---

### 3.4 Load Testing ⏳
**Priority:** MEDIUM | **Time Estimate:** 4 hours | **Dependencies:** 3.3

**Tasks:**
- [ ] Setup load testing with Locust
- [ ] Test 10 concurrent analyses
- [ ] Test 100 concurrent WebSocket connections
- [ ] Monitor memory usage and CPU utilization
- [ ] Identify bottlenecks

**Acceptance Criteria:**
- System handles 10 concurrent analyses without crashes
- Memory usage stays <4GB
- CPU utilization <80% average

---

### 3.5 Documentation ⏳
**Priority:** MEDIUM | **Time Estimate:** 4 hours | **Dependencies:** Phase 3 completion

**Tasks:**
- [ ] Write API documentation (OpenAPI/Swagger)
- [ ] Write deployment guide (Docker, systemd)
- [ ] Write developer setup guide
- [ ] Document architecture decisions
- [ ] Create usage examples

**Acceptance Criteria:**
- API documentation generated with Swagger UI
- Deployment guide tested on clean Ubuntu 22.04 machine
- Developer setup works in <15 minutes

---

## Phase 4: Deployment & Frontend Integration (Week 5-6) - 55 hours

### 4.1 Docker Containerization ⏳
**Priority:** HIGH | **Time Estimate:** 6 hours | **Dependencies:** Phase 3 completion

**Tasks:**
- [ ] Create `Dockerfile` for backend
- [ ] Create `docker-compose.yml` with services
- [ ] Add health checks and restart policies
- [ ] Optimize image size (<500MB)
- [ ] Test deployment with Docker

**Acceptance Criteria:**
- Docker image builds without errors
- Container starts and serves requests
- Health check endpoint accessible
- Image size <500MB

---

### 4.2 CI/CD Pipeline ⏳
**Priority:** MEDIUM | **Time Estimate:** 4 hours | **Dependencies:** 4.1

**Tasks:**
- [ ] Setup GitHub Actions workflow
- [ ] Add automated testing on PR
- [ ] Add Docker image build and push
- [ ] Add deployment to staging environment
- [ ] Add rollback mechanism

**Acceptance Criteria:**
- CI runs on every PR
- CD deploys on main branch merge
- Rollback works within 5 minutes

---

### 4.3 Frontend Integration ⏳
**Priority:** HIGH | **Time Estimate:** 20 hours | **Dependencies:** Phase 2 completion

**Tasks:**
- [ ] Create React app with Vite
- [ ] Setup Shadcn UI components
- [ ] Implement WebSocket client with Socket.IO client
- [ ] Create analysis dashboard with real-time progress
- [ ] Create results viewer with CVE details
- [ ] Add authentication (optional)

**Acceptance Criteria:**
- Frontend connects to backend WebSocket
- Real-time progress updates display correctly
- Results display with filtering and sorting
- UI is responsive on mobile/tablet/desktop

---

### 4.4 Monitoring & Logging ⏳
**Priority:** MEDIUM | **Time Estimate:** 5 hours | **Dependencies:** 4.1

**Tasks:**
- [ ] Setup structured logging with loguru
- [ ] Add API request/response logging
- [ ] Add performance metrics (latency, throughput)
- [ ] Setup log aggregation (optional: ELK stack)
- [ ] Add alerting for critical errors

**Acceptance Criteria:**
- Logs are structured and searchable
- Metrics tracked for all API endpoints
- Alerts trigger on failures

---

### 4.5 Security Hardening ⏳
**Priority:** HIGH | **Time Estimate:** 4 hours | **Dependencies:** Phase 4 completion

**Tasks:**
- [ ] Add rate limiting on API endpoints
- [ ] Add authentication and authorization
- [ ] Sanitize user inputs (repo URLs)
- [ ] Add HTTPS support
- [ ] Implement secrets management (Vault/AWS Secrets)

**Acceptance Criteria:**
- Rate limiting prevents abuse
- Authentication works for protected endpoints
- All secrets stored securely (not in code)

---

### 4.6 Production Deployment ⏳
**Priority:** CRITICAL | **Time Estimate:** 8 hours | **Dependencies:** 4.1-4.5

**Tasks:**
- [ ] Deploy to cloud (AWS/Azure/GCP)
- [ ] Configure load balancer
- [ ] Setup SSL certificates
- [ ] Configure domain and DNS
- [ ] Run smoke tests

**Acceptance Criteria:**
- Backend accessible via HTTPS
- Load balancer distributes traffic
- Smoke tests pass

---

### 4.7 User Acceptance Testing ⏳
**Priority:** HIGH | **Time Estimate:** 8 hours | **Dependencies:** 4.6

**Tasks:**
- [ ] Test with real repositories (Flask, Django, Express)
- [ ] Validate CVE detection accuracy (>85%)
- [ ] Collect user feedback
- [ ] Fix critical bugs
- [ ] Document known limitations

**Acceptance Criteria:**
- CVE detection accuracy >85%
- No critical bugs in production
- User feedback positive

---

## Summary Statistics

**Total Tasks:** 45  
**Total Estimated Time:** 150 hours  
**Priority Breakdown:**
- CRITICAL: 8 tasks (35 hours)
- HIGH: 18 tasks (78 hours)
- MEDIUM: 19 tasks (37 hours)

**Phase Breakdown:**
- Phase 1 (Setup): 25 hours (1 week)
- Phase 2 (Pipeline): 40 hours (2 weeks)
- Phase 3 (Testing): 30 hours (1 week)
- Phase 4 (Deployment): 55 hours (2 weeks)

**Current Progress:** 0% (0/45 tasks completed)

---

## Notes

- **Parallel Development:** Phases 1-2 can be parallelized with frontend development
- **Incremental Testing:** Run tests after completing each service (don't wait for Phase 3)
- **Progress Tracking:** Update MEMORY.md after completing each task
- **Blockers:** Azure Cohere credentials must be valid and have sufficient quota
- **Risk Mitigation:** If Cohere API fails, have fallback to OpenAI embeddings

**Next Action:** Start with 1.1 (Project Initialization) - ETA 2 hours
