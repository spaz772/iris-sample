"""Transparent, configurable domain classification for IRIS-SIG-15."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClassificationResult:
    signal_types: tuple[str, ...]
    matched_terms: tuple[str, ...]
    status: str


DEFAULT_RULES: dict[str, tuple[str, ...]] = {
    "port_logistics": (
        "hafen",
        "logistik",
        "terminal",
        "umschlag",
        "gueterverkehr",
        "güterverkehr",
        "lager",
        "spedition",
    ),
    "grid_heavy_industry": (
        "industriegebiet",
        "industrie",
        "kraftwerk",
        "umspannwerk",
        "energie",
        "rechenzentrum",
        "grossverbraucher",
        "großverbraucher",
    ),
    "commercial_zone": (
        "gewerbegebiet",
        "gewerbe",
        "sondergebiet",
        "mischgebiet",
        "geschaeft",
        "geschäft",
    ),
}


def classify_signal(
    properties: dict[str, Any],
    *,
    rules: dict[str, tuple[str, ...]] | None = None,
) -> ClassificationResult:
    """Classify using visible source text only; never invent a category."""
    active_rules = rules or DEFAULT_RULES
    searchable = " ".join(
        str(value).lower()
        for value in properties.values()
        if isinstance(value, (str, int, float))
    )

    signal_types: list[str] = []
    matched_terms: list[str] = []
    for signal_type, terms in active_rules.items():
        hits = [term for term in terms if term.lower() in searchable]
        if hits:
            signal_types.append(signal_type)
            matched_terms.extend(hits)

    if not signal_types:
        return ClassificationResult((), (), "unclassified")

    return ClassificationResult(
        tuple(signal_types),
        tuple(dict.fromkeys(matched_terms)),
        "classified",
    )
