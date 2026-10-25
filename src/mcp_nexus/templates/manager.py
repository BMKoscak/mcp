"""Parameterized MCP prompt template management."""

from __future__ import annotations

import re

from ..services.database import Database

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class TemplateManager:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def variables(body: str) -> list[str]:
        return list(dict.fromkeys(VARIABLE_PATTERN.findall(body)))

    async def save(self, name: str, body: str) -> dict[str, object]:
        variables = self.variables(body)
        await self.database.save_template(name, body, variables)
        return (await self.database.get_template(name)) or {}

    async def render(self, name: str, values: dict[str, str]) -> str:
        template = await self.database.get_template(name)
        if template is None:
            raise KeyError(f"Unknown template: {name}")
        missing = [variable for variable in template["variables"] if variable not in values]
        if missing:
            raise ValueError(f"Missing template variables: {', '.join(missing)}")
        return VARIABLE_PATTERN.sub(lambda match: values[match.group(1)], str(template["body"]))
