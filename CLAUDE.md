# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

QueryLens is a production-grade AI-powered SQL review platform. It accepts SQL queries, runs deterministic static analysis and EXPLAIN ANALYZE, then augments results with AI-generated explanations and rewrite suggestions. The goal is portfolio-quality code, not a toy — production-minded development is expected throughout.

## Commands

### Backend (Python / FastAPI)

```bash
cd backend

# Setup (first time)
pip install hatchling
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload

# Tests
pytest                          # all tests
pytest tests/unit/              # unit tests only
pytest tests/unit/test_health.py -v  # single file
pytest -k "test_liveness"       # single test by name

# Lint / format
ruff check .
ruff format .

# Type check
mypy app/
```

### Frontend (Next.js / TypeScript)

```bash
cd frontend

# Setup (first time)
npm install

# Run dev server (http://localhost:3000)
npm run dev

# Type check
npm run type-check

# Production build
npm run build
```

Note: Node is not in the default shell PATH on this machine. Use the binary at
`/Users/kodox/.cache/pyright-python/nodeenv/src/node-v25.6.0-darwin-x64/bin/`
or add it to PATH: `export PATH="/Users/kodox/.cache/pyright-python/nodeenv/src/node-v25.6.0-darwin-x64/bin:$PATH"`

### Docker

```bash
docker compose up postgres      # PostgreSQL only
docker compose up               # all services (postgres + backend + frontend)
docker compose up --build       # rebuild images
```

## Architecture

### Frontend structure

Next.js App Router at `frontend/src/`:
- `app/` — layout and page (server components)
- `components/ReviewWorkspace.tsx` — top-level client component owning all interactive state (SQL editor, submission, results display)
- `components/SqlEditor.tsx` — CodeMirror 6 editor, dynamically imported with `ssr: false`
- `components/StaticAnalysisCard.tsx`, `AiReviewCard.tsx`, `ExecutionPlanCard.tsx` — result sections
- `lib/api.ts` — typed API client (`createReview`, `getReview`) with `ApiError` class
- `types/review.ts` — TypeScript types mirroring backend response schemas

The frontend makes direct browser requests to the backend (`NEXT_PUBLIC_API_URL`). No Next.js API routes/proxy layer.

### Backend layer map

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `app/api/v1/` | FastAPI routers — request validation, response shaping only |
| Domain | `app/domain/` | Framework-agnostic business logic and orchestration |
| Analysis | `app/analysis/` | SQL parsing and anti-pattern detection |
| AI | `app/ai/` | LLM provider abstraction and prompt system |
| Infrastructure | `app/infrastructure/` | Database connection and repositories |
| Core | `app/core/` | Config, logging, exceptions |

### Analysis pipeline (order matters)

1. **Static analysis** — sqlglot parses the AST; anti-pattern rules run against it (always runs, no I/O)
2. **Execution plan** — EXPLAIN ANALYZE fires against PostgreSQL; plan nodes parsed for bottlenecks (skipped if DB unreachable)
3. **AI augmentation** — LLM explains findings, suggests rewrites, adjusts tone per review mode

AI is never the primary analysis engine. It only explains and educates on top of deterministic findings.

### Anti-pattern rule system

Each rule lives in `app/analysis/anti_patterns/` and is a standalone class with a stable `rule_id`. `RULE_REGISTRY` in `__init__.py` lists all rules — adding a new rule means adding a file and one line in the registry. No changes to core analysis code. Rules are injected into `StaticAnalyzer` and can be replaced in tests for isolation.

Current rules: `select_star`, `missing_where`, `implicit_cross_join`, `leading_wildcard`, `function_on_column`, `order_without_limit`.

### AI provider abstraction

All LLM providers implement a shared `LLMProvider` Protocol defined in `app/ai/base.py`. The domain layer never imports `openai` or `anthropic` directly — only the Protocol. `app/ai/factory.py` holds a module-level singleton cache (`_instances`) and returns providers by name. Providers: `OpenAIProvider`, `AnthropicProvider`, `OllamaProvider` (uses the OpenAI client pointed at Ollama's `/v1` endpoint). All providers use tenacity for retry on transient errors.

### Prompt system

`app/ai/prompts/templates.py` holds system prompt strings keyed by `ReviewMode`. `PromptBuilder` in `app/ai/prompts/builder.py` assembles the message list — it formats findings and injects the JSON response schema. The schema instructs the LLM to return `summary`, `improved_query`, `findings[]`, and `educational_note`.

`AIResponseParser` in `app/ai/response_parser.py` handles three formats the LLM might return: bare JSON, JSON in a code fence, and unstructured text (fallback). When the LLM returns empty findings but static analysis has some, the parser synthesizes AI findings from the static ones.

### Domain service

`QueryReviewService` in `app/domain/services/query_review_service.py` is the single orchestration point: static analysis → prompt build → LLM call → parse response → return `QueryReview`. It holds no state and is fully injectable.

### Review modes

`junior` / `senior` / `performance` modes are passed as context into the prompt system. Different system prompt templates are selected per mode — there is no conditional branching in the service layer.

### Execution plan analysis

`app/analysis/execution_plan/` mirrors the anti-pattern module structure:
- `runner.py` — `ExplainAnalyzeRunner` takes an `AsyncSession`, runs `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` for SELECT and plain `EXPLAIN (FORMAT JSON)` for DML (avoids executing DML). Uses `asyncio.wait_for` for timeout.
- `parser.py` — recursively parses PostgreSQL's JSON plan tree into `PlanNode` dataclasses.
- `rules.py` — `PlanRule` ABC + 4 concrete rules: `seq_scan`, `row_estimation_error`, `expensive_sort`, `nested_loop_large`.
- `analyzer.py` — `ExecutionPlanAnalyzer` tree-walks all nodes and collects `PlanFinding` objects.

The plan step is optional in `QueryReviewService` — pass `plan_runner=None` to skip it (tests do this). If the runner raises `ExecutionPlanError`, the service logs a warning and continues without plan data. `QueryReview.execution_plan` is `None` when skipped.

Plan findings are included in the LLM prompt via `PromptBuilder.build_review_messages(query, analysis, plan_result)`.

Unit tests use sample EXPLAIN JSON fixtures in `tests/unit/analysis/execution_plan/fixtures.py` — no live DB required.

### Config

All settings live in `app/core/config.py` (Pydantic `BaseSettings`). Environment variables or a `.env` file (copy `.env.example`) override defaults. `get_settings()` is cached via `@lru_cache`.

### Error handling

Domain exceptions in `app/core/exceptions.py` are mapped to HTTP status codes in `app/main.py` exception handlers. Never raise `HTTPException` from domain or analysis code — raise domain exceptions and let the API layer translate.

### Logging

Structured logging via `structlog`. Use `get_logger(__name__)` everywhere. In production, emits JSON. In development, pretty console output. Log event names use `dot.notation` (e.g., `sql.parse.error`, `llm.provider.error`).

## Key Conventions

- Type hints everywhere, including return types
- Async throughout — FastAPI endpoints, DB calls, AI SDK calls
- Repositories handle all DB interaction; services never touch SQLAlchemy directly
- `.env` is gitignored; `.env.example` is the reference
- Tests live next to the code they test: `tests/unit/` for logic, `tests/integration/` for DB/API roundtrips
