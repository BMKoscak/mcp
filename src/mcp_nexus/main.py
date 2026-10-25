"""FastAPI application for MCP Nexus."""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .mcp_engine import MCPEngine
from .services.database import Database
from .services.llm_router import LLMRequest, LLMRouter
from .templates.manager import TemplateManager


class TemplatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1)


class RenderPayload(BaseModel):
    values: dict[str, str] = {}


def create_app(
    *,
    database_path: str | Path = "./data/mcp_nexus.db",
    filesystem_root: str | Path = ".",
    llm_router: LLMRouter | None = None,
) -> FastAPI:
    database = Database(database_path)
    engine = MCPEngine(filesystem_root=filesystem_root)
    router = llm_router or LLMRouter(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    )
    templates = TemplateManager(database)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await database.connect()
        yield
        await database.close()

    app = FastAPI(title="MCP Nexus", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.state.engine = engine

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "mcp-nexus"}

    @app.get("/api/connectors")
    async def connectors() -> dict[str, list[str]]:
        return {"connectors": list(engine.registry.names())}

    @app.get("/api/events")
    async def events(limit: int = 100) -> list[dict[str, Any]]:
        return await database.list_events(limit)

    @app.get("/api/events/stream")
    async def event_stream(request: Request) -> StreamingResponse:
        async def generate():
            latest = (await database.list_events(1))
            last_id = latest[0]["id"] if latest else 0
            yield "event: ready\ndata: {}\n\n"
            while not await request.is_disconnected():
                new_events = await database.list_events_after(last_id)
                for event in reversed(new_events):
                    last_id = event["id"]
                    yield f"event: protocol\ndata: {json.dumps(event)}\n\n"
                await asyncio.sleep(1)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/templates")
    async def list_templates() -> list[dict[str, Any]]:
        return await database.list_templates()

    @app.post("/api/templates")
    async def save_template(payload: TemplatePayload) -> dict[str, object]:
        return await templates.save(payload.name, payload.body)

    @app.post("/api/templates/{name}/render")
    async def render_template(name: str, payload: RenderPayload) -> dict[str, str]:
        try:
            return {"name": name, "body": await templates.render(name, payload.values)}
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/chat")
    async def chat(payload: LLMRequest, request: Request) -> dict[str, Any]:
        await database.record_event("request", payload.model_dump(), method="chat")
        try:
            response = await router.complete(payload)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        await database.record_event("response", response.raw, method="chat")
        return response.model_dump()

    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("mcp_nexus.main:app", host="127.0.0.1", port=8000, reload=False)
