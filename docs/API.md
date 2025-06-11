# API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication
Currently, no authentication is required for the demo version. In production, implement proper authentication and authorization.

## Endpoints

### Health Check

#### GET /healthz
Check service health status.

**Response:**
```json
{
  "status": "ok"
}
```

### Chat Interface

#### POST /api/chat
Process conversational input through the LangGraph workflow.

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string",
  "user_id": "string (optional)"
}
```

**Response:**
```json
{
  "message": "string",
  "session_id": "string",
  "is_complete": "boolean",
  "next_step": "string",
  "collected_data": "object"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to enroll in your membership program",
    "session_id": "session_123"
  }'
```

### Session Management

#### GET /api/session/{session_id}
Retrieve session data including conversation history and collected information.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
{
  "session_id": "string",
  "user_id": "string",
  "messages": [
    {
      "role": "string",
      "content": "string"
    }
  ],
  "current_step": "string",
  "collected_data": "object",
  "is_complete": "boolean",
  "created_at": "string",
  "updated_at": "string"
}
```

### Ticket Management

#### GET /api/ticket/{session_id}
Retrieve generated ticket data for a completed enrollment session.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
```json
{
  "ticket_id": "string",
  "subject": "string",
  "description": "string",
  "category": "string",
  "assignee": "string",
  "priority": "string",
  "status": "string",
  "requester_email": "string",
  "member_details": "object",
  "created_at": "string"
}
```

### PDF Summary

#### GET /api/summary/{session_id}
Generate and download PDF summary of enrollment.

**Parameters:**
- `session_id` (path): Session identifier

**Response:**
- Content-Type: `application/pdf`
- File download with name: `enrollment_summary_{session_id}.pdf`

### Zendesk Integration

#### POST /api/zendesk/datadump
Import Zendesk datadump file (JSON or CSV format).

**Request:**
- Content-Type: `multipart/form-data`
- File field: `file`

**Response:**
```json
{
  "message": "string",
  "imported_count": "number"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/zendesk/datadump" \
  -F "file=@sample_zendesk_data.json"
```

#### GET /api/zendesk/tickets
List imported Zendesk tickets.

**Query Parameters:**
- `limit` (optional): Number of tickets to return (default: 50)
- `offset` (optional): Number of tickets to skip (default: 0)

**Response:**
```json
{
  "tickets": [
    {
      "id": "string",
      "subject": "string",
      "description": "string",
      "status": "string",
      "priority": "string",
      "requester_email": "string",
      "created_at": "string",
      "updated_at": "string",
      "tags": ["string"]
    }
  ],
  "total": "number"
}
```

#### POST /api/zendesk/ticket
Create ticket via Zendesk API (placeholder for future implementation).

**Request Body:**
```json
{
  "subject": "string",
  "description": "string",
  "requester_email": "string",
  "priority": "string"
}
```

**Response:**
```json
{
  "message": "Zendesk real-time API integration - Coming Soon",
  "ticket_id": "string"
}
```

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

Currently no rate limiting is implemented. In production, consider implementing:
- Per-IP rate limiting
- Per-user rate limiting
- API key-based quotas

## Data Models

### ChatRequest
```typescript
interface ChatRequest {
  message: string
  session_id: string
  user_id?: string
}
```

### ChatResponse
```typescript
interface ChatResponse {
  message: string
  session_id: string
  is_complete: boolean
  next_step: string
  collected_data: Record<string, any>
}
```

### EnrollmentData
```typescript
interface EnrollmentData {
  name?: string
  email?: string
  program_type?: string
  company?: string
  job_title?: string
  referral_source?: string
}
```

### TicketData
```typescript
interface TicketData {
  ticket_id: string
  subject: string
  description: string
  category: string
  assignee: string
  priority: string
  status: string
  requester_email: string
  member_details: EnrollmentData
  created_at: string
}
```

## WebSocket Support

Future versions may include WebSocket support for real-time chat updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/{session_id}')
ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // Handle real-time updates
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000'
})

// Send chat message
const response = await api.post('/api/chat', {
  message: 'Hello',
  session_id: 'session_123'
})

// Get session data
const session = await api.get('/api/session/session_123')

// Download PDF
const pdf = await api.get('/api/summary/session_123', {
  responseType: 'blob'
})
```

### Python
```python
import requests

# Send chat message
response = requests.post('http://localhost:8000/api/chat', json={
    'message': 'Hello',
    'session_id': 'session_123'
})

# Get session data
session = requests.get('http://localhost:8000/api/session/session_123')

# Upload datadump
with open('zendesk_data.json', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/zendesk/datadump', files=files)
```

## Testing

Use the provided sample data and test scripts:

```bash
# Test chat endpoint
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test_123"}'

# Test health check
curl http://localhost:8000/healthz

# Upload sample datadump
curl -X POST "http://localhost:8000/api/zendesk/datadump" \
  -F "file=@scripts/sample_zendesk_data.json"
```
