from pathlib import Path

import pytest

from mcp_nexus.services.database import Database


@pytest.mark.asyncio
async def test_database_persists_settings_and_events(tmp_path: Path) -> None:
    database = Database(tmp_path / "nexus.db")
    await database.connect()
    await database.set_setting("active_model", {"provider": "ollama", "model": "llama3"})
    event_id = await database.record_event("request", {"jsonrpc": "2.0"}, method="tools/list")

    assert await database.get_setting("active_model") == {
        "provider": "ollama",
        "model": "llama3",
    }
    assert (await database.list_events())[0]["id"] == event_id
    await database.close()

