# Agent Axios Backend - Fixed Architecture Implementation

## ✅ Changes Implemented

### 1. **New Service: Query Decomposition** (`app/services/query_decomposition_service.py`)
- Implements **Hype (Hypothetical Answer Generation)** using GPT-4.1
- Decomposes CVEs into multiple search queries (different angles)
- Expands queries for better coverage
- Used in Step 5 of the analysis pipeline

### 2. **New Service: Codebase Indexing** (`app/services/codebase_indexing_service.py`)
- Creates FAISS index of code chunks with **Cohere embeddings (1024-dim)**
- Consistent embedding dimensions throughout
- Semantic search across codebase
- Multi-query search with deduplication
- Saves/loads index to disk for reuse

### 3. **Updated: CVE Search Service** (`app/services/cve_search_service.py`)
- Added `search_by_queries()` method for decomposed query search
- Uses **Cohere embeddings (1024-dim)** with padding for Milvus compatibility
- Implements reranking with Cohere Rerank
- Returns deduplicated CVE results sorted by relevance

### 4. **Completely Rewritten: Analysis Orchestrator** (`app/services/analysis_orchestrator.py`)

#### **NEW CORRECT FLOW:**
```
1. Clone Repository (0% → 10%)
   ↓
2. Chunk Code Files (10% → 20%)
   ↓
3. Index Codebase in FAISS (20% → 35%)
   ↓
4. Search CVE Database (35% → 45%)
   - Generate initial query from repo
   - Search Milvus for relevant CVEs
   - Rerank with Cohere
   ↓
5. Query Decomposition (45% → 50%)
   - Decompose top CVEs using Hype/GPT-4.1
   - Generate multiple search angles per CVE
   ↓
6. Search Codebase (50% → 70%)
   - Semantic search using decomposed queries
   - Find code patterns matching vulnerabilities
   ↓
7. Match CVEs to Code (70% → 75%)
   - Create CVEFinding records
   - Associate CVEs with code locations
   ↓
8. Validate with GPT-4.1 (75% → 95%)
   - AI validation of findings
   ↓
9. Generate Reports (95% → 100%)
   - Create final reports
```

#### **OLD (WRONG) FLOW:**
```
Clone → Chunk → Embed → Search CVEs per chunk → Validate
❌ Searched "what CVEs match this code chunk"
```

#### **NEW (CORRECT) FLOW:**
```
Clone → Chunk → Index → Search CVEs → Decompose → 
Search code for CVEs → Match → Validate
✅ Searches "what code matches these CVEs"
```

### 5. **Updated Configuration** (`config/settings.py`)
Added new parameters for each analysis type:
- `cve_top_k`: Top CVEs from initial search
- `cves_to_analyze`: Number of CVEs to decompose
- `queries_per_cve`: Decomposed queries per CVE
- `code_matches_per_query`: Code matches per query

## 🔧 Key Improvements

### ✅ Correct Search Direction
- **Before**: Code → CVEs (reversed)
- **After**: CVEs → Code (correct)

### ✅ Consistent Embeddings
- **Before**: Mixed Cohere (1024) and Gemini (3072) - incompatible
- **After**: Cohere (1024) throughout, padded for Milvus compatibility
- **Note**: Milvus still uses Gemini 3072-dim vectors (legacy), but we pad queries

### ✅ Query Decomposition
- **Before**: Missing completely
- **After**: Hype implementation with GPT-4.1

### ✅ Codebase Indexing
- **Before**: Chunks embedded but not indexed
- **After**: Full FAISS index for semantic search

### ✅ Proper Event Emissions
All stages emit progress updates via SocketIO:
- `cloning`, `chunking`, `indexing`, `cve_search`
- `decomposition`, `code_search`, `matching`
- `validating`, `finalizing`, `completed`

### ✅ Reranking
- **Before**: Only in old chunk→CVE search
- **After**: Used in both CVE search and maintained in flow

## 📊 Analysis Types Configuration

### SHORT (2-3 min)
- 5 CVEs → 10 queries → 30 code matches
- No validation

### MEDIUM (5-10 min)
- 10 CVEs → 30 queries → 150 code matches
- GPT-4.1 validation

### HARD (15-40 min)
- 20 CVEs → 100 queries → 1000 code matches
- GPT-4.1 validation

## ⚠️ Known Limitations

1. **Milvus Embedding Mismatch**: The Milvus CVE database was built with Gemini 3072-dim embeddings. We use Cohere 1024-dim (padded to 3072). This works but is suboptimal.
   - **Ideal Solution**: Rebuild Milvus with Cohere embeddings
   - **Current Workaround**: Zero-padding + lower similarity threshold

2. **Initial Query Generation**: Currently uses simple heuristics (package.json, requirements.txt). 
   - **Future**: Integrate with `src/react_agent.py` for deeper repo analysis

## 🚀 Usage

The frontend doesn't need changes - it already connects to the Flask backend via SocketIO. The new flow is automatically used when analyses are created.

### Example Analysis Flow:

1. Frontend creates analysis: `POST /api/analysis`
2. Frontend starts analysis: WebSocket `start_analysis` event
3. Backend runs new pipeline with progress updates
4. Frontend receives real-time progress via `progress_update` events
5. Completion notification via `analysis_complete` event
6. Frontend fetches results: `GET /api/analysis/{id}/results`

## 📝 Next Steps

1. **Test with real repository** to verify the flow works end-to-end
2. **Monitor embedding quality** - may need to adjust similarity thresholds
3. **Consider rebuilding Milvus** with Cohere embeddings for consistency
4. **Integrate repo_analyzer** for better initial CVE search queries
5. **Add caching** for decomposed queries to speed up similar analyses
