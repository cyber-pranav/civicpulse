"""
jargon_killer.py — The "Jargon-Killer" NLP Translation Layer.

Automatically intercepts and replaces high-friction government / election
terminology with plain-language equivalents in all assistant responses.

Design Notes
------------
* The dictionary is ordered longest-phrase-first so that multi-word terms
  (e.g., "Nomination filing") are replaced before their sub-phrases.
* Matching is case-insensitive; the replacement preserves the original
  casing style (Title Case if the match was Title Case, etc.).
* The module exposes a single public function ``translate()`` that the
  response pipeline calls before returning any text to the user.
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Core Jargon Dictionary
# ---------------------------------------------------------------------------
# Format: { government_term: plain_language_replacement }
# Keep alphabetical within each group for maintainability.

_JARGON_MAP_RAW: dict[str, str] = {
    # --- Electoral Structure ---
    "constituency": "your voting area",
    "parliamentary constituency": "your Lok Sabha voting area",
    "assembly constituency": "your Vidhan Sabha voting area",
    "delimitation": "redrawing of voting area boundaries",
    "reservation of constituencies": "seats reserved for SC/ST communities",

    # --- Voter Registration ---
    "electoral roll": "the official voter list",
    "supplementary electoral roll": "the updated voter list",
    "EPIC number": "Voter ID number",
    "EPIC": "Voter ID card",
    "electors photo identity card": "Voter ID card",
    "Form 6": "new voter registration form",
    "Form 6A": "overseas voter registration form",
    "Form 7": "objection form for removing a name from the voter list",
    "Form 8": "correction form for voter details",
    "Form 8A": "transposition form for shifting within the same voting area",
    "qualifying date": "the cutoff date to be old enough to vote",

    # --- Candidates & Nominations ---
    "nomination filing": "candidate application",
    "nomination": "candidate application",
    "affidavit": "sworn legal declaration by the candidate",
    "returning officer": "the official in charge of the election in your voting area",
    "election agent": "candidate's authorised representative",
    "recognized political party": "a party officially registered with the Election Commission",
    "registered unrecognized party": "a smaller party registered but without a reserved symbol",
    "independent candidate": "a candidate not backed by any party",

    # --- Voting Process ---
    "VVPAT": "Voting Receipt Machine",
    "voter verifiable paper audit trail": "Voting Receipt Machine",
    "EVM": "Electronic Voting Machine",
    "electronic voting machine": "Electronic Voting Machine",
    "ballot unit": "the part of the machine where you press the button",
    "control unit": "the part of the machine the officer operates",
    "presiding officer": "the official in charge at your polling booth",
    "polling officer": "an official assisting at your polling booth",
    "tendered vote": "a backup paper vote if someone already voted in your name",
    "challenged vote": "a vote questioned by a candidate's representative",
    "NOTA": "None Of The Above (reject all candidates)",
    "none of the above": "reject all candidates option",

    # --- Election Phases & Dates ---
    "model code of conduct": "rules candidates and parties must follow during elections",
    "MCC": "election conduct rules",
    "gazette notification": "official government announcement of the election schedule",
    "poll day": "voting day",
    "counting day": "the day votes are counted",
    "re-poll": "a do-over election at specific booths",

    # --- Results & Post-Election ---
    "simple majority": "more than half the votes",
    "absolute majority": "winning with over 50 percent of votes",
    "coalition": "alliance of multiple parties forming government together",
    "hung assembly": "no single party won enough seats to form government",
    "floor test": "a trust vote in the legislature to prove majority support",
}

# Normalize all keys to lowercase for reliable case-insensitive lookup.
JARGON_MAP: dict[str, str] = {k.lower(): v for k, v in _JARGON_MAP_RAW.items()}

# ---------------------------------------------------------------------------
# Pre-compile a single regex for fast scanning
# ---------------------------------------------------------------------------
# Sort by length (descending) so longer phrases match first.
_sorted_terms = sorted(JARGON_MAP.keys(), key=len, reverse=True)
_JARGON_PATTERN: re.Pattern = re.compile(
    "|".join(re.escape(term) for term in _sorted_terms),
    flags=re.IGNORECASE,
)


def _match_case(original: str, replacement: str) -> str:
    """
    Attempt to mirror the casing style of *original* onto *replacement*.

    Handles three common styles:
      - ALL CAPS  → replacement uppercased.
      - Title Case → replacement title-cased.
      - lowercase  → replacement lowercased.

    Parameters
    ----------
    original : str
        The matched substring from the source text.
    replacement : str
        The plain-language replacement.

    Returns
    -------
    str
        The replacement with casing adjusted.
    """
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement.lower()


def translate(text: str) -> str:
    """
    Replace all recognised jargon terms in *text* with plain-language equivalents.

    This is the single public entry-point used by the response pipeline.

    Parameters
    ----------
    text : str
        Raw assistant response text (may contain government jargon).

    Returns
    -------
    str
        Cleaned text with jargon replaced.

    Examples
    --------
    >>> translate("Please check the electoral roll for your constituency.")
    'Please check the official voter list for your voting area.'
    """
    if not text:
        return text

    def _replacer(match: re.Match) -> str:
        matched = match.group(0)
        key = matched.lower()
        replacement = JARGON_MAP.get(key, matched)
        return _match_case(matched, replacement)

    result = _JARGON_PATTERN.sub(_replacer, text)
    # Clean up repeated words caused by contextual overlap,
    # e.g. "the electoral roll" → "the the official voter list"
    # or "your constituency" → "your your voting area"
    result = re.sub(r'\b(\w+)\s+\1\b', r'\1', result, flags=re.IGNORECASE)
    return result


def get_glossary() -> dict[str, str]:
    """
    Return the full jargon dictionary for reference / API exposure.

    Returns
    -------
    dict[str, str]
        Mapping of government term → plain-language replacement.
    """
    return dict(JARGON_MAP)
