from typing import Any

import pytest
import requests

from app.integrations.hamburg_planning.client import HamburgPlanningClient, HamburgPlanningError


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = iter(responses)

    def get(self, url: str, params: dict[str, Any] | None = None, timeout: float = 30.0) -> FakeResponse:
        return next(self.responses)


def test_iter_features_follows_next_link() -> None:
    session = FakeSession([
        FakeResponse({
            "features": [{"id": "1"}],
            "links": [{"rel": "next", "href": "https://example.test/page-2"}],
        }),
        FakeResponse({"features": [{"id": "2"}], "links": []}),
    ])
    client = HamburgPlanningClient(base_url="https://example.test/", session=session)  # type: ignore[arg-type]

    assert [feature["id"] for feature in client.iter_features("plans")] == ["1", "2"]


def test_empty_response_is_valid() -> None:
    session = FakeSession([FakeResponse({"features": [], "links": []})])
    client = HamburgPlanningClient(base_url="https://example.test/", session=session)  # type: ignore[arg-type]

    assert list(client.iter_features("plans")) == []


def test_malformed_json_is_reported() -> None:
    session = FakeSession([FakeResponse(ValueError("bad json"))])
    client = HamburgPlanningClient(base_url="https://example.test/", session=session)  # type: ignore[arg-type]

    with pytest.raises(HamburgPlanningError, match="not valid JSON"):
        list(client.iter_features("plans"))


def test_http_failure_is_reported() -> None:
    session = FakeSession([FakeResponse({}, status_code=503)])
    client = HamburgPlanningClient(base_url="https://example.test/", session=session)  # type: ignore[arg-type]

    with pytest.raises(HamburgPlanningError, match="request failed"):
        list(client.iter_features("plans"))
