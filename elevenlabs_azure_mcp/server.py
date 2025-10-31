"""MCP server bridging ElevenLabs and Azure DevOps stories."""

from __future__ import annotations

import asyncio
import os
import re
import sys
from mcp.server.fastmcp import FastMCP

from .azure import AzureDevOpsStoryCreator, AzureDevOpsError
from .config import SettingsError, load_settings

app = FastMCP("elevenlabs-azure-mcp")

_CLI_COMMAND_RE = re.compile(
    r'^create\s+story\s+with\s+title\s+"(?P<title>.+?)"\s+and\s+description\s+"(?P<description>.+?)"$',
    re.IGNORECASE,
)


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


async def _handle_cli_command(line: str) -> None:
    """Parse and execute a CLI command."""

    if not line:
        return

    if line.lower() in {"exit", "quit"}:
        raise SystemExit

    match = _CLI_COMMAND_RE.match(line)
    if not match:
        print(
            "Unrecognized command. Expected:"
            '\n  create story with title "<title>" and description "<description>"'
        )
        return

    try:
        result = await create_story(**match.groupdict())
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    print(result)


def _run_cli() -> None:
    """Run a simple interactive CLI for manual usage."""

    print(
        "Interactive mode detected. Enter commands in the form:\n"
        '  create story with title "<title>" and description "<description>"\n'
        "Type 'exit' or press Ctrl+D to quit."
    )

    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print()
            break

        try:
            asyncio.run(_handle_cli_command(line))
        except SystemExit:
            break


__all__ = ["app", "create_story"]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    if sys.stdin.isatty() or os.getenv("ELEVENLABS_AZURE_MCP_FORCE_CLI") == "1":
        _run_cli()
    else:
        app.run()
