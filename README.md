# SmartAIHub — Unified AI & System Services Platform

A comprehensive **microservices-based platform** integrating AI-powered services and system utilities with shared authentication, API gateway, centralized logging, search, and an admin dashboard.

---

## 🏗️ Architecture

```
Frontend (React)
        ↓
API Gateway (FastAPI)
        ↓
Microservices (AI + System Services)
```

---

## 📁 Project Structure (Merged)

```
SmartAIHub/
├── frontend/                 # React frontend
├── gateway/                  # API Gateway (FastAPI)
├── auth-service/             # Authentication & Authorization
├── ai-services/              # AI-powered services
│   ├── spam-detection/
│   ├── whatsapp-analysis/
│   ├── movie-recommendation/
│   ├── resume-matcher/
│   ├── house-price-prediction/
│   └── fraud-detection/
├── system-services/          # System utilities
│   ├── code-review/
│   ├── logging-service/
│   ├── search-service/
│   └── model-management/
├── shared/                   # Shared configs & utilities
├── docker-compose.yml        # Service orchestration
├── README.md                 # Documentation
└── SETUP.md                  # Setup guide
```

---

## 🚀 Services Overview

### Core Services

| Service         | Port | Description                 |
| --------------- | ---- | --------------------------- |
| API Gateway     | 8000 | Routes requests, auth, CORS |
| Auth Service    | 8001 | JWT auth, RBAC              |
| Logging Service | 8009 | Centralized logs            |

### AI Services

| Service                | Port | Function                      |
| ---------------------- | ---- | ----------------------------- |
| Spam Detection         | 8002 | Email/SMS spam detection      |
| WhatsApp Analysis      | 8003 | Chat sentiment & stats        |
| Movie Recommendation   | 8004 | Content-based recommendations |
| Resume Matcher         | 8005 | Resume–job matching           |
| House Price Prediction | 8006 | ML price prediction           |
| Fraud Detection        | 8007 | Transaction anomaly detection |

### System Services

| Service          | Port | Function                 |
| ---------------- | ---- | ------------------------ |
| Code Review      | 8008 | Automated code analysis  |
| Search Service   | 8010 | Global full-text search  |
| Model Management | 8011 | MLOps & model versioning |

### Frontend

| App             | Port |
| --------------- | ---- |
| React Dashboard | 3000 |

---

## 🛠️ Tech Stack

### Backend

* FastAPI, Node.js
* PostgreSQL, MongoDB (optional)
* Redis (caching)
* JWT Authentication

### Frontend

* React 18 (Vite)
* Tailwind CSS
* Axios, Recharts

### AI / ML

* Scikit-learn
* NLTK / spaCy
* Transformers (BERT)

### Infrastructure

* Docker & Docker Compose
* Nginx
* Prometheus + Grafana
* Elasticsearch (Search & Logs)

---

## 🗄️ Database Structure

| Database          | Purpose           |
| ----------------- | ----------------- |
| smartaihub        | Users & auth      |
| smartaihub_logs   | Logs & monitoring |
| smartaihub_search | Search indexing   |
| smartaihub_models | Model metadata    |

---

## ⚙️ Quick Start

### Prerequisites

* Docker & Docker Compose
* Python 3.9+
* Node.js 18+
* PostgreSQL

### Run Platform

```bash
git clone <repo-url>
cd SmartAIHub
docker-compose up -d
```

### Access

* Frontend: [http://localhost:3000](http://localhost:3000)
* API Gateway: [http://localhost:8000](http://localhost:8000)
* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔐 Authentication

* JWT-based authentication
* Centralized auth via Auth Service
* Role-based access control (RBAC)

---

## 📊 Monitoring & Health

* Centralized logging
* Prometheus metrics
* `/health` endpoint on each service

---

## ✅ Key Features

* Microservices architecture
* Unified API Gateway
* JWT authentication
* Centralized logging & search
* AI-powered services
* MLOps model management
* Dockerized deployment
* Scalable & modular design

---

## 📌 Next Steps

1. Configure `.env` files
2. Start services with Docker
3. Register a user
4. Explore services via dashboard
5. Monitor logs & metrics

---

## 📄 License

MIT License
