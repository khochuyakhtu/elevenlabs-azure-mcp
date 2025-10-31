import pathlib
import os
import sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from elevenlabs_azure_mcp.config import load_settings


def test_load_settings_returns_hardcoded_azure_settings_without_env():
    with patch.dict(os.environ, {}, clear=True):
        settings = load_settings()

    assert settings.azure.organization == "test"
    assert settings.azure.project == "test"
    assert settings.azure.personal_access_token == "test"
    assert settings.azure.area_path is None
    assert settings.azure.iteration_path is None
    assert settings.azure.api_version == "7.0"
    assert settings.public_url.enabled is False
    assert settings.public_url.authtoken is None
    assert settings.public_url.proto == "http"
    assert settings.public_url.ngrok_path is None


def test_load_settings_normalizes_optional_environment_variables():
    env = {
        "AZURE_DEVOPS_AREA_PATH": "   ",
        "AZURE_DEVOPS_API_VERSION": "  7.1-preview  ",
    }

    with patch.dict(os.environ, env, clear=True):
        settings = load_settings()

    assert settings.azure.organization == "test"
    assert settings.azure.project == "test"
    assert settings.azure.personal_access_token == "test"
    assert settings.azure.area_path is None
    assert settings.azure.iteration_path is None
    assert settings.azure.api_version == "7.1-preview"
