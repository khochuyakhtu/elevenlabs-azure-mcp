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


_REQUIRED_ENVIRONMENT = {
    "AZURE_DEVOPS_ORGANIZATION": "Azure DevOps organization name",
    "AZURE_DEVOPS_PROJECT": "Azure DevOps project name",
    "AZURE_DEVOPS_PAT": "Azure DevOps Personal Access Token",
}


def _get_required_env(name: str) -> str:
    try:
        value = os.environ[name]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise SettingsError(
            f"Missing required environment variable: {name}."
        ) from exc

    if not value.strip():
        raise SettingsError(
            f"Environment variable {name} must not be empty."
        )

    return value


def load_settings() -> Settings:
    """Load settings from environment variables."""

    required = {name: _get_required_env(name) for name in _REQUIRED_ENVIRONMENT}

    azure_settings = AzureDevOpsSettings(
        organization=required["AZURE_DEVOPS_ORGANIZATION"],
        project=required["AZURE_DEVOPS_PROJECT"],
        personal_access_token=required["AZURE_DEVOPS_PAT"],
        area_path=os.environ.get("AZURE_DEVOPS_AREA_PATH"),
        iteration_path=os.environ.get("AZURE_DEVOPS_ITERATION_PATH"),
        api_version=os.environ.get("AZURE_DEVOPS_API_VERSION", "7.0"),
    )

    elevenlabs_settings = ElevenLabsSettings(
        api_key=os.environ.get("ELEVENLABS_API_KEY"),
    )

    return Settings(azure=azure_settings, elevenlabs=elevenlabs_settings)
