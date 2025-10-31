"""Tests for the public URL helper utilities."""

from __future__ import annotations

import pytest

from elevenlabs_azure_mcp.public_url import (
    PublicURLConfig,
    PublicURLError,
    create_public_url,
)


def test_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should populate the public URL configuration."""

    monkeypatch.setenv("MCP_PUBLIC_URL", "true")
    monkeypatch.setenv("MCP_PUBLIC_URL_AUTHTOKEN", "token")
    monkeypatch.setenv("MCP_PUBLIC_URL_PROTO", "tcp")

    config = PublicURLConfig.from_environment()

    assert config.enabled is True
    assert config.authtoken == "token"
    assert config.proto == "tcp"


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
        "elevenlabs_azure_mcp.public_url._default_ngrok_path",
        lambda: "C:/ngrok.exe",
    )

    with create_public_url(
        host="localhost",
        port=9999,
        authtoken="secret",
        proto="http",
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
