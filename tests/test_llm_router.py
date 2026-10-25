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


def test_provider_status_does_not_expose_credentials() -> None:
    router = LLMRouter(openai_api_key="secret")
    status = router.provider_status()
    openai = next(item for item in status if item["provider"] == "openai")
    assert openai["configured"] is True
    assert "secret" not in str(status)


@pytest.mark.asyncio
async def test_ollama_connection_check() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await LLMRouter(client=client).test_connection("ollama")
    assert result["ok"] is True
