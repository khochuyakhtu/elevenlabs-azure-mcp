"""Utilities for exposing the MCP server over a public URL."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
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


def _default_ngrok_path() -> str | None:
    """Return a likely ngrok executable path for the current platform."""

    if os.name != "nt":
        return None

    candidates: list[str] = []

    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(os.path.join(program_files, "ngrok", "ngrok.exe"))

    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidates.append(os.path.join(program_files_x86, "ngrok", "ngrok.exe"))

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(
            os.path.join(local_app_data, "Microsoft", "WindowsApps", "ngrok.exe")
        )

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return None


def _pick_ngrok_path(configured_path: str | None) -> str | None:
    """Return the ngrok executable path, validating configured values."""

    def _is_executable(path: str) -> bool:
        if not os.path.exists(path):
            return False

        if os.name == "nt":
            return True

        return os.access(path, os.X_OK)

    if configured_path:
        expanded_path = os.path.expanduser(configured_path)

        if _is_executable(expanded_path):
            return expanded_path

        raise PublicURLError(
            f"Configured ngrok executable not found or not executable: {configured_path}"
        )

    default_path = _default_ngrok_path()

    if default_path and _is_executable(default_path):
        return default_path

    return None


@contextlib.contextmanager
def create_public_url(
    host: str,
    port: int,
    *,
    authtoken: str | None = None,
    proto: str = "http",
    ngrok_path: str | None = None,
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

    resolved_ngrok_path = _pick_ngrok_path(ngrok_path)

    if resolved_ngrok_path:
        default_conf.ngrok_path = resolved_ngrok_path

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


__all__ = ["PublicURLError", "create_public_url"]
