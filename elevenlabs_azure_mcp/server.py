"""MCP server bridging ElevenLabs and Azure DevOps stories."""

from __future__ import annotations

import asyncio
from mcp.server.fastmcp import FastMCP

from .azure import AzureDevOpsStoryCreator, AzureDevOpsError
from .config import SettingsError, load_settings

app = FastMCP("elevenlabs-azure-mcp")


@app.tool(
    name="create_story",
    title="Create Story",
    description=(
        "Create an Azure DevOps user story. "
        "Provide a title and description gathered during the ElevenLabs call."
    ),
)
async def create_story(title: str, description: str) -> str:
    """Create a user story in Azure DevOps."""

    try:
        settings = load_settings()
    except SettingsError as exc:
        raise RuntimeError(str(exc)) from exc

    creator = AzureDevOpsStoryCreator(
        organization=settings.azure.organization,
        project=settings.azure.project,
        personal_access_token=settings.azure.personal_access_token,
        api_version=settings.azure.api_version,
        area_path=settings.azure.area_path,
        iteration_path=settings.azure.iteration_path,
    )

    try:
        work_item = await asyncio.to_thread(
            creator.create_story,
            title,
            description,
        )
    except AzureDevOpsError as exc:
        raise RuntimeError(str(exc)) from exc

    web_url = work_item.web_url or work_item.url
    return (
        "Created Azure DevOps story "
        f"#{work_item.work_item_id} ({work_item.title}). View it at: {web_url}"
    )


__all__ = ["app", "create_story"]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    app.run()
