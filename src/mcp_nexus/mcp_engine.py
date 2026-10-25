"""FastMCP server assembly and connector lifecycle."""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .connectors.filesystem import filesystem_connector
from .connectors.web_fetcher import web_fetcher_connector
from .connectors.webhook import webhook_connector
from .services.registry import ConnectorRegistry


class MCPEngine:
    """Build and expose the local MCP server with standard connectors."""

    def __init__(
        self,
        *,
        filesystem_root: str | Path = ".",
        require_outbound_confirmation: bool = True,
    ) -> None:
        self.server = FastMCP("MCP Nexus")
        self.registry = ConnectorRegistry()
        self.registry.add(filesystem_connector(filesystem_root))
        self.registry.add(
            webhook_connector(require_confirmation=require_outbound_confirmation)
        )
        self.registry.add(web_fetcher_connector())
        self.registry.register_all(self.server)

    def run(self, **kwargs: object) -> None:
        """Run the MCP server using FastMCP's configured transport."""
        self.server.run(**kwargs)

