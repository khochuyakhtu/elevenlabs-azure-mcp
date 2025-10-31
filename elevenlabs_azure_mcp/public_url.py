"""Utilities for exposing the MCP server over a public URL."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass
import os

from pyngrok import conf, ngrok
from pyngrok.exception import PyngrokNgrokError


class PublicURLError(RuntimeError):
    """Raised when a public URL tunnel cannot be created."""


@dataclass(frozen=True)
class PublicURLConfig:
    """Configuration needed to create a public URL tunnel."""

    enabled: bool
    authtoken: str | None = None
    proto: str = "http"

    @classmethod
    def from_environment(cls) -> "PublicURLConfig":
        """Build configuration by inspecting environment variables."""

        value = os.environ.get("MCP_PUBLIC_URL", "").strip().lower()
        enabled = value in {"1", "true", "yes", "on"}
        authtoken = os.environ.get("MCP_PUBLIC_URL_AUTHTOKEN") or os.environ.get(
            "NGROK_AUTHTOKEN"
        )
        proto = os.environ.get("MCP_PUBLIC_URL_PROTO", "http")
        return cls(enabled=enabled, authtoken=authtoken, proto=proto)


@contextlib.contextmanager
def create_public_url(
    host: str,
    port: int,
    *,
    authtoken: str | None = None,
    proto: str = "http",
) -> Iterator[str]:
    """Create a public URL for the local MCP server.

    Args:
        host: Hostname where the MCP server is bound.
        port: Local port where the MCP server is listening.
        authtoken: Optional ngrok authtoken. If provided it will be used to
            authenticate the tunnel before creation.
        proto: Protocol to use when creating the tunnel. Defaults to ``"http"``.

    Yields:
        The public URL that forwards traffic to the MCP server.
    """

    if authtoken:
        conf.get_default().auth_token = authtoken

    try:
        tunnel = ngrok.connect(addr=f"{host}:{port}", proto=proto, bind_tls=True)
    except PyngrokNgrokError as exc:  # pragma: no cover - requires network access
        raise PublicURLError("Failed to create ngrok tunnel") from exc

    try:
        yield tunnel.public_url
    finally:
        try:
            ngrok.disconnect(tunnel.public_url)
        finally:
            ngrok.kill()


__all__ = ["PublicURLConfig", "PublicURLError", "create_public_url"]
