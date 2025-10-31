"""Azure DevOps integration utilities."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib import request, error


@dataclass
class AzureWorkItem:
    """Represents a created Azure DevOps work item."""

    work_item_id: int
    url: str
    web_url: str | None
    title: str


class AzureDevOpsError(RuntimeError):
    """Raised when Azure DevOps returns an error response."""


class AzureDevOpsStoryCreator:
    """Client for creating stories in Azure DevOps."""

    def __init__(
        self,
        *,
        organization: str,
        project: str,
        personal_access_token: str,
        api_version: str = "7.0",
        area_path: str | None = None,
        iteration_path: str | None = None,
        base_url: str = "https://dev.azure.com",
    ) -> None:
        self._organization = organization
        self._project = project
        self._personal_access_token = personal_access_token
        self._api_version = api_version
        self._area_path = area_path
        self._iteration_path = iteration_path
        self._base_url = base_url.rstrip("/")

    def create_story(self, title: str, description: str) -> AzureWorkItem:
        """Create a new Azure DevOps user story."""

        if not title.strip():
            raise ValueError("Story title must not be empty.")

        url = (
            f"{self._base_url}/{self._organization}/{self._project}/_apis/wit/workitems/"
            f"$User%20Story?api-version={self._api_version}"
        )

        payload = self._build_payload(title=title, description=description)
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json-patch+json")
        req.add_header("Accept", "application/json")
        req.add_header("Authorization", f"Basic {self._encode_pat()}")

        try:
            with request.urlopen(req) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:  # pragma: no cover - network errors hard to test
            details = exc.read().decode("utf-8", errors="ignore")
            raise AzureDevOpsError(
                f"Azure DevOps API request failed with status {exc.code}: {details or exc.reason}"
            ) from exc

        payload = json.loads(body)
        return AzureWorkItem(
            work_item_id=int(payload["id"]),
            url=payload.get("url", ""),
            web_url=(payload.get("_links", {}).get("html", {}) or {}).get("href"),
            title=payload.get("fields", {}).get("System.Title", title),
        )

    def _encode_pat(self) -> str:
        token = f":{self._personal_access_token}".encode("utf-8")
        return base64.b64encode(token).decode("ascii")

    def _build_payload(self, *, title: str, description: str) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": _format_description(description),
            },
        ]

        if self._area_path:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.AreaPath",
                    "value": self._area_path,
                }
            )

        if self._iteration_path:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.IterationPath",
                    "value": self._iteration_path,
                }
            )

        return payload


def _format_description(description: str) -> str:
    if not description:
        return ""

    # Azure DevOps expects HTML in the description field. For simplicity we escape
    # basic characters and translate newlines to <br/> tags.
    escaped = (
        description.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return escaped.replace("\n", "<br />\n")
