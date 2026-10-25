from pathlib import Path

import pytest

from mcp_nexus.services.database import Database
from mcp_nexus.templates.manager import TemplateManager


@pytest.mark.asyncio
async def test_template_manager_extracts_and_renders_variables(tmp_path: Path) -> None:
    database = Database(tmp_path / "templates.db")
    await database.connect()
    manager = TemplateManager(database)
    saved = await manager.save("greeting", "Hello {{ name }} from {{place}}.")

    assert saved["variables"] == ["name", "place"]
    assert await manager.render("greeting", {"name": "Ada", "place": "London"}) == (
        "Hello Ada from London."
    )
    with pytest.raises(ValueError):
        await manager.render("greeting", {"name": "Ada"})
    await database.close()
