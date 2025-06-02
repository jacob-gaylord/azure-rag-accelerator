# Admin API

The Admin API provides comprehensive analytics, feedback management, and data export capabilities for administrators and system managers. These endpoints require elevated permissions and are designed for monitoring usage, performance, and user satisfaction.

## 📋 Table of Contents

- [Endpoints Overview](#endpoints-overview)
- [Analytics Endpoint](#analytics-endpoint)
- [Feedback Management](#feedback-management)
- [Chat History Management](#chat-history-management)
- [Data Export](#data-export)
- [Authentication & Authorization](#authentication--authorization)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Rate Limiting](#rate-limiting)

## 🔗 Endpoints Overview

| Method | Endpoint | Description | Auth Level |
|--------|----------|-------------|------------|
| `GET` | `/admin/analytics` | Get aggregated analytics and metrics | Admin |
| `GET` | `/admin/feedback` | Retrieve user feedback with filtering | Admin |
| `GET` | `/admin/chat-history` | Access chat session data | Admin |
| `POST` | `/admin/export` | Export data in CSV/JSON format | Admin |

## 📊 Analytics Endpoint

**Endpoint:** `GET /admin/analytics`

Retrieve comprehensive analytics including user engagement, feedback trends, and system performance metrics.

### Request Format

```http
GET /admin/analytics?timeframe=7d&include_trends=true
Authorization: Bearer YOUR_ADMIN_TOKEN
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | String | `"7d"` | Time period: `"1d"`, `"7d"`, `"30d"`, `"90d"` |
| `include_trends` | Boolean | `false` | Include trend analysis data |
| `granularity` | String | `"day"` | Data granularity: `"hour"`, `"day"`, `"week"` |

### Response Format

```json
{
  "summary": {
    "totalFeedback": 1247,
    "averageRating": 4.2,
    "totalSessions": 3891,
    "totalMessages": 15642,
    "uniqueUsers": 892,
    "responseTime": {
      "average": 2.3,
      "p95": 4.8,
      "p99": 8.2
    }
  },
  "trends": {
    "feedbackTrend": [
      {
        "date": "2024-01-08",
        "count": 45,
        "averageRating": 4.1
      },
      {
        "date": "2024-01-09",
        "count": 52,
        "averageRating": 4.3
      }
    ],
    "sessionTrend": [
      {
        "date": "2024-01-08",
        "count": 156,
        "averageLength": 8.4
      },
      {
        "date": "2024-01-09",
        "count": 189,
        "averageLength": 9.1
      }
    ]
  },
  "ratingDistribution": {
    "1": 23,
    "2": 45,
    "3": 156,
    "4": 387,
    "5": 636
  },
  "topIssues": [
    {
      "category": "accuracy",
      "count": 34,
      "percentage": 12.5
    },
    {
      "category": "response_time",
      "count": 28,
      "percentage": 10.3
    }
  ],
  "systemMetrics": {
    "uptime": 99.87,
    "errorRate": 0.13,
    "averageResponseTime": 2.3,
    "peakConcurrency": 156
  },
  "metadata": {
    "generatedAt": "2024-01-15T10:30:00Z",
    "timeframe": "7d",
    "dataSource": "cosmos_db"
  }
}
```

## 💬 Feedback Management

**Endpoint:** `GET /admin/feedback`

Retrieve user feedback with comprehensive filtering and sorting options.

### Request Format

```http
GET /admin/feedback?rating=1,2&start_date=2024-01-01&limit=50&sort=timestamp_desc
Authorization: Bearer YOUR_ADMIN_TOKEN
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `rating` | String | Filter by rating (1-5), comma-separated: `"1,2,3"` |
| `start_date` | String | Start date in ISO format: `"2024-01-01T00:00:00Z"` |
| `end_date` | String | End date in ISO format: `"2024-01-31T23:59:59Z"` |
| `user_id` | String | Filter by specific user ID |
| `session_id` | String | Filter by specific session ID |
| `has_comment` | Boolean | Filter entries with/without comments |
| `limit` | Integer | Number of results (1-1000), default: 50 |
| `offset` | Integer | Results offset for pagination, default: 0 |
| `sort` | String | Sort order: `"timestamp_asc"`, `"timestamp_desc"`, `"rating_asc"`, `"rating_desc"` |

### Response Format

```json
{
  "feedback": [
    {
      "id": "fb_12345",
      "timestamp": "2024-01-15T10:30:00Z",
      "userId": "user_789",
      "sessionId": "session_456",
      "messageId": "msg_123",
      "rating": 5,
      "comment": "Very helpful response! The AI understood my question perfectly and provided relevant citations.",
      "messageContent": "What are the benefits of cloud computing?",
      "responseContent": "Cloud computing offers several key benefits...",
      "metadata": {
        "userAgent": "Mozilla/5.0...",
        "responseTime": 2.4,
        "citationCount": 3,
        "tokenCount": 245
      }
    },
    {
      "id": "fb_12346",
      "timestamp": "2024-01-15T10:25:00Z",
      "userId": "user_123",
      "sessionId": "session_789",
      "messageId": "msg_456",
      "rating": 2,
      "comment": "The response was not accurate and didn't address my specific question about Azure pricing.",
      "messageContent": "How much does Azure cost for a small business?",
      "responseContent": "Azure offers various pricing tiers...",
      "metadata": {
        "userAgent": "Mozilla/5.0...",
        "responseTime": 3.1,
        "citationCount": 1,
        "tokenCount": 198
      }
    }
  ],
  "pagination": {
    "total": 1247,
    "limit": 50,
    "offset": 0,
    "hasMore": true,
    "nextOffset": 50
  },
  "filters": {
    "applied": {
      "rating": [1, 2],
      "start_date": "2024-01-01T00:00:00Z"
    },
    "available": {
      "ratings": [1, 2, 3, 4, 5],
      "dateRange": {
        "earliest": "2023-12-01T00:00:00Z",
        "latest": "2024-01-15T10:30:00Z"
      }
    }
  }
}
```

## 💬 Chat History Management

**Endpoint:** `GET /admin/chat-history`

Access comprehensive chat session data for analysis and monitoring.

### Request Format

```http
GET /admin/chat-history?start_date=2024-01-01&user_id=user_123&include_messages=false
Authorization: Bearer YOUR_ADMIN_TOKEN
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | String | Start date filter |
| `end_date` | String | End date filter |
| `user_id` | String | Filter by user ID |
| `session_id` | String | Filter by session ID |
| `min_messages` | Integer | Minimum message count filter |
| `max_messages` | Integer | Maximum message count filter |
| `include_messages` | Boolean | Include full message content (default: false) |
| `limit` | Integer | Number of results (1-500), default: 50 |
| `offset` | Integer | Results offset for pagination |

### Response Format

```json
{
  "sessions": [
    {
      "sessionId": "session_456",
      "userId": "user_789",
      "startTime": "2024-01-15T10:00:00Z",
      "endTime": "2024-01-15T10:15:00Z",
      "duration": 900,
      "messageCount": 8,
      "tokensUsed": 1247,
      "lastActivity": "2024-01-15T10:15:00Z",
      "metadata": {
        "userAgent": "Mozilla/5.0...",
        "ipAddress": "192.168.1.100",
        "device": "desktop",
        "averageResponseTime": 2.3
      },
      "messages": [
        {
          "messageId": "msg_123",
          "timestamp": "2024-01-15T10:00:30Z",
          "role": "user",
          "content": "What are the benefits of cloud computing?",
          "tokens": 12
        },
        {
          "messageId": "msg_124",
          "timestamp": "2024-01-15T10:00:32Z",
          "role": "assistant",
          "content": "Cloud computing offers several key benefits...",
          "tokens": 245,
          "citationCount": 3,
          "responseTime": 2.1
        }
      ]
    }
  ],
  "summary": {
    "totalSessions": 3891,
    "totalMessages": 15642,
    "averageSessionLength": 8.4,
    "averageMessagesPerSession": 4.0,
    "totalTokensUsed": 1247832
  },
  "pagination": {
    "total": 3891,
    "limit": 50,
    "offset": 0,
    "hasMore": true
  }
}
```

## 📤 Data Export

**Endpoint:** `POST /admin/export`

Export analytics data, feedback, or chat history in CSV or JSON format.

### Request Format

```json
{
  "type": "feedback",
  "format": "csv",
  "filters": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "rating": [1, 2, 3, 4, 5]
  },
  "fields": [
    "timestamp",
    "userId",
    "rating",
    "comment",
    "messageContent"
  ],
  "options": {
    "include_headers": true,
    "date_format": "iso",
    "timezone": "UTC"
  }
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | String | ✅ | Export type: `"feedback"`, `"chat-history"`, `"analytics"` |
| `format` | String | ✅ | Output format: `"csv"`, `"json"` |
| `filters` | Object | ❌ | Same filters as respective GET endpoints |
| `fields` | Array | ❌ | Specific fields to include (default: all) |
| `options` | Object | ❌ | Export formatting options |

### Response Format

**Success Response:**
```json
{
  "success": true,
  "download_url": "https://your-app.azurecontainerapps.io/admin/download/export_12345.csv",
  "expires_at": "2024-01-15T11:30:00Z",
  "metadata": {
    "export_id": "export_12345",
    "record_count": 1247,
    "file_size": 245760,
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

**CSV Example Output:**
```csv
timestamp,userId,sessionId,rating,comment,messageContent
2024-01-15T10:30:00Z,user_789,session_456,5,"Very helpful response!","What are the benefits of cloud computing?"
2024-01-15T10:25:00Z,user_123,session_789,2,"Not accurate enough","How much does Azure cost?"
```

**JSON Example Output:**
```json
[
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "userId": "user_789",
    "sessionId": "session_456",
    "rating": 5,
    "comment": "Very helpful response!",
    "messageContent": "What are the benefits of cloud computing?"
  },
  {
    "timestamp": "2024-01-15T10:25:00Z",
    "userId": "user_123",
    "sessionId": "session_789",
    "rating": 2,
    "comment": "Not accurate enough",
    "messageContent": "How much does Azure cost?"
  }
]
```

## 🔐 Authentication & Authorization

### Required Permissions

Admin API endpoints require elevated permissions beyond standard user authentication:

```http
Authorization: Bearer YOUR_ADMIN_TOKEN
X-Admin-Role: administrator
```

### Role Requirements

| Endpoint | Required Role | Description |
|----------|---------------|-------------|
| `/admin/analytics` | `admin`, `analyst` | Read-only analytics access |
| `/admin/feedback` | `admin`, `analyst` | Feedback data access |
| `/admin/chat-history` | `admin` | Full chat history access |
| `/admin/export` | `admin` | Data export capabilities |

### Token Validation

Admin tokens include additional claims:

```json
{
  "sub": "admin_user_id",
  "roles": ["admin"],
  "permissions": [
    "admin:read_analytics",
    "admin:read_feedback",
    "admin:read_chat_history",
    "admin:export_data"
  ],
  "aud": "https://your-app.azurecontainerapps.io",
  "exp": 1705327800
}
```

## ❌ Error Handling

### Common Error Responses

#### 403 Forbidden (Insufficient Permissions)

```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "Admin access required",
    "details": {
      "required_role": "admin",
      "user_roles": ["user"],
      "endpoint": "/admin/analytics"
    }
  }
}
```

#### 422 Unprocessable Entity (Invalid Filters)

```json
{
  "error": {
    "code": "INVALID_FILTER",
    "message": "Invalid date range",
    "details": {
      "field": "start_date",
      "issue": "Start date cannot be after end date",
      "provided": "2024-01-31T00:00:00Z",
      "end_date": "2024-01-01T00:00:00Z"
    }
  }
}
```

#### 429 Too Many Requests (Rate Limited)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Export rate limit exceeded",
    "details": {
      "limit": 10,
      "window": "3600s",
      "retry_after": 2700,
      "current_usage": 10
    }
  }
}
```

## 💻 Code Examples

### Python Example

```python
import asyncio
import httpx
import json
from datetime import datetime, timedelta

class AdminClient:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
    
    async def get_analytics(self, timeframe: str = "7d") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/admin/analytics",
                headers=self.headers,
                params={"timeframe": timeframe, "include_trends": True}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_feedback(self, rating_filter: list = None, limit: int = 50) -> dict:
        params = {"limit": limit}
        if rating_filter:
            params["rating"] = ",".join(map(str, rating_filter))
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/admin/feedback",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def export_data(self, export_type: str, format: str = "csv") -> dict:
        export_request = {
            "type": export_type,
            "format": format,
            "filters": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/admin/export",
                headers=self.headers,
                json=export_request
            )
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    admin = AdminClient("https://your-app.azurecontainerapps.io", "your_admin_token")
    
    # Get analytics
    analytics = await admin.get_analytics("30d")
    print(f"Total sessions: {analytics['summary']['totalSessions']}")
    
    # Get low-rated feedback
    feedback = await admin.get_feedback([1, 2], limit=100)
    print(f"Found {len(feedback['feedback'])} low-rated items")
    
    # Export feedback data
    export_result = await admin.export_data("feedback", "csv")
    print(f"Export ready: {export_result['download_url']}")

asyncio.run(main())
```

### JavaScript Example

```javascript
class AdminClient {
  constructor(baseUrl, adminToken) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    };
  }

  async getAnalytics(timeframe = '7d') {
    const response = await fetch(
      `${this.baseUrl}/admin/analytics?timeframe=${timeframe}&include_trends=true`,
      { headers: this.headers }
    );
    
    if (!response.ok) {
      throw new Error(`Analytics request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async getFeedback(ratingFilter = null, limit = 50) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (ratingFilter) {
      params.append('rating', ratingFilter.join(','));
    }

    const response = await fetch(
      `${this.baseUrl}/admin/feedback?${params}`,
      { headers: this.headers }
    );
    
    if (!response.ok) {
      throw new Error(`Feedback request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async exportData(type, format = 'csv') {
    const exportRequest = {
      type: type,
      format: format,
      filters: {
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()
      }
    };

    const response = await fetch(
      `${this.baseUrl}/admin/export`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify(exportRequest)
      }
    );
    
    if (!response.ok) {
      throw new Error(`Export request failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// Usage
async function adminDashboard() {
  const admin = new AdminClient('https://your-app.azurecontainerapps.io', 'your_admin_token');
  
  try {
    // Get analytics
    const analytics = await admin.getAnalytics('30d');
    console.log(`Average rating: ${analytics.summary.averageRating}`);
    
    // Get problematic feedback
    const lowRatedFeedback = await admin.getFeedback([1, 2], 100);
    console.log(`Low-rated feedback items: ${lowRatedFeedback.feedback.length}`);
    
    // Export data
    const exportResult = await admin.exportData('feedback', 'csv');
    console.log(`Export URL: ${exportResult.download_url}`);
    
  } catch (error) {
    console.error('Admin API error:', error);
  }
}

adminDashboard();
```

### C# Example

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;

public class AdminClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public AdminClient(string baseUrl, string adminToken)
    {
        _httpClient = new HttpClient();
        _httpClient.DefaultRequestHeaders.Authorization = 
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", adminToken);
        _baseUrl = baseUrl;
    }

    public async Task<AnalyticsResponse> GetAnalyticsAsync(string timeframe = "7d")
    {
        var response = await _httpClient.GetAsync(
            $"{_baseUrl}/admin/analytics?timeframe={timeframe}&include_trends=true"
        );
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<AnalyticsResponse>(json);
    }

    public async Task<FeedbackResponse> GetFeedbackAsync(int[] ratingFilter = null, int limit = 50)
    {
        var queryParams = $"limit={limit}";
        if (ratingFilter != null)
        {
            queryParams += $"&rating={string.Join(",", ratingFilter)}";
        }

        var response = await _httpClient.GetAsync($"{_baseUrl}/admin/feedback?{queryParams}");
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<FeedbackResponse>(json);
    }

    public async Task<ExportResponse> ExportDataAsync(string type, string format = "csv")
    {
        var exportRequest = new
        {
            type = type,
            format = format,
            filters = new
            {
                start_date = DateTime.UtcNow.AddDays(-30).ToString("yyyy-MM-ddTHH:mm:ssZ")
            }
        };

        var json = JsonSerializer.Serialize(exportRequest);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync($"{_baseUrl}/admin/export", content);
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ExportResponse>(responseJson);
    }
}

// Usage
public async Task RunAdminOperationsAsync()
{
    var admin = new AdminClient("https://your-app.azurecontainerapps.io", "your_admin_token");

    try
    {
        // Get analytics
        var analytics = await admin.GetAnalyticsAsync("30d");
        Console.WriteLine($"Total sessions: {analytics.Summary.TotalSessions}");

        // Get low-rated feedback
        var lowRatedFeedback = await admin.GetFeedbackAsync(new[] { 1, 2 }, 100);
        Console.WriteLine($"Low-rated feedback count: {lowRatedFeedback.Feedback.Length}");

        // Export data
        var exportResult = await admin.ExportDataAsync("feedback", "csv");
        Console.WriteLine($"Export URL: {exportResult.DownloadUrl}");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Admin API error: {ex.Message}");
    }
}
```

## ⚡ Rate Limiting

Admin endpoints have specific rate limits to protect system resources:

| Endpoint | Rate Limit | Window | Notes |
|----------|------------|--------|-------|
| `/admin/analytics` | 60 requests | 1 hour | Heavy computation |
| `/admin/feedback` | 120 requests | 1 hour | Database intensive |
| `/admin/chat-history` | 30 requests | 1 hour | Privacy sensitive |
| `/admin/export` | 10 requests | 1 hour | Resource intensive |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705327800
X-RateLimit-Window: 3600
```

---

For more information about implementing admin dashboards and analytics visualization, see the [Admin Dashboard Guide](../admin-dashboard.md). 