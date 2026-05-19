# QueryLens

AI-powered SQL review platform. Paste a query, get deterministic anti-pattern analysis, EXPLAIN ANALYZE bottleneck detection, and LLM-generated explanations with rewrite suggestions — all in one structured review.

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi) ![Next.js](https://img.shields.io/badge/Next.js-15.5-black?style=flat-square&logo=nextdotjs) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql) ![Tests](https://img.shields.io/badge/tests-118%20passing-brightgreen?style=flat-square)

## What it does

1. **Static analysis** — sqlglot parses the SQL AST and runs anti-pattern rules (SELECT \*, missing WHERE on DELETE/UPDATE, implicit cross joins, leading wildcards, functions on indexed columns, ORDER BY without LIMIT).
2. **Execution plan analysis** — EXPLAIN ANALYZE fires against PostgreSQL; the JSON plan tree is walked to detect sequential scans on large tables, row estimation errors, expensive sorts, and nested loop blowups.
3. **AI augmentation** — An LLM explains each finding, suggests rewrites, adjusts tone for the selected review mode (junior / senior / performance), and optionally provides an educational note.

AI is never the primary analysis engine. It explains and educates on top of deterministic findings.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 async, Alembic |
| SQL analysis | sqlglot (AST parsing), pluggable rule registry |
| AI providers | OpenAI, Anthropic, Ollama (via OpenAI-compatible endpoint) |
| Database | PostgreSQL 16, asyncpg |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS, CodeMirror 6 |
| Infra | Docker Compose, multi-stage Dockerfiles |

## Quick start

### With Docker Compose

The default AI provider is **Ollama** (local, no API key needed). On first run, Docker Compose automatically pulls the `llama3.1` model (~4.7 GB) before starting the backend. Subsequent starts are instant because the model is cached in a named volume.

```bash
# 1. Copy backend config (no changes needed for Ollama)
cp backend/.env.example backend/.env

# 2. Start everything (first run pulls the model — allow a few minutes)
docker compose up --build

# Backend:  http://localhost:8000
# Frontend: http://localhost:3000
# Ollama:   http://localhost:11434
# API docs: http://localhost:8000/docs
```

To use a cloud LLM instead, set `DEFAULT_LLM_PROVIDER=openai` (or `anthropic`) and add your API key in `backend/.env`.

### Local development

**Backend:**

```bash
cd backend
pip install hatchling
pip install -e ".[dev]"
cp .env.example .env

# Start PostgreSQL + Ollama
docker compose up postgres ollama ollama-init -d

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## API

### POST `/api/v1/queries/review`

Submit a SQL query for review.

```json
{
  "sql": "SELECT * FROM orders WHERE customer_id = 42",
  "dialect": "",
  "review_mode": "senior",
  "provider": "openai"
}
```

**Fields:**
- `sql` — required, max 50,000 characters
- `dialect` — optional sqlglot dialect name (`"bigquery"`, `"mysql"`, `"spark"`, …)
- `review_mode` — `junior` | `senior` | `performance` (default: `senior`)
- `provider` — `openai` | `anthropic` | `ollama` (defaults to `DEFAULT_LLM_PROVIDER`)

**Response `201`:**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "sql": "SELECT * FROM orders WHERE customer_id = 42",
  "dialect": "",
  "review_mode": "senior",
  "static_analysis": {
    "query_type": "SELECT",
    "table_references": ["orders"],
    "findings": [
      {
        "rule_id": "select_star",
        "severity": "warning",
        "category": "performance",
        "title": "SELECT * detected",
        "message": "Fetching all columns prevents index-only scans and increases network overhead.",
        "suggestion": "List only the columns you need."
      }
    ],
    "critical_count": 0,
    "warning_count": 1,
    "info_count": 0
  },
  "execution_plan": {
    "findings": [],
    "execution_time_ms": 0.12,
    "planning_time_ms": 0.08,
    "has_analyze_data": true
  },
  "ai_review": {
    "summary": "The query is functional but fetches more data than needed.",
    "findings": [
      {
        "rule_id": "select_star",
        "explanation": "SELECT * forces PostgreSQL to read every column...",
        "suggestion": "Replace * with the specific columns your application uses."
      }
    ],
    "improved_query": "SELECT id, status, total FROM orders WHERE customer_id = 42",
    "educational_note": null,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "input_tokens": 312,
    "output_tokens": 187
  },
  "created_at": "2026-05-19T10:00:00Z"
}
```

### GET `/api/v1/queries/review/{id}`

Retrieve a previously created review by UUID.

## Configuration

All settings are environment variables (or `backend/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/querylens` | Async PostgreSQL DSN |
| `DEFAULT_LLM_PROVIDER` | `openai` | Which provider to use by default |
| `OPENAI_API_KEY` | — | OpenAI secret key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `ANTHROPIC_API_KEY` | — | Anthropic secret key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Anthropic model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Ollama model name |
| `ENVIRONMENT` | `development` | `development` \| `staging` \| `production` |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array of allowed origins |

## Anti-pattern rules

| Rule ID | Severity | Description |
|---------|----------|-------------|
| `select_star` | warning | `SELECT *` fetches unnecessary columns |
| `missing_where` | critical | `DELETE` or `UPDATE` without a WHERE clause |
| `implicit_cross_join` | warning | Comma-separated tables in FROM without a join condition |
| `leading_wildcard` | warning | `LIKE '%value'` prevents index usage |
| `function_on_column` | warning | Function call wrapping an indexed column in WHERE |
| `order_without_limit` | info | `ORDER BY` on a large result set with no `LIMIT` |

Adding a new rule: create a class in `backend/app/analysis/anti_patterns/` implementing `AntiPatternRule`, then add one line to `RULE_REGISTRY` in `__init__.py`. No other changes required.

## Execution plan rules

| Rule ID | Severity | Trigger |
|---------|----------|---------|
| `seq_scan` | warning | Sequential scan on > 500 estimated rows |
| `row_estimation_error` | warning | Planner estimate off by > 10× (≥ 10 actual rows) |
| `expensive_sort` | info | Sort node contributes > 10% of total plan cost |
| `nested_loop_large` | warning | Nested loop with > 100 actual loop iterations |

## Tests

```bash
cd backend

# Unit tests (no DB or API keys required)
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL)
INTEGRATION_TESTS=1 \
  DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/querylens_test \
  pytest tests/integration/ -v

# All unit tests
pytest tests/unit/              # 106 tests
pytest -k "select_star"         # filter by name
```

Unit tests need no running database or API keys — execution plan tests use fixture JSON, and API tests use FastAPI `dependency_overrides`. Integration tests (12 tests) exercise the repository and endpoints against a real PostgreSQL instance.

## Project structure

```
query-lens/
├── backend/
│   ├── app/
│   │   ├── ai/               # LLM provider abstraction + prompt system
│   │   ├── analysis/         # SQL parser, anti-pattern rules, execution plan
│   │   ├── api/v1/           # FastAPI routers + request/response schemas
│   │   ├── core/             # Config, logging, exceptions
│   │   ├── domain/           # Models + QueryReviewService orchestration
│   │   └── infrastructure/   # SQLAlchemy ORM + repository pattern
│   ├── alembic/              # DB migrations
│   └── tests/
│       ├── unit/
│       └── integration/
└── frontend/
    └── src/
        ├── app/              # Next.js App Router (layout + page)
        ├── components/       # ReviewWorkspace, SqlEditor, result cards
        ├── lib/              # Typed API client
        └── types/            # TypeScript types mirroring backend schemas
```
