# Feedback API Documentation

The Azure RAG Accelerator includes a comprehensive feedback system that allows users to rate and comment on chat responses. This API enables collection and management of user feedback for improving the system.

## Authentication

All feedback endpoints require authentication. Users must be logged in with valid Azure Entra ID credentials.

## Rate Limiting

- **POST /feedback**: 10 submissions per minute per user
- **PUT /feedback/{feedbackId}**: 5 updates per minute per user
- **GET endpoints**: No rate limiting applied

## Endpoints

### 1. Submit Feedback

Submit feedback for a specific chat message.

**Endpoint:** `POST /feedback`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "sessionId": "string (required)",
  "messageId": "string (required)", 
  "rating": "number (required, 1-5)",
  "comment": "string (optional, max 1000 chars)"
}
```

**Validation Rules:**
- `sessionId`: Required, must be a valid session ID
- `messageId`: Required, must start with the sessionId (format: `{sessionId}-{index}`)
- `rating`: Required, must be a number between 1 and 5 (inclusive)
- `comment`: Optional, maximum 1000 characters

**Success Response:**
```json
HTTP 201 Created
{
  "id": "session123-0-feedback",
  "message": "Feedback saved successfully"
}
```

**Error Responses:**
```json
HTTP 400 Bad Request
{
  "error": "sessionId, messageId, and rating are required"
}

HTTP 400 Bad Request  
{
  "error": "Rating must be a number between 1 and 5"
}

HTTP 400 Bad Request
{
  "error": "Comment must be 1000 characters or less"
}

HTTP 400 Bad Request
{
  "error": "Invalid messageId format"
}

HTTP 401 Unauthorized
{
  "error": "User OID not found"
}

HTTP 429 Too Many Requests
{
  "error": "Rate limit exceeded"
}
```

### 2. Get Feedback by Message

Retrieve feedback for a specific message.

**Endpoint:** `GET /feedback/message/{messageId}`

**Parameters:**
- `messageId`: The ID of the message to get feedback for

**Success Response:**
```json
HTTP 200 OK
{
  "feedback": [
    {
      "id": "session123-0-feedback",
      "sessionId": "session123",
      "messageId": "session123-0",
      "rating": 4,
      "comment": "Very helpful response",
      "timestamp": "2024-01-15T10:30:00.000Z"
    }
  ]
}
```

### 3. Get Feedback by Session

Retrieve all feedback for a specific session.

**Endpoint:** `GET /feedback/session/{sessionId}`

**Parameters:**
- `sessionId`: The ID of the session to get feedback for

**Success Response:**
```json
HTTP 200 OK
{
  "feedback": [
    {
      "id": "session123-0-feedback",
      "sessionId": "session123", 
      "messageId": "session123-0",
      "rating": 4,
      "comment": "Very helpful response",
      "timestamp": "2024-01-15T10:30:00.000Z"
    },
    {
      "id": "session123-1-feedback",
      "sessionId": "session123",
      "messageId": "session123-1", 
      "rating": 5,
      "comment": "Excellent answer",
      "timestamp": "2024-01-15T10:35:00.000Z"
    }
  ]
}
```

### 4. Update Feedback

Update existing feedback.

**Endpoint:** `PUT /feedback/{feedbackId}`

**Parameters:**
- `feedbackId`: The ID of the feedback to update

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "rating": "number (optional, 1-5)",
  "comment": "string (optional, max 1000 chars)"
}
```

**Success Response:**
```json
HTTP 200 OK
{
  "message": "Feedback updated successfully"
}
```

**Error Responses:**
```json
HTTP 404 Not Found
{
  "error": "Feedback not found"
}

HTTP 403 Forbidden
{
  "error": "Unauthorized"
}
```

## Configuration

The feedback system requires the following environment variables:

- `USE_CHAT_HISTORY_COSMOS`: Set to "true" to enable feedback functionality
- `AZURE_COSMOSDB_ACCOUNT`: Cosmos DB account name
- `AZURE_CHAT_HISTORY_DATABASE`: Database name for chat history
- `AZURE_USER_FEEDBACK_CONTAINER`: Container name for feedback storage

If `AZURE_USER_FEEDBACK_CONTAINER` is not configured, feedback endpoints will return a 400 error indicating that feedback is not configured.

## Data Schema

Feedback items are stored in Cosmos DB with the following schema:

```json
{
  "id": "session123-0-feedback",
  "sessionId": "session123",
  "messageId": "session123-0", 
  "userId": "user-oid-from-entra-id",
  "version": "1.0",
  "type": "feedback",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "rating": 4,
  "comment": "Optional comment text"
}
```

**Partition Key:** `[userId, sessionId]`

## Error Handling

All endpoints include comprehensive error handling:

- **400 Bad Request**: Invalid input data or missing required fields
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: User not authorized to access/modify the resource
- **404 Not Found**: Requested resource does not exist
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Database or server errors

## Example Usage

### JavaScript/TypeScript

```javascript
// Submit feedback
const submitFeedback = async (sessionId, messageId, rating, comment) => {
  const response = await fetch('/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      sessionId,
      messageId, 
      rating,
      comment
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  
  return await response.json();
};

// Get feedback for a message
const getFeedback = async (messageId) => {
  const response = await fetch(`/feedback/message/${messageId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

### Python

```python
import requests

def submit_feedback(session_id, message_id, rating, comment=None):
    payload = {
        "sessionId": session_id,
        "messageId": message_id,
        "rating": rating
    }
    if comment:
        payload["comment"] = comment
        
    response = requests.post(
        "/feedback",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()
```

## Security Considerations

- All endpoints require authentication
- Users can only access their own feedback
- Rate limiting prevents abuse
- Input validation prevents injection attacks
- Partition keys ensure data isolation between users 