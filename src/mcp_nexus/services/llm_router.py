"""Direct async adapters for supported LLM providers."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    provider: str = "ollama"
    model: str
    messages: list[ChatMessage]
    temperature: float = Field(default=0.2, ge=0, le=2)


class LLMResponse(BaseModel):
    provider: str
    model: str
    content: str
    raw: dict[str, Any]


class LLMRouter:
    """Route chat completion requests without coupling the API to one vendor."""

    def __init__(
        self,
        *,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        ollama_base_url: str = "http://127.0.0.1:11434",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self._client = client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=60.0)
        try:
            if request.provider == "openai":
                return await self._openai(client, request)
            if request.provider == "anthropic":
                return await self._anthropic(client, request)
            if request.provider == "ollama":
                return await self._ollama(client, request)
            raise ValueError(f"Unsupported LLM provider: {request.provider}")
        finally:
            if owns_client:
                await client.aclose()

    async def _openai(self, client: httpx.AsyncClient, request: LLMRequest) -> LLMResponse:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
        }
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.openai_api_key}"},
            json=payload,
        )
        response.raise_for_status()
        raw = response.json()
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            content=raw["choices"][0]["message"]["content"],
            raw=raw,
        )

    async def _anthropic(self, client: httpx.AsyncClient, request: LLMRequest) -> LLMResponse:
        if not self.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        messages = [m.model_dump() for m in request.messages if m.role != "system"]
        payload: dict[str, Any] = {
            "model": request.model,
            "max_tokens": 4096,
            "messages": messages,
            "temperature": request.temperature,
        }
        if system:
            payload["system"] = system
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
            },
            json=payload,
        )
        response.raise_for_status()
        raw = response.json()
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            content="".join(block["text"] for block in raw["content"] if block["type"] == "text"),
            raw=raw,
        )

    async def _ollama(self, client: httpx.AsyncClient, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        response = await client.post(f"{self.ollama_base_url}/api/chat", json=payload)
        response.raise_for_status()
        raw = response.json()
        return LLMResponse(
            provider=request.provider,
            model=request.model,
            content=raw["message"]["content"],
            raw=raw,
        )
