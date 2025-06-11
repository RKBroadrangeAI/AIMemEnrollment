# Deployment Guide

This guide covers deploying the AI Membership Enrollment application to various environments.

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker and Docker Compose
- OpenAI API key

### Quick Start
```bash
# Clone repository
git clone https://github.com/RKBroadrangeAI/AIMemEnrollment.git
cd AIMemEnrollment

# Use deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Manual Setup

1. **Start Qdrant Database**
   ```bash
   docker-compose up -d qdrant
   ```

2. **Backend Setup**
   ```bash
   cd backend/ai-membership-enrollment
   
   # Install dependencies
   poetry install
   
   # Set environment variables
   cp .env .env.local
   # Edit .env.local with your OpenAI API key
   
   # Start server
   poetry run fastapi dev app/main.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend/ai-membership-enrollment-ui
   
   # Install dependencies
   npm install
   
   # Set environment variables
   cp .env .env.local
   # Edit .env.local if needed
   
   # Start development server
   npm run dev
   ```

## Production Deployment

### AWS EC2 Deployment

#### Prerequisites
- AWS CLI configured
- EC2 instance (t3.medium or larger)
- Security groups configured for ports 80, 443, 8000, 3000
- Domain name (optional)

#### Step 1: EC2 Instance Setup
```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### Step 2: Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and Poetry
sudo apt install python3.12 python3.12-venv python3-pip -y
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

#### Step 3: Deploy Application
```bash
# Clone repository
git clone https://github.com/RKBroadrangeAI/AIMemEnrollment.git
cd AIMemEnrollment

# Set up environment variables
cp backend/ai-membership-enrollment/.env backend/ai-membership-enrollment/.env.production
# Edit with production values

# Start Qdrant
docker-compose up -d qdrant

# Build and start backend
cd backend/ai-membership-enrollment
poetry install --no-dev
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 &

# Build and serve frontend
cd ../../frontend/ai-membership-enrollment-ui
npm install
npm run build
npx serve -s dist -l 3000 &
```

#### Step 4: Configure Nginx (Optional)
```bash
# Install Nginx
sudo apt install nginx -y

# Configure Nginx
sudo tee /etc/nginx/sites-available/ai-enrollment << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-enrollment /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Docker Deployment

#### Create Dockerfiles

**Backend Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY . .

EXPOSE 8000
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose for Production
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  backend:
    build: ./backend/ai-membership-enrollment
    ports:
      - "8000:8000"
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant
    restart: unless-stopped

  frontend:
    build: ./frontend/ai-membership-enrollment-ui
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  qdrant_data:
```

### Kubernetes Deployment

#### Prerequisites
- EKS cluster or Kubernetes cluster
- kubectl configured
- Docker images pushed to registry

#### Deployment Manifests

**Namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-enrollment
```

**Qdrant Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: ai-enrollment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
      volumes:
      - name: qdrant-storage
        persistentVolumeClaim:
          claimName: qdrant-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant-service
  namespace: ai-enrollment
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
```

**Backend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: ai-enrollment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/ai-enrollment-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: QDRANT_HOST
          value: "qdrant-service"
        - name: QDRANT_PORT
          value: "6333"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: ai-enrollment
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

**Frontend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: ai-enrollment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/ai-enrollment-frontend:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: ai-enrollment
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

#### Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n ai-enrollment
kubectl get services -n ai-enrollment

# Get external IPs
kubectl get services -n ai-enrollment -o wide
```

## Environment Variables

### Backend (.env)
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=ai-membership-enrollment

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Frontend (.env)
```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# For production
VITE_API_URL=https://api.your-domain.com
```

## Monitoring and Logging

### Health Checks
```bash
# Backend health
curl http://your-backend-url/healthz

# Qdrant health
curl http://your-qdrant-url:6333/health
```

### Logging Configuration
```python
# In production, configure structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_entry)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitoring with CloudWatch (AWS)
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## Security Considerations

### SSL/TLS Configuration
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### Environment Security
- Store secrets in AWS Secrets Manager or Kubernetes secrets
- Use IAM roles for AWS resource access
- Enable VPC security groups
- Regular security updates

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   ```bash
   # Check Qdrant status
   docker logs qdrant_container_name
   
   # Verify network connectivity
   telnet qdrant_host 6333
   ```

2. **OpenAI API Errors**
   ```bash
   # Verify API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **Frontend Build Issues**
   ```bash
   # Clear cache and rebuild
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. **Backend Import Errors**
   ```bash
   # Check Python environment
   poetry show
   poetry install --no-dev
   ```

### Performance Tuning

1. **Backend Optimization**
   - Use Gunicorn with multiple workers
   - Enable connection pooling for Qdrant
   - Implement caching for frequent queries

2. **Frontend Optimization**
   - Enable gzip compression
   - Use CDN for static assets
   - Implement code splitting

3. **Database Optimization**
   - Configure Qdrant memory settings
   - Use appropriate vector dimensions
   - Implement proper indexing

## Backup and Recovery

### Qdrant Backup
```bash
# Create backup
docker exec qdrant_container tar -czf /tmp/qdrant_backup.tar.gz /qdrant/storage

# Copy backup
docker cp qdrant_container:/tmp/qdrant_backup.tar.gz ./qdrant_backup.tar.gz

# Restore backup
docker cp ./qdrant_backup.tar.gz qdrant_container:/tmp/
docker exec qdrant_container tar -xzf /tmp/qdrant_backup.tar.gz -C /
```

### Application Backup
```bash
# Backup application code and configs
tar -czf app_backup.tar.gz \
  --exclude=node_modules \
  --exclude=.git \
  --exclude=__pycache__ \
  .
```

This deployment guide provides comprehensive instructions for deploying the AI Membership Enrollment application in various environments, from local development to production Kubernetes clusters.
