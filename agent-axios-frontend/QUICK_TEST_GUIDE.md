# Quick Test Guide - Chat Interface Integration

## 🎯 Test Your Integration in 3 Steps

### Step 1: Start Backend (if not already running)
The backend is already running at:
```
http://140.238.227.29:5000
```

### Step 2: Start Frontend
```bash
cd agent-axios-frontend
npm run dev
```

### Step 3: Test in Chat Interface

Open your browser and navigate to the Dashboard. Try these test messages:

---

## ✅ Test Cases

### Test 1: Simple GitHub URL
**Message:**
```
https://github.com/pallets/flask
```

**Expected Behavior:**
1. ✅ URL detected automatically
2. ✅ Analysis created (MEDIUM type by default)
3. ✅ WebSocket connection established
4. ✅ Progress bar appears showing 0-100%
5. ✅ Real-time updates: "Cloning repository..." → "Parsing code..." → etc.
6. ✅ Findings appear as they're discovered
7. ✅ Final summary with vulnerability counts
8. ✅ Analysis completes successfully

---

### Test 2: Quick Scan
**Message:**
```
quick scan https://github.com/django/django
```

**Expected Behavior:**
1. ✅ Detects "quick" keyword
2. ✅ Uses SHORT analysis type
3. ✅ Completes in ~2-3 minutes
4. ✅ No AI validation (faster)

---

### Test 3: Deep Scan
**Message:**
```
deep analysis of https://github.com/expressjs/express
```

**Expected Behavior:**
1. ✅ Detects "deep" keyword
2. ✅ Uses HARD analysis type
3. ✅ Takes 15-40 minutes
4. ✅ Includes AI validation
5. ✅ Comprehensive results

---

### Test 4: Invalid Input
**Message:**
```
What are CVEs?
```

**Expected Behavior:**
1. ✅ No GitHub URL detected
2. ✅ Helpful response asking for GitHub URL
3. ✅ Shows example format
4. ✅ Explains analysis types

---

## 🔍 What to Watch For

### In Browser Console:
```
✅ Connected to analysis agent
🚀 Analysis started: { analysis_id: 123, ... }
⚡ 0% - cloning: Cloning repository...
⚡ 20% - chunking: Parsing code files...
⚡ 55% - searching: Searching CVE database...
📦 Intermediate result: { cve_id: "CVE-2024-12345", ... }
🎉 Analysis complete! { status: "completed", total_findings: 5 }
```

### In Chat Interface:
1. User message appears immediately
2. "🚀 Analysis started..." message
3. "✅ Analysis started" confirmation
4. **Progress bar component** showing:
   - Current stage (with icon)
   - Percentage (0-100%)
   - Stage description
5. Real-time vulnerability findings
6. Final summary with statistics

---

## 🛠️ Troubleshooting

### Issue: "Cannot find module 'socket.io-client'"
**Solution:** Already installed! ✅
```bash
npm install socket.io-client
```

### Issue: "Failed to start analysis"
**Check:**
1. Backend is running at `http://140.238.227.29:5000`
2. Run health check:
   ```bash
   curl http://140.238.227.29:5000/api/health
   ```
3. Check browser console for errors
4. Verify network connectivity

### Issue: "Analysis not completing"
**Check:**
1. Browser console for WebSocket connection
2. Look for `analysis_complete` event
3. Check backend logs if accessible
4. Try a smaller repository first

### Issue: Progress stuck at 0%
**Solution:**
- WebSocket might not be connected
- Check browser DevTools → Network → WS tab
- Should show connection to `/analysis`
- Verify `start_analysis` event was sent

---

## 🎨 UI States

### State 1: Initial Welcome
```
👋 Welcome! I'm your AI-powered CVE analysis assistant...
```
- Shows 3 quick action cards
- Empty chat state

### State 2: User Sends URL
```
User: https://github.com/pallets/flask
```

### State 3: Analysis Starting
```
Assistant: 🚀 Analysis started for **https://github.com/pallets/flask**

Analysis Type: **MEDIUM**
Analysis ID: 123

Connecting to analysis agent...
```

### State 4: Analysis Running
```
Assistant: ✅ Analysis started

Starting automated security scan...
```
**+ Progress Bar Component:**
- ✅ Cloning repository (complete)
- 🔄 Parsing code files (active - spinning icon)
- ⭕ Generating embeddings (pending)
- ⭕ Searching CVE database (pending)
- ⭕ Validating findings (pending)
- ⭕ Generating report (pending)

Progress: 35% ████████░░░░░░░░░░░

### State 5: Findings Discovered
```
Assistant: 🔍 Found vulnerability: **CVE-2021-44228**
- File: `src/logger.py`
- Severity: **CRITICAL**
- Confidence: 95.0%
```
(Multiple findings appear as discovered)

### State 6: Analysis Complete
```
Assistant: 🎉 **Analysis Complete!**

**Summary:**
- Total Files: 523
- Code Chunks: 1247
- Vulnerabilities Found: 5
- Confirmed: 3
- False Positives: 2

**Severity Breakdown:**
- CRITICAL: 1
- HIGH: 1
- MEDIUM: 1

**Duration:** 180s

Would you like me to show detailed findings?
```

---

## 📊 Expected Timing

| Analysis Type | Duration | Validation | Files Limit |
|--------------|----------|------------|-------------|
| SHORT        | 2-3 min  | ❌ No      | 500         |
| MEDIUM       | 5-10 min | ✅ Yes     | 2000        |
| HARD         | 15-40 min| ✅ Yes     | ♾️ Unlimited |

---

## 🎬 Demo Script

1. **Open Dashboard** → Navigate to Chat Interface
2. **Type:** `https://github.com/pallets/flask`
3. **Press Enter** → Watch analysis start
4. **Observe:**
   - Progress bar advancing through stages
   - Real-time vulnerability findings
   - Completion summary
5. **Try another:** `quick scan https://github.com/your-repo`
6. **Compare results** between SHORT and MEDIUM types

---

## ✨ Success Indicators

- ✅ Chat messages flowing naturally
- ✅ Progress bar updating smoothly
- ✅ Real-time findings appearing
- ✅ Completion message with statistics
- ✅ No console errors
- ✅ WebSocket connected (check DevTools)
- ✅ Analysis ID assigned
- ✅ Proper error handling if URL invalid

---

## 🐛 Debug Mode

Add this to test the API directly:

```typescript
// In browser console
import { healthCheck, createAnalysis } from '@/services/api';

// Test health
await healthCheck();

// Test create analysis
await createAnalysis('https://github.com/pallets/flask', 'SHORT');
```

Or use curl:

```bash
# Health check
curl http://140.238.227.29:5000/api/health

# Create analysis
curl -X POST http://140.238.227.29:5000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/pallets/flask","analysis_type":"SHORT"}'

# Check status
curl http://140.238.227.29:5000/api/analysis/123

# Get results (after completion)
curl http://140.238.227.29:5000/api/analysis/123/results
```

---

## 🎉 You're All Set!

The integration is complete and ready to test. The ChatInterface now:
- ✅ Detects GitHub URLs automatically
- ✅ Creates analyses via REST API
- ✅ Connects to WebSocket for real-time updates
- ✅ Shows dynamic progress bars
- ✅ Streams vulnerability findings
- ✅ Displays comprehensive results
- ✅ Handles errors gracefully

**Just paste a GitHub URL and watch the magic happen! 🚀**
