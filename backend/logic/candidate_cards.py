"""
candidate_cards.py — Candidate Profile Parser.

Provides utilities to normalise raw candidate data (from the Google Civic
Information API or any external source) into simplified, voter-friendly
"Candidate Cards."

A Candidate Card contains:
  - Name & Party (with symbol)
  - Education
  - Criminal Record summary
  - Declared Assets (in ₹ Lakh / Crore)
  - Key Promises (top 3–5)

The parser is intentionally decoupled from the JourneyManager so it can
be reused by any API endpoint or service.
"""

from __future__ import annotations

from typing import Any

from backend.utils.jargon_killer import translate


def parse_candidate(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a raw candidate profile dict into a Candidate Card.

    Parameters
    ----------
    raw : dict
        Raw profile, expected keys:
          name, party, symbol, education, criminal_cases,
          assets_inr, promises, age, gender.

    Returns
    -------
    dict
        Simplified Candidate Card.
    """
    criminal = raw.get("criminal_cases", 0)
    criminal_label = (
        "✅ No criminal cases"
        if criminal == 0
        else f"⚠️ {criminal} pending criminal case(s)"
    )

    assets = raw.get("assets_inr", 0)
    assets_label = _format_inr(assets)

    promises = raw.get("promises", [])
    if len(promises) > 5:
        promises = promises[:5]

    return {
        "name": raw.get("name", "Unknown Candidate"),
        "party": translate(raw.get("party", "Unknown Party")),
        "symbol": raw.get("symbol", ""),
        "age": raw.get("age"),
        "gender": raw.get("gender"),
        "education": raw.get("education", "Not disclosed"),
        "criminal_record": criminal_label,
        "declared_assets": assets_label,
        "key_promises": [translate(p) for p in promises],
    }


def parse_candidates(raw_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Batch-parse a list of raw candidate profiles.

    Parameters
    ----------
    raw_list : list[dict]
        List of raw candidate dicts.

    Returns
    -------
    list[dict]
        List of Candidate Cards.
    """
    return [parse_candidate(c) for c in raw_list]


def compare_candidates(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate a quick comparison summary across candidate cards.

    Useful for the frontend to render a side-by-side comparison table.

    Parameters
    ----------
    cards : list[dict]
        List of parsed Candidate Cards.

    Returns
    -------
    dict
        Comparison payload with categories as keys.
    """
    return {
        "candidates": [c["name"] for c in cards],
        "parties": [c["party"] for c in cards],
        "education": [c["education"] for c in cards],
        "criminal_records": [c["criminal_record"] for c in cards],
        "assets": [c["declared_assets"] for c in cards],
        "promise_count": [len(c["key_promises"]) for c in cards],
    }


def _format_inr(amount: int | float) -> str:
    """
    Format an INR amount in Indian notation (Lakh / Crore).

    Parameters
    ----------
    amount : int | float
        Amount in INR.

    Returns
    -------
    str
        Formatted string, e.g. "₹12.0 Lakh" or "₹1.5 Crore".
    """
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.1f} Crore"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.1f} Lakh"
    return f"₹{amount:,.0f}"
