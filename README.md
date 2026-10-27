# DocMind — Knowledge Assistant for SMEs

DocMind is an internal Knowledge Assistant powered by **Retrieval-Augmented Generation (RAG)**, designed for Small and Medium Enterprises (SMEs) with first-class support for Vietnamese documents. It allows teams to ingest internal documents (PDF, DOCX, Markdown, URLs) and ask questions with real-time streaming responses and verifiable source citations.

## Project Goals

- **Solve Real-World Knowledge Discovery:** Help employees quickly and accurately search company policies, contracts, SOPs, and technical documentation while minimizing LLM hallucinations through strict source citations.
- **Production & Multi-Tenant Architecture:** Built from the ground up with workspace isolation, flexible LLM provider routing, automated RAG evaluation, cost tracking, and full observability.

## Tech Stack

- **Backend:** Python 3.12 (`uv`), FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async) + Alembic
- **Database & Vector Store:** PostgreSQL 17 + `pgvector`
- **AI / RAG Orchestration:** LlamaIndex, Multi-provider LLM Abstraction (Gemini / OpenAI / Ollama)
- **Async Background Jobs & Caching:** Redis + ARQ
- **Observability & Quality Assurance:** Langfuse, Pytest, Ruff
- **Infrastructure:** Docker & Docker Compose

## Project Structure

```text
docmind/
├── backend/
│   ├── app/
│   │   ├── core/          # Application settings & environment configuration
│   │   ├── schemas/       # Pydantic v2 DTOs & domain dataclasses
│   │   ├── utils/         # Vietnamese text normalization & async helpers
│   │   └── main.py        # FastAPI application entrypoint
│   ├── tests/             # Automated test suite (Pytest)
│   ├── Dockerfile         # Multi-stage Dockerfile (dev & prod targets)
│   └── pyproject.toml     # Dependencies, Ruff, and Pytest configuration
├── infra/
│   └── db/init.sql        # PostgreSQL initialization script (vector, uuid-ossp)
├── docker-compose.yml     # Local development container stack
├── dev.sh                 # Development task runner script
└── .env.example           # Environment variables template
```

## Getting Started (Local Development)

### 1. Prerequisites
- Docker & Docker Compose
- A running PostgreSQL 17 container (`postgres-17`) on the host machine

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

### 3. Initialize Database & `pgvector` Extension
The following command automatically checks/installs `pgvector` inside the `postgres-17` container, creates the `docmind` database, and enables required extensions:
```bash
./dev.sh init-db
```

### 4. Start the Backend Stack
```bash
./dev.sh up
```
The API will be available at `http://localhost:8000`:
- **Swagger UI:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

### 5. Common Development Commands (`./dev.sh`)
```bash
./dev.sh logs      # Tail FastAPI container logs
./dev.sh test      # Run the Pytest test suite inside the container
./dev.sh lint      # Run static analysis and linting with Ruff
./dev.sh fmt       # Auto-format code with Ruff
./dev.sh psql      # Open an interactive psql shell in the docmind database
./dev.sh migrate   # Run Alembic database migrations
./dev.sh down      # Stop and remove running containers
```
