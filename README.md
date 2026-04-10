# AgentAichain

[![GitHub license](https://img.shields.io/badge/license-proprietary-blue.svg)](https://github.com/aichainssrl-collab/agentAichain)
[![GitHub issues](https://img.shields.io/github/issues/aichainssrl-collab/agentAichain)](https://github.com/aichainssrl-collab/agentAichain/issues)
[![GitHub stars](https://img.shields.io/github/stars/aichainssrl-collab/agentAichain)](https://github.com/aichainssrl-collab/agentAichain/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/aichainssrl-collab/agentAichain)](https://github.com/aichainssrl-collab/agentAichain/network)

**B2B Multi-Agent Platform** based on AGNO. Build, orchestrate, and scale AI agents in a multi-tenant enterprise environment.

---

## 🚀 Features

### Core Platform
- **Multi-tenancy** – Full isolation (DB, memory, logging) per client
- **FastAPI REST** – Ready for B2B integrations
- **AGNO Core** – Agent, Team, Workflow, Memory
- **Audit Logging** – Structured JSON, 10+ years retention
- **GCP Native** – Cloud Run, Cloud SQL, Redis, GCS
- **Scalable** – Horizontal scaling, stateless design
- **Secure** – API keys, JWT, tenant isolation
- **Async Execution** – Celery for long-running agent tasks

### Settings Management
- **Skills** – Catalog of reusable agent capabilities
- **AI Models** – Provider-agnostic model configuration (OpenAI, Anthropic, Ollama, OpenRouter, etc.)
- Cost tracking & context window management
- Active/inactive model status for controlled deployment

### React Frontend (v1.0)
- **TypeScript + React 18** – Type-safe development
- **Vite** – Lightning-fast HMR and builds
- **Tailwind CSS** – Utility-first styling
- **React Query** – Intelligent data fetching and caching
- **React Router v6** – Modern client-side routing
- **Features:**
  - User authentication (login/register)
  - Dashboard with system overview
  - Agent management: CRUD with dynamic model selection
  - Team management: create teams, add/remove agents
  - Run monitoring: real-time status updates
  - API key management
  - Settings: Skills & AI Models configuration

---

## 📦 Installation

### Local Development (Docker Compose)

```bash
# Clone
git clone https://github.com/aichainssrl-collab/agentAichain.git
cd agentAichain

# Copy environment
cp .env.example .env
# Edit .env if needed (defaults work for local)

# Start services (Postgres, Redis, API)
docker-compose up -d

# Check logs
docker-compose logs -f api

# Initialize DB and seed demo data
docker-compose exec api python scripts/seed.py

# Create additional tenant (optional)
docker-compose exec api python scripts/create_tenant.py --name "Acme" --slug "acme" --email "admin@acme.com" --password "secure123"

# Access API
curl http://localhost:8000/health
# API docs: http://localhost:8000/docs
```

**Default credentials after seed:**
- Tenant: `demo`
- Admin email: `admin@demo.com`
- Password: `demo123`

---

### Manual Setup (without Docker)

```bash
# Prerequisites: Python 3.11+, PostgreSQL, Redis

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt

# Set environment variables (or create .env)
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost/agent_aichain
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key-here
export AGNO_API_KEY=your-agno-key

# Initialize database
alembic upgrade head

# Seed demo data (optional)
python scripts/seed.py

# Run API
uvicorn agent_aichain.main:app --reload
```

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐
│   Client App    │
│  (Frontend/BC)  │
└────────┬────────┘
         │ HTTPS (API Key / JWT)
┌────────▼──────────────┐
│     FastAPI Layer     │
│  (AgentAichain API)   │
│  • Auth               │
│  • Tenant isolation   │
│  • Request validation │
└────────┬──────────────┘
         │
    ┌────┴────┬───────────────┐
    ▼         ▼               ▼
┌──────┐ ┌──────────┐ ┌─────────────┐
│Agent │ │   Team   │ │     Run     │
│Svc   │ │   Svc    │ │   Service   │
└──────┘ └──────────┘ └─────────────┘
    │         │               │
    └─────────┼───────────────┘
              ▼
      ┌──────────────┐
      │   Celery     │
      │  (Background │
      │   Workers)   │
      └──────┬───────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌───────┐       ┌──────────┐
│ AGNO  │       │  Redis   │
│  API  │       │ (Queue & │
│(LLM)  │       │  Cache)  │
└───────┘       └──────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────┐
│PostgreSQL │ │    │         │
│ (Metadata)│ │    │         │
└───────────┘ │    │         │
              │    │         │
         ┌────┴────┴────┐
         ▼              ▼
   ┌──────────┐  ┌──────────┐
   │ Cloud SQL│  │Memorystore│
   │   &      │  │  (Redis) │
   │  Terraform│  │          │
   └──────────┘  └──────────┘
```

### Components

1. **FastAPI Application** (`agent_aichain/main.py`)
   - REST API endpoints
   - CORS middleware
   - Structured logging (structlog)
   - Health checks
   - Error handling

2. **SQLAlchemy Models** (`agent_aichain/models/`)
   - `Tenant` – Organization (multi-tenancy root)
   - `User` – Human users (belongs to tenant)
   - `APIKey` – Machine authentication
   - `Agent` – AI agent definition (role, model, tools)
   - `Team` – Group of agents working together
   - `Run` – Execution record (async task tracking)
   - `team_agents` – Many-to-many association

3. **Database Layer**
   - PostgreSQL (Cloud SQL) for metadata
   - Async SQLAlchemy 2.0
   - Alembic migrations
   - All queries tenant-scoped via `WHERE tenant_id = current_tenant`

4. **Agent Execution Engine**
   - `TenantAwareAgent` / `TenantAwareTeam` wrappers (`workers/agno_wrapper.py`)
   - Injects tenant context into AGNO API calls
   - Handles timeouts, retries, error logging
   - Communicates with external AGNO service

5. **Celery Workers** (`workers/`)
   - `run_agent_task` – Execute single agent
   - `run_team_task` – Execute team collaboration
   - Async tasks queued in Redis
   - Update Run status (pending → running → completed/failed)

6. **Authentication**
   - API Key (primary B2B): `X-API-Key` header, hashed with bcrypt
   - JWT (user auth): OAuth2 password flow, 30min expiry
   - Secret Manager for production secrets

7. **Infrastructure** (GCP)
   - Cloud Run (stateless API containers)
   - Cloud SQL (PostgreSQL)
   - Memorystore (Redis)
   - Secret Manager (credentials)
   - Cloud Monitoring & Logging

---

## 🔐 Authentication

Two methods available:

### API Key (Machine-to-Machine)

Create an API key via API or script, then include in requests:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.example.com/api/v1/agents
```

### JWT (User Login)

Obtain token via password grant:

```bash
curl -X POST https://api.example.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"
```

Then use:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.example.com/api/v1/agents
```

---

## 📚 Quick Example

```python
import httpx

# Initialize client
client = httpx.Client(
    base_url="http://localhost:8000/api/v1",
    headers={"X-API-Key": "your_api_key_here"}
)

# Create an agent
resp = client.post("/agents", json={
    "name": "Support Bot",
    "role": "assistant",
    "model": "gpt-4o",
    "instructions": "Be helpful and concise.",
    "tools": ["search_kb"]
})
agent_id = resp.json()["id"]

# Run the agent (async)
run_resp = client.post(f"/runs/agent/{agent_id}", json={
    "task": "Answer question",
    "input": {"question": "What is your return policy?"}
})
run_id = run_resp.json()["run_id"]

# Poll for result
import time
while True:
    run = client.get(f"/runs/{run_id}").json()
    if run["status"] in ("completed", "failed"):
        print(f"Result: {run.get('output')}")
        break
    time.sleep(1)

client.close()
```

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run unit tests
pytest tests/unit -v

# Run integration tests (requires Postgres + Redis running)
pytest tests/integration -v

# With coverage
pytest --cov=agent_aichain --cov-report=html
```

---

## 🐳 Docker

```bash
# Build image
docker build -t agent-aichain .

# Run all services (API, Postgres, Redis, Celery worker, Flower)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## ☁️ Deployment to GCP

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed guide.

Quick steps:

```bash
# 1. Build and push to GCR
gcloud auth configure-docker
docker build -t gcr.io/YOUR_PROJECT/agent-aichain:latest .
docker push gcr.io/YOUR_PROJECT/agent-aichain:latest

# 2. Create Cloud SQL & Redis (or use Terraform)
#   See terraform/gcp/ for infrastructure as code

# 3. Deploy to Cloud Run
gcloud run deploy agent-aichain \
  --image gcr.io/YOUR_PROJECT/agent-aichain:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-env-vars REDIS_URL=redis://... \
  --set-secrets SECRET_KEY=agent-aichain-jwt-secret:latest

# 4. Run migrations
gcloud run services execute agent-aichain --region=europe-west1 -- alembic upgrade head

# 5. Create first tenant
gcloud run services execute agent-aichain --region=europe-west1 -- python scripts/create_tenant.py --name "Demo" --slug demo --email admin@demo.com --password "change_me"
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, scalability |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API endpoint documentation |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | GCP deployment guide (manual + Terraform) |
| [SECURITY.md](docs/SECURITY.md) | Security policy, threat model, compliance |
| [MULTI_TENANCY.md](docs/MULTI_TENANCY.md) | Multi-tenant architecture guide |
| [AGENT.md](docs/AGENT.md) | Guide to Agent configuration and AGNO Integration |
| [EXAMPLES.md](docs/EXAMPLES.md) | Practical usage examples (curl, Python) |
| [OPERATIONS.md](docs/OPERATIONS.md) | Runbook, monitoring, incident response |

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow code style (black, ruff)
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. **NEVER commit API keys or sensitive secrets to Git. Always use `.env` files or dummy values for testing.**
7. Submit a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for details.

---

## 📄 License

Proprietary – All rights reserved. See [LICENSE](LICENSE) for details.

---

## 🏢 About

AgentAichain is developed by **Aichain Solutions** for enterprise multi-agent orchestration.

**Tech Stack:**
- Python 3.11
- FastAPI
- SQLAlchemy (async)
- PostgreSQL + Redis
- Celery
- AGNO
- Terraform (GCP)
- Docker

**Status:** Phase 1 complete (Core Platform). Phase 2: Settings Management & Testing (Apr 3-10, 2026).

---

*Built with ❤️ in Italy*