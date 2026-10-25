"""Confirmation-gated outbound HTTP webhook connector."""

from __future__ import annotations

from typing import Any

import httpx

from ..services.registry import Connector


def webhook_connector(*, require_confirmation: bool = True) -> Connector:
    def register(server: object) -> None:
        @server.tool(
            name="send_webhook",
            description="POST a JSON payload to a webhook URL.",
        )
        async def send_webhook(url: str, payload: dict[str, Any], confirmed: bool = False) -> str:
            if require_confirmation and not confirmed:
                raise PermissionError("Outbound webhook requires confirmed=true")
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                response = await client.post(url, json=payload)
            response.raise_for_status()
            return f"Webhook delivered with HTTP {response.status_code}"

    return Connector(name="webhook", register=register)

