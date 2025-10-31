"""Tests for the public URL helper utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

import elevenlabs_azure_mcp.public_url as public_url
from elevenlabs_azure_mcp.config import PublicURLConfig
from elevenlabs_azure_mcp.public_url import PublicURLError, create_public_url


def test_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should populate the public URL configuration."""

    monkeypatch.setenv("MCP_PUBLIC_URL", "true")
    monkeypatch.setenv("MCP_PUBLIC_URL_AUTHTOKEN", "token")
    monkeypatch.setenv("MCP_PUBLIC_URL_PROTO", "tcp")
    monkeypatch.setenv("MCP_PUBLIC_URL_NGROK_PATH", "~/bin/ngrok")

    config = PublicURLConfig.from_environment()

    assert config.enabled is True
    assert config.authtoken == "token"
    assert config.proto == "tcp"
    assert config.ngrok_path == "~/bin/ngrok"


def test_create_public_url_configures_ngrok(monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper should wire up the pyngrok configuration before connecting."""

    class DummyConfig:
        def __init__(self) -> None:
            self.auth_token: str | None = None
            self.ngrok_path: str | None = None

    dummy_config = DummyConfig()

    class DummyNgrok:
        def __init__(self) -> None:
            self.disconnected: list[str] = []
            self.killed = False

        def connect(self, *, addr: str, proto: str, bind_tls: bool):
            assert addr == "localhost:9999"
            assert proto == "http"
            assert bind_tls is True
            assert dummy_config.auth_token == "secret"
            assert dummy_config.ngrok_path == "C:/ngrok.exe"

            class Tunnel:
                public_url = "https://example.ngrok.app"

            return Tunnel()

        def disconnect(self, url: str) -> None:
            self.disconnected.append(url)

        def kill(self) -> None:
            self.killed = True

    dummy_ngrok = DummyNgrok()

    monkeypatch.setattr(
        "elevenlabs_azure_mcp.public_url._pyngrok_conf",
        type("Conf", (), {"get_default": lambda: dummy_config}),
        raising=False,
    )
    monkeypatch.setattr(
        "elevenlabs_azure_mcp.public_url._pyngrok_ngrok",
        dummy_ngrok,
        raising=False,
    )
    monkeypatch.setattr(
        "elevenlabs_azure_mcp.public_url._pick_ngrok_path",
        lambda configured_path: "C:/ngrok.exe",
    )

    with create_public_url(
        host="localhost",
        port=9999,
        authtoken="secret",
        proto="http",
        ngrok_path="C:/ngrok.exe",
    ) as url:
        assert url == "https://example.ngrok.app"

    assert dummy_ngrok.disconnected == ["https://example.ngrok.app"]
    assert dummy_ngrok.killed is True


def test_create_public_url_wraps_permission_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Permission problems when launching ngrok should raise a friendly error."""

    dummy_config = type("Config", (), {"auth_token": None, "ngrok_path": None})()

    monkeypatch.setattr(
        "elevenlabs_azure_mcp.public_url._pyngrok_conf",
        type("Conf", (), {"get_default": lambda: dummy_config}),
        raising=False,
    )

    class FailingNgrok:
        def connect(self, **_: object) -> None:
            raise PermissionError("access denied")

    monkeypatch.setattr(
        "elevenlabs_azure_mcp.public_url._pyngrok_ngrok",
        FailingNgrok(),
        raising=False,
    )

    with pytest.raises(PublicURLError) as excinfo:
        with create_public_url(host="127.0.0.1", port=1111):
            pass

    assert "Failed to create ngrok tunnel" in str(excinfo.value)


def test_pick_ngrok_path_validates_configured_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """User-provided paths should be returned when they exist."""

    ngrok_exe = tmp_path / "ngrok.exe"
    ngrok_exe.write_text("binary")

    monkeypatch.setattr(public_url.os, "name", "nt", raising=False)

    resolved = public_url._pick_ngrok_path(str(ngrok_exe))

    assert resolved == str(ngrok_exe)


def test_pick_ngrok_path_raises_for_missing_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """A helpful error should surface when a configured path is invalid."""

    monkeypatch.setattr(public_url.os, "name", "nt", raising=False)

    with pytest.raises(PublicURLError):
        public_url._pick_ngrok_path("C:/missing/ngrok.exe")


def test_default_ngrok_path_checks_windows_apps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The WindowsApps installation should be detected when present."""

    ngrok_exe = tmp_path / "Microsoft" / "WindowsApps" / "ngrok.exe"
    ngrok_exe.parent.mkdir(parents=True)
    ngrok_exe.write_text("binary")

    monkeypatch.setattr(public_url.os, "name", "nt", raising=False)
    monkeypatch.setenv("ProgramFiles", "")
    monkeypatch.setenv("ProgramFiles(x86)", "")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert public_url._default_ngrok_path() == str(ngrok_exe)
