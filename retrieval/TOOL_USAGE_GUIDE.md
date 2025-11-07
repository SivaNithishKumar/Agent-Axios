# AI Agent Tools - Complete Usage Guide

## Overview

Both tools work automatically via the `/execute` endpoint. No need for separate endpoints!

## Configuration (.env file)

Create a `.env` file in the root directory:

```env
# Codebase Configuration
CODEBASE_PATH=F:\Programs\Vuln_detection\app\retrieval
FAISS_DB_PATH=codebase_faiss_db

# MongoDB Configuration (optional)
MONGODB_URI=mongodb://adya_vanij_user:adya_vanij_user@4.240.98.192:27020/vanij_db
```

## Tool 1: CVE Retrieval Tool

### Action: analyze_markdown
Analyzes markdown security reports and finds relevant CVEs.

**curl Example:**
```bash
curl --location 'http://localhost:5000/execute' \
  --header 'Content-Type: application/json' \
  --data '{
    "tool": "cve_retrieval",
    "parameters": {
      "action": "analyze_markdown",
      "markdown_report": "# Security Analysis\n- SQL injection\n- Buffer overflow\n- XSS",
      "top_k": 10
    }
  }'
```

**PowerShell Example:**
```powershell
$body = @{
    tool = "cve_retrieval"
    parameters = @{
        action = "analyze_markdown"
        markdown_report = "SQL injection, buffer overflow, XSS vulnerabilities"
        top_k = 10
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
```

**Response Format:**
```json
{
  "success": true,
  "tool": "cve_retrieval",
  "result": {
    "success": true,
    "count": 10,
    "message": "Successfully retrieved 10 vulnerabilities",
    "vulnerabilities": [
      {
        "cve_id": "CVE-1999-0276",
        "summary": "mSQL v2.0.1 and below allows remote execution through a buffer overflow.",
        "cvss_score": 7.5,
        "cvss_vector": "AV:N/AC:L/Au:N/C:P/I:P/A:P",
        "severity": "HIGH",
        "similarity_score": 0.676542,
        "rerank_score": 0.0,
        "rank": 1
      }
    ]
  }
}
```

## Tool 2: Codebase Indexing Tool

### Action: auto_index
Automatically indexes the codebase from `.env` configuration. Each file becomes one chunk in FAISS.

**curl Example:**
```bash
curl --location 'http://localhost:5000/execute' \
  --header 'Content-Type: application/json' \
  --data '{
    "tool": "codebase_indexing",
    "parameters": {
      "action": "auto_index",
      "overwrite": true
    }
  }'
```

**PowerShell Example:**
```powershell
$body = @{
    tool = "codebase_indexing"
    parameters = @{
        action = "auto_index"
        overwrite = $true
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
```

**Response Format:**
```json
{
  "success": true,
  "tool": "codebase_indexing",
  "result": {
    "success": true,
    "message": "Successfully indexed 150 files from .env config",
    "stats": {
      "total_files": 150,
      "files_processed": 150,
      "codebase_path": "F:\\Programs\\Vuln_detection\\app\\retrieval",
      "database_path": "codebase_faiss_db",
      "time_taken": 45.2
    }
  }
}
```

### Action: search
Search the indexed codebase with natural language query.

**curl Example:**
```bash
curl --location 'http://localhost:5000/execute' \
  --header 'Content-Type: application/json' \
  --data '{
    "tool": "codebase_indexing",
    "parameters": {
      "action": "search",
      "query": "authentication and login functions",
      "top_k": 5
    }
  }'
```

**PowerShell Example:**
```powershell
$body = @{
    tool = "codebase_indexing"
    parameters = @{
        action = "search"
        query = "authentication and login functions"
        top_k = 5
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
```

**Response Format:**
```json
{
  "success": true,
  "tool": "codebase_indexing",
  "result": {
    "tool": "codebase_indexing",
    "action": "search",
    "success": true,
    "data": {
      "query": "authentication and login functions",
      "results": [
        {
          "file_path": "agent_tools/base_tool.py",
          "content": "def initialize(self) -> bool...",
          "score": 0.89,
          "relative_path": "agent_tools/base_tool.py"
        }
      ],
      "total_results": 5
    }
  }
}
```

## Complete Workflow Example

### Step 1: Index the Codebase
```powershell
# This reads CODEBASE_PATH from .env and indexes all files
$body = @{
    tool = "codebase_indexing"
    parameters = @{
        action = "auto_index"
        overwrite = $true
    }
} | ConvertTo-Json -Depth 5

$indexResult = Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
Write-Host "Indexed $($indexResult.result.stats.total_files) files"
```

### Step 2: Search the Codebase
```powershell
$body = @{
    tool = "codebase_indexing"
    parameters = @{
        action = "search"
        query = "tool initialization and setup"
        top_k = 5
    }
} | ConvertTo-Json -Depth 5

$searchResult = Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
$searchResult.result.data.results | ForEach-Object {
    Write-Host "File: $($_.file_path) (Score: $($_.score))"
}
```

### Step 3: Analyze Security
```powershell
$body = @{
    tool = "cve_retrieval"
    parameters = @{
        action = "analyze_markdown"
        markdown_report = "Found SQL injection and buffer overflow vulnerabilities"
        top_k = 10
    }
} | ConvertTo-Json -Depth 5

$cveResult = Invoke-RestMethod -Uri 'http://localhost:5000/execute' -Method Post -Body $body -ContentType 'application/json'
$cveResult.result.vulnerabilities | ForEach-Object {
    Write-Host "CVE: $($_.cve_id) - Severity: $($_.severity) - Score: $($_.cvss_score)"
}
```

## Key Features

### Codebase Indexing
- ✅ Automatically reads path from `.env`
- ✅ Each file = one chunk in FAISS
- ✅ Recursively scans all folders
- ✅ Supports 40+ file types (.py, .js, .java, etc.)
- ✅ Skips unnecessary directories (node_modules, __pycache__, etc.)
- ✅ Configurable file size limit
- ✅ Batch processing for large codebases

### CVE Retrieval
- ✅ Extracts keywords from markdown
- ✅ Searches Milvus vector database
- ✅ Returns CVEs with all details (ID, summary, CVSS, severity)
- ✅ Includes similarity scores
- ✅ No CVSS filtering - pure text-based search

## Tool Discovery

List all available tools and their actions:
```bash
curl http://localhost:5000/tools
```

## Health Check

```bash
curl http://localhost:5000/health
```

## Error Handling

All responses include a `success` field:
```json
{
  "success": false,
  "tool": "codebase_indexing",
  "error": "Codebase path from .env does not exist"
}
```

---

**Server**: http://localhost:5000
**API Docs**: http://localhost:5000/docs
