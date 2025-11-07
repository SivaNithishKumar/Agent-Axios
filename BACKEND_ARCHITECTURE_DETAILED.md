# Agent Axios Backend - Detailed Architecture

**Version:** 1.0  
**Last Updated:** 2025-06-XX

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer (React)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  Dashboard   │  │   Results    │  │   Settings   │                 │
│  │   Component  │  │   Viewer     │  │   Panel      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│           │                │                  │                          │
│           └────────────────┴──────────────────┘                          │
│                            │                                             │
│                   Socket.IO Client + REST API                           │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Flask Application                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │  │
│  │  │   CORS     │  │   Rate     │  │   Auth     │                │  │
│  │  │ Middleware │  │  Limiter   │  │ Middleware │                │  │
│  │  └────────────┘  └────────────┘  └────────────┘                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           │                                                              │
│           ├──────────────────┬────────────────────┐                     │
│           ▼                  ▼                    ▼                     │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │
│  │  REST Endpoints │ │ WebSocket      │ │ Health Check   │            │
│  │  /api/*        │ │ /analysis      │ │ /health        │            │
│  └────────────────┘ └────────────────┘ └────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Analysis Orchestrator Service                       │  │
│  │  ┌────────────────────────────────────────────────────────────┐ │  │
│  │  │  Analysis Pipeline:                                        │ │  │
│  │  │  Clone → Chunk → Embed → Search → Rerank → Validate       │ │  │
│  │  └────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│           │                                                              │
│           ├──────────┬──────────┬──────────┬──────────┬────────────┐   │
│           ▼          ▼          ▼          ▼          ▼            ▼   │
│  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐  │
│  │   Repo     │ │ Chunking │ │Embedding │ │   CVE    │ │Validation│  │
│  │  Service   │ │ Service  │ │ Service  │ │  Search  │ │ Service  │  │
│  └────────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      External Services Layer                            │
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────┐   │
│  │ Azure Cohere      │  │ Azure Cohere      │  │ Azure OpenAI     │   │
│  │ Embeddings        │  │ Reranker          │  │ GPT-4.1          │   │
│  │ (embed-v3-eng)    │  │ (rerank-v3-5)     │  │                  │   │
│  └───────────────────┘  └───────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Storage Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │   SQLite DB      │  │   FAISS Index    │  │   FAISS Index    │    │
│  │  (Metadata)      │  │   (CVE Vectors)  │  │ (Code Vectors)   │    │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │    │
│  │  │ analyses   │  │  │  │ ~50K CVE   │  │  │  │ ~10K code  │  │    │
│  │  │code_chunks │  │  │  │ vectors    │  │  │  │ chunks/repo│  │    │
│  │  │cve_findings│  │  │  │ (1024 dim) │  │  │  │ (1024 dim) │  │    │
│  │  │cve_dataset │  │  │  └────────────┘  │  │  └────────────┘  │    │
│  │  └────────────┘  │  └──────────────────┘  └──────────────────┘    │
│  └──────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### Analysis Request Flow

```
User → Frontend → POST /api/analysis
                      │
                      ▼
              Create Analysis Record
                (SQLite DB)
                      │
                      ▼
              Return analysis_id
                      │
                      ▼
        Frontend → WebSocket Connect
            (Socket.IO /analysis namespace)
                      │
                      ▼
          Emit 'start_analysis' event
                      │
                      ▼
        Start Background Task (eventlet)
                      │
                      ▼
        ┌─────────────────────────────┐
        │  Analysis Pipeline Starts   │
        └─────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│ Clone Repo   │          │ Emit Progress:   │
│ (git clone)  │────────→│ 0% "Cloning"    │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Chunk Files  │          │ Emit Progress:   │
│ (AST/Regex)  │────────→│ 25% "Chunking"  │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Embed Chunks │          │ Emit Progress:   │
│ (Cohere API) │────────→│ 40% "Embedding" │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Search CVEs  │          │ Emit Progress:   │
│ (FAISS+Rerank)────────→│ 60% "Searching" │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Validate     │          │ Emit Progress:   │
│ (GPT-4.1)    │────────→│ 75% "Validating"│
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Generate     │          │ Emit Progress:   │
│ Reports      │────────→│ 90% "Reporting" │
└──────────────┘          └──────────────────┘
        │
        ▼
┌──────────────┐          ┌──────────────────┐
│ Complete     │          │ Emit Progress:   │
│ Analysis     │────────→│ 100% "Complete" │
└──────────────┘          └──────────────────┘
        │
        ▼
Emit 'analysis_complete' event
        │
        ▼
Frontend → GET /api/analysis/:id/results
        │
        ▼
Display Results Dashboard
```

---

## Service Layer Architecture

### 1. Repository Service
**File:** `app/services/repo_service.py`

**Responsibilities:**
- Clone Git repositories to temporary directories
- Handle authentication (SSH keys, tokens)
- Clean up after analysis

**Key Methods:**
```python
class RepoService:
    def clone(repo_url: str) -> str:
        """Clone repo and return local path."""
    
    def cleanup(repo_path: str):
        """Remove temporary repository."""
```

**Dependencies:**
- Git CLI
- Temp directory manager

---

### 2. Chunking Service
**File:** `app/services/chunking_service.py`

**Responsibilities:**
- Parse code files by language
- Extract function/class definitions
- Create overlapping chunks for context

**Key Methods:**
```python
class ChunkingService:
    def chunk_file(file_path: str, content: str) -> List[Chunk]:
        """Chunk file based on extension."""
    
    def _chunk_python(content: str) -> List[Chunk]:
        """AST-based Python chunking."""
    
    def _chunk_generic(content: str) -> List[Chunk]:
        """Line-based generic chunking."""
```

**Chunking Strategy:**
| Language | Method | Chunk Size | Overlap |
|----------|--------|------------|---------|
| Python | AST (function-level) | Variable | N/A |
| JavaScript | Regex (function-level) | Variable | N/A |
| TypeScript | Regex (function-level) | Variable | N/A |
| Generic | Line-based | 100 lines | 20 lines |

---

### 3. Embedding Service
**File:** `app/services/embedding_service.py`

**Responsibilities:**
- Generate embeddings via Cohere API
- Batch processing (10 chunks at a time)
- Store embeddings in FAISS index

**Key Methods:**
```python
class EmbeddingService:
    def embed_chunks(chunks: List[CodeChunk], progress_callback=None):
        """Generate and store embeddings."""
    
    def _batch_embed(texts: List[str]) -> np.ndarray:
        """Batch embedding generation."""
```

**Performance Metrics:**
- Batch size: 10 chunks
- Embedding time: <100ms per chunk
- Retry logic: 3 attempts with exponential backoff

---

### 4. CVE Search Service
**File:** `app/services/cve_search_service.py`

**Responsibilities:**
- FAISS similarity search (top 50 candidates)
- Cohere reranking (refine to top 10)
- Score threshold filtering (>0.7)

**Key Methods:**
```python
class CVESearchService:
    def search_cves_for_chunk(chunk: CodeChunk) -> List[CVEFinding]:
        """Search CVEs for single chunk."""
    
    def search_all_chunks(chunks: List[CodeChunk]) -> List[CVEFinding]:
        """Parallel CVE search."""
```

**Search Pipeline:**
```
Code Chunk Text
    │
    ▼
Generate Query Embedding (Cohere)
    │
    ▼
FAISS Search (top 50 candidates)
    ├─→ Candidate 1 (distance: 0.45)
    ├─→ Candidate 2 (distance: 0.52)
    └─→ ... (48 more)
    │
    ▼
Cohere Reranker (top 10 refined)
    ├─→ Result 1 (relevance: 0.92)
    ├─→ Result 2 (relevance: 0.85)
    └─→ ... (8 more)
    │
    ▼
Filter by Threshold (>0.7)
    ├─→ Finding 1 (confidence: 0.92) ✅
    ├─→ Finding 2 (confidence: 0.85) ✅
    └─→ Finding 3 (confidence: 0.62) ❌
    │
    ▼
Store in cve_findings table
```

---

### 5. Validation Service
**File:** `app/services/validation_service.py`

**Responsibilities:**
- Validate CVE findings with GPT-4.1
- Classify as confirmed/false_positive/needs_review
- Assign severity levels

**Key Methods:**
```python
class ValidationService:
    def validate_finding(finding: CVEFinding, code: str, cve_desc: str) -> Dict:
        """Validate single finding with GPT-4.1."""
    
    def validate_all_findings(findings: List[CVEFinding]) -> None:
        """Batch validation with progress tracking."""
```

**Validation Prompt Template:**
```
You are a security expert. Analyze if the following code is vulnerable.

**Code:**
{code_chunk}

**CVE Description:**
{cve_description}

**Analysis:**
1. Does the code exhibit the vulnerability pattern? (yes/no/uncertain)
2. Severity if confirmed? (critical/high/medium/low)
3. Explanation (1-2 sentences)

Respond in JSON: {"vulnerable": true/false, "severity": "...", "explanation": "..."}
```

---

### 6. Report Service
**File:** `app/services/report_service.py`

**Responsibilities:**
- Generate JSON reports
- Generate PDF reports with visualizations
- Store reports in file system

**Key Methods:**
```python
class ReportService:
    def generate_json_report(analysis_id: int) -> Dict:
        """Generate JSON report."""
    
    def generate_pdf_report(analysis_id: int) -> str:
        """Generate PDF report and return path."""
```

**Report Structure:**
```json
{
  "analysis_id": 123,
  "repo_url": "https://github.com/...",
  "analysis_type": "MEDIUM",
  "start_time": "2025-06-15T10:00:00Z",
  "end_time": "2025-06-15T10:04:32Z",
  "summary": {
    "total_files": 245,
    "total_chunks": 1832,
    "total_cves_found": 12,
    "confirmed_vulnerabilities": 8,
    "false_positives": 4,
    "severity_breakdown": {
      "critical": 2,
      "high": 3,
      "medium": 3,
      "low": 0
    }
  },
  "findings": [
    {
      "cve_id": "CVE-2024-1234",
      "file_path": "src/auth/login.py",
      "severity": "critical",
      "confidence_score": 0.92,
      "validation_status": "confirmed",
      "description": "SQL Injection vulnerability...",
      "affected_code": "...",
      "recommendation": "Use parameterized queries..."
    }
  ]
}
```

---

### 7. Analysis Orchestrator
**File:** `app/services/analysis_service.py`

**Responsibilities:**
- Coordinate all services in pipeline
- Manage analysis lifecycle
- Emit real-time progress updates
- Handle errors and cleanup

**Key Methods:**
```python
class AnalysisOrchestrator:
    def run(self):
        """Execute full analysis pipeline."""
    
    def emit_progress(percentage: int, stage: str):
        """Emit progress via SocketIO."""
```

**Analysis Type Configurations:**
```python
ANALYSIS_CONFIGS = {
    'SHORT': {
        'max_files': 500,
        'max_chunks_per_file': 20,
        'validation_enabled': False,
        'estimated_time': '2-3 minutes'
    },
    'MEDIUM': {
        'max_files': 2000,
        'max_chunks_per_file': 50,
        'validation_enabled': True,
        'estimated_time': '5-10 minutes'
    },
    'HARD': {
        'max_files': None,  # No limit
        'max_chunks_per_file': None,
        'validation_enabled': True,
        'estimated_time': '15-40 minutes'
    }
}
```

---

## Database Schema

### SQLite Tables

#### 1. analyses
```sql
CREATE TABLE analyses (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_url VARCHAR(500) NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,  -- SHORT, MEDIUM, HARD
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    config_json TEXT NULL,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
```

#### 2. code_chunks
```sql
CREATE TABLE code_chunks (
    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    chunk_text TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    embedding_id INTEGER NULL,  -- FAISS vector ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE
);

CREATE INDEX idx_code_chunks_analysis_id ON code_chunks(analysis_id);
CREATE INDEX idx_code_chunks_file_path ON code_chunks(file_path);
```

#### 3. cve_findings
```sql
CREATE TABLE cve_findings (
    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    cve_id VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    chunk_id INTEGER NULL,
    severity VARCHAR(20) NULL,  -- critical, high, medium, low
    confidence_score FLOAT NOT NULL,  -- 0.0 - 1.0
    validation_status VARCHAR(20) DEFAULT 'pending',  -- pending, confirmed, false_positive, needs_review
    validation_explanation TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES code_chunks(chunk_id) ON DELETE SET NULL
);

CREATE INDEX idx_cve_findings_analysis_id ON cve_findings(analysis_id);
CREATE INDEX idx_cve_findings_severity ON cve_findings(severity);
CREATE INDEX idx_cve_findings_validation_status ON cve_findings(validation_status);
```

#### 4. cve_dataset
```sql
CREATE TABLE cve_dataset (
    cve_id VARCHAR(50) PRIMARY KEY,
    cve_json TEXT NOT NULL,  -- Full CVE details as JSON
    description TEXT NOT NULL,
    severity VARCHAR(20) NULL,
    cvss_score FLOAT NULL,
    embedding_id INTEGER NULL,  -- FAISS vector ID
    last_updated TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cve_dataset_severity ON cve_dataset(severity);
CREATE INDEX idx_cve_dataset_cvss_score ON cve_dataset(cvss_score DESC);
```

---

## FAISS Index Structure

### CVE Index
**File:** `data/cve_index.faiss`

**Specifications:**
- Index Type: `IndexFlatL2` (exact search, no training required)
- Dimensions: 1024 (Cohere embed-v3-english)
- Vector Count: ~50,000 CVEs
- Metadata File: `data/cve_index.faiss.metadata` (pickle)

**Metadata Structure:**
```python
[
    {
        'faiss_id': 0,
        'cve_id': 'CVE-2024-1234',
        'description': 'SQL injection vulnerability...',
        'severity': 'critical',
        'cvss_score': 9.8
    },
    # ... 49,999 more
]
```

### Codebase Index
**File:** `data/codebase_index.faiss`

**Specifications:**
- Index Type: `IndexFlatL2`
- Dimensions: 1024
- Vector Count: ~10,000 chunks per repository (varies)
- Metadata File: `data/codebase_index.faiss.metadata`

**Metadata Structure:**
```python
[
    {
        'faiss_id': 0,
        'chunk_id': 1,
        'analysis_id': 123,
        'file_path': 'src/auth/login.py',
        'line_start': 45,
        'line_end': 67
    },
    # ... 9,999 more
]
```

---

## API Endpoints

### REST API

#### POST /api/analysis
**Description:** Create new analysis

**Request:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "analysis_type": "MEDIUM",
  "config": {
    "max_files": 1000,
    "validation_enabled": true
  }
}
```

**Response (201):**
```json
{
  "analysis_id": 123,
  "status": "pending",
  "estimated_time": "5-10 minutes",
  "created_at": "2025-06-15T10:00:00Z"
}
```

---

#### GET /api/analysis/:id
**Description:** Get analysis status

**Response (200):**
```json
{
  "analysis_id": 123,
  "repo_url": "https://github.com/user/repo",
  "analysis_type": "MEDIUM",
  "status": "running",
  "progress": 65,
  "current_stage": "Searching for vulnerabilities",
  "start_time": "2025-06-15T10:00:00Z",
  "estimated_completion": "2025-06-15T10:07:30Z"
}
```

---

#### GET /api/analysis/:id/results
**Description:** Get analysis results

**Response (200):**
```json
{
  "analysis_id": 123,
  "summary": {
    "total_cves_found": 12,
    "confirmed_vulnerabilities": 8,
    "severity_breakdown": {
      "critical": 2,
      "high": 3,
      "medium": 3
    }
  },
  "findings": [
    {
      "finding_id": 456,
      "cve_id": "CVE-2024-1234",
      "file_path": "src/auth/login.py",
      "severity": "critical",
      "confidence_score": 0.92,
      "validation_status": "confirmed"
    }
  ],
  "reports": {
    "json_url": "/api/analysis/123/report.json",
    "pdf_url": "/api/analysis/123/report.pdf"
  }
}
```

---

### WebSocket Events (Socket.IO)

**Namespace:** `/analysis`

#### Client → Server Events

##### `connect`
**Description:** Client connects to analysis namespace

**Response:**
```json
{
  "event": "connected",
  "message": "Connected to analysis namespace"
}
```

---

##### `start_analysis`
**Description:** Start analysis for given ID

**Payload:**
```json
{
  "analysis_id": 123
}
```

**Response:**
```json
{
  "event": "analysis_started",
  "analysis_id": 123,
  "room": "analysis_123"
}
```

---

#### Server → Client Events

##### `progress_update`
**Description:** Real-time progress updates

**Payload:**
```json
{
  "analysis_id": 123,
  "progress": 65,
  "stage": "Searching for vulnerabilities",
  "details": "Processed 650/1000 chunks"
}
```

**Frequency:** Every 2-5 seconds

---

##### `analysis_complete`
**Description:** Analysis finished successfully

**Payload:**
```json
{
  "analysis_id": 123,
  "duration_seconds": 347,
  "results_url": "/api/analysis/123/results"
}
```

---

##### `error`
**Description:** Error occurred during analysis

**Payload:**
```json
{
  "analysis_id": 123,
  "error_code": "CLONE_FAILED",
  "message": "Failed to clone repository: Invalid URL",
  "recoverable": false
}
```

---

## Deployment Architecture

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - COHERE_EMBED_ENDPOINT=${COHERE_EMBED_ENDPOINT}
      - COHERE_EMBED_API_KEY=${COHERE_EMBED_API_KEY}
      - COHERE_RERANK_ENDPOINT=${COHERE_RERANK_ENDPOINT}
      - COHERE_RERANK_API_KEY=${COHERE_RERANK_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    volumes:
      - ./data:/app/data  # FAISS indexes and reports
      - ./agent_axios.db:/app/agent_axios.db  # SQLite database
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:5000
      - REACT_APP_WS_URL=ws://localhost:5000
    depends_on:
      - backend
    restart: unless-stopped
```

---

### Production Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                        │
│                  (Static Frontend Assets)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Load Balancer                 │
│                    (HTTPS Termination)                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌──────────────────┐                        ┌──────────────────┐
│   EC2 Instance 1 │                        │   EC2 Instance 2 │
│  (Backend + DB)  │                        │  (Backend + DB)  │
│  ┌────────────┐  │                        │  ┌────────────┐  │
│  │   Flask    │  │                        │  │   Flask    │  │
│  │  SocketIO  │  │                        │  │  SocketIO  │  │
│  │            │  │                        │  │            │  │
│  │  SQLite    │  │                        │  │  SQLite    │  │
│  │  FAISS     │  │                        │  │  FAISS     │  │
│  └────────────┘  │                        │  └────────────┘  │
└──────────────────┘                        └──────────────────┘
        │                                           │
        └─────────────────────┬─────────────────────┘
                              ▼
                  ┌────────────────────────┐
                  │    S3 Bucket           │
                  │  (Reports, Backups)    │
                  └────────────────────────┘
```

---

## Performance Specifications

### Latency Targets

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Repository Clone | <30s (1GB repo) | TBD | ⏳ |
| File Chunking | <5s (1000 files) | TBD | ⏳ |
| Embedding Generation | <100ms/chunk | TBD | ⏳ |
| FAISS Search | <50ms (50K vectors) | TBD | ⏳ |
| Cohere Reranking | <150ms (50→10) | TBD | ⏳ |
| GPT-4.1 Validation | <2s/finding | TBD | ⏳ |
| Full Analysis (SHORT) | <5 min (1000 files) | TBD | ⏳ |

### Throughput Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Concurrent Analyses | 10 | TBD | ⏳ |
| WebSocket Connections | 100 | TBD | ⏳ |
| API Requests/Second | 50 | TBD | ⏳ |
| Embedding API Calls/Min | 600 (10/sec) | TBD | ⏳ |

### Resource Limits

| Resource | Limit | Justification |
|----------|-------|---------------|
| Memory | 4GB per instance | FAISS index + SQLite + buffers |
| CPU | 4 cores | Parallel chunking + embedding |
| Disk | 50GB | CVE index (10GB) + temp repos (20GB) + logs (20GB) |
| Database | 5GB | ~100K analyses + findings |

---

## Security Considerations

### 1. API Key Management
- Store all API keys in `.env` file (never in code)
- Use environment-specific keys (dev/staging/prod)
- Rotate keys quarterly
- Monitor API usage for anomalies

### 2. Input Validation
- Validate repository URLs (whitelist GitHub, GitLab, Bitbucket)
- Sanitize all user inputs to prevent injection attacks
- Limit analysis config values (max_files, max_chunks)

### 3. Rate Limiting
- API endpoints: 100 requests/hour per IP
- WebSocket connections: 10 concurrent per user
- Analysis submissions: 5 per hour per user

### 4. Authentication & Authorization (Future)
- JWT-based authentication
- Role-based access control (admin, user, viewer)
- API key authentication for programmatic access

---

## Monitoring & Observability

### Key Metrics to Track

1. **Performance Metrics**
   - API latency (p50, p95, p99)
   - WebSocket connection duration
   - Analysis completion time by type

2. **Business Metrics**
   - Analyses per day
   - CVE detection accuracy
   - False positive rate

3. **Infrastructure Metrics**
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network bandwidth

### Logging Strategy

```python
# Structured logging example
import logging
import json

logger = logging.getLogger('agent-axios')

def log_analysis_start(analysis_id, repo_url):
    logger.info(json.dumps({
        'event': 'analysis_started',
        'analysis_id': analysis_id,
        'repo_url': repo_url,
        'timestamp': datetime.utcnow().isoformat()
    }))
```

**Log Levels:**
- DEBUG: Detailed diagnostic info (disabled in production)
- INFO: General operational events
- WARNING: Potential issues (high API latency)
- ERROR: Errors requiring attention
- CRITICAL: System failures

---

## Future Enhancements

### Phase 5 (Post-MVP)

1. **Advanced Analysis Types**
   - CUSTOM: User-defined chunk size, validation rules
   - INCREMENTAL: Only analyze changed files (git diff)

2. **Performance Optimizations**
   - Caching layer (Redis) for repeated analyses
   - Distributed FAISS with multi-node setup
   - GPU acceleration for embeddings

3. **Feature Additions**
   - Scheduled analyses (cron-like)
   - Webhook notifications on completion
   - Integration with Slack, Jira, GitHub Issues

4. **ML Improvements**
   - Fine-tune Cohere embeddings on security data
   - Train custom reranker on CVE dataset
   - Implement active learning for validation

---

**Document Version:** 1.0  
**Last Updated:** 2025-06-XX  
**Maintained By:** Agent Axios Team
