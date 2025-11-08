# 📋 Quick Reference - Curl Commands

## Backend URL
```
http://140.238.227.29:5000
```

---

## 🔍 All Available Endpoints

### 1️⃣ Health Check
```bash
curl --location 'http://140.238.227.29:5000/api/health'
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T14:30:00.000000"
}
```

---

### 2️⃣ Create Analysis - SHORT (Quick Scan)
```bash
curl --location 'http://140.238.227.29:5000/api/analysis' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/pallets/flask",
    "analysis_type": "SHORT"
}'
```

**Duration:** 2-3 minutes  
**Validation:** No GPT-4 validation  
**Files:** Max 500

---

### 3️⃣ Create Analysis - MEDIUM (Recommended) ⭐
```bash
curl --location 'http://140.238.227.29:5000/api/analysis' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/django/django",
    "analysis_type": "MEDIUM"
}'
```

**Duration:** 5-10 minutes  
**Validation:** ✅ GPT-4 validation enabled  
**Files:** Max 2000

---

### 4️⃣ Create Analysis - HARD (Deep Scan)
```bash
curl --location 'http://140.238.227.29:5000/api/analysis' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/expressjs/express",
    "analysis_type": "HARD"
}'
```

**Duration:** 15-40 minutes  
**Validation:** ✅ GPT-4 validation enabled  
**Files:** Unlimited

---

### 5️⃣ Get Analysis Status
```bash
# Replace 123 with your analysis_id from create response
curl --location 'http://140.238.227.29:5000/api/analysis/123'
```

**Response Fields:**
- `status`: `pending` | `running` | `completed` | `failed`
- `total_files`: Number of files analyzed
- `total_chunks`: Code chunks processed
- `total_findings`: Vulnerabilities found

---

### 6️⃣ Get Analysis Results (After Completion)
```bash
# Replace 123 with your analysis_id
curl --location 'http://140.238.227.29:5000/api/analysis/123/results'
```

**Only works when `status` = `"completed"`**

**Response includes:**
- Full analysis details
- Summary statistics
- Severity breakdown (CRITICAL/HIGH/MEDIUM/LOW)
- Complete list of CVE findings
- File paths and confidence scores

---

### 7️⃣ List All Analyses
```bash
# Get all analyses
curl --location 'http://140.238.227.29:5000/api/analyses'

# With pagination
curl --location 'http://140.238.227.29:5000/api/analyses?page=1&per_page=20'

# Filter by status
curl --location 'http://140.238.227.29:5000/api/analyses?status=completed'
```

---

## 🔄 Complete Workflow Example

### Step 1: Create Analysis
```bash
curl --location 'http://140.238.227.29:5000/api/analysis' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/pallets/flask",
    "analysis_type": "MEDIUM"
}'
```

**Save the `analysis_id` from response** (e.g., 123)

---

### Step 2: Check Status (Repeat Until Completed)
```bash
curl --location 'http://140.238.227.29:5000/api/analysis/123'
```

Watch for `status` field:
- `pending` → Analysis queued
- `running` → In progress
- `completed` → ✅ Done!
- `failed` → ❌ Error

---

### Step 3: Get Results
```bash
curl --location 'http://140.238.227.29:5000/api/analysis/123/results'
```

---

## 🌐 WebSocket Connection (For Real-Time Updates)

**Instead of polling, connect to WebSocket:**

```
ws://140.238.227.29:5000/analysis
```

**Events:**
- `start_analysis` (send) → Start the agent
- `progress_update` (receive) → Get 0-100% progress
- `analysis_complete` (receive) → Done!

**See `BACKEND_INTEGRATION.md` for full WebSocket guide**

---

## 📊 Response Examples

### Create Analysis Response:
```json
{
  "analysis_id": 123,
  "repo_url": "https://github.com/pallets/flask",
  "analysis_type": "MEDIUM",
  "status": "pending",
  "total_files": 0,
  "total_chunks": 0,
  "total_findings": 0,
  "created_at": "2025-11-08T14:30:00.000000"
}
```

### Get Status Response (Running):
```json
{
  "analysis_id": 123,
  "status": "running",
  "total_files": 150,
  "total_chunks": 450,
  "total_findings": 3,
  "start_time": "2025-11-08T14:30:00.000000"
}
```

### Get Results Response (Completed):
```json
{
  "analysis": {
    "analysis_id": 123,
    "status": "completed",
    "total_files": 523,
    "total_chunks": 1247,
    "total_findings": 5
  },
  "summary": {
    "confirmed_vulnerabilities": 3,
    "false_positives": 2,
    "severity_breakdown": {
      "CRITICAL": 1,
      "HIGH": 1,
      "MEDIUM": 1,
      "LOW": 0
    }
  },
  "findings": [
    {
      "cve_id": "CVE-2021-44228",
      "file_path": "src/logger.py",
      "severity": "CRITICAL",
      "confidence_score": 0.95,
      "validation_status": "confirmed"
    }
  ]
}
```

---

## ⚠️ Common Errors

### Missing repo_url:
```json
{
  "error": "repo_url is required"
}
```

### Invalid analysis_type:
```json
{
  "error": "analysis_type must be SHORT, MEDIUM, or HARD"
}
```

### Analysis not found:
```json
{
  "error": "Analysis not found"
}
```

### Results not ready:
```json
{
  "error": "Analysis not completed yet"
}
```

---

## 🚀 Quick Test Script

Save as `test_api.sh` (Linux/Mac) or `test_api.ps1` (Windows):

### Bash (Linux/Mac):
```bash
#!/bin/bash

echo "1. Health Check..."
curl http://140.238.227.29:5000/api/health

echo -e "\n\n2. Creating Analysis..."
RESPONSE=$(curl -s -X POST http://140.238.227.29:5000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/pallets/flask","analysis_type":"SHORT"}')

echo $RESPONSE

ANALYSIS_ID=$(echo $RESPONSE | grep -o '"analysis_id":[0-9]*' | grep -o '[0-9]*')
echo -e "\nAnalysis ID: $ANALYSIS_ID"

echo -e "\n\n3. Checking Status..."
curl http://140.238.227.29:5000/api/analysis/$ANALYSIS_ID

echo -e "\n\nDone! Check status again in a few minutes, then run:"
echo "curl http://140.238.227.29:5000/api/analysis/$ANALYSIS_ID/results"
```

### PowerShell (Windows):
```powershell
# 1. Health Check
Write-Host "1. Health Check..."
$health = Invoke-RestMethod -Uri "http://140.238.227.29:5000/api/health"
$health | ConvertTo-Json

# 2. Create Analysis
Write-Host "`n2. Creating Analysis..."
$body = @{
    repo_url = "https://github.com/pallets/flask"
    analysis_type = "SHORT"
} | ConvertTo-Json

$analysis = Invoke-RestMethod -Method Post `
    -Uri "http://140.238.227.29:5000/api/analysis" `
    -ContentType "application/json" `
    -Body $body

$analysis | ConvertTo-Json
$analysisId = $analysis.analysis_id

# 3. Check Status
Write-Host "`n3. Checking Status..."
$status = Invoke-RestMethod -Uri "http://140.238.227.29:5000/api/analysis/$analysisId"
$status | ConvertTo-Json

Write-Host "`nDone! Check status again in a few minutes, then run:"
Write-Host "Invoke-RestMethod -Uri 'http://140.238.227.29:5000/api/analysis/$analysisId/results'"
```

---

## 📱 For Chat Interface Integration

**The frontend automatically uses these endpoints!**

When user types:
```
https://github.com/pallets/flask
```

Backend flow:
1. `POST /api/analysis` - Create analysis
2. WebSocket `/analysis` - Connect for real-time updates
3. `GET /api/analysis/:id/results` - Fetch final results

**All handled by `src/services/api.ts` ✅**

---

## 🔗 Related Documentation

- **Full Integration Guide:** `BACKEND_INTEGRATION.md`
- **Testing Guide:** `QUICK_TEST_GUIDE.md`
- **Summary:** `INTEGRATION_SUMMARY.md`
- **Original Backend Docs:** `agent-axios-backend/API_CURL_COMMANDS.md`

---

## 📞 Quick Help

**Need to test?**
```bash
curl http://140.238.227.29:5000/api/health
```

**Start analysis?**
```bash
curl -X POST http://140.238.227.29:5000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"YOUR_GITHUB_URL","analysis_type":"MEDIUM"}'
```

**Check results?**
```bash
curl http://140.238.227.29:5000/api/analysis/YOUR_ID/results
```

---

**✨ That's it! Your backend is ready to analyze repositories! 🚀**
