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

