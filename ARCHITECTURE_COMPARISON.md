# Agent Axios: Current vs Required Architecture

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                   │
│                           ❌ COMPLETELY MISSING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐   │
│  │  Home Page      │  │  Analysis Page   │  │  Results Page           │   │
│  │  - Repo input   │  │  - Progress bar  │  │  - CVE findings cards   │   │
│  │  - Type select  │  │  - Step tracker  │  │  - Severity badges      │   │
│  │  - Submit       │  │  - Live updates  │  │  - Code snippets        │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────┘   │
│         │                       │                        │                   │
│         └───────────────────────┴────────────────────────┘                  │
│                                 │                                            │
│                         React + Shadcn UI                                    │
│                         Socket.IO Client                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                        WebSocket Connection
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY LAYER                                │
│                           🔧 NEEDS ENHANCEMENT                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Flask Application (agent_server.py)                                         │
│                                                                               │
│  Current Endpoints:            │  Required Endpoints:                        │
│  ✅ /tools                     │  ❌ POST /api/analyze                       │
│  ✅ /execute                   │  ❌ GET  /api/analysis/:id                  │
│  ✅ /health                    │  ❌ GET  /api/analyses                      │
│                                 │  ❌ DELETE /api/analysis/:id                │
│                                 │  ❌ WebSocket endpoint                       │
│                                                                               │
│  Missing:                                                                     │
│  - Pydantic request/response schemas                                         │
│  - Flask-SocketIO integration                                                │
│  - Error handling middleware                                                 │
│  - CORS configuration for React                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATION LAYER                                  │
│                           🔧 NEEDS MODIFICATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Analysis Orchestrator (analysis_orchestrator.py)                     │   │
│  │  ✅ Has: CVE retrieval, Hype decomposition, semantic search          │   │
│  │  ❌ Missing: WebSocket events, analysis type configs, progress %     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│        ┌────────────────────────┼────────────────────────┐                  │
│        │                        │                        │                   │
│  ┌─────▼─────┐          ┌──────▼──────┐        ┌───────▼────────┐         │
│  │ SHORT     │          │  MEDIUM     │        │  HARD          │         │
│  │ Analysis  │          │  Analysis   │        │  Analysis      │         │
│  │ ❌ Missing│          │  ❌ Missing │        │  ❌ Missing    │         │
│  └───────────┘          └─────────────┘        └────────────────┘         │
│  • 30% files            • 100% files            • 100% + overlap           │
│  • 5 CVEs/query         • 10 CVEs/query         • 20 CVEs/query            │
│  • 15-20 min            • 20-40 min             • 40+ min                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BUSINESS LOGIC LAYER                               │
│                           ✅ MOSTLY COMPLETE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐    │
│  │ Repository Tools   │  │ Analysis Tools      │  │ Validation       │    │
│  ├────────────────────┤  ├─────────────────────┤  ├──────────────────┤    │
│  │ ✅ Repo Loader    │  │ ✅ Project Detector │  │ 🔧 Validator     │    │
│  │ ✅ File Processor │  │ ✅ Dependency Extr. │  │ ❌ Multi-pass    │    │
│  │ ✅ Chunking       │  │ ✅ Framework Detect │  │ ❌ Confidence    │    │
│  │ ✅ Structure Map  │  │ ✅ Report Generator │  │ ❌ GPT-4 Valid   │    │
│  └────────────────────┘  └─────────────────────┘  └──────────────────┘    │
│                                                                               │
│  ┌────────────────────┐  ┌─────────────────────┐                            │
│  │ CVE Retrieval     │  │ Semantic Search     │                            │
│  ├────────────────────┤  ├─────────────────────┤                            │
│  │ ✅ Text search    │  │ ✅ FAISS for code   │                            │
│  │ ✅ Similar CVEs   │  │ 🔧 FAISS for CVEs   │ (Currently Milvus)        │
│  │ ✅ Filter by CVSS │  │ ✅ Top-K retrieval  │                            │
│  │ ✅ Get by ID      │  │ ✅ Hype queries     │                            │
│  └────────────────────┘  └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EMBEDDING LAYER                                    │
│                           🔧 NEEDS MIGRATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Current: Google Gemini          │  Required: OpenAI                         │
│  ┌──────────────────────┐        │  ┌──────────────────────┐                │
│  │ Gemini Embeddings    │        │  │ OpenAI Embeddings    │                │
│  │ Model: text-emb-004  │   VS   │  │ Model: text-emb-3-sm │                │
│  │ Dimension: 768       │        │  │ Dimension: 1536      │                │
│  │ ❌ Wrong model       │        │  │ ✅ Required model    │                │
│  └──────────────────────┘        │  └──────────────────────┘                │
│                                                                               │
│  Impact: CRITICAL - Dimension mismatch breaks similarity search              │
│  Effort: 1-2 days to update query_processor.py                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PERSISTENCE LAYER                                  │
│                           ❌ COMPLETELY MISSING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          SQLite Database                               │  │
│  │                          (Not Implemented)                             │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │  ❌ analyses table      - Analysis metadata, status, progress         │  │
│  │  ❌ code_chunks table   - File content, embeddings, line numbers      │  │
│  │  ❌ cve_findings table  - Detected vulnerabilities, confidence        │  │
│  │  ❌ cve_dataset table   - CVE reference data with embeddings          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Impact: HIGH - Cannot persist analysis results or track history             │
│  Effort: 3-5 days for SQLAlchemy models + migrations                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            VECTOR STORE LAYER                                 │
│                           🔧 NEEDS MIGRATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Codebase Vectors                │  CVE Vectors                              │
│  ┌─────────────────────┐          │  ┌─────────────────────┐                │
│  │  FAISS Index        │          │  │  Milvus DB          │                │
│  │  ✅ Local file      │    VS    │  │  ❌ External server │                │
│  │  ✅ Self-contained  │          │  │  ❌ Complex setup   │                │
│  │  ✅ Perfect for MVP │          │  │  ❌ Overkill for MVP│                │
│  └─────────────────────┘          │  └─────────────────────┘                │
│                                    │                                          │
│                                    │  Required: FAISS for CVEs               │
│                                    │  ┌─────────────────────┐                │
│                                    │  │  FAISS Index        │                │
│                                    │  │  ✅ Local file      │                │
│                                    │  │  ✅ 5420 CVEs       │                │
│                                    │  │  ✅ Simple          │                │
│                                    │  └─────────────────────┘                │
│                                                                               │
│  Impact: HIGH - Simplifies deployment, no external dependencies              │
│  Effort: 3-5 days to migrate from Milvus to FAISS                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES                                  │
│                           ✅ CONFIGURED                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐      │
│  │  Azure OpenAI    │  │  GitHub API      │  │  LangSmith (Opt.)    │      │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────────┤      │
│  │ ✅ GPT-4.1       │  │ ✅ Repo cloning  │  │ ✅ Tracking          │      │
│  │ ✅ Configured    │  │ ✅ Working       │  │ ✅ Optional          │      │
│  │ Model: gpt-4.1   │  │ Public repos     │  │ Observability        │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Coverage Analysis

### Overall System Completion

```
┌────────────────────────────────────────────────────────────┐
│  Layer                    │  Coverage  │  Status           │
├────────────────────────────────────────────────────────────┤
│  Frontend                 │    0%      │  ❌ Not started   │
│  API Gateway              │   30%      │  🔧 Needs work    │
│  Orchestration            │   70%      │  🔧 Needs config  │
│  Business Logic           │   85%      │  ✅ Mostly done   │
│  Embedding                │    0%      │  🔧 Wrong model   │
│  Persistence (DB)         │    0%      │  ❌ Not started   │
│  Vector Store (CVEs)      │    0%      │  🔧 Wrong tech    │
│  Vector Store (Code)      │  100%      │  ✅ Complete      │
│  External Services        │  100%      │  ✅ Complete      │
├────────────────────────────────────────────────────────────┤
│  TOTAL SYSTEM             │   45%      │  🔧 Needs work    │
└────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: Current vs Required

### Current Flow (Partial)

```
User
  │
  ❌ No Frontend
  │
  ▼
Agent Server (/execute endpoint)
  │
  ▼
Analysis Orchestrator
  │
  ├──► CVE Retrieval Tool
  │      └─► Milvus DB (❌ Wrong tech)
  │          └─► Gemini Embeddings (❌ Wrong model)
  │
  ├──► Codebase Indexing Tool
  │      └─► FAISS (✅ Correct)
  │          └─► Gemini Embeddings (❌ Wrong model)
  │
  ├──► File Reading
  │
  └──► Report Generation (✅ Works)
       └─► PDF + JSON
```

**Issues:**
- No real-time updates
- No persistence
- Wrong embedding model
- No analysis type selection

---

### Required Flow (Complete)

```
User
  │
  ▼
React Frontend
  │
  ├─► Repo URL input
  ├─► Analysis type (SHORT/MEDIUM/HARD)
  └─► Submit
      │
      ▼
POST /api/analyze
      │
      ▼
Flask API Gateway
  │
  ├─► Validate request (Pydantic)
  ├─► Create analysis record in SQLite
  ├─► Start background thread
  └─► Return analysis_id
      │
      ▼
WebSocket Connection Established
      │
      ▼
Analysis Orchestrator (with config)
  │
  ├─► Step 1: Clone Repo
  │    └─► Emit: "Cloning repo..." (5%)
  │
  ├─► Step 2: Analyze Structure  
  │    └─► Emit: "Analyzing structure..." (15%)
  │
  ├─► Step 3: Chunk Files (based on analysis type)
  │    │    SHORT: 30% of files
  │    │    MEDIUM: 100% of files
  │    │    HARD: 100% + fine overlap
  │    └─► Emit: "Chunking files... 45/150" (25%)
  │    └─► Store in SQLite code_chunks table
  │
  ├─► Step 4: Generate Embeddings
  │    └─► OpenAI text-embedding-3-small (✅ Correct)
  │    └─► Emit: "Generating embeddings... 230/500" (40%)
  │    └─► Store embeddings in SQLite
  │
  ├─► Step 5: Load CVE Dataset
  │    └─► FAISS Index (✅ Local)
  │    └─► Emit: "Loading CVE database..." (50%)
  │
  ├─► Step 6: CVE Retrieval (Top-K)
  │    └─► Semantic similarity search
  │    └─► Emit: "Found 15 potential CVEs" (60%)
  │
  ├─► Step 7: Query Decomposition (Hype)
  │    └─► GPT-4.1 generates search queries
  │    └─► Emit: "Decomposing queries... 8 variations" (70%)
  │
  ├─► Step 8: Semantic Search in Codebase
  │    └─► FAISS similarity search
  │    └─► Emit: "Searching codebase... query 5/8" (80%)
  │
  ├─► Step 9: Validation (NEW - Enhanced)
  │    │    Multi-pass validation:
  │    ├──► Semantic similarity (already have)
  │    ├──► Dependency version check
  │    ├──► GPT-4.1 code validation
  │    └──► Calculate confidence score
  │    └─► Emit: "Validating CVE-2023-1234... (85%)"
  │    └─► Store in cve_findings table
  │
  └─► Step 10: Generate Report
       └─► Emit: "Generating report..." (95%)
       └─► Create PDF + JSON
       └─► Update analysis status: "completed"
       └─► Emit: "Analysis complete!" (100%)
```

**Real-time Updates:**
Every step emits WebSocket events with:
- Progress percentage
- Current action
- Metadata (files processed, CVEs found, etc.)
- Timestamp

---

## 🎯 Priority Matrix

### What to Build First?

```
High Impact, Low Effort (DO FIRST)
┌──────────────────────────────────────────┐
│ 1. Switch to OpenAI embeddings (2 days) │
│ 2. Add SQLite database (3 days)         │
│ 3. Basic WebSocket events (2 days)      │
└──────────────────────────────────────────┘

High Impact, High Effort (DO SECOND)
┌──────────────────────────────────────────┐
│ 4. Build React frontend (2-3 weeks)     │
│ 5. Migrate CVE to FAISS (3-5 days)      │
└──────────────────────────────────────────┘

Medium Impact, Medium Effort (DO THIRD)
┌──────────────────────────────────────────┐
│ 6. Add analysis type configs (2 days)   │
│ 7. Enhanced validation agent (3 days)   │
└──────────────────────────────────────────┘

Low Impact, Any Effort (DO LAST)
┌──────────────────────────────────────────┐
│ 8. Polish UI/UX                          │
│ 9. Advanced filtering                    │
│ 10. Performance optimizations            │
└──────────────────────────────────────────┘
```

---

## ⚡ Quick Start Path

### Week 1: Backend Foundation

```bash
# Day 1-2: OpenAI Embeddings
- Update retrieval/query_processor.py
- Change from Gemini → OpenAI
- Test embedding generation
- Rebuild FAISS indices

# Day 3-4: SQLite Database
- Create models.py with SQLAlchemy
- Define 4 tables: analyses, code_chunks, cve_findings, cve_dataset
- Add CRUD operations
- Test persistence

# Day 5: WebSocket Setup
- Install Flask-SocketIO
- Add emit_progress() function
- Test events from analysis pipeline
```

### Week 2: API + CVE Migration

```bash
# Day 1-2: Flask API Enhancement
- Add Pydantic schemas
- Implement /api/analyze POST
- Implement /api/analysis/:id GET
- Add error handling

# Day 3-5: CVE FAISS Migration
- Create faiss_cve_manager.py
- Load CVE dataset (5420 CVEs)
- Build FAISS index
- Test similarity search
- Update retrieval_service.py
```

### Week 3-5: Frontend Development

```bash
# Week 3: Core UI
- Create React + TypeScript project
- Install Shadcn UI
- Build home page (repo input + type selector)
- Build API client

# Week 4: Progress Tracking
- Socket.IO client setup
- Progress bar component
- Step indicator
- Live metadata display

# Week 5: Results Display
- CVE findings cards
- Code snippet viewer
- Severity badges
- Report download
```

### Week 6: Testing & Polish

```bash
# Integration testing
- Test SHORT/MEDIUM/HARD modes
- Test error scenarios
- Test WebSocket reconnection

# Performance
- Optimize embedding generation
- Add caching
- Frontend optimizations

# Documentation
- Update README
- API docs
- Deployment guide
```

---

## 📦 File Structure: Current vs Required

### Current Structure

```
sem/
├── retrieval/                    ✅ Core backend
│   ├── agent_server.py          🔧 Basic Flask app
│   ├── agent_tools/             ✅ Business logic tools
│   ├── codebase_indexing/       ✅ FAISS for code
│   ├── query_processor.py       ❌ Uses Gemini
│   ├── milvus_client.py         ❌ Should be FAISS
│   └── retrieval_service.py     🔧 Needs update
├── src/                          ✅ Analysis tools
│   ├── react_agent.py           ✅ ReAct agent
│   └── tools/                   ✅ All working
└── main.py                       ✅ CLI interface
```

### Required Structure

```
sem/
├── backend/                      🆕 Reorganized backend
│   ├── app.py                   🆕 Main Flask app with SocketIO
│   ├── models.py                🆕 SQLAlchemy models
│   ├── schemas.py               🆕 Pydantic request/response
│   ├── routes/                  🆕 API routes
│   │   ├── analyze.py
│   │   └── results.py
│   ├── services/                🔧 Refactored services
│   │   ├── orchestrator.py     (from analysis_orchestrator)
│   │   ├── embeddings.py       🆕 OpenAI embeddings
│   │   ├── cve_manager.py      🆕 FAISS for CVEs
│   │   └── validator.py        🆕 Enhanced validation
│   ├── database/                🆕 Database layer
│   │   ├── sqlite_manager.py
│   │   └── migrations/
│   └── tools/                   ✅ Reuse existing
│
├── frontend/                     🆕 React application
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Analysis.tsx
│   │   │   └── Results.tsx
│   │   ├── components/
│   │   │   ├── RepoInput.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   ├── CVECard.tsx
│   │   │   └── CodeSnippet.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── data/                         🆕 Local data storage
│   ├── cve_embeddings.faiss
│   ├── cve_metadata.pkl
│   └── analyses.db              (SQLite)
│
└── docs/                         ✅ Documentation
    ├── STRATEGIC_ANALYSIS.md
    ├── TOOLS_CATALOG.md
    └── API_REFERENCE.md          🆕 To be created
```

---

## 🚀 Success Checklist

### Phase 1: Backend (Week 1-2) ✅ or ❌

- [ ] OpenAI embeddings working
- [ ] SQLite database created
- [ ] WebSocket emitting events
- [ ] CVE FAISS index built
- [ ] API endpoints responding
- [ ] Analysis pipeline runs end-to-end

### Phase 2: Frontend (Week 3-5) ✅ or ❌

- [ ] React app runs locally
- [ ] Can submit repo URL
- [ ] WebSocket connects
- [ ] Progress bar updates
- [ ] Results display correctly
- [ ] Report downloads

### Phase 3: Integration (Week 6) ✅ or ❌

- [ ] Full workflow works (URL → Report)
- [ ] SHORT mode: <20 minutes
- [ ] MEDIUM mode: <40 minutes
- [ ] No crashes on large repos
- [ ] Error handling works
- [ ] Documentation complete

---

## 🎓 Key Learnings

### What Works Well ✅
- Modular tool architecture is excellent
- FAISS for codebase search is perfect
- Report generation is solid
- Repository analysis tools are comprehensive

### What Needs Work 🔧
- Technology stack misalignment (Gemini → OpenAI, Milvus → FAISS)
- No persistence layer (critical for web app)
- No real-time communication
- No frontend (obviously critical)

### What's Missing ❌
- Analysis type configurations
- Multi-pass validation
- Confidence scoring
- WebSocket infrastructure
- Complete API layer
- Frontend application

---

## 💰 Estimated Costs

### Development Time
- Backend refactor: 2 weeks
- Frontend build: 3 weeks
- Testing & polish: 1 week
- **Total: 6 weeks**

### Operational Costs (per analysis)
- OpenAI Embeddings: ~$5-10
- GPT-4 Turbo: ~$2-5
- **Total per analysis: $7-15**

### Infrastructure (Monthly)
- Hosting (Digital Ocean/Heroku): $20-50
- OpenAI API: Variable ($200-500 for 50 analyses)
- **Total: $220-550/month**

---

*Architecture comparison prepared for Agent Axios*  
*Last Updated: November 7, 2025*
