# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

OpenAlgo — an open-source algorithmic trading platform that provides a unified REST API layer across 30+ Indian stock brokers. Python Flask backend with a React (Vite + TypeScript) frontend. Uses SQLite databases, ZeroMQ for internal messaging, and WebSockets for real-time market data streaming.

## Commands

### Backend

```bash
# Install dependencies (uses uv, not pip)
uv sync            # production deps
uv sync --dev      # includes ruff, bandit, detect-secrets, pip-audit

# Run the app (starts Flask + WebSocket proxy on ports 5000 and 8765)
python app.py

# Lint
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Tests (CI-safe subset — most tests need broker credentials)
uv run pytest test/test_log_location.py test/test_navigation_update.py \
  test/test_python_editor.py test/test_rate_limits_simple.py \
  test/test_logout_csrf.py -v --timeout=60

# Run a single test file
uv run pytest test/test_rate_limits_simple.py -v

# Security scanning
uv run bandit -r . -x ./.venv,./frontend,./node_modules
uv run detect-secrets scan --baseline .secrets.baseline
uv run pip-audit
```

### Frontend (from `frontend/` directory)

```bash
npm ci              # install
npm run dev         # dev server (Vite)
npm run build       # tsc + vite build → frontend/dist/
npm run lint        # Biome lint
npm run format      # Biome format
npm run check       # Biome lint + format (auto-fix)
npm run test:run    # Vitest (single run)
npm run test:coverage
npm run e2e         # Playwright E2E tests
```

### Pre-commit hooks

Ruff (lint + format), Biome (frontend), detect-secrets, trailing whitespace, YAML/JSON checks. Run `pre-commit install` to set up.

## Architecture

### Request Flow

`Client → Flask route (blueprints/) or REST API (restx_api/) → service layer (services/) → broker adapter (broker/<name>/api/) → external broker API`

### Key Layers

- **`app.py`** — Flask app factory (`create_app()`), blueprint registration, background DB init, cache restoration, WebSocket proxy startup. Entry point: `python app.py`.
- **`blueprints/`** — Flask blueprints for web UI routes (auth, dashboard, orders, settings, etc.). Each blueprint handles a page or feature area.
- **`restx_api/`** — Flask-RESTX API namespaces mounted at `/api/v1/`. Each file = one endpoint (placeorder, quotes, history, etc.). Uses API key auth, CSRF-exempt.
- **`services/`** — Business logic layer. Each service corresponds to a restx_api endpoint or blueprint feature. Services call into broker adapters.
- **`broker/<name>/`** — Plugin-based broker integrations. Each broker has:
  - `plugin.json` — metadata (supported exchanges, broker type, leverage config)
  - `api/` — `auth_api.py`, `order_api.py`, `data.py`, `funds.py`, `margin_api.py`
  - `mapping/` — `order_data.py`, `transform_data.py`, `margin_data.py`
  - `database/` — `master_contract_db.py` (symbol downloads)
  - `streaming/` — WebSocket adapter for real-time market data
- **`database/`** — SQLAlchemy-based DB modules. Each `*_db.py` owns its own scoped session and table definitions. Multiple SQLite databases: main (`openalgo.db`), latency, logs, sandbox. DuckDB for historical data (`historify.duckdb`).
- **`events/`** + **`subscribers/`** — In-process EventBus (pub/sub). Order events are published by services and consumed by three subscribers: `log_subscriber`, `socketio_subscriber`, `telegram_subscriber`. Events: `order.placed`, `order.failed`, `order.modified`, `order.cancelled`, `position.closed`, `basket.completed`, etc.
- **`websocket_proxy/`** — Standalone WebSocket server (port 8765) that bridges broker-specific streaming APIs into a unified WebSocket interface. Uses ZeroMQ internally. Runs in-process locally, separately in Docker.
- **`sandbox/`** — Analyzer mode: paper trading engine with virtual capital. Execution engine, position/order/fund managers, square-off scheduler.
- **`frontend/`** — React 19 + TypeScript + Vite + Tailwind CSS 4. Uses Radix UI, React Router, Zustand for state, TanStack Query for data fetching, Socket.IO client for real-time updates. Built output served by Flask from `frontend/dist/`.
- **`utils/`** — Shared utilities: logging, auth, config, security middleware, traffic logging, health monitoring, ngrok, event bus.

### Broker Plugin System

Brokers are loaded dynamically via `utils/plugin_loader.py`. At startup, `plugin.json` files are read for capabilities. Actual broker modules are imported lazily at login time. The `VALID_BROKERS` env var controls which brokers are available. All brokers implement the same API interface (`order_api.py`, `data.py`, etc.), making them interchangeable.

### Database Architecture

Multiple isolated SQLite databases (configured via env vars `DATABASE_URL`, `LATENCY_DATABASE_URL`, `LOGS_DATABASE_URL`, `SANDBOX_DATABASE_URL`). Each `database/*_db.py` module creates its own engine and scoped session. Tables are initialized in parallel at startup via `ThreadPoolExecutor`. Session cleanup happens in `app.teardown_appcontext`.

### Real-Time Data

ZeroMQ pub/sub bus distributes market data internally. The WebSocket proxy (`websocket_proxy/server.py`) authenticates clients via API key, creates broker-specific streaming adapters, and forwards normalized LTP/Quote/Depth data over WebSocket.

## Configuration

All config is via `.env` (copy `.sample.env`). Key variables: `BROKER_API_KEY`, `BROKER_API_SECRET`, `DATABASE_URL`, `APP_KEY`, `API_KEY_PEPPER`, `FLASK_HOST_IP`, `FLASK_PORT`, `WEBSOCKET_PORT`, `HOST_SERVER`, `VALID_BROKERS`.

## Tooling

- **Python**: 3.12+ required. Uses `uv` for dependency management (`pyproject.toml` + `uv.lock`).
- **Linting**: Ruff (backend), Biome (frontend). Config in `pyproject.toml` and `frontend/biome.json`.
- **Testing**: pytest (backend), Vitest (frontend unit), Playwright (frontend E2E).
- **CI**: GitHub Actions — backend lint/test, frontend lint/build/test/e2e, security scan (bandit, pip-audit, detect-secrets).
- **Docker**: `Dockerfile` + `docker-compose.yaml`. In Docker, WebSocket server runs as a separate process via `start.sh`.
