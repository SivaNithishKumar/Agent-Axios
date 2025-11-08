# Backend API Documentation - CVE Analyzer

This document outlines all required backend endpoints, request payloads, and expected responses for the CVE Analyzer application.

## Base URL
```
https://api.cve-analyzer.com/v1
```

## Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### 1.1 User Login
**Endpoint:** `POST /auth/login`

**Request Payload:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123456",
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "company": "Acme Inc.",
      "avatar": "https://api.cve-analyzer.com/avatars/user_123456.jpg",
      "plan": "pro",
      "createdAt": "2024-01-15T10:30:00Z"
    },
    "token": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600,
      "tokenType": "Bearer"
    }
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "timestamp": "2024-11-08T14:30:00Z"
  }
}
```

---

### 1.2 User Registration
**Endpoint:** `POST /auth/register`

**Request Payload:**
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "firstName": "Jane",
  "lastName": "Smith",
  "company": "Tech Corp"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_789012",
      "email": "newuser@example.com",
      "firstName": "Jane",
      "lastName": "Smith",
      "company": "Tech Corp",
      "avatar": null,
      "plan": "free",
      "createdAt": "2024-11-08T14:30:00Z"
    },
    "token": {
      "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expiresIn": 3600,
      "tokenType": "Bearer"
    }
  }
}
```

---

### 1.3 Refresh Token
**Endpoint:** `POST /auth/refresh`

**Request Payload:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

---

### 1.4 Logout
**Endpoint:** `POST /auth/logout`
**Authentication:** Required

**Request Payload:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

---

### 1.5 Password Reset Request
**Endpoint:** `POST /auth/password-reset/request`

**Request Payload:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

---

### 1.6 Password Reset Confirm
**Endpoint:** `POST /auth/password-reset/confirm`

**Request Payload:**
```json
{
  "token": "reset_token_here",
  "newPassword": "newSecurePassword123"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Password successfully reset"
}
```

---

## 2. Repository Management Endpoints

### 2.1 Get All Repositories
**Endpoint:** `GET /repositories`
**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `search` (optional): Search query
- `status` (optional): Filter by status (healthy, warning, critical)
- `starred` (optional): Filter starred repos (true/false)

**Example Request:**
```
GET /repositories?page=1&limit=20&search=frontend&starred=true
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "repositories": [
      {
        "id": "repo_001",
        "name": "my-app/frontend",
        "url": "https://github.com/my-app/frontend",
        "fullName": "my-app/frontend",
        "language": "TypeScript",
        "defaultBranch": "main",
        "branches": 12,
        "lastScan": "2024-11-08T12:00:00Z",
        "nextScan": "2024-11-09T10:00:00Z",
        "starred": true,
        "status": "healthy",
        "vulnerabilities": {
          "critical": 0,
          "high": 0,
          "medium": 3,
          "low": 2,
          "total": 5
        },
        "scanFrequency": "daily",
        "autoScan": true,
        "createdAt": "2024-10-15T08:30:00Z",
        "updatedAt": "2024-11-08T12:00:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 100,
      "itemsPerPage": 20,
      "hasNextPage": true,
      "hasPreviousPage": false
    },
    "stats": {
      "total": 100,
      "starred": 15,
      "needsAttention": 23,
      "totalVulnerabilities": 456
    }
  }
}
```

---

### 2.2 Get Repository by ID
**Endpoint:** `GET /repositories/:id`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "repo_001",
    "name": "my-app/frontend",
    "url": "https://github.com/my-app/frontend",
    "fullName": "my-app/frontend",
    "description": "Frontend application for CVE Analyzer",
    "language": "TypeScript",
    "defaultBranch": "main",
    "branches": 12,
    "stars": 245,
    "forks": 12,
    "lastScan": "2024-11-08T12:00:00Z",
    "nextScan": "2024-11-09T10:00:00Z",
    "starred": true,
    "status": "healthy",
    "vulnerabilities": {
      "critical": 0,
      "high": 0,
      "medium": 3,
      "low": 2,
      "total": 5
    },
    "scanHistory": [
      {
        "scanId": "scan_123",
        "timestamp": "2024-11-08T12:00:00Z",
        "duration": 145,
        "vulnerabilitiesFound": 5,
        "status": "completed"
      }
    ],
    "dependencies": {
      "total": 234,
      "direct": 45,
      "transitive": 189,
      "outdated": 12
    },
    "scanFrequency": "daily",
    "autoScan": true,
    "createdAt": "2024-10-15T08:30:00Z",
    "updatedAt": "2024-11-08T12:00:00Z"
  }
}
```

---

### 2.3 Add New Repository
**Endpoint:** `POST /repositories`
**Authentication:** Required

**Request Payload:**
```json
{
  "url": "https://github.com/username/repository",
  "autoScan": true,
  "scanFrequency": "daily"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "repo_new_001",
    "name": "username/repository",
    "url": "https://github.com/username/repository",
    "fullName": "username/repository",
    "language": "JavaScript",
    "defaultBranch": "main",
    "branches": 1,
    "starred": false,
    "status": "pending",
    "vulnerabilities": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0,
      "total": 0
    },
    "scanFrequency": "daily",
    "autoScan": true,
    "createdAt": "2024-11-08T14:30:00Z",
    "updatedAt": "2024-11-08T14:30:00Z"
  },
  "message": "Repository added successfully. Initial scan queued."
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REPOSITORY",
    "message": "Invalid GitHub repository URL or repository not accessible",
    "timestamp": "2024-11-08T14:30:00Z"
  }
}
```

---

### 2.4 Update Repository
**Endpoint:** `PATCH /repositories/:id`
**Authentication:** Required

**Request Payload:**
```json
{
  "starred": true,
  "autoScan": false,
  "scanFrequency": "weekly"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "repo_001",
    "starred": true,
    "autoScan": false,
    "scanFrequency": "weekly",
    "updatedAt": "2024-11-08T14:30:00Z"
  },
  "message": "Repository updated successfully"
}
```

---

### 2.5 Delete Repository
**Endpoint:** `DELETE /repositories/:id`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Repository removed successfully"
}
```

---

### 2.6 Trigger Manual Scan
**Endpoint:** `POST /repositories/:id/scan`
**Authentication:** Required

**Request Payload:**
```json
{
  "branch": "main",
  "fullScan": true
}
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "data": {
    "scanId": "scan_456",
    "repositoryId": "repo_001",
    "status": "queued",
    "estimatedDuration": 120,
    "queuePosition": 3,
    "startedAt": null
  },
  "message": "Scan queued successfully"
}
```

---

### 2.7 Get Scan Status
**Endpoint:** `GET /repositories/:id/scan/:scanId`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "scanId": "scan_456",
    "repositoryId": "repo_001",
    "status": "in_progress",
    "progress": {
      "percentage": 50,
      "currentStep": "scanning_dependencies",
      "steps": [
        {
          "name": "cloning_repository",
          "status": "completed",
          "completedAt": "2024-11-08T14:30:15Z"
        },
        {
          "name": "scanning_dependencies",
          "status": "in_progress",
          "startedAt": "2024-11-08T14:30:30Z"
        },
        {
          "name": "analyzing_vulnerabilities",
          "status": "pending"
        },
        {
          "name": "generating_report",
          "status": "pending"
        }
      ]
    },
    "startedAt": "2024-11-08T14:30:00Z",
    "estimatedCompletion": "2024-11-08T14:33:00Z"
  }
}
```

---

## 3. Reports Endpoints

### 3.1 Get All Reports
**Endpoint:** `GET /reports`
**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number
- `limit` (optional): Items per page
- `repositoryId` (optional): Filter by repository
- `status` (optional): Filter by status (critical, warning, safe)
- `startDate` (optional): Filter from date (ISO 8601)
- `endDate` (optional): Filter to date (ISO 8601)

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "report_001",
        "repositoryId": "repo_001",
        "repositoryName": "user/react-app",
        "scanId": "scan_123",
        "date": "2024-11-08T12:00:00Z",
        "status": "critical",
        "vulnerabilities": {
          "critical": 2,
          "high": 5,
          "medium": 8,
          "low": 3,
          "total": 18
        },
        "dependencies": {
          "total": 234,
          "vulnerable": 15
        },
        "summary": "Found 18 vulnerabilities across 15 dependencies",
        "riskScore": 7.8,
        "createdAt": "2024-11-08T12:00:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 10,
      "totalItems": 200,
      "itemsPerPage": 20
    },
    "stats": {
      "totalReports": 200,
      "criticalIssues": 45,
      "highPriority": 123,
      "safeRepos": 32
    }
  }
}
```

---

### 3.2 Get Report by ID
**Endpoint:** `GET /reports/:id`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "report_001",
    "repositoryId": "repo_001",
    "repositoryName": "user/react-app",
    "repositoryUrl": "https://github.com/user/react-app",
    "scanId": "scan_123",
    "date": "2024-11-08T12:00:00Z",
    "status": "critical",
    "branch": "main",
    "commit": "a1b2c3d4e5f6",
    "vulnerabilities": {
      "critical": 2,
      "high": 5,
      "medium": 8,
      "low": 3,
      "total": 18,
      "details": [
        {
          "id": "vuln_001",
          "cveId": "CVE-2024-12345",
          "severity": "critical",
          "package": "express",
          "packageVersion": "4.17.1",
          "fixedVersion": "4.18.2",
          "title": "Remote Code Execution in Express.js",
          "description": "A critical vulnerability allows remote code execution through crafted HTTP requests",
          "cvssScore": 9.8,
          "cvssVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
          "publishedDate": "2024-10-15T00:00:00Z",
          "affectedVersions": ["<4.18.2"],
          "references": [
            "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
            "https://github.com/expressjs/express/security/advisories/GHSA-xxxx"
          ],
          "exploit": {
            "available": true,
            "maturity": "functional"
          },
          "patchAvailable": true,
          "recommendation": "Upgrade to express@4.18.2 or later"
        }
      ]
    },
    "dependencies": {
      "total": 234,
      "direct": 45,
      "transitive": 189,
      "vulnerable": 15,
      "outdated": 28
    },
    "summary": "Found 18 vulnerabilities across 15 dependencies. 2 critical issues require immediate attention.",
    "riskScore": 7.8,
    "recommendations": [
      "Immediately upgrade express to version 4.18.2",
      "Update lodash to version 4.17.21",
      "Consider implementing additional security headers"
    ],
    "scanDuration": 145,
    "createdAt": "2024-11-08T12:00:00Z",
    "updatedAt": "2024-11-08T12:00:00Z"
  }
}
```

---

### 3.3 Export Report
**Endpoint:** `GET /reports/:id/export`
**Authentication:** Required

**Query Parameters:**
- `format`: pdf, json, csv, html (default: pdf)

**Success Response (200 OK):**
Returns file download with appropriate Content-Type header

For JSON format:
```json
{
  "success": true,
  "data": {
    // Same as Get Report by ID response
  }
}
```

---

### 3.4 Compare Reports
**Endpoint:** `POST /reports/compare`
**Authentication:** Required

**Request Payload:**
```json
{
  "reportIds": ["report_001", "report_002"]
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "comparison": {
      "report1": {
        "id": "report_001",
        "date": "2024-11-08T12:00:00Z",
        "vulnerabilities": {
          "critical": 2,
          "high": 5,
          "medium": 8,
          "low": 3,
          "total": 18
        }
      },
      "report2": {
        "id": "report_002",
        "date": "2024-11-07T12:00:00Z",
        "vulnerabilities": {
          "critical": 3,
          "high": 6,
          "medium": 7,
          "low": 2,
          "total": 18
        }
      },
      "changes": {
        "newVulnerabilities": 5,
        "fixedVulnerabilities": 4,
        "unchangedVulnerabilities": 13,
        "improvement": false
      }
    }
  }
}
```

---

## 4. Dashboard / Analytics Endpoints

### 4.1 Get Dashboard Overview
**Endpoint:** `GET /dashboard/overview`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalRepositories": 45,
      "activeScans": 3,
      "totalVulnerabilities": 234,
      "criticalIssues": 12
    },
    "recentActivity": [
      {
        "id": "activity_001",
        "type": "scan_completed",
        "repositoryName": "user/frontend",
        "message": "Scan completed for user/frontend",
        "timestamp": "2024-11-08T14:25:00Z",
        "severity": "warning"
      }
    ],
    "vulnerabilityTrend": [
      {
        "date": "2024-11-01",
        "critical": 15,
        "high": 45,
        "medium": 89,
        "low": 32
      },
      {
        "date": "2024-11-08",
        "critical": 12,
        "high": 42,
        "medium": 85,
        "low": 35
      }
    ],
    "topVulnerableRepos": [
      {
        "repositoryId": "repo_001",
        "repositoryName": "user/backend",
        "vulnerabilities": 45
      }
    ]
  }
}
```

---

### 4.2 Get Analytics
**Endpoint:** `GET /analytics`
**Authentication:** Required

**Query Parameters:**
- `timeRange`: 7d, 30d, 90d, 1y (default: 30d)
- `groupBy`: day, week, month

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "timeRange": "30d",
    "metrics": {
      "totalScans": 145,
      "averageScanDuration": 123,
      "vulnerabilitiesFound": 456,
      "vulnerabilitiesFixed": 234
    },
    "trends": {
      "scansOverTime": [
        {
          "date": "2024-11-01",
          "count": 12
        }
      ],
      "vulnerabilitiesByType": {
        "critical": 23,
        "high": 67,
        "medium": 145,
        "low": 221
      },
      "vulnerabilitiesBySeverityOverTime": [
        {
          "date": "2024-11-01",
          "critical": 25,
          "high": 70,
          "medium": 150,
          "low": 200
        }
      ]
    },
    "topVulnerabilities": [
      {
        "cveId": "CVE-2024-12345",
        "occurrences": 15,
        "severity": "critical"
      }
    ]
  }
}
```

---

## 5. Chat / AI Assistant Endpoints

### 5.1 Send Chat Message
**Endpoint:** `POST /chat/message`
**Authentication:** Required

**Request Payload:**
```json
{
  "message": "Analyze github.com/user/repository",
  "sessionId": "session_123",
  "context": {
    "repositoryId": "repo_001"
  }
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "messageId": "msg_456",
    "sessionId": "session_123",
    "response": "I've started analyzing the repository. Let me scan it for vulnerabilities...",
    "timestamp": "2024-11-08T14:30:00Z",
    "actions": [
      {
        "type": "start_scan",
        "repositoryUrl": "https://github.com/user/repository",
        "scanId": "scan_789"
      }
    ]
  }
}
```

---

### 5.2 Get Chat History
**Endpoint:** `GET /chat/sessions/:sessionId/messages`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "sessionId": "session_123",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "Analyze github.com/user/repository",
        "timestamp": "2024-11-08T14:25:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "I've completed the analysis! Found 3 medium-severity vulnerabilities...",
        "timestamp": "2024-11-08T14:27:00Z",
        "metadata": {
          "scanId": "scan_789",
          "repositoryId": "repo_001"
        }
      }
    ]
  }
}
```

---

### 5.3 Stream Chat Response (SSE)
**Endpoint:** `GET /chat/stream/:sessionId`
**Authentication:** Required

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
```
event: message
data: {"token": "I've", "type": "text"}

event: message
data: {"token": " started", "type": "text"}

event: progress
data: {"step": "scanning_dependencies", "percentage": 50}

event: complete
data: {"messageId": "msg_456", "scanId": "scan_789"}
```

---

## 6. User Profile & Settings Endpoints

### 6.1 Get User Profile
**Endpoint:** `GET /user/profile`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "user_123456",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "company": "Acme Inc.",
    "bio": "Security enthusiast and developer",
    "avatar": "https://api.cve-analyzer.com/avatars/user_123456.jpg",
    "plan": {
      "name": "pro",
      "displayName": "Pro Plan",
      "price": 29,
      "currency": "USD",
      "billingCycle": "monthly",
      "features": [
        "Unlimited repositories",
        "Priority scanning",
        "Advanced analytics",
        "API access"
      ]
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-11-08T14:30:00Z"
  }
}
```

---

### 6.2 Update User Profile
**Endpoint:** `PATCH /user/profile`
**Authentication:** Required

**Request Payload:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "company": "New Company Inc.",
  "bio": "Updated bio"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "user_123456",
    "firstName": "John",
    "lastName": "Doe",
    "company": "New Company Inc.",
    "bio": "Updated bio",
    "updatedAt": "2024-11-08T14:30:00Z"
  },
  "message": "Profile updated successfully"
}
```

---

### 6.3 Upload Avatar
**Endpoint:** `POST /user/avatar`
**Authentication:** Required
**Content-Type:** multipart/form-data

**Request:**
```
FormData:
  avatar: [image file]
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "avatar": "https://api.cve-analyzer.com/avatars/user_123456.jpg",
    "updatedAt": "2024-11-08T14:30:00Z"
  },
  "message": "Avatar uploaded successfully"
}
```

---

### 6.4 Get User Settings
**Endpoint:** `GET /user/settings`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": {
      "email": {
        "vulnerabilityAlerts": true,
        "weeklyReports": true,
        "scanComplete": true
      },
      "push": {
        "enabled": true,
        "criticalOnly": false
      }
    },
    "preferences": {
      "theme": "light",
      "language": "en",
      "timezone": "America/New_York"
    },
    "scanning": {
      "autoScan": true,
      "scanFrequency": "daily",
      "includeDevDependencies": true
    },
    "security": {
      "twoFactorEnabled": false,
      "apiKeyGenerated": true
    }
  }
}
```

---

### 6.5 Update User Settings
**Endpoint:** `PATCH /user/settings`
**Authentication:** Required

**Request Payload:**
```json
{
  "notifications": {
    "email": {
      "vulnerabilityAlerts": false
    }
  },
  "preferences": {
    "theme": "dark"
  },
  "scanning": {
    "autoScan": false,
    "scanFrequency": "weekly"
  }
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": {
      "email": {
        "vulnerabilityAlerts": false,
        "weeklyReports": true,
        "scanComplete": true
      }
    },
    "preferences": {
      "theme": "dark"
    },
    "scanning": {
      "autoScan": false,
      "scanFrequency": "weekly"
    }
  },
  "message": "Settings updated successfully"
}
```

---

### 6.6 Change Password
**Endpoint:** `POST /user/password`
**Authentication:** Required

**Request Payload:**
```json
{
  "currentPassword": "oldPassword123",
  "newPassword": "newSecurePassword456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Password updated successfully"
}
```

---

### 6.7 Enable Two-Factor Authentication
**Endpoint:** `POST /user/2fa/enable`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "qrCode": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret": "JBSWY3DPEHPK3PXP",
    "backupCodes": [
      "12345678",
      "87654321",
      "11223344"
    ]
  },
  "message": "Scan the QR code with your authenticator app"
}
```

---

### 6.8 Verify Two-Factor Authentication
**Endpoint:** `POST /user/2fa/verify`
**Authentication:** Required

**Request Payload:**
```json
{
  "code": "123456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Two-factor authentication enabled successfully"
}
```

---

### 6.9 Generate API Key
**Endpoint:** `POST /user/api-keys`
**Authentication:** Required

**Request Payload:**
```json
{
  "name": "Production API Key",
  "expiresIn": 365
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "key_789",
    "key": "sk_live_abc123def456ghi789",
    "name": "Production API Key",
    "createdAt": "2024-11-08T14:30:00Z",
    "expiresAt": "2025-11-08T14:30:00Z"
  },
  "message": "API key generated successfully. Store it securely as it won't be shown again."
}
```

---

### 6.10 List API Keys
**Endpoint:** `GET /user/api-keys`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "apiKeys": [
      {
        "id": "key_789",
        "name": "Production API Key",
        "keyPreview": "sk_live_***************789",
        "createdAt": "2024-11-08T14:30:00Z",
        "expiresAt": "2025-11-08T14:30:00Z",
        "lastUsed": "2024-11-08T10:15:00Z"
      }
    ]
  }
}
```

---

### 6.11 Revoke API Key
**Endpoint:** `DELETE /user/api-keys/:keyId`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "API key revoked successfully"
}
```

---

## 7. Notifications Endpoints

### 7.1 Get Notifications
**Endpoint:** `GET /notifications`
**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number
- `limit` (optional): Items per page
- `unreadOnly` (optional): true/false

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_001",
        "type": "vulnerability_found",
        "title": "Critical vulnerability found",
        "message": "Found CVE-2024-12345 in repository user/frontend",
        "severity": "critical",
        "read": false,
        "repositoryId": "repo_001",
        "repositoryName": "user/frontend",
        "metadata": {
          "cveId": "CVE-2024-12345",
          "reportId": "report_001"
        },
        "createdAt": "2024-11-08T14:25:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 89,
      "unreadCount": 23
    }
  }
}
```

---

### 7.2 Mark Notification as Read
**Endpoint:** `PATCH /notifications/:id/read`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### 7.3 Mark All Notifications as Read
**Endpoint:** `POST /notifications/read-all`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "All notifications marked as read"
}
```

---

## 8. Webhooks Endpoints

### 8.1 List Webhooks
**Endpoint:** `GET /webhooks`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "webhooks": [
      {
        "id": "webhook_001",
        "url": "https://example.com/webhook",
        "events": ["scan.completed", "vulnerability.found"],
        "active": true,
        "createdAt": "2024-10-15T10:30:00Z",
        "lastTriggered": "2024-11-08T12:00:00Z"
      }
    ]
  }
}
```

---

### 8.2 Create Webhook
**Endpoint:** `POST /webhooks`
**Authentication:** Required

**Request Payload:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["scan.completed", "vulnerability.found"],
  "secret": "webhook_secret_key"
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "webhook_002",
    "url": "https://example.com/webhook",
    "events": ["scan.completed", "vulnerability.found"],
    "active": true,
    "createdAt": "2024-11-08T14:30:00Z"
  },
  "message": "Webhook created successfully"
}
```

---

### 8.3 Delete Webhook
**Endpoint:** `DELETE /webhooks/:id`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Webhook deleted successfully"
}
```

---

## 9. CVE Database Endpoints

### 9.1 Search CVEs
**Endpoint:** `GET /cves/search`
**Authentication:** Required

**Query Parameters:**
- `query`: Search query
- `severity`: critical, high, medium, low
- `year`: Filter by year
- `page`: Page number
- `limit`: Items per page

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "cves": [
      {
        "cveId": "CVE-2024-12345",
        "title": "Remote Code Execution in Express.js",
        "description": "A critical vulnerability allows remote code execution...",
        "severity": "critical",
        "cvssScore": 9.8,
        "publishedDate": "2024-10-15T00:00:00Z",
        "affectedPackages": ["express"],
        "exploitAvailable": true
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 45,
      "totalItems": 890
    }
  }
}
```

---

### 9.2 Get CVE Details
**Endpoint:** `GET /cves/:cveId`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "cveId": "CVE-2024-12345",
    "title": "Remote Code Execution in Express.js",
    "description": "A critical vulnerability allows remote code execution through crafted HTTP requests",
    "severity": "critical",
    "cvssScore": 9.8,
    "cvssVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
    "publishedDate": "2024-10-15T00:00:00Z",
    "lastModifiedDate": "2024-10-20T00:00:00Z",
    "affectedPackages": [
      {
        "name": "express",
        "ecosystem": "npm",
        "affectedVersions": ["<4.18.2"],
        "fixedVersion": "4.18.2"
      }
    ],
    "references": [
      "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
      "https://github.com/expressjs/express/security/advisories/GHSA-xxxx"
    ],
    "exploit": {
      "available": true,
      "maturity": "functional",
      "publicSince": "2024-10-17T00:00:00Z"
    },
    "patchAvailable": true,
    "cwe": ["CWE-94"],
    "affectedRepositories": 15
  }
}
```

---

## 10. Billing Endpoints (Optional)

### 10.1 Get Billing Info
**Endpoint:** `GET /billing`
**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "currentPlan": {
      "name": "pro",
      "displayName": "Pro Plan",
      "price": 29,
      "currency": "USD",
      "billingCycle": "monthly"
    },
    "paymentMethod": {
      "type": "card",
      "last4": "4242",
      "brand": "visa",
      "expiryMonth": 12,
      "expiryYear": 2025
    },
    "nextBillingDate": "2024-12-08T00:00:00Z",
    "usage": {
      "repositories": 45,
      "scansThisMonth": 234,
      "limits": {
        "repositories": 100,
        "scansPerMonth": 1000
      }
    }
  }
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details"
    },
    "timestamp": "2024-11-08T14:30:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Invalid email or password |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `FORBIDDEN` | 403 | User doesn't have permission |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `REPOSITORY_NOT_ACCESSIBLE` | 400 | Cannot access repository |
| `SCAN_IN_PROGRESS` | 409 | Scan already in progress |
| `PLAN_LIMIT_REACHED` | 403 | Plan limit reached |

---

## Rate Limiting

API requests are rate-limited based on your plan:

**Free Plan:** 100 requests/hour
**Pro Plan:** 1000 requests/hour
**Enterprise Plan:** Unlimited

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699459200
```

---

## Webhook Event Payloads

### Scan Completed Event
```json
{
  "event": "scan.completed",
  "timestamp": "2024-11-08T14:30:00Z",
  "data": {
    "scanId": "scan_123",
    "repositoryId": "repo_001",
    "repositoryName": "user/frontend",
    "status": "completed",
    "vulnerabilities": {
      "critical": 2,
      "high": 5,
      "medium": 8,
      "low": 3,
      "total": 18
    },
    "reportId": "report_001"
  }
}
```

### Vulnerability Found Event
```json
{
  "event": "vulnerability.found",
  "timestamp": "2024-11-08T14:30:00Z",
  "data": {
    "repositoryId": "repo_001",
    "repositoryName": "user/frontend",
    "cveId": "CVE-2024-12345",
    "severity": "critical",
    "package": "express",
    "cvssScore": 9.8
  }
}
```

---

## WebSocket Events (Real-time Updates)

Connect to: `wss://api.cve-analyzer.com/v1/ws`

**Authentication:**
```json
{
  "type": "auth",
  "token": "your_access_token"
}
```

**Subscribe to events:**
```json
{
  "type": "subscribe",
  "channels": ["scans", "notifications"]
}
```

**Event examples:**
```json
{
  "type": "scan.progress",
  "data": {
    "scanId": "scan_123",
    "progress": 75,
    "currentStep": "analyzing_vulnerabilities"
  }
}
```

---

## Notes

1. All timestamps are in ISO 8601 format (UTC)
2. All endpoints support pagination where applicable
3. File uploads have a 10MB size limit
4. API version is included in the URL path
5. CORS is enabled for registered domains
6. All responses use consistent JSON structure
7. Partial updates use PATCH method
8. Full updates use PUT method (if implemented)

---

**Document Version:** 1.0
**Last Updated:** November 8, 2024
