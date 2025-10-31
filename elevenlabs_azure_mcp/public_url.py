"""Utilities for exposing the MCP server over a public URL."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass
import os

try:  # pyngrok is an optional dependency at runtime
    from pyngrok import conf as _pyngrok_conf, ngrok as _pyngrok_ngrok
    from pyngrok.exception import PyngrokNgrokError
except ImportError:  # pragma: no cover - exercised when dependency missing
    _pyngrok_conf = None
    _pyngrok_ngrok = None
    PyngrokNgrokError = RuntimeError


def _require_pyngrok() -> tuple[object, object]:
    """Return pyngrok modules or raise a clear error if unavailable."""

    if _pyngrok_conf is None or _pyngrok_ngrok is None:
        raise PublicURLError(
            "pyngrok is required to create public URLs. Install the 'pyngrok' "
            "package or disable public URL support by unsetting MCP_PUBLIC_URL."
        )

    return _pyngrok_conf, _pyngrok_ngrok


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
        return cls(
            enabled=enabled,
            authtoken=authtoken,
            proto=proto,
        )


def _default_ngrok_path() -> str | None:
    """Return the built-in ngrok executable path for the current platform."""

    if os.name == "nt":
        # Use the standard installation path for the Windows ngrok client.
        return r"C:\\Program Files\\ngrok\\ngrok.exe"

    return None


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

    conf, ngrok = _require_pyngrok()

    default_conf = conf.get_default()

    if authtoken:
        default_conf.auth_token = authtoken

    ngrok_path = _default_ngrok_path()

    if ngrok_path:
        default_conf.ngrok_path = ngrok_path

    try:
        tunnel = ngrok.connect(addr=f"{host}:{port}", proto=proto, bind_tls=True)
    except (PyngrokNgrokError, OSError) as exc:  # pragma: no cover - requires network access
        raise PublicURLError("Failed to create ngrok tunnel") from exc

    try:
        yield tunnel.public_url
    finally:
        try:
            ngrok.disconnect(tunnel.public_url)
        finally:
            ngrok.kill()


__all__ = ["PublicURLConfig", "PublicURLError", "create_public_url"]
