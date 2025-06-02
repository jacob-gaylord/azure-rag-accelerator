# UserFeedback Container Schema

## Overview
The UserFeedback container stores user feedback for individual chat messages within the Azure RAG Accelerator. It follows the same patterns as the existing `chat-history-v2` container for consistency and performance.

## Container Configuration
- **Container Name**: `UserFeedback`
- **Database**: `chat-database` (same as existing chat history)
- **Partition Key**: `[/userId, /sessionId]` (MultiHash, following existing pattern)
- **Versioning**: Uses `version` field set to `"cosmosdb-v2"` for consistency

## Document Schema

### Core Fields
```json
{
  "id": "string",           // Unique feedback identifier: {sessionId}-{messageId}-feedback
  "sessionId": "string",    // Links to session in chat-history-v2
  "messageId": "string",    // Links to specific message: {sessionId}-{index}
  "userId": "string",       // User identifier (entra_oid)
  "version": "string",      // Schema version: "cosmosdb-v2"
  "type": "string",         // Document type: "feedback"
  "timestamp": "string",    // ISO 8601 timestamp: 2024-01-01T12:00:00.000Z
  "rating": "number",       // Feedback rating: 1-5 scale
  "comment": "string",      // Optional text feedback (max 1000 chars)
  "ttl": "number"          // Time to live in seconds (optional)
}
```

### Field Specifications

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `id` | string | Yes | Unique identifier for feedback | `"session123-0-feedback"` |
| `sessionId` | string | Yes | Reference to chat session | `"session123"` |
| `messageId` | string | Yes | Reference to specific message | `"session123-0"` |
| `userId` | string | Yes | User identifier from Azure AD | `"user-entra-oid-12345"` |
| `version` | string | Yes | Schema version for evolution | `"cosmosdb-v2"` |
| `type` | string | Yes | Document type identifier | `"feedback"` |
| `timestamp` | string | Yes | When feedback was submitted | `"2024-01-01T12:00:00.000Z"` |
| `rating` | number | Yes | Numerical rating (1-5) | `4` |
| `comment` | string | No | Optional text feedback | `"This answer was helpful"` |
| `ttl` | number | No | Auto-expiration in seconds | `31536000` (1 year) |

### Sample Documents

#### Basic Feedback (Rating Only)
```json
{
  "id": "session123-0-feedback",
  "sessionId": "session123",
  "messageId": "session123-0",
  "userId": "user-entra-oid-12345",
  "version": "cosmosdb-v2",
  "type": "feedback",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "rating": 4
}
```

#### Detailed Feedback (Rating + Comment)
```json
{
  "id": "session456-2-feedback",
  "sessionId": "session456",
  "messageId": "session456-2",
  "userId": "user-entra-oid-67890",
  "version": "cosmosdb-v2",
  "type": "feedback",
  "timestamp": "2024-01-01T15:30:00.000Z",
  "rating": 5,
  "comment": "Excellent answer with detailed citations. Very helpful!",
  "ttl": 31536000
}
```

## Indexing Strategy

### Primary Indexes
- **Partition Key**: `[/userId, /sessionId]` for user-scoped queries
- **Include Paths**:
  - `/sessionId/?` - Session-based queries
  - `/messageId/?` - Message-specific feedback lookup
  - `/timestamp/?` - Time-based sorting
  - `/rating/?` - Rating aggregation queries
  - `/type/?` - Document type filtering

### Excluded Paths
- `/comment/*` - Large text field, not indexed for performance
- `/ttl/?` - System field, not needed for queries

### Composite Indexes
1. **Session Timeline**: `(sessionId ASC, timestamp ASC)` - For chronological feedback in sessions
2. **User Rating History**: `(userId ASC, rating ASC, timestamp DESC)` - For user analytics

## Constraints and Validation

### Business Rules
- One feedback per message per user (enforced by `id` pattern)
- Rating must be 1-5 inclusive
- Comment limited to 1000 characters
- sessionId and messageId must reference existing documents

### Data Validation
```javascript
// Pseudo-validation logic
const isValidFeedback = (feedback) => {
  return feedback.rating >= 1 && 
         feedback.rating <= 5 &&
         feedback.comment.length <= 1000 &&
         feedback.messageId.startsWith(feedback.sessionId);
};
```

## TTL (Time To Live) Configuration

### Purpose
- Automatic cleanup of old feedback data
- GDPR compliance for data retention
- Storage cost optimization

### Default Settings
- **Default TTL**: 31,536,000 seconds (1 year)
- **Configurable**: Via environment variable `FEEDBACK_TTL_SECONDS`
- **Optional**: Can be omitted for permanent storage

## Integration Points

### Existing Systems
- **Chat History**: Links to `chat-history-v2` container via `sessionId` and `messageId`
- **Authentication**: Uses same `userId` (entra_oid) pattern
- **Cosmos Client**: Shares database and connection with existing containers

### API Endpoints
- `POST /feedback` - Submit new feedback
- `GET /feedback/session/{sessionId}` - Get all feedback for session
- `GET /feedback/message/{messageId}` - Get feedback for specific message
- `PUT /feedback/{feedbackId}` - Update existing feedback
- `DELETE /feedback/{feedbackId}` - Remove feedback

## Performance Considerations

### Query Patterns
1. **Most Common**: Get feedback by messageId (point read)
2. **Common**: Get all feedback for session (partition query)
3. **Analytics**: Aggregate ratings by user or timeframe

### Optimization
- Partition key design ensures user data isolation
- Composite indexes support common query patterns
- TTL reduces storage overhead
- Excluded paths minimize index storage

## Migration and Deployment

### Bicep Template Updates
- Add UserFeedback container to existing database
- Configure partition key and indexing policy
- Set throughput appropriately for expected load

### Backward Compatibility
- No changes to existing containers
- New container is additive only
- Existing chat functionality unaffected 