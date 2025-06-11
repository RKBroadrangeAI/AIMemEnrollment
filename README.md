# AI Membership Enrollment

An intelligent membership enrollment system powered by OpenAI GPT-4, LangGraph workflows, and Qdrant vector database. This application automates the membership enrollment process through conversational AI, reducing manual processing time by 50% and achieving 80% conversation completion without human intervention.

## Features

- **Conversational AI Bot**: Natural language processing using OpenAI GPT-4
- **Agentic Workflows**: LangGraph-powered state machine for enrollment flow
- **Vector Database**: Qdrant for semantic search and data storage
- **React Frontend**: Modern UI with Tailwind CSS and shadcn/ui components
- **Zendesk Integration**: Datadump import with placeholder for real-time API
- **PII Protection**: Automatic PII detection and anonymization using Presidio
- **PDF Generation**: Automated enrollment summary generation
- **Ticket Management**: Automatic ticket creation and classification

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangGraph**: Agentic workflow orchestration
- **OpenAI GPT-4**: Natural language processing
- **Qdrant**: Vector database for embeddings and semantic search
- **Presidio**: PII detection and anonymization
- **LangSmith**: Observability and tracing

### Frontend
- **React 18**: Modern React with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality React components
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication

### Database
- **Qdrant**: Single vector database instance
  - Collection: `enrollment_data`
  - Vector dimensions: 1536 (OpenAI embeddings)
  - Index: HNSW for fast similarity search
  - Payloads: sessions, tickets, summaries, logs, zendesk_tickets

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker and Docker Compose
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RKBroadrangeAI/AIMemEnrollment.git
   cd AIMemEnrollment
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/ai-membership-enrollment/.env backend/ai-membership-enrollment/.env.local
   # Edit the .env.local file with your OpenAI API key and other settings
   
   # Frontend
   cp frontend/ai-membership-enrollment-ui/.env frontend/ai-membership-enrollment-ui/.env.local
   ```

3. **Start Qdrant database**
   ```bash
   docker-compose up -d qdrant
   ```

4. **Install and start backend**
   ```bash
   cd backend/ai-membership-enrollment
   poetry install
   poetry run fastapi dev app/main.py
   ```

5. **Install and start frontend**
   ```bash
   cd frontend/ai-membership-enrollment-ui
   npm install
   npm run dev
   ```

### Quick Deploy Script
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## API Documentation

### Core Endpoints

#### Chat Interface
- `POST /api/chat` - Process conversational input
- `GET /api/session/{session_id}` - Retrieve session data
- `GET /api/ticket/{session_id}` - Get generated ticket
- `GET /api/summary/{session_id}` - Download PDF summary

#### Zendesk Integration
- `POST /api/zendesk/datadump` - Import Zendesk datadump
- `GET /api/zendesk/tickets` - List imported tickets
- `POST /api/zendesk/ticket` - Create ticket (placeholder)

#### Health Check
- `GET /healthz` - Service health status

## Workflow Architecture

### LangGraph Enrollment Flow

1. **Start** → Welcome user and initialize session
2. **Ask Name** → Collect user's full name
3. **Ask Email** → Collect and validate email address
4. **Ask Program Type** → Determine membership program preference
5. **Ask Company** → Collect company information
6. **Validate Profile** → Ensure all required data is collected
7. **Generate Ticket** → Create membership ticket with MP category
8. **Complete** → Finalize enrollment and offer summary download

### Data Flow

1. **User Input** → Conversational interface
2. **LangGraph Processing** → State machine workflow
3. **OpenAI GPT-4** → Natural language understanding
4. **PII Anonymization** → Presidio processing
5. **Qdrant Storage** → Vector embeddings and metadata
6. **Ticket Generation** → Structured data for Zendesk
7. **PDF Summary** → Downloadable enrollment report

## Qdrant Schema

### Collection: `enrollment_data`
- **Vectors**: 1536-dimensional OpenAI embeddings
- **Distance**: Cosine similarity
- **Index**: HNSW for fast search

### Payload Types
- `session`: User conversation sessions
- `ticket`: Generated membership tickets
- `summary`: Enrollment summaries
- `log`: System logs and events
- `zendesk_ticket`: Imported Zendesk tickets

### Indexed Fields
- `type`: Payload type for filtering
- `user_id`: User identifier
- `session_id`: Session identifier
- `ticket_id`: Ticket identifier
- `category`: Ticket category (MP for membership)

## Zendesk Integration

### Datadump Import
Supports JSON and CSV formats with the following structure:

```json
{
  "id": "12345",
  "subject": "Membership Inquiry",
  "description": "User asking about premium membership",
  "status": "open",
  "priority": "normal",
  "requester_email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "tags": ["membership", "premium"]
}
```

### Future Real-time API
Placeholder endpoints prepared for:
- OAuth authentication
- Ticket creation via Zendesk API
- Real-time ticket updates
- Rate limiting and error handling

## Security & Privacy

### PII Protection
- **Presidio Integration**: Automatic detection of names, emails, phone numbers
- **Anonymization**: PII replaced with placeholders before storage
- **Configurable**: Adjustable sensitivity levels

### Security Measures
- **CORS Configuration**: Proper cross-origin resource sharing
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Secure error messages without data leakage
- **Environment Variables**: Sensitive data in environment configuration

## Performance & Monitoring

### Response Time Targets
- **Chat Responses**: < 3 seconds
- **PDF Generation**: < 5 seconds
- **Database Queries**: < 1 second

### Observability
- **LangSmith**: Workflow tracing and performance monitoring
- **Logging**: Structured logging with correlation IDs
- **Health Checks**: Service availability monitoring

### Success Metrics
- **80% Conversation Completion**: Without human intervention
- **50% Manual Processing Reduction**: Automated ticket generation
- **High User Satisfaction**: Measured through LangSmith feedback

## Development

### Backend Development
```bash
cd backend/ai-membership-enrollment
poetry shell
poetry run fastapi dev app/main.py --reload
```

### Frontend Development
```bash
cd frontend/ai-membership-enrollment-ui
npm run dev
```

### Testing
```bash
# Backend tests
cd backend/ai-membership-enrollment
poetry run pytest

# Frontend tests
cd frontend/ai-membership-enrollment-ui
npm test
```

### Code Quality
```bash
# Backend linting
poetry run black .
poetry run isort .
poetry run flake8

# Frontend linting
npm run lint
npm run type-check
```

## Deployment

### Local Development
Use the provided `docker-compose.yml` for local Qdrant instance and the deploy script for full local setup.

### Production Deployment
The application is designed for AWS EC2 deployment with:
- **EKS**: Kubernetes orchestration
- **API Gateway**: Request routing and rate limiting
- **CloudFront**: CDN for frontend assets
- **ELB**: Load balancing
- **CloudWatch**: Monitoring and alerting
- **WAF**: Web application firewall
- **KMS**: Key management for secrets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions or support, please contact the development team or create an issue in the GitHub repository.
