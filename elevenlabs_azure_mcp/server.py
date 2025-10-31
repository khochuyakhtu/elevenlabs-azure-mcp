"""MCP server bridging ElevenLabs and Azure DevOps stories."""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from typing import NoReturn

from mcp.server.fastmcp import FastMCP

from .azure import AzureDevOpsStoryCreator, AzureDevOpsError
from .config import SettingsError, load_settings
from .public_url import PublicURLConfig, PublicURLError, create_public_url

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


_INTERACTIVE_PROMPT = (
    'Enter commands like: create story with title "Story title" '
    'and description "Story details".'
)


def _run_interactive_cli() -> NoReturn:
    """Provide a text interface for creating stories from the terminal."""

    print("elevenlabs-azure-mcp interactive mode", flush=True)
    print(_INTERACTIVE_PROMPT, flush=True)
    print("Type 'quit' or 'exit' to leave.\n", flush=True)

    pattern = re.compile(
        r'^\s*create\s+story\s+with\s+title\s+"(?P<title>.+?)"\s+'
        r'and\s+description\s+"(?P<description>.+?)"\s*(?:[.!?])?\s*$'
    )

    while True:
        try:
            command = input("> ").strip()
        except EOFError:  # pragma: no cover - depends on user input
            print()
            break

        if not command:
            continue

        if command.lower() in {"quit", "exit"}:
            break

        match = pattern.match(command)
        if not match:
            print("Unrecognised command.", flush=True)
            print(_INTERACTIVE_PROMPT, flush=True)
            continue

        try:
            result = asyncio.run(
                create_story(
                    title=match.group("title"),
                    description=match.group("description"),
                )
            )
        except RuntimeError as exc:
            print(f"Error: {exc}", flush=True)
            continue

        print(result, flush=True)

    raise SystemExit(0)


def _run_jsonrpc_server(transport: str | None = None) -> None:
    """Run the JSON-RPC MCP server, optionally exposing it via a public URL."""

    public_url_config = PublicURLConfig.from_environment()

    if not public_url_config.enabled:
        app.run(transport=transport)
        return

    try:
        with create_public_url(
            host=app.settings.host,
            port=app.settings.port,
            authtoken=public_url_config.authtoken,
            proto=public_url_config.proto,
        ) as public_url:
            print(f"Public MCP server available at: {public_url}", flush=True)
            app.run(transport="sse")
    except PublicURLError as exc:
        raise RuntimeError(str(exc)) from exc


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry point
    """Entry point that selects between interactive and JSON-RPC modes."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices={"auto", "interactive", "jsonrpc"},
        default="auto",
        help=(
            "How to run the server. 'interactive' enables a text interface; "
            "'jsonrpc' forces the MCP transport. The default 'auto' chooses "
            "interactive when stdin is a TTY."
        ),
    )
    parser.add_argument(
        "--transport",
        choices={"stdio", "sse"},
        default=None,
        help="Override the MCP transport when running in JSON-RPC mode.",
    )
    args = parser.parse_args(argv)

    should_use_interactive = args.mode == "interactive" or (
        args.mode == "auto" and sys.stdin.isatty()
    )

    if should_use_interactive:
        _run_interactive_cli()

    _run_jsonrpc_server(transport=args.transport)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
