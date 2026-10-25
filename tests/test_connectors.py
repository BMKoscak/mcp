from pathlib import Path

import pytest

from mcp_nexus.connectors.filesystem import filesystem_connector
from mcp_nexus.services.registry import ConnectorRegistry


class FakeServer:
    def __init__(self) -> None:
        self.tools = {}
        self.resources = {}

    def tool(self, *, name: str, description: str):
        def decorator(function):
            self.tools[name] = function
            return function

        return decorator

    def resource(self, pattern: str):
        def decorator(function):
            self.resources[pattern] = function
            return function

        return decorator


@pytest.mark.asyncio
async def test_filesystem_connector_is_sandboxed(tmp_path: Path) -> None:
    server = FakeServer()
    filesystem_connector(tmp_path).register(server)
    await server.tools["write_file"]("nested/example.txt", "hello")
    assert await server.tools["read_file"]("nested/example.txt") == "hello"

    with pytest.raises(ValueError):
        await server.tools["read_file"]("../outside.txt")


def test_registry_rejects_duplicate_names() -> None:
    registry = ConnectorRegistry()
    connector = filesystem_connector(".")
    registry.add(connector)
    with pytest.raises(ValueError):
        registry.add(connector)
