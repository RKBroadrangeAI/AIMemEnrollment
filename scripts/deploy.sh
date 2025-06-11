#!/bin/bash

echo "Starting deployment of AI Membership Enrollment application..."

echo "1. Starting Qdrant database..."
docker-compose up -d qdrant

echo "2. Installing backend dependencies..."
cd backend/ai-membership-enrollment
poetry install

echo "3. Installing frontend dependencies..."
cd ../../frontend/ai-membership-enrollment-ui
npm install

echo "4. Building frontend..."
npm run build

echo "5. Starting backend server..."
cd ../../backend/ai-membership-enrollment
poetry run fastapi dev app/main.py --host 0.0.0.0 --port 8000 &

echo "6. Starting frontend development server..."
cd ../../frontend/ai-membership-enrollment-ui
npm run dev --host 0.0.0.0 --port 3000 &

echo "Deployment complete!"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:3000"
echo "Qdrant Dashboard: http://localhost:6333/dashboard"
