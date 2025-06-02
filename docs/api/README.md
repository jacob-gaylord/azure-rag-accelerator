# API Documentation

This directory contains comprehensive API documentation for the Azure RAG Accelerator. The API provides endpoints for chat, search, feedback, administration, and file management.

## 📋 Table of Contents

- [Getting Started](getting-started.md) - Authentication, base URLs, and quick start
- [Chat API](chat.md) - Conversational endpoints for Q&A and streaming
- [Search API](search.md) - Document search and retrieval endpoints
- [Feedback API](feedback.md) - User feedback collection and management
- [Admin API](admin.md) - Administrative endpoints for analytics and management
- [Upload API](upload.md) - File upload and document management
- [Configuration API](config.md) - Application configuration endpoints
- [Authentication](authentication.md) - Detailed authentication and authorization
- [Error Handling](errors.md) - Error codes, responses, and troubleshooting
- [Integration Examples](integration-examples.md) - Code samples in multiple languages
- [Rate Limiting](rate-limiting.md) - Rate limits and throttling guidelines
- [Webhooks](webhooks.md) - Event-driven integrations

## 🚀 Quick Start

### Base URL
```
https://your-app.azurecontainerapps.io
```

### Authentication
All API endpoints require authentication via Azure AD Bearer token:

```http
Authorization: Bearer YOUR_AZURE_AD_TOKEN
```

### Example Request
```bash
curl -X POST "https://your-app.azurecontainerapps.io/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the benefits of cloud computing?"}
    ]
  }'
```

## 📊 API Endpoints Overview

### Core Chat & Search Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send chat message and get AI response |
| `POST` | `/chat/stream` | Stream chat response in real-time |
| `POST` | `/ask` | Ask a question without conversation context |
| `POST` | `/search` | Search documents with optional filters |

### Feedback & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/feedback` | Submit user feedback on responses |
| `GET` | `/admin/analytics` | Get aggregated analytics data |
| `GET` | `/admin/feedback` | Retrieve feedback with filtering |
| `POST` | `/admin/export` | Export data in CSV/JSON format |

### File Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload documents for processing |
| `GET` | `/list_uploaded` | List user's uploaded files |
| `DELETE` | `/delete_uploaded` | Delete uploaded files |
| `GET` | `/content/{path}` | Retrieve file content by path |

### Configuration & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/config` | Get application configuration |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/speech` | Text-to-speech conversion |
| `GET` | `/auth_setup` | Authentication configuration |

## 🔧 Integration Patterns

### Synchronous Chat Integration
```javascript
// JavaScript/Node.js example
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: 'Your question here' }
    ]
  })
});

const data = await response.json();
console.log(data.message.content);
```

### Streaming Chat Integration
```python
# Python example with streaming
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        'POST', 
        '/chat/stream',
        headers={'Authorization': f'Bearer {token}'},
        json={'messages': [{'role': 'user', 'content': 'Your question'}]}
    ) as response:
        async for chunk in response.aiter_text():
            print(chunk, end='')
```

### Feedback Integration
```csharp
// C# example
using var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", token);

var feedback = new {
    rating = 5,
    comment = "Very helpful response!",
    messageId = "msg_123",
    sessionId = "session_456"
};

var response = await client.PostAsJsonAsync("/feedback", feedback);
```

## 📈 Response Formats

### Standard Response Structure
```json
{
  "success": true,
  "data": {
    // Response payload
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request format",
    "details": {
      "field": "messages",
      "issue": "Required field missing"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Chat Response Structure
```json
{
  "message": {
    "content": "AI response content here",
    "role": "assistant"
  },
  "citations": [
    {
      "id": "doc_1",
      "title": "Document Title",
      "url": "https://source.url",
      "excerpt": "Relevant excerpt from document"
    }
  ],
  "session_state": "encrypted_session_data"
}
```

## 🔒 Security Considerations

- **Authentication**: All endpoints require valid Azure AD tokens
- **Authorization**: Role-based access control for admin endpoints
- **Rate Limiting**: Requests are throttled to prevent abuse
- **Data Privacy**: User data is encrypted in transit and at rest
- **CORS**: Configured for specific allowed origins
- **Input Validation**: All inputs are validated and sanitized

## 📚 Additional Resources

- [OpenAPI Specification](openapi.yaml) - Machine-readable API spec
- [Postman Collection](postman_collection.json) - Ready-to-use API collection
- [SDKs](sdks/README.md) - Official SDKs for popular languages
- [Changelog](CHANGELOG.md) - API version history and changes
- [Migration Guide](migration.md) - Upgrading between API versions

## 🆘 Support

For API support and questions:
- [GitHub Issues](https://github.com/your-org/azure-rag-accelerator/issues)
- [Documentation](../README.md)
- [Community Discussions](https://github.com/your-org/azure-rag-accelerator/discussions)

---

*Last updated: 2024-01-15*
*API Version: 1.0* 