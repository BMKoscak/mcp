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
- FastMCP engine smoke test — registered `filesystem`, `webhook`, and
  `web_fetcher`.

### Next phase

Build the FastAPI host, LLM connection router, and parameterized prompt-template
manager on top of the Phase 2 services.
