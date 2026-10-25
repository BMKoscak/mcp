# MCP Nexus Development Log

## 2026-10-25 — Phase 1: project scaffold

### Built

- Initialized the local Git repository.
- Added a Python 3.12+ project definition in `pyproject.toml`.
- Added a matching `requirements.txt` for direct environment setup.
- Created the package layout for the MCP engine, connectors, services, templates,
  frontend, and tests.
- Added `.gitignore` and `.env.example` for safe local development.
- Added the initial architecture document and Mermaid component diagram.
- Added this development log as the source of incremental project history.

### Architectural decisions

- Use a `src/` package layout to keep imports and packaging boundaries explicit.
- Use FastAPI and async Python interfaces throughout the runtime.
- Keep SQLite as the local persistence boundary, accessed asynchronously.
- Keep connectors independent from the browser layer so they can be registered
  and tested without starting the web server.
- Treat outbound actions as confirmation-gated by default.

### Next phase

Implement the MCP engine, SQLite persistence, and the first filesystem,
webhook, and web-fetch connectors.

## 2026-10-25 — Phase 2: MCP core and starter connectors

### Built

- Added `Database`, an async SQLite persistence service for settings, prompt
  state, and structured protocol events.
- Added `ConnectorRegistry` with duplicate-name protection and deterministic
  registration order.
- Added `MCPEngine`, which assembles a FastMCP server and registers the starter
  connector set.
- Added a sandboxed filesystem connector with UTF-8 read/write tools and a file
  resource.
- Added a confirmation-gated webhook sender using async HTTP.
- Added a read-only HTTP(S) fetcher with response-size limits.
- Added focused persistence, registry, and filesystem safety tests.
- Pinned the MCP SDK to `<2.0.0` because Phase 2 targets the FastMCP 1.x API.

### Architectural decisions

- Connector factories return a small `Connector` value object so connector
  configuration remains explicit and testable.
- Filesystem paths are resolved against a configured root and rejected if they
  escape that root.
- Outbound webhooks require an explicit `confirmed=true` argument by default.
- Protocol payloads are stored as JSON in SQLite so the inspector can consume
  exact request and response data later.

### Validation

- `python -m pytest -q` — 3 passed.
- `python -m ruff check src tests` — passed.

## 2026-10-25 — Provider connections

### Built

- Added provider status reporting for Ollama, OpenAI, and Anthropic without
  returning credentials.
- Added safe reachability checks using provider model-list endpoints.
- Wired the Connections tab to display configuration state and test results.
- Added status and mocked connection-check coverage.

### Validation

- `python -m pytest -q` — 10 passed.
- `python -m ruff check src tests` — passed.
- FastMCP engine smoke test — registered `filesystem`, `webhook`, and
  `web_fetcher`.

### Next phase

Build the FastAPI host, LLM connection router, and parameterized prompt-template
manager on top of the Phase 2 services.

## 2026-10-25 — Phase 3: FastAPI host and LLM routing

### Built

- Added `LLMRouter` adapters for OpenAI Chat Completions, Anthropic Messages,
  and local Ollama chat APIs.
- Added normalized Pydantic request/response models for provider-independent
  chat calls.
- Added `TemplateManager` with `{{ variable }}` extraction, persistence, and
  missing-variable validation.
- Extended SQLite persistence with prompt template CRUD and protocol event
  storage.
- Added the FastAPI application with health, connector, event, template, render,
  and chat endpoints.
- Added application lifecycle management so the database is connected and
  closed with the FastAPI app.
- Added six tests covering routing, templates, persistence, connector exposure,
  and API health.

### Architectural decisions

- Provider adapters share one normalized `LLMRequest`/`LLMResponse` contract,
  keeping frontend and API code independent of vendor-specific response shapes.
- Provider credentials are read from environment variables and are never stored
  in the SQLite event log.
- Template variables are extracted from the body at save time and validated
  before rendering.
- Chat requests and raw provider responses are recorded as inspector events.

### Validation

- `python -m pytest -q` — 6 passed.
- `python -m ruff check src tests` — passed.
- `python -m compileall -q src tests` — passed.

### Next phase

Build the dashboard UI with Chat & Execution, Connections, Templates, and Live
JSON-RPC Inspector tabs.

## 2026-10-25 — Phase 4: local dashboard

### Built

- Added a zero-build `frontend/index.html` dashboard using Tailwind CDN,
  Alpine.js, and HTMX.
- Added tabs for Chat & Execution, Connections, Templates, and Live Inspector.
- Added browser actions for chat requests, template saves, connector discovery,
  and event refresh.
- Mounted the frontend from FastAPI so `GET /` serves the local dashboard.
- Added a frontend serving smoke test.

### Architectural decisions

- Keep the frontend dependency-light and local-first: CDN assets are used to
  avoid introducing a build pipeline during the initial release.
- Use the existing JSON API as the UI boundary, keeping frontend state separate
  from MCP connector implementation.
- Treat the inspector as an event view over persisted request/response payloads;
  a future phase can replace polling with SSE without changing its data shape.

### Validation

- `python -m pytest -q` — 7 passed.
- `python -m ruff check src tests` — passed.
- `git diff --check` — passed.

### Next phase

Finalize the README, complete release documentation, run endpoint verification,
and publish the repository to GitHub.

## 2026-10-25 — Phase 5: documentation and release preparation

### Built

- Replaced the initial README with a complete project guide, badges, feature
  overview, Mermaid architecture diagram, quickstart, API table, layout guide,
  and sub-20-line connector example.
- Added the MIT `LICENSE`.
- Confirmed the repository is ready for publication as `BMKoscak/mcp`.

### Validation

- Full test suite and lint remain green after documentation changes.
- Git history contains one Conventional Commit per completed milestone.

## 2026-10-25 — Live inspector streaming

### Built

- Added `GET /api/events/stream`, an SSE endpoint that emits new persisted
  protocol events without requiring dashboard refreshes.
- Updated the dashboard to subscribe with `EventSource` and prepend incoming
  events to the inspector.
- Added an SSE response test while preserving the existing events history API.

### Validation

- `python -m pytest -q` — 8 passed.
- `python -m ruff check src tests` — passed.
