"""SANI Tool Registry."""

from typing import Any, Callable
from pydantic import BaseModel, ConfigDict
from sani.models import ActionRiskLevel


class ToolDefinition(BaseModel):
    """Metadata and execution function for a registered SANI tool."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    risk_level: ActionRiskLevel
    func: Callable[..., Any]



class ToolRegistry:
    """Registry for discovering, retrieving, and inspecting available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, risk_level: ActionRiskLevel, func: Callable[..., Any]) -> None:
        """Register a new tool."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            risk_level=risk_level,
            func=func,
        )

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tools."""
        return list(self._tools.values())
