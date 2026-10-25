"""Connector registration primitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Connector:
    """A named collection of MCP tools and resources."""

    name: str
    register: Callable[[Any], None]


class ConnectorRegistry:
    """Deterministic registry used by the MCP engine."""

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def add(self, connector: Connector) -> None:
        if connector.name in self._connectors:
            raise ValueError(f"Connector already registered: {connector.name}")
        self._connectors[connector.name] = connector

    def get(self, name: str) -> Connector:
        try:
            return self._connectors[name]
        except KeyError as exc:
            raise KeyError(f"Unknown connector: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(self._connectors)

    def register_all(self, server: Any) -> None:
        for connector in self._connectors.values():
            connector.register(server)

