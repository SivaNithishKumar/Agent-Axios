# Backend Integration Guide

## 🌐 API Configuration

**Backend URL:** `http://140.238.227.29:5000`  
**WebSocket URL:** `http://140.238.227.29:5000/analysis`

---

## 📡 Available Endpoints

### 1. Health Check
```bash
curl -X GET http://140.238.227.29:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T14:30:00.000000"
}
```

---

### 2. Create Analysis (Main Entry Point)

**Endpoint:** `POST /api/analysis`

**Request:**
```bash
curl --location 'http://140.238.227.29:5000/api/analysis' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/pallets/flask",
    "analysis_type": "SHORT"
}'
```

**Request Body:**
```typescript
{
  repo_url: string;          // GitHub repository URL
  analysis_type: "SHORT" | "MEDIUM" | "HARD";
  config?: {                 // Optional custom configuration
    max_files?: number;
    max_chunks_per_file?: number;
    // ... other configs
  }
}
```

**Response:**
```json
{
  "analysis_id": 123,
  "repo_url": "https://github.com/pallets/flask",
  "analysis_type": "SHORT",
  "status": "pending",
  "start_time": null,
  "end_time": null,
  "config": null,
  "error_message": null,
  "total_files": 0,
  "total_chunks": 0,
  "total_findings": 0,
  "created_at": "2025-11-08T14:30:00.000000",
  "updated_at": "2025-11-08T14:30:00.000000"
}
```

---

### 3. Get Analysis Status

**Endpoint:** `GET /api/analysis/:id`

```bash
curl --location 'http://140.238.227.29:5000/api/analysis/123'
```

**Response:**
```json
{
  "analysis_id": 123,
  "repo_url": "https://github.com/pallets/flask",
  "analysis_type": "SHORT",
  "status": "running",  // pending | running | completed | failed
  "start_time": "2025-11-08T14:30:00.000000",
  "end_time": null,
  "total_files": 150,
  "total_chunks": 450,
  "total_findings": 3,
  "created_at": "2025-11-08T14:30:00.000000",
  "updated_at": "2025-11-08T14:31:00.000000"
}
```

---

### 4. Get Analysis Results

**Endpoint:** `GET /api/analysis/:id/results`

```bash
curl --location 'http://140.238.227.29:5000/api/analysis/123/results'
```

**Response:**
```json
{
  "analysis": {
    "analysis_id": 123,
    "repo_url": "https://github.com/pallets/flask",
    "analysis_type": "SHORT",
    "status": "completed",
    "start_time": "2025-11-08T14:30:00.000000",
    "end_time": "2025-11-08T14:33:00.000000",
    "total_files": 523,
    "total_chunks": 1247,
    "total_findings": 5
  },
  "summary": {
    "total_files": 523,
    "total_chunks": 1247,
    "total_findings": 5,
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
      "finding_id": 1,
      "analysis_id": 123,
      "cve_id": "CVE-2021-44228",
      "file_path": "src/logger.py",
      "chunk_id": 45,
      "severity": "CRITICAL",
      "confidence_score": 0.95,
      "validation_status": "confirmed",
      "validation_explanation": "Log4j vulnerability pattern detected",
      "cve_description": "Apache Log4j2 Remote Code Execution",
      "created_at": "2025-11-08T14:32:00.000000",
      "updated_at": "2025-11-08T14:32:30.000000"
    }
  ]
}
```

---

### 5. List All Analyses

**Endpoint:** `GET /api/analyses`

```bash
curl --location 'http://140.238.227.29:5000/api/analyses'
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `status` (optional): Filter by status (pending/running/completed/failed)

**Response:**
```json
{
  "analyses": [
    {
      "analysis_id": 123,
      "repo_url": "https://github.com/pallets/flask",
      "analysis_type": "SHORT",
      "status": "completed",
      "created_at": "2025-11-08T14:30:00.000000"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

---

## 🔌 WebSocket Integration (Real-Time Updates)

### Connection

**URL:** `ws://140.238.227.29:5000/analysis`  
**Namespace:** `/analysis`

### Events Flow

```typescript
import io from 'socket.io-client';

// 1. Connect to WebSocket
const socket = io('http://140.238.227.29:5000/analysis');

// 2. Listen for connection
socket.on('connect', () => {
  console.log('Connected to analysis agent');
  
  // 3. Start analysis
  socket.emit('start_analysis', { analysis_id: 123 });
});

// 4. Listen for analysis started
socket.on('analysis_started', (data) => {
  console.log('Analysis started:', data);
  // data: { analysis_id, room, message }
});

// 5. Listen for progress updates
socket.on('progress_update', (data) => {
  console.log(`Progress: ${data.progress}%`);
  // data: { analysis_id, progress, stage, message, timestamp }
  // stage: 'cloning' | 'chunking' | 'embedding' | 'searching' | 'validating' | 'finalizing'
  // progress: 0-100
});

// 6. Listen for intermediate results (optional)
socket.on('intermediate_result', (data) => {
  console.log('Found vulnerability:', data.cve_id);
  // data: { type: 'finding', analysis_id, cve_id, file_path, severity, confidence_score }
});

// 7. Listen for completion
socket.on('analysis_complete', (data) => {
  console.log('Analysis complete!', data);
  // data: { analysis_id, status, message, total_findings, duration_seconds, timestamp }
  socket.disconnect();
});

// 8. Listen for errors
socket.on('error', (data) => {
  console.error('Error:', data.message);
  // data: { message, details?, stage? }
});
```

---

## 🎯 Analysis Types

### SHORT (2-3 minutes)
- **Max files:** 500
- **Max chunks per file:** 20
- **FAISS top K:** 30
- **Rerank top N:** 5
- **GPT-4 validation:** ❌ Disabled
- **Use case:** Quick security scan for small projects

### MEDIUM (5-10 minutes) ⭐ **Recommended**
- **Max files:** 2000
- **Max chunks per file:** 50
- **FAISS top K:** 50
- **Rerank top N:** 10
- **GPT-4 validation:** ✅ **Enabled**
- **Use case:** Standard security audit with AI validation

### HARD (15-40 minutes)
- **Max files:** ♾️ Unlimited
- **Max chunks per file:** ♾️ Unlimited
- **FAISS top K:** 100
- **Rerank top N:** 20
- **GPT-4 validation:** ✅ **Enabled**
- **Use case:** Comprehensive enterprise-grade security assessment

---

## 📊 Pipeline Stages

The agent processes through these stages automatically:

1. **cloning** (0-20%) - Cloning repository
2. **chunking** (20-35%) - Parsing and chunking code files
3. **embedding** (35-55%) - Generating embeddings with Cohere
4. **searching** (55-75%) - Searching CVE database with FAISS + reranking
5. **validating** (75-95%) - Validating findings with GPT-4.1 (MEDIUM/HARD only)
6. **finalizing** (95-100%) - Generating reports and saving results

---

## 🎨 Frontend Integration Example

### Complete Chat Interface Flow

```typescript
// services/api.ts - Already implemented ✅

import { 
  createAnalysis, 
  connectToAnalysis, 
  disconnectSocket,
  extractGitHubUrl,
  getAnalysisResults,
  type AnalysisType
} from '@/services/api';
import { Socket } from 'socket.io-client';

// State management
const [isAnalyzing, setIsAnalyzing] = useState(false);
const [analysisState, setAnalysisState] = useState<{
  id: number;
  progress: number;
  stage: string;
  status: string;
} | null>(null);
const [currentSocket, setCurrentSocket] = useState<Socket | null>(null);

// User sends message with GitHub URL
const startAnalysis = async (repoUrl: string, analysisType: AnalysisType) => {
  try {
    setIsAnalyzing(true);
    
    // 1. Create analysis
    const analysis = await createAnalysis(repoUrl, analysisType);
    console.log('Analysis created:', analysis.analysis_id);
    
    // 2. Connect to WebSocket
    const socket = connectToAnalysis(analysis.analysis_id, {
      onConnect: () => console.log('Connected'),
      
      onAnalysisStarted: (data) => {
        // Show analysis started message
        console.log('Started:', data.message);
      },
      
      onProgress: (data) => {
        // Update progress bar
        setAnalysisState({
          id: analysis.analysis_id,
          progress: data.progress,
          stage: data.stage,
          status: 'running'
        });
        // data.progress: 0-100
        // data.stage: 'cloning', 'chunking', etc.
      },
      
      onIntermediateResult: (data) => {
        // Show real-time findings
        console.log('Found:', data.cve_id, data.severity);
      },
      
      onComplete: async (data) => {
        // 3. Fetch final results
        const results = await getAnalysisResults(analysis.analysis_id);
        console.log('Results:', results);
        
        // Display summary
        console.log(`Found ${results.summary.total_findings} vulnerabilities`);
        console.log(`Confirmed: ${results.summary.confirmed_vulnerabilities}`);
        console.log('Breakdown:', results.summary.severity_breakdown);
        
        setIsAnalyzing(false);
        socket.disconnect();
      },
      
      onError: (data) => {
        console.error('Error:', data.message);
        setIsAnalyzing(false);
        socket.disconnect();
      }
    });
    
    setCurrentSocket(socket);
    
  } catch (error) {
    console.error('Failed to start:', error);
    setIsAnalyzing(false);
  }
};

// Extract GitHub URL from user message
const handleUserMessage = async (message: string) => {
  const githubUrl = extractGitHubUrl(message);
  
  if (githubUrl) {
    // Determine analysis type from message
    let type: AnalysisType = 'MEDIUM';
    if (message.toLowerCase().includes('quick') || message.includes('short')) {
      type = 'SHORT';
    } else if (message.toLowerCase().includes('deep') || message.includes('hard')) {
      type = 'HARD';
    }
    
    await startAnalysis(githubUrl, type);
  } else {
    // Handle general questions
    console.log('Please provide a GitHub URL');
  }
};
```

---

## 🔑 Key Integration Points for Chat Interface

### 1. URL Detection
```typescript
import { extractGitHubUrl } from '@/services/api';

const url = extractGitHubUrl("Check https://github.com/user/repo");
// Returns: "https://github.com/user/repo"
```

### 2. Analysis Type Selection
```typescript
// Default to MEDIUM for best results
let analysisType: AnalysisType = 'MEDIUM';

// Detect from user message
if (userMessage.includes('quick') || userMessage.includes('fast')) {
  analysisType = 'SHORT';
} else if (userMessage.includes('deep') || userMessage.includes('comprehensive')) {
  analysisType = 'HARD';
}
```

### 3. Progress Display
```typescript
// In ChatInterface component
{isAnalyzing && analysisState && (
  <AnalysisProgress 
    progress={analysisState.progress}
    stage={analysisState.stage}
    status={analysisState.status}
  />
)}
```

### 4. Real-Time Messages
```typescript
// Add messages to chat as events occur
onProgress: (data) => {
  addMessage({
    role: 'assistant',
    content: `⚡ ${data.progress}% - ${data.stage}: ${data.message}`
  });
},

onIntermediateResult: (data) => {
  addMessage({
    role: 'assistant',
    content: `🔍 Found: ${data.cve_id} (${data.severity}) in ${data.file_path}`
  });
}
```

### 5. Final Results
```typescript
onComplete: async (data) => {
  const results = await getAnalysisResults(analysisId);
  
  addMessage({
    role: 'assistant',
    content: `
🎉 Analysis Complete!

**Summary:**
- Files Analyzed: ${results.summary.total_files}
- Code Chunks: ${results.summary.total_chunks}
- Vulnerabilities: ${results.summary.total_findings}
- Confirmed: ${results.summary.confirmed_vulnerabilities}
- False Positives: ${results.summary.false_positives}

**Severity Breakdown:**
${Object.entries(results.summary.severity_breakdown)
  .map(([severity, count]) => `- ${severity}: ${count}`)
  .join('\n')}
    `
  });
}
```

---

## ⚠️ Error Handling

### Common Errors

```typescript
// Invalid repository
{
  "error": "repo_url is required"
}

// Invalid analysis type
{
  "error": "analysis_type must be SHORT, MEDIUM, or HARD"
}

// Analysis not found
{
  "error": "Analysis not found"
}

// Results not ready
{
  "error": "Analysis not completed yet"
}
```

### WebSocket Error Handling

```typescript
socket.on('error', (data) => {
  // data.message: Error description
  // data.details: Additional details
  // data.stage: Stage where error occurred
  
  toast.error("Analysis failed", {
    description: data.message
  });
});

socket.on('disconnect', () => {
  // Handle disconnect
  console.log('WebSocket disconnected');
});
```

---

## 🧪 Testing the Integration

### 1. Test Health Check
```typescript
import { healthCheck } from '@/services/api';

const status = await healthCheck();
console.log(status); // { status: 'healthy', timestamp: '...' }
```

### 2. Test Quick Analysis
```typescript
import { createAnalysis } from '@/services/api';

const analysis = await createAnalysis(
  'https://github.com/pallets/flask',
  'SHORT'
);
console.log('Analysis ID:', analysis.analysis_id);
```

### 3. Test Full Flow
```typescript
// See complete example in ChatInterface.tsx
// Already integrated! ✅
```

---

## 📝 Notes

1. **All timestamps are in ISO 8601 format (UTC)**
2. **Analysis statuses:** `pending`, `running`, `completed`, `failed`
3. **Validation statuses:** `pending`, `confirmed`, `false_positive`, `needs_review`
4. **Severity levels:** `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
5. **Confidence scores:** Range from 0.0 to 1.0
6. **WebSocket auto-reconnects** on connection loss (max 5 attempts)
7. **Progress updates stream in real-time** throughout pipeline
8. **Results available after** `analysis_complete` event

---

## ✅ Implementation Checklist

- [x] API service created (`src/services/api.ts`)
- [x] WebSocket integration implemented
- [x] ChatInterface updated with real backend
- [x] AnalysisProgress component updated with dynamic props
- [x] socket.io-client installed
- [x] URL extraction logic
- [x] Error handling
- [x] Real-time progress updates
- [x] Message streaming to chat

---

## 🚀 Quick Start

1. **Backend is already running** at `http://140.238.227.29:5000`
2. **Frontend integration is complete** - just use the ChatInterface
3. **Paste a GitHub URL** in the chat
4. **Watch real-time analysis** with progress updates
5. **Get comprehensive results** when complete

**Ready to analyze repositories! 🎉**
