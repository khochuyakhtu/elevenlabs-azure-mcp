"""Configuration helpers for the ElevenLabs Azure MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AzureDevOpsSettings:
    """Settings required to connect to Azure DevOps."""

    organization: str
    project: str
    personal_access_token: str
    area_path: str | None = None
    iteration_path: str | None = None
    api_version: str = "7.0"


@dataclass(frozen=True)
class ElevenLabsSettings:
    """Settings used when authenticating against ElevenLabs."""

    api_key: str | None = None


@dataclass(frozen=True)
class PublicURLConfig:
    """Configuration needed to expose the MCP server publicly."""

    enabled: bool
    authtoken: str | None = None
    proto: str = "http"
    ngrok_path: str | None = None

    @classmethod
    def from_environment(cls) -> "PublicURLConfig":
        """Build configuration by inspecting environment variables."""

        enabled = _parse_bool(os.environ.get("MCP_PUBLIC_URL"))
        authtoken = os.environ.get("MCP_PUBLIC_URL_AUTHTOKEN") or os.environ.get(
            "NGROK_AUTHTOKEN"
        )
        ngrok_path_env = os.environ.get("MCP_PUBLIC_URL_NGROK_PATH") or os.environ.get(
            "NGROK_PATH"
        )
        proto = os.environ.get("MCP_PUBLIC_URL_PROTO", "http")
        return cls(
            enabled=enabled,
            authtoken=authtoken,
            proto=proto,
            ngrok_path=(ngrok_path_env or None),
        )


@dataclass(frozen=True)
class Settings:
    """Aggregate application settings."""

    azure: AzureDevOpsSettings
    elevenlabs: ElevenLabsSettings
    public_url: PublicURLConfig


class SettingsError(RuntimeError):
    """Raised when configuration is invalid or incomplete."""


def load_settings() -> Settings:
    """Load settings from environment variables."""

    def _optional_env(name: str) -> str | None:
        raw_value = os.environ.get(name)
        if raw_value is None:
            return None

        value = raw_value.strip()
        return value or None

    def _env_with_default(name: str, default: str) -> str:
        raw_value = os.environ.get(name)
        if raw_value is None:
            return default

        value = raw_value.strip()
        return value or default

    azure_settings = AzureDevOpsSettings(
        organization="test",
        project="test",
        personal_access_token="test",
        area_path=_optional_env("AZURE_DEVOPS_AREA_PATH"),
        iteration_path=_optional_env("AZURE_DEVOPS_ITERATION_PATH"),
        api_version=_env_with_default("AZURE_DEVOPS_API_VERSION", "7.0"),
    )

    elevenlabs_settings = ElevenLabsSettings(
        api_key=os.environ.get("ELEVENLABS_API_KEY"),
    )

    public_url_settings = PublicURLConfig.from_environment()

    return Settings(
        azure=azure_settings,
        elevenlabs=elevenlabs_settings,
        public_url=public_url_settings,
    )
