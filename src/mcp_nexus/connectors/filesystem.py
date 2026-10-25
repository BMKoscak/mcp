"""Sandboxed local filesystem MCP connector."""

from __future__ import annotations

from pathlib import Path

from ..services.registry import Connector


def filesystem_connector(root: str | Path) -> Connector:
    base = Path(root).expanduser().resolve()

    def resolve(relative_path: str) -> Path:
        candidate = (base / relative_path).resolve()
        if candidate != base and base not in candidate.parents:
            raise ValueError("Path escapes the configured filesystem root")
        return candidate

    def register(server: object) -> None:
        @server.tool(name="read_file", description="Read UTF-8 text from a sandboxed local file.")
        async def read_file(path: str) -> str:
            target = resolve(path)
            if not target.is_file():
                raise FileNotFoundError(path)
            return target.read_text(encoding="utf-8")

        @server.tool(name="write_file", description="Write UTF-8 text to a sandboxed local file.")
        async def write_file(path: str, content: str) -> str:
            target = resolve(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} characters to {path}"

        @server.resource("file:///{path}")
        async def file_resource(path: str) -> str:
            return await read_file(path)

    return Connector(name="filesystem", register=register)

