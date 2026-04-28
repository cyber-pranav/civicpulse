"""
date_helpers.py — Date and Time Utilities for the Election Journey.

Provides helpers for:
  - Calculating voting-eligible age from a date of birth.
  - Computing time remaining until election day.
  - Formatting dates in human-friendly Indian English.

All functions are pure (no side-effects) and use the ``datetime`` stdlib.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Application Constants
# ---------------------------------------------------------------------------
# Hardcoded per spec §2: "Current Date: April 28, 2026"
CURRENT_DATE: date = date(2026, 4, 28)

# Phase II (West Bengal) election date.
PHASE_II_DATE: date = date(2026, 4, 29)

# Minimum voting age in India.
MINIMUM_VOTING_AGE: int = 18

# The qualifying date for voter registration (Jan 1 of election year).
QUALIFYING_DATE: date = date(2026, 1, 1)


def calculate_age(dob: date, reference: date = QUALIFYING_DATE) -> int:
    """
    Calculate a person's age in completed years as of *reference* date.

    In Indian elections the qualifying date is January 1 of the election year,
    meaning you must be 18 by Jan 1, 2026 to vote in the 2026 general election.

    Parameters
    ----------
    dob : date
        Date of birth.
    reference : date
        The date against which age is computed (defaults to Jan 1, 2026).

    Returns
    -------
    int
        Age in completed years.

    Examples
    --------
    >>> calculate_age(date(2008, 6, 15))
    17
    >>> calculate_age(date(2008, 1, 1))
    18
    """
    age = reference.year - dob.year
    if (reference.month, reference.day) < (dob.month, dob.day):
        age -= 1
    return max(age, 0)


def is_eligible_to_vote(dob: date) -> bool:
    """
    Determine if a person is old enough to vote.

    Parameters
    ----------
    dob : date
        Date of birth.

    Returns
    -------
    bool
        ``True`` if age ≥ 18 on the qualifying date.
    """
    return calculate_age(dob) >= MINIMUM_VOTING_AGE


def hours_until_election(
    now: datetime | None = None,
    election: date = PHASE_II_DATE,
) -> float:
    """
    Compute hours remaining until election day (midnight IST).

    Parameters
    ----------
    now : datetime, optional
        Current timestamp.  Defaults to ``datetime.now()``.
    election : date
        Target election date.

    Returns
    -------
    float
        Hours remaining (can be negative if the election has passed).
    """
    if now is None:
        now = datetime.now()
    election_start = datetime.combine(election, datetime.min.time())
    delta: timedelta = election_start - now
    return delta.total_seconds() / 3600


def format_date_indian(d: date) -> str:
    """
    Format a date in Indian English style: "29 April 2026".

    Parameters
    ----------
    d : date
        The date to format.

    Returns
    -------
    str
        Human-friendly date string.
    """
    return d.strftime("%d %B %Y")


def get_election_countdown(election: date = PHASE_II_DATE) -> str:
    """
    Generate a human-readable countdown string for display.

    Returns
    -------
    str
        e.g. "Voting is TOMORROW!" or "3 days until voting day."
    """
    delta = (election - CURRENT_DATE).days
    if delta < 0:
        return "Voting day has passed."
    if delta == 0:
        return "🗳️ TODAY is voting day!"
    if delta == 1:
        return "🗳️ Voting is TOMORROW!"
    return f"🗳️ {delta} days until voting day."


def get_registration_deadlines() -> dict[str, str]:
    """
    Return key registration deadlines for the current election cycle.

    These are illustrative dates aligned with the spec's April 2026 timeline.

    Returns
    -------
    dict[str, str]
        Mapping of deadline name → formatted date.
    """
    return {
        "Last date for new voter registration": "15 March 2026",
        "Last date for corrections in voter list": "20 March 2026",
        "Final voter list publication": "01 April 2026",
        "Phase II polling day (West Bengal)": format_date_indian(PHASE_II_DATE),
    }
