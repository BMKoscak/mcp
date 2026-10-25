import httpx
import pytest

from mcp_nexus.services.llm_router import ChatMessage, LLMRequest, LLMRouter


@pytest.mark.asyncio
async def test_ollama_router_parses_chat_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"message": {"content": "hello"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        router = LLMRouter(client=client)
        response = await router.complete(
            LLMRequest(model="llama3", messages=[ChatMessage(role="user", content="hi")])
        )

    assert response.content == "hello"
    assert response.provider == "ollama"
