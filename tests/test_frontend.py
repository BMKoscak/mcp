from pathlib import Path

from fastapi.testclient import TestClient

from mcp_nexus.main import create_app


def test_frontend_is_served(tmp_path: Path) -> None:
    with TestClient(create_app(database_path=tmp_path / "ui.db", filesystem_root=tmp_path)) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "MCP Nexus" in response.text
