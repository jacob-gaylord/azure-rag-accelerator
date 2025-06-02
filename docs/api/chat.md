# Chat API

The Chat API provides conversational AI capabilities with document grounding, citation support, and real-time streaming. It supports both single-turn questions and multi-turn conversations with context preservation.

## 📋 Table of Contents

- [Endpoints Overview](#endpoints-overview)
- [Chat Endpoint](#chat-endpoint)
- [Chat Stream Endpoint](#chat-stream-endpoint)
- [Ask Endpoint](#ask-endpoint)
- [Request/Response Schemas](#requestresponse-schemas)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)

## 🔗 Endpoints Overview

| Method | Endpoint | Description | Streaming |
|--------|----------|-------------|-----------|
| `POST` | `/chat` | Multi-turn conversation with context | No |
| `POST` | `/chat/stream` | Multi-turn conversation with streaming | Yes |
| `POST` | `/ask` | Single-turn question without context | No |

## 💬 Chat Endpoint

**Endpoint:** `POST /chat`

Send messages in a conversational context with full history and state management. Best for building chatbot interfaces where context matters.

### Request Format

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What are the benefits of cloud computing?"
    }
  ],
  "context": {
    "overrides": {
      "retrieval_mode": "hybrid",
      "semantic_ranker": true,
      "semantic_captions": false,
      "top": 3,
      "temperature": 0.7,
      "prompt_template": null,
      "prompt_template_prefix": null,
      "prompt_template_suffix": null,
      "exclude_category": null,
      "use_oid_security_filter": false,
      "use_groups_security_filter": false,
      "vector_fields": ["content_vector"],
      "use_gpt4v": false,
      "gpt4v_input": null
    }
  },
  "session_state": "encrypted_session_data",
  "cited_content": {}
}
```

### Response Format

```json
{
  "message": {
    "content": "Cloud computing offers several key benefits:\n\n1. **Cost Efficiency**: Reduces capital expenditure on hardware and infrastructure.\n2. **Scalability**: Easily scale resources up or down based on demand.\n3. **Accessibility**: Access your data and applications from anywhere with internet connectivity.\n\nFor more details, see the referenced documents below.",
    "role": "assistant",
    "context": {
      "data_points": [
        "Cloud computing provides cost-effective solutions for businesses by eliminating the need for physical hardware maintenance.",
        "Modern cloud platforms offer auto-scaling capabilities that adjust resources automatically based on traffic patterns.",
        "Remote access capabilities enable distributed teams to collaborate effectively."
      ],
      "thoughts": "The user is asking about cloud computing benefits. I should provide a comprehensive overview covering the main advantages while citing relevant documentation."
    }
  },
  "citations": [
    {
      "id": "aHR0cHM6Ly9zdG9yYWdlYWNjb3VudC5ibG9iLmNvcmUud2luZG93cy5uZXQvY29udGFpbmVyL2Nsb3VkLWJlbmVmaXRzLnBkZg2",
      "title": "Cloud Computing Benefits Guide",
      "filepath": "cloud-benefits.pdf",
      "url": "https://storageaccount.blob.core.windows.net/container/cloud-benefits.pdf",
      "metadata": {
        "chunked": true,
        "offset": 1024,
        "page_number": 3
      }
    }
  ],
  "session_state": "updated_encrypted_session_data"
}
```

### Parameters

#### Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `messages` | Array | ✅ | Array of conversation messages |
| `context` | Object | ❌ | Configuration overrides for this request |
| `session_state` | String | ❌ | Encrypted session data for context preservation |
| `cited_content` | Object | ❌ | Previously cited content to avoid duplication |

#### Context Overrides

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retrieval_mode` | String | `"hybrid"` | Search mode: `"text"`, `"vector"`, or `"hybrid"` |
| `semantic_ranker` | Boolean | `true` | Enable semantic ranking for search results |
| `semantic_captions` | Boolean | `false` | Generate semantic captions for results |
| `top` | Integer | `3` | Number of search results to retrieve (1-50) |
| `temperature` | Float | `0.7` | AI model creativity (0.0-2.0) |
| `prompt_template` | String | `null` | Custom prompt template |
| `exclude_category` | String | `null` | Category to exclude from search |
| `use_oid_security_filter` | Boolean | `false` | Apply OID-based security filtering |
| `use_groups_security_filter` | Boolean | `false` | Apply group-based security filtering |
| `vector_fields` | Array | `["content_vector"]` | Vector fields to search |
| `use_gpt4v` | Boolean | `false` | Enable GPT-4 Vision for image analysis |

## 🌊 Chat Stream Endpoint

**Endpoint:** `POST /chat/stream`

Stream chat responses in real-time for better user experience. Same request format as `/chat` but responses are streamed as Server-Sent Events.

### Request Format

Same as `/chat` endpoint.

### Response Format (Streaming)

The response is streamed as Server-Sent Events (SSE) with the following format:

```
data: {"delta": {"content": "Cloud"}}

data: {"delta": {"content": " computing"}}

data: {"delta": {"content": " offers"}}

data: {"delta": {"content": " several"}}

data: {"delta": {"content": " key"}}

data: {"delta": {"content": " benefits:"}}

data: {"delta": {"content": "\n\n1. **Cost"}}

data: {"delta": {"content": " Efficiency**:"}}

...

data: {"delta": {"context": {"data_points": [...], "thoughts": "..."}}}

data: {"delta": {"citations": [...]}}

data: {"delta": {"session_state": "updated_encrypted_session_data"}}

data: [DONE]
```

### Streaming Client Example

```javascript
// JavaScript SSE client
const eventSource = new EventSource('/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: 'What are the benefits of cloud computing?' }
    ]
  })
});

eventSource.onmessage = function(event) {
  if (event.data === '[DONE]') {
    eventSource.close();
    return;
  }
  
  const delta = JSON.parse(event.data);
  if (delta.delta.content) {
    // Append content to UI
    appendToChat(delta.delta.content);
  }
  
  if (delta.delta.citations) {
    // Display citations
    displayCitations(delta.delta.citations);
  }
};
```

## ❓ Ask Endpoint

**Endpoint:** `POST /ask`

Single-turn question answering without conversation context. Best for one-off questions or when you don't need conversation history.

### Request Format

```json
{
  "question": "What are the benefits of cloud computing?",
  "context": {
    "overrides": {
      "retrieval_mode": "hybrid",
      "top": 3,
      "temperature": 0.7
    }
  }
}
```

### Response Format

```json
{
  "answer": "Cloud computing offers several key benefits including cost efficiency, scalability, and accessibility. Businesses can reduce infrastructure costs, scale resources on-demand, and enable remote access to applications and data.",
  "citations": [
    {
      "id": "aHR0cHM6Ly9zdG9yYWdlYWNjb3VudC5ibG9iLmNvcmUud2luZG93cy5uZXQvY29udGFpbmVyL2Nsb3VkLWJlbmVmaXRzLnBkZg2",
      "title": "Cloud Computing Benefits Guide",
      "filepath": "cloud-benefits.pdf",
      "url": "https://storageaccount.blob.core.windows.net/container/cloud-benefits.pdf"
    }
  ],
  "context": {
    "data_points": [
      "Cloud computing provides cost-effective solutions...",
      "Modern cloud platforms offer auto-scaling capabilities...",
      "Remote access capabilities enable distributed teams..."
    ],
    "thoughts": "The user is asking about cloud computing benefits. I should provide a comprehensive overview covering the main advantages."
  }
}
```

## 🔧 Request/Response Schemas

### Message Schema

```json
{
  "role": "user|assistant|system",
  "content": "string"
}
```

### Citation Schema

```json
{
  "id": "string",
  "title": "string",
  "filepath": "string",
  "url": "string",
  "metadata": {
    "chunked": "boolean",
    "offset": "integer",
    "page_number": "integer"
  }
}
```

### Context Schema

```json
{
  "data_points": ["string"],
  "thoughts": "string"
}
```

## 🔐 Authentication

All chat endpoints require authentication via Azure AD Bearer token:

```http
Authorization: Bearer YOUR_AZURE_AD_TOKEN
```

To obtain a token:

```javascript
// JavaScript example using MSAL
const tokenRequest = {
  scopes: ['https://your-app.azurecontainerapps.io/.default']
};

const token = await msalInstance.acquireTokenSilent(tokenRequest);
```

## ❌ Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request format",
    "details": {
      "field": "messages",
      "issue": "Messages array cannot be empty"
    }
  }
}
```

#### 401 Unauthorized

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or expired token",
    "details": {
      "token_status": "expired",
      "expires_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

#### 429 Too Many Requests

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 100,
      "window": "3600s",
      "retry_after": 1800
    }
  }
}
```

#### 500 Internal Server Error

```json
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "OpenAI service unavailable",
    "details": {
      "service": "azure_openai",
      "status": "503",
      "retry_recommended": true
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

async def chat_with_ai(messages, token):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://your-app.azurecontainerapps.io/chat',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                'messages': messages,
                'context': {
                    'overrides': {
                        'temperature': 0.7,
                        'top': 3
                    }
                }
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
messages = [
    {'role': 'user', 'content': 'What are the benefits of cloud computing?'}
]
result = await chat_with_ai(messages, 'your_token_here')
print(result['message']['content'])
```

### Node.js Example

```javascript
const axios = require('axios');

async function chatWithAI(messages, token) {
  try {
    const response = await axios.post(
      'https://your-app.azurecontainerapps.io/chat',
      {
        messages: messages,
        context: {
          overrides: {
            temperature: 0.7,
            top: 3
          }
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Chat error:', error.response?.data || error.message);
    throw error;
  }
}

// Usage
const messages = [
  { role: 'user', content: 'What are the benefits of cloud computing?' }
];

chatWithAI(messages, 'your_token_here')
  .then(result => console.log(result.message.content))
  .catch(error => console.error(error));
```

### C# Example

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class ChatClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;

    public ChatClient(string baseUrl, string token)
    {
        _httpClient = new HttpClient();
        _httpClient.DefaultRequestHeaders.Authorization = 
            new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
        _baseUrl = baseUrl;
    }

    public async Task<ChatResponse> SendChatAsync(ChatRequest request)
    {
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await _httpClient.PostAsync($"{_baseUrl}/chat", content);
        response.EnsureSuccessStatusCode();

        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<ChatResponse>(responseJson);
    }
}

// Usage
var client = new ChatClient("https://your-app.azurecontainerapps.io", "your_token");
var request = new ChatRequest
{
    Messages = new[]
    {
        new Message { Role = "user", Content = "What are the benefits of cloud computing?" }
    }
};

var response = await client.SendChatAsync(request);
Console.WriteLine(response.Message.Content);
```

## 📋 Best Practices

### 1. Session Management

- Always include `session_state` in subsequent requests to maintain conversation context
- Store session state securely on the client side
- Handle session expiration gracefully

### 2. Error Handling

- Implement exponential backoff for rate limiting (429 errors)
- Gracefully handle AI service outages (500 errors)
- Validate input before sending requests

### 3. Performance Optimization

- Use streaming endpoints for real-time user experience
- Cache static configuration to reduce API calls
- Implement request debouncing for user input

### 4. Security

- Always validate and sanitize user input
- Use HTTPS for all requests
- Store tokens securely (never in localStorage)
- Implement proper token refresh logic

### 5. Content Management

- Monitor citation usage for content tracking
- Implement feedback collection for quality improvement
- Use appropriate temperature settings for your use case

### 6. Resource Management

- Close streaming connections properly
- Implement request timeouts
- Monitor API usage and costs

---

For more examples and advanced usage patterns, see the [Integration Examples](integration-examples.md) documentation. 