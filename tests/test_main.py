from pathlib import Path

from fastapi.testclient import TestClient

from mcp_nexus.main import create_app


def test_health_and_connector_endpoints(tmp_path: Path) -> None:
    with TestClient(create_app(database_path=tmp_path / "api.db", filesystem_root=tmp_path)) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/api/connectors").json()["connectors"] == [
            "filesystem",
            "webhook",
            "web_fetcher",
        ]
        providers = client.get("/api/providers").json()
        assert {item["provider"] for item in providers} == {"ollama", "openai", "anthropic"}


def test_event_stream_advertises_sse(tmp_path: Path) -> None:
    with (
        TestClient(create_app(database_path=tmp_path / "stream.db", filesystem_root=tmp_path)) as client,
        client.stream("GET", "/api/events/stream", headers={"Accept": "text/event-stream"}) as response,
    ):
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")


def test_template_render_endpoint(tmp_path: Path) -> None:
    with TestClient(create_app(database_path=tmp_path / "template.db", filesystem_root=tmp_path)) as client:
        saved = client.post("/api/templates", json={"name": "brief", "body": "Hi {{ name }}"}).json()
        assert saved["variables"] == ["name"]
        response = client.post("/api/templates/brief/render", json={"values": {"name": "Ada"}})
    assert response.status_code == 200
    assert response.json()["body"] == "Hi Ada"
