"""HTTP client for Hamburg's public Bebauungsplaene OGC API.

The live endpoint is configurable so the same client can be exercised against
fixtures/mocks when the public service is unavailable. No credentials are
required by the public source.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_BASE_URL = "https://api.hamburg.de/datasets/v1/bplaene/"


class HamburgPlanningError(RuntimeError):
    """Raised when the Hamburg planning source cannot be consumed safely."""


class HamburgPlanningClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.mount("http://", HTTPAdapter(max_retries=retry))
        session.headers.update({"Accept": "application/geo+json, application/json"})
        return session

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HamburgPlanningError(f"Hamburg planning request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise HamburgPlanningError("Hamburg planning response was not valid JSON") from exc

        if not isinstance(payload, dict):
            raise HamburgPlanningError("Hamburg planning response must be a JSON object")
        return payload

    def list_collections(self) -> list[dict[str, Any]]:
        payload = self.get_json(urljoin(self.base_url, "collections"))
        collections = payload.get("collections", [])
        if not isinstance(collections, list):
            raise HamburgPlanningError("OGC collections response has an invalid 'collections' field")
        return [item for item in collections if isinstance(item, dict)]

    def iter_features(
        self,
        collection_id: str,
        *,
        limit: int = 100,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        if not collection_id:
            raise ValueError("collection_id is required")
        if limit < 1:
            raise ValueError("limit must be positive")

        next_url = urljoin(
            self.base_url,
            f"collections/{collection_id}/items",
        )
        params: dict[str, Any] | None = {"limit": limit}
        page_count = 0
        visited: set[str] = set()

        while next_url:
            if next_url in visited:
                raise HamburgPlanningError("Pagination loop detected in Hamburg OGC response")
            visited.add(next_url)

            payload = self.get_json(next_url, params=params)
            params = None
            features = payload.get("features", [])
            if not isinstance(features, list):
                raise HamburgPlanningError("OGC items response has an invalid 'features' field")

            for feature in features:
                if isinstance(feature, dict):
                    yield feature

            page_count += 1
            if max_pages is not None and page_count >= max_pages:
                break

            next_url = self._next_link(payload)

    @staticmethod
    def _next_link(payload: dict[str, Any]) -> str | None:
        links = payload.get("links", [])
        if not isinstance(links, list):
            return None
        for link in links:
            if isinstance(link, dict) and link.get("rel") == "next":
                href = link.get("href")
                if isinstance(href, str) and href:
                    return href
        return None
