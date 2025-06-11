# Qdrant Database Schema

This document describes the Qdrant vector database schema used in the AI Membership Enrollment application.

## Collection Overview

### Collection Name: `enrollment_data`

**Configuration:**
- **Vector Size**: 768 dimensions (OpenAI text-embedding-ada-002)
- **Distance Metric**: Cosine similarity
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **HNSW Parameters**:
  - `m`: 16 (number of bi-directional links for each node)
  - `ef_construct`: 100 (size of dynamic candidate list)

## Payload Schema

All points in the collection contain vector embeddings and structured payload data. The payload includes a `type` field that categorizes the data and additional fields specific to each type.

### Common Fields

All payloads include these common fields:

```json
{
  "type": "string",           // Payload type identifier
  "created_at": "string",     // ISO 8601 timestamp
  "updated_at": "string"      // ISO 8601 timestamp (optional)
}
```

### Indexed Fields

The following fields are indexed for efficient filtering:

- `type`: Payload type for filtering queries
- `user_id`: User identifier for user-specific queries
- `session_id`: Session identifier for session-specific queries
- `ticket_id`: Ticket identifier for ticket-specific queries
- `category`: Ticket category (e.g., "MP" for membership)

## Payload Types

### 1. Session Data (`type: "session"`)

Stores user conversation sessions and collected enrollment data.

**Schema:**
```json
{
  "type": "session",
  "session_id": "string",
  "user_id": "string",
  "data": {
    "messages": [
      {
        "role": "user|assistant",
        "content": "string",
        "timestamp": "string"
      }
    ],
    "current_step": "string",
    "collected_data": {
      "name": "string",
      "email": "string",
      "program_type": "string",
      "company": "string",
      "job_title": "string",
      "referral_source": "string"
    },
    "is_complete": "boolean",
    "ticket_generated": "boolean"
  },
  "created_at": "string",
  "updated_at": "string"
}
```

**Vector Source**: Embedding of the latest user message or session summary.

### 2. Ticket Data (`type: "ticket"`)

Stores generated membership tickets for Zendesk integration.

**Schema:**
```json
{
  "type": "ticket",
  "session_id": "string",
  "ticket_data": {
    "ticket_id": "string",
    "subject": "string",
    "description": "string",
    "category": "string",
    "assignee": "string",
    "priority": "string",
    "status": "string",
    "requester_email": "string",
    "member_details": {
      "name": "string",
      "email": "string",
      "program_type": "string",
      "company": "string"
    }
  },
  "created_at": "string"
}
```

**Vector Source**: Embedding of ticket subject and description combined.

### 3. Summary Data (`type: "summary"`)

Stores enrollment summary information for PDF generation.

**Schema:**
```json
{
  "type": "summary",
  "session_id": "string",
  "summary_text": "string",
  "created_at": "string"
}
```

**Vector Source**: Embedding of the summary text.

### 4. Log Data (`type: "log"`)

Stores system logs and events for monitoring and debugging.

**Schema:**
```json
{
  "type": "log",
  "level": "string",
  "message": "string",
  "module": "string",
  "session_id": "string",
  "user_id": "string",
  "metadata": "object",
  "created_at": "string"
}
```

**Vector Source**: Embedding of the log message.

### 5. Zendesk Ticket Data (`type: "zendesk_ticket"`)

Stores imported Zendesk tickets from datadumps.

**Schema:**
```json
{
  "type": "zendesk_ticket",
  "ticket_id": "string",
  "data": {
    "id": "string",
    "subject": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "requester_email": "string",
    "created_at": "string",
    "updated_at": "string",
    "tags": ["string"]
  },
  "created_at": "string"
}
```

**Vector Source**: Embedding of ticket subject and description combined.

### 6. Question Data (`type: "question"`)

Stores predefined enrollment questions for semantic matching.

**Schema:**
```json
{
  "type": "question",
  "text": "string",
  "category": "string",
  "created_at": "string"
}
```

**Vector Source**: Embedding of the question text.

## Query Patterns

### 1. Retrieve Session Data

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Get session by session_id
filter = Filter(
    must=[
        FieldCondition(key="type", match=MatchValue(value="session")),
        FieldCondition(key="session_id", match=MatchValue(value="session_123"))
    ]
)

results = client.scroll(
    collection_name="enrollment_data",
    scroll_filter=filter,
    limit=1
)
```

### 2. Semantic Search for Similar Questions

```python
# Find similar questions using vector search
results = client.search(
    collection_name="enrollment_data",
    query_vector=question_embedding,
    query_filter=Filter(
        must=[FieldCondition(key="type", match=MatchValue(value="question"))]
    ),
    limit=5
)
```

### 3. Get User's Tickets

```python
# Get all tickets for a user
filter = Filter(
    must=[
        FieldCondition(key="type", match=MatchValue(value="ticket")),
        FieldCondition(key="user_id", match=MatchValue(value="user_456"))
    ]
)

results = client.scroll(
    collection_name="enrollment_data",
    scroll_filter=filter,
    limit=10
)
```

### 4. Search Zendesk Tickets by Content

```python
# Semantic search in Zendesk tickets
results = client.search(
    collection_name="enrollment_data",
    query_vector=search_embedding,
    query_filter=Filter(
        must=[FieldCondition(key="type", match=MatchValue(value="zendesk_ticket"))]
    ),
    limit=20
)
```

## Performance Considerations

### Indexing Strategy

1. **Vector Index**: HNSW for fast approximate nearest neighbor search
2. **Payload Index**: Keyword indexes on frequently filtered fields
3. **Memory Usage**: Optimize vector dimensions and payload size

### Query Optimization

1. **Use Filters**: Always combine vector search with payload filters when possible
2. **Limit Results**: Use appropriate limit values to reduce response time
3. **Batch Operations**: Use batch upsert for multiple points

### Monitoring

1. **Collection Stats**: Monitor collection size and memory usage
2. **Query Performance**: Track search latency and throughput
3. **Index Health**: Monitor HNSW index performance metrics

## Data Lifecycle

### Data Retention

1. **Session Data**: Retain for 90 days for analytics
2. **Ticket Data**: Permanent retention for audit trail
3. **Log Data**: Retain for 30 days for debugging
4. **Zendesk Data**: Permanent retention for historical analysis

### Backup Strategy

1. **Regular Snapshots**: Daily collection snapshots
2. **Point-in-Time Recovery**: Maintain transaction logs
3. **Cross-Region Replication**: For disaster recovery

## Security

### Access Control

1. **API Keys**: Secure Qdrant API access
2. **Network Security**: VPC isolation and security groups
3. **Encryption**: At-rest and in-transit encryption

### Data Privacy

1. **PII Anonymization**: Before storing in Qdrant
2. **Data Masking**: Sensitive fields in logs
3. **Compliance**: GDPR and data protection requirements

This schema provides a comprehensive foundation for the AI Membership Enrollment application's vector database needs, supporting both operational requirements and analytical capabilities.
