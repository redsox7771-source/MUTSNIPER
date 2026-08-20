from __future__ import annotations

import json
import logging
from string import Template

import httpx

from ..config import Settings
from .base import EAAuthError, EAClient, EARateLimitError, EAServerError, Listing, ListingFilter

logger = logging.getLogger("mutsniper.ea_client.real")


class RealEAClient(EAClient):
    """Talks to the real EA auction search endpoint. URL, headers, token,
    and request template all come from .env - nothing here is guessed or
    hardcoded.

    The one piece that can't come from .env is the response field mapping
    in _parse_response: EA's JSON shape isn't known ahead of time. Send a
    sample response from the real endpoint and that method gets filled in.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.ea_endpoint_url:
            raise ValueError("MUTSNIPER_EA_ENDPOINT_URL is not set")

        self._url = settings.ea_endpoint_url
        self._method = settings.ea_http_method.upper()
        self._headers: dict[str, str] = json.loads(settings.ea_headers_json)
        if settings.ea_token:
            self._headers.setdefault("Authorization", settings.ea_token)
        self._template = settings.ea_request_template_json
        self._client = httpx.AsyncClient(timeout=15)

    async def search_listings(self, filters: ListingFilter) -> list[Listing]:
        payload = self._render_template(filters)

        if self._method == "GET":
            response = await self._client.get(self._url, headers=self._headers, params=payload)
        else:
            response = await self._client.post(self._url, headers=self._headers, json=payload)

        if response.status_code == 401:
            raise EAAuthError("401 from EA auction endpoint")
        if response.status_code == 429:
            raise EARateLimitError("429 from EA auction endpoint")
        if response.status_code >= 500:
            raise EAServerError(f"{response.status_code} from EA auction endpoint")
        response.raise_for_status()

        return self._parse_response(response.json())

    def _render_template(self, filters: ListingFilter) -> dict:
        # string.Template's $identifier syntax is used (not str.format's
        # {}) so literal JSON braces in the template don't need escaping.
        rendered = Template(self._template).safe_substitute(
            min_ovr=filters.min_ovr if filters.min_ovr is not None else "",
            max_ovr=filters.max_ovr if filters.max_ovr is not None else "",
            program=filters.program or "",
            position=filters.position or "",
        )
        return json.loads(rendered)

    def _parse_response(self, data: dict) -> list[Listing]:
        raise NotImplementedError(
            "RealEAClient._parse_response needs EA's actual response shape "
            "to map fields into Listing objects - see the class docstring."
        )

    async def aclose(self) -> None:
        await self._client.aclose()
