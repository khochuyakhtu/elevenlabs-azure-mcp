# elevenlabs-azure-mcp

This repository hosts an [MCP](https://modelcontextprotocol.io) server that allows
an ElevenLabs voice agent to create Azure DevOps stories on behalf of a caller.
When a customer requests "Create story" and provides a title and description,
the tool creates a corresponding **User Story** work item in Azure DevOps.

## Features

- Minimal MCP server implemented with `mcp.server.fastmcp`
- Azure DevOps integration using the REST Work Item API
- Environment-driven configuration for sensitive credentials

## Configuration

Set the following environment variables before launching the server:

| Variable | Description |
| --- | --- |
| `AZURE_DEVOPS_ORGANIZATION` | Azure DevOps organization name |
| `AZURE_DEVOPS_PROJECT` | Azure DevOps project name |
| `AZURE_DEVOPS_PAT` | Personal Access Token with `Work Items (Read & Write)` scope |
| `AZURE_DEVOPS_AREA_PATH` | Optional area path to assign to new stories |
| `AZURE_DEVOPS_ITERATION_PATH` | Optional iteration path to assign to new stories |
| `AZURE_DEVOPS_API_VERSION` | Optional API version (defaults to `7.0`) |
| `ELEVENLABS_API_KEY` | Optional ElevenLabs API key (not currently required) |

## Running the server

Install dependencies and launch the MCP server:

```bash
pip install -e .
python -m elevenlabs_azure_mcp.server
```

When executed with an MCP-compatible client (such as an ElevenLabs voice agent)
the process expects JSON-RPC messages on stdin/stdout. If you invoke the module
directly from a terminal the server detects interactive mode and provides a
simple CLI. Enter commands using the following format:

```
create story with title "<title>" and description "<description>"
```

Type `exit` (or press <kbd>Ctrl</kbd> + <kbd>D</kbd>) to leave the CLI. The tool
returns a confirmation message containing the Azure DevOps work item ID and the
web URL to the newly created story. Set the environment variable
`ELEVENLABS_AZURE_MCP_FORCE_CLI=1` to force the CLI mode when running in an
environment where stdin is not detected as a TTY (useful for automated tests).
