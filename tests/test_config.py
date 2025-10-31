import pathlib
import os
import sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from elevenlabs_azure_mcp.config import SettingsError, load_settings


def test_load_settings_reports_all_missing_required_variables():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SettingsError) as exc_info:
            load_settings()

    message = str(exc_info.value)
    assert "AZURE_DEVOPS_ORGANIZATION" in message
    assert "AZURE_DEVOPS_PROJECT" in message
    assert "AZURE_DEVOPS_PAT" in message
    assert "Missing required environment variables" in message


def test_load_settings_reports_empty_required_variables():
    env = {
        "AZURE_DEVOPS_ORGANIZATION": "   ",
        "AZURE_DEVOPS_PROJECT": "MyProject",
        "AZURE_DEVOPS_PAT": "   ",
    }
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(SettingsError) as exc_info:
            load_settings()

    message = str(exc_info.value)
    assert "Environment variables must not be empty" in message
    assert "AZURE_DEVOPS_ORGANIZATION" in message
    assert "AZURE_DEVOPS_PAT" in message


def test_load_settings_returns_settings_when_required_variables_present():
    env = {
        "AZURE_DEVOPS_ORGANIZATION": "my-org",
        "AZURE_DEVOPS_PROJECT": "my-project",
        "AZURE_DEVOPS_PAT": "pat-123",
        "AZURE_DEVOPS_AREA_PATH": "area/path",
        "AZURE_DEVOPS_ITERATION_PATH": "iteration/path",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = load_settings()

    assert settings.azure.organization == "my-org"
    assert settings.azure.project == "my-project"
    assert settings.azure.personal_access_token == "pat-123"
    assert settings.azure.area_path == "area/path"
    assert settings.azure.iteration_path == "iteration/path"
    assert settings.azure.api_version == "7.0"
