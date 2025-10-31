"""Configuration helpers for the ElevenLabs Azure MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


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
class Settings:
    """Aggregate application settings."""

    azure: AzureDevOpsSettings
    elevenlabs: ElevenLabsSettings


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

    return Settings(azure=azure_settings, elevenlabs=elevenlabs_settings)
