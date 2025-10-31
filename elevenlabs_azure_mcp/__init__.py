"""Azure-integrated MCP server for ElevenLabs."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - imported only for type checkers
    from .server import app as _app

__all__ = ["app"]


def __getattr__(name: str) -> Any:
    if name == "app":
        module = import_module("elevenlabs_azure_mcp.server")
        return module.app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
