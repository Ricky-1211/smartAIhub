# SmartAIHub Complete Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Local Development Setup](#local-development-setup)
4. [Environment Variables Setup](#environment-variables-setup)
5. [Database Setup](#database-setup)
6. [Running Services Individually](#running-services-individually)
7. [Frontend Setup](#frontend-setup)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

1. **Python 3.9+**
   - Download from: https://www.python.org/downloads/
   - Verify installation: `python --version` or `python3 --version`
   - Ensure `pip` is installed: `pip --version`

2. **Node.js 18+ and npm**
   - Download from: https://nodejs.org/
   - Verify installation: `node --version` and `npm --version`

3. **PostgreSQL** (Choose one option)
   - **Option A**: Docker (Recommended for development)
   - **Option B**: Local PostgreSQL installation
     - Windows: https://www.postgresql.org/download/windows/
     - Linux: `sudo apt-get install postgresql` (Ubuntu/Debian)
     - Mac: `brew install postgresql` or download from postgresql.org

4. **Git** (for cloning repository)
   - Download from: https://git-scm.com/downloads

5. **Docker & Docker Compose** (Optional, for containerized deployment)
   - Download from: https://www.docker.com/get-started

### Verify Prerequisites
```bash
# Check Python
python --version  # Should show 3.9 or higher

# Check Node.js
node --version    # Should show 18 or higher
npm --version

# Check PostgreSQL (if installed locally)
psql --version

# Check Docker (optional)
docker --version
docker-compose --version
```

---

## Quick Start with Docker

If you want to run everything in Docker containers:

1. **Clone the repository**
```bash
git clone <repo-url>
cd SmartAIHub
```

2. **Start all services**
```bash
docker-compose up -d
```

3. **Check service status**
```bash
docker-compose ps
```

4. **View logs**
```bash
docker-compose logs -f <service-name>
```

5. **Access the application**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Service Health: http://localhost:8000/health

6. **Stop all services**
```bash
docker-compose down
```

---

## Local Development Setup

### Step 1: Clone Repository
```bash
git clone <repo-url>
cd SmartAIHub
```

### Step 2: Install Shared Dependencies
```bash
# Install shared Python packages (required by all services)
cd shared
pip install -r requirements.txt
cd ..
```

**Note**: The `shared` directory contains common utilities and configuration used by all services.

### Step 3: Database Setup

#### Option 1: Docker PostgreSQL (Recommended)

**Windows:**
```bash
docker run -d `
  --name smartaihub-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=smartaihub `
  -p 5432:5432 `
  postgres:15-alpine
```

**Linux/Mac:**
```bash
docker run -d \
docker run -d \
  --name smartaihub-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=smartaihub \
  -p 5432:5432 \
  postgres:15-alpine
```

**Using Docker Compose (only PostgreSQL):**
```bash
docker-compose up -d postgres
```

#### Option 2: Local PostgreSQL Installation

1. **Install PostgreSQL** from https://www.postgresql.org/download/

2. **Create databases:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create databases
CREATE DATABASE smartaihub;
CREATE DATABASE smartaihub_logs;
CREATE DATABASE smartaihub_search;
CREATE DATABASE smartaihub_models;

# Exit
\q
```

3. **Verify connection:**
```bash
psql -U postgres -d smartaihub -c "SELECT version();"
```

---

## Environment Variables Setup

Each service requires a `.env` file. Example files are provided in `env-examples/` directory.

### 1. Gateway Service
```bash
# Copy example file
cp env-examples/gateway.env.example gateway/.env

# Edit gateway/.env and update service URLs for local development:
# AUTH_SERVICE_URL=http://localhost:8001
# SPAM_SERVICE_URL=http://localhost:8002
# ... etc
```

### 2. Auth Service
```bash
# Copy example file
cp env-examples/auth-service.env.example auth-service/.env

# Edit auth-service/.env and update:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=smartaihub
# JWT_SECRET_KEY=your-secret-key-change-in-production
```

### 3. Frontend
```bash
# Copy example file
cp env-examples/frontend.env.example frontend/.env

# Edit frontend/.env (usually no changes needed for local dev):
# VITE_API_URL=http://localhost:8000
```

### 4. Other Services
Copy and configure `.env` files for other services as needed:
```bash
cp env-examples/spam-detection.env.example ai-services/spam-detection/.env
cp env-examples/logging-service.env.example system-services/logging-service/.env
# ... etc for other services
```

**Important**: Update database credentials and service URLs in each `.env` file to match your local setup.

---

## Running Services Individually

### Service Ports Reference
- **8000** - API Gateway
- **8001** - Auth Service
- **8002** - Spam Detection
- **8003** - WhatsApp Analysis
- **8004** - Movie Recommendation
- **8005** - Resume Matcher
- **8006** - House Price Prediction
- **8007** - Fraud Detection
- **8008** - Code Review
- **8009** - Logging Service
- **8010** - Search Service
- **8011** - Model Management
- **3000** - Frontend

### Step-by-Step: Running Each Service

#### 1. Start PostgreSQL (Required First)
```bash
# Using Docker (recommended)
docker start smartaihub-postgres

# Or using Docker Compose
docker-compose up -d postgres

# Verify it's running
docker ps | grep postgres
```

#### 2. Install Service Dependencies

For each service you want to run, install its dependencies:

```bash
# Gateway
cd gateway
pip install -r requirements.txt
pip install -r ../shared/requirements.txt
cd ..

# Auth Service
cd auth-service
pip install -r requirements.txt
pip install -r ../shared/requirements.txt
cd ..

# Spam Detection
cd ai-services/spam-detection
pip install -r requirements.txt
pip install -r ../../shared/requirements.txt
cd ../..

# Repeat for other services as needed
```

**Tip**: You can install all dependencies at once:
```bash
# From project root
for dir in gateway auth-service ai-services/* system-services/*; do
  if [ -f "$dir/requirements.txt" ]; then
    echo "Installing dependencies for $dir"
    pip install -r "$dir/requirements.txt"
    pip install -r shared/requirements.txt
  fi
done
```

#### 3. Run Services in Separate Terminals

**Terminal 1 - API Gateway** (Required - routes all requests)
```bash
cd gateway
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```
- Access: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Terminal 2 - Auth Service** (Required - handles authentication)
```bash
cd auth-service
uvicorn main:app --reload --port 8001 --host 0.0.0.0
```
- Access: http://localhost:8001
- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health

**Terminal 3 - Spam Detection Service**
```bash
cd ai-services/spam-detection
uvicorn main:app --reload --port 8002 --host 0.0.0.0
```
- Access: http://localhost:8002
- Docs: http://localhost:8002/docs

**Terminal 4 - WhatsApp Analysis Service**
```bash
cd ai-services/whatsapp-analysis
uvicorn main:app --reload --port 8003 --host 0.0.0.0
```

**Terminal 5 - Movie Recommendation Service**
```bash
cd ai-services/movie-recommendation
uvicorn main:app --reload --port 8004 --host 0.0.0.0
```

**Terminal 6 - Resume Matcher Service**
```bash
cd ai-services/resume-matcher
uvicorn main:app --reload --port 8005 --host 0.0.0.0
```

**Terminal 7 - House Price Prediction Service**
```bash
cd ai-services/house-price-prediction
uvicorn main:app --reload --port 8006 --host 0.0.0.0
```

**Terminal 8 - Fraud Detection Service**
```bash
cd ai-services/fraud-detection
uvicorn main:app --reload --port 8007 --host 0.0.0.0
```

**Terminal 9 - Code Review Service**
```bash
cd system-services/code-review
uvicorn main:app --reload --port 8008 --host 0.0.0.0
```

**Terminal 10 - Logging Service**
```bash
cd system-services/logging-service
uvicorn main:app --reload --port 8009 --host 0.0.0.0
```

**Terminal 11 - Search Service**
```bash
cd system-services/search-service
uvicorn main:app --reload --port 8010 --host 0.0.0.0
```

**Terminal 12 - Model Management Service**
```bash
cd system-services/model-management
uvicorn main:app --reload --port 8011 --host 0.0.0.0
```

### Minimum Required Services for Basic Functionality

For basic testing, you only need:
1. **PostgreSQL** (database)
2. **Gateway** (port 8000)
3. **Auth Service** (port 8001)

Other services can be started as needed.

### Verify Services Are Running

```bash
# Check Gateway
curl http://localhost:8000/health

# Check Auth Service
curl http://localhost:8001/health

# Check all services status via Gateway
curl http://localhost:8000/services/status
```

---

## Frontend Setup

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

This installs:
- React 18.2.0
- React Router DOM
- Axios (for API calls)
- Tailwind CSS
- Vite (build tool)

### Step 2: Configure Environment Variables
```bash
# Copy example file
cp ../env-examples/frontend.env.example .env

# Edit .env if needed (usually defaults are fine for local dev)
# VITE_API_URL=http://localhost:8000
```

### Step 3: Start Development Server
```bash
npm run dev
```

The frontend will start on **http://localhost:3000**

### Step 4: Verify Frontend Connection

1. Open browser: http://localhost:3000
2. Check browser console for errors
3. Try logging in/registering to test API connection

### Frontend Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Frontend Structure
- `src/App.jsx` - Main app component
- `src/pages/` - Page components
- `src/components/` - Reusable components
- `src/contexts/` - React contexts (Auth, etc.)
- `vite.config.js` - Vite configuration with API proxy

---

## Testing

### Test Database Connection
```bash
# Using psql
psql -U postgres -d smartaihub -c "SELECT 1;"
```

### Test Authentication Service

**1. Register a new user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**2. Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

Save the `access_token` from the response.

**3. Test protected endpoint:**
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Spam Detection Service
```bash
curl -X POST http://localhost:8000/spam/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Free money now! Click here!",
    "type": "email"
  }'
```

### Test Gateway Health
```bash
# Gateway health
curl http://localhost:8000/health

# All services status
curl http://localhost:8000/services/status
```

### Using curl for Testing
You can use curl commands (shown above) or any HTTP client to test the services.

---

## Troubleshooting

### Services Not Starting

**Problem**: Port already in use
```bash
# Windows - Find process using port
netstat -ano | findstr :8000

# Linux/Mac - Find process using port
lsof -i :8000

# Kill the process or use a different port
```

**Problem**: Module not found errors
```bash
# Ensure shared dependencies are installed
pip install -r shared/requirements.txt

# Reinstall service dependencies
pip install -r <service>/requirements.txt
```

**Problem**: Import errors
```bash
# Make sure you're running from the correct directory
# Services need access to ../shared directory
```

### Database Connection Errors

**Problem**: Cannot connect to PostgreSQL
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Or for local PostgreSQL
# Windows
Get-Service postgresql*

# Linux
sudo systemctl status postgresql

# Verify connection string in .env file
# Test connection
psql -U postgres -h localhost -p 5432 -d smartaihub
```

**Problem**: Database does not exist
```bash
# Create database
psql -U postgres
CREATE DATABASE smartaihub;
CREATE DATABASE smartaihub_logs;
CREATE DATABASE smartaihub_search;
CREATE DATABASE smartaihub_models;
\q
```

**Problem**: Authentication failed
- Check `POSTGRES_USER` and `POSTGRES_PASSWORD` in `.env` file
- Verify credentials match your PostgreSQL setup

### Frontend Not Connecting to API

**Problem**: CORS errors
- Check `ALLOWED_ORIGINS` in gateway `.env` includes `http://localhost:3000`
- Verify gateway is running on port 8000

**Problem**: Network errors
- Verify API Gateway is running: `curl http://localhost:8000/health`
- Check `VITE_API_URL` in frontend `.env` is `http://localhost:8000`
- Check browser console for specific error messages

**Problem**: 404 errors
- Ensure Gateway is running and routing correctly
- Check service URLs in gateway `.env` file
- Verify target service is running

### Service-Specific Issues

**Spam Detection**: Requires trained models
```bash
# If models are missing, train them first
cd ai-services/spam-detection
python train.py
```

**Auth Service**: Database tables not created
- Tables are created automatically on first run
- Check database connection and permissions

### General Debugging Tips

1. **Check service logs** - Look at terminal output for errors
2. **Verify environment variables** - Ensure `.env` files are correct
3. **Test endpoints directly** - Use `curl` or Postman to test services
4. **Check service health** - Visit `/health` endpoint for each service
5. **Verify dependencies** - Reinstall requirements if needed

---

## Production Deployment

### 1. Environment Variables
- Update all `.env` files with production values
- Use strong `JWT_SECRET_KEY`
- Set production database credentials
- Configure proper `ALLOWED_ORIGINS`

### 2. Database
- Use managed PostgreSQL service (AWS RDS, Azure, etc.)
- Not Docker volumes for production
- Set up proper backups

### 3. Security
- Enable HTTPS with reverse proxy (Nginx/Traefik)
- Set secure JWT secret (use environment variable, not file)
- Configure proper CORS origins (no wildcards)
- Use environment variables for all secrets

### 4. Frontend Build
```bash
cd frontend
npm run build
# Serve the dist/ directory with a web server
```

### 5. Monitoring
- Set up logging aggregation
- Monitor service health endpoints
- Set up alerts for service failures

### 6. Docker Production
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d
```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Service Health**: http://localhost:8000/health
- **Services Status**: http://localhost:8000/services/status
- **Admin Panel**: http://localhost:3000/admin

## Quick Reference

### Start Minimum Services (Basic Testing)
```bash
# Terminal 1: PostgreSQL
docker start smartaihub-postgres

# Terminal 2: Gateway
cd gateway && uvicorn main:app --reload --port 8000

# Terminal 3: Auth Service
cd auth-service && uvicorn main:app --reload --port 8001

# Terminal 4: Frontend
cd frontend && npm run dev
```

### Stop All Services
```bash
# Stop Docker containers
docker stop smartaihub-postgres

# Stop Python services: Ctrl+C in each terminal
# Stop Frontend: Ctrl+C in frontend terminal
```

### Check Everything is Running
```bash
# Check all services
curl http://localhost:8000/services/status

# Check individual services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

