"""Read-only web fetch MCP connector."""

from __future__ import annotations

import httpx

from ..services.registry import Connector


def web_fetcher_connector() -> Connector:
    def register(server: object) -> None:
        @server.tool(
            name="fetch_url",
            description="Fetch a public HTTP(S) URL and return its response text.",
        )
        async def fetch_url(url: str, max_chars: int = 20_000) -> str:
            if not url.startswith(("http://", "https://")):
                raise ValueError("Only HTTP(S) URLs are supported")
            if max_chars < 1:
                raise ValueError("max_chars must be positive")
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
            response.raise_for_status()
            return response.text[:max_chars]

    return Connector(name="web_fetcher", register=register)

