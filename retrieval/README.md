# AI Agent Tools - Retrieval Service

Clean AI agent tool server for CVE vulnerability search and codebase indexing.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env
CODEBASE_PATH=F:\Programs\Vuln_detection\app\retrieval
FAISS_DB_PATH=codebase_faiss_db

# Run server
python agent_server.py
```

**Server:** http://localhost:5000

## Tools

**1. CVE Retrieval** - Search vulnerabilities from markdown reports  
**2. Codebase Indexing** - Index and search code with semantic search

## Usage

All tools via `/execute` endpoint:

```bash
# CVE Search
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"cve_retrieval","parameters":{"action":"analyze_markdown","markdown_report":"SQL injection","top_k":10}}'

# Auto-index from .env
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"codebase_indexing","parameters":{"action":"auto_index"}}'

# Search code
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"codebase_indexing","parameters":{"action":"search","query":"authentication"}}'
```

## Endpoints

- `POST /execute` - Execute tools
- `GET /tools` - List tools
- `GET /health` - Health check

## Documentation

See `TOOL_USAGE_GUIDE.md` for complete docs.
