# How to Run the AI Agent Server

## Simple Start

```bash
python agent_server.py
```

The server will start on **http://localhost:5000**

## What Happens When You Start

1. **Server initializes** all AI tools
2. **Connects to Milvus** (CVE vector database)
3. **Loads FAISS** (code indexing database if exists)
4. **Ready to accept** tool execution requests

## Test if Running

```bash
# Health check
curl http://localhost:5000/health

# List available tools
curl http://localhost:5000/tools
```

## Example Usage

### 1. Search CVE Vulnerabilities
```bash
curl -X POST http://localhost:5000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"tool\":\"cve_retrieval\",\"parameters\":{\"action\":\"analyze_markdown\",\"markdown_report\":\"SQL injection vulnerability found\",\"top_k\":10}}"
```

### 2. Auto-Index Codebase (from .env)
```bash
curl -X POST http://localhost:5000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"tool\":\"codebase_indexing\",\"parameters\":{\"action\":\"auto_index\",\"overwrite\":true}}"
```

### 3. Search Code
```bash
curl -X POST http://localhost:5000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"tool\":\"codebase_indexing\",\"parameters\":{\"action\":\"search\",\"query\":\"authentication logic\",\"top_k\":5}}"
```

## PowerShell Version

```powershell
# Start server
python agent_server.py

# Test health
Invoke-RestMethod -Uri http://localhost:5000/health

# Execute CVE tool
$body = @{
    tool = "cve_retrieval"
    parameters = @{
        action = "analyze_markdown"
        markdown_report = "SQL injection found"
        top_k = 10
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri http://localhost:5000/execute -Method Post -Body $body -ContentType 'application/json'
```

## Configuration

Edit `.env` file before starting:

```env
CODEBASE_PATH=F:\Programs\Vuln_detection\app\retrieval\codebase_indexing\flask
FAISS_DB_PATH=codebase_faiss_db
MONGODB_URI=mongodb://user:pass@host:port/db
```

## Server Configuration

Edit `config.py` to change:
- API_HOST (default: "0.0.0.0")
- API_PORT (default: 5000)
- API_DEBUG (default: True)

## Logs

Server logs are saved to: `logs/retrieval_service.log`

## Stop Server

Press `Ctrl+C` in the terminal
