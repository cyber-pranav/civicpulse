"""
state_machine.py — Defines the Journey State Machine.

Architecture: State Design Pattern.
Each user session progresses through a strict linear sequence of states.
Transitions are guarded by preconditions (e.g., age >= 18 to move past
ELIGIBILITY_CHECK) and may branch into alternative paths based on context
(location, phase urgency, etc.).

States
------
UNINITIALIZED      → Fresh session, no data collected yet.
ELIGIBILITY_CHECK  → Collecting age, citizenship, location.
CIVIC_EDUCATION    → Terminal branch for users under 18.
REGISTRATION_VERIFIED → User confirmed on voter list.
CANDIDATE_RESEARCH → Reviewing candidate cards.
POLLING_SIMULATION → Mock-voting experience.
POLLING_READY      → Checklist complete, ready for booth.
RESULTS_WAITING    → Post-election state.
EMERGENCY_SIMPLE   → Overlay state — reduces responses to ≤ 15 words.
"""

from __future__ import annotations

from enum import Enum


class JourneyState(str, Enum):
    """
    Enumeration of every state in the Election Journey.

    Using ``str`` mixin so that JSON serialization works transparently
    with Pydantic / FastAPI.
    """

    UNINITIALIZED = "UNINITIALIZED"
    ELIGIBILITY_CHECK = "ELIGIBILITY_CHECK"
    CIVIC_EDUCATION = "CIVIC_EDUCATION"
    REGISTRATION_VERIFIED = "REGISTRATION_VERIFIED"
    CANDIDATE_RESEARCH = "CANDIDATE_RESEARCH"
    POLLING_SIMULATION = "POLLING_SIMULATION"
    POLLING_READY = "POLLING_READY"
    RESULTS_WAITING = "RESULTS_WAITING"
    EMERGENCY_SIMPLE = "EMERGENCY_SIMPLE"


# ---------------------------------------------------------------------------
# Transition Table
# ---------------------------------------------------------------------------
# Maps (current_state) → set of valid next-states.
# Guards are enforced in JourneyManager, not here.
TRANSITION_TABLE: dict[JourneyState, set[JourneyState]] = {
    JourneyState.UNINITIALIZED: {
        JourneyState.ELIGIBILITY_CHECK,
    },
    JourneyState.ELIGIBILITY_CHECK: {
        JourneyState.CIVIC_EDUCATION,        # age < 18
        JourneyState.REGISTRATION_VERIFIED,  # age >= 18
    },
    JourneyState.CIVIC_EDUCATION: set(),     # terminal state
    JourneyState.REGISTRATION_VERIFIED: {
        JourneyState.CANDIDATE_RESEARCH,
    },
    JourneyState.CANDIDATE_RESEARCH: {
        JourneyState.POLLING_SIMULATION,
    },
    JourneyState.POLLING_SIMULATION: {
        JourneyState.POLLING_READY,
    },
    JourneyState.POLLING_READY: {
        JourneyState.RESULTS_WAITING,
    },
    JourneyState.RESULTS_WAITING: set(),     # terminal state
}

# Emergency Simple Mode can be entered/exited from ANY non-terminal state.
EMERGENCY_ELIGIBLE_STATES: set[JourneyState] = {
    s for s, targets in TRANSITION_TABLE.items() if len(targets) > 0
}


class TransitionError(Exception):
    """Raised when a state transition is not allowed."""


def validate_transition(
    current: JourneyState,
    target: JourneyState,
) -> bool:
    """
    Check whether moving from *current* to *target* is a legal transition.

    Parameters
    ----------
    current : JourneyState
        The state the session is currently in.
    target : JourneyState
        The desired next state.

    Returns
    -------
    bool
        ``True`` if the transition is valid.

    Raises
    ------
    TransitionError
        If the transition violates the state machine rules.
    """
    # Emergency mode can be entered from any eligible state.
    if target == JourneyState.EMERGENCY_SIMPLE:
        if current in EMERGENCY_ELIGIBLE_STATES:
            return True
        raise TransitionError(
            f"Cannot enter EMERGENCY_SIMPLE from terminal state {current.value}."
        )

    # Normal transition lookup.
    allowed = TRANSITION_TABLE.get(current, set())
    if target in allowed:
        return True

    raise TransitionError(
        f"Transition {current.value} → {target.value} is not permitted. "
        f"Allowed targets: {[s.value for s in allowed]}."
    )


# ---------------------------------------------------------------------------
# Path Descriptors (used by the Journey Controller for branching logic)
# ---------------------------------------------------------------------------

class JourneyPath(str, Enum):
    """
    High-level path the user is on, determined during ELIGIBILITY_CHECK.
    """

    CIVIC_EDUCATION = "CIVIC_EDUCATION"       # age < 18
    URGENT_POLLING = "URGENT_POLLING"          # West Bengal, Phase II
    STANDARD_REGISTRATION = "STANDARD_REGISTRATION"  # all other eligible users


def determine_path(
    age: int,
    state_or_ut: str,
    *,
    election_date_str: str = "2026-04-29",
    current_date_str: str = "2026-04-28",
) -> JourneyPath:
    """
    Determine which journey path a user should follow.

    Decision tree (mirrors spec §2 Logical Branching):
      1. age < 18  → CIVIC_EDUCATION
      2. location == "West Bengal" AND election is ≤ 24 h away → URGENT_POLLING
      3. Otherwise → STANDARD_REGISTRATION

    Parameters
    ----------
    age : int
        User's age in years (computed from DOB).
    state_or_ut : str
        Indian state or union territory name.
    election_date_str : str
        ISO date of the relevant election phase.
    current_date_str : str
        ISO date representing "today".

    Returns
    -------
    JourneyPath
    """
    if age < 18:
        return JourneyPath.CIVIC_EDUCATION

    from datetime import date

    election_date = date.fromisoformat(election_date_str)
    current_date = date.fromisoformat(current_date_str)
    hours_until = (election_date - current_date).total_seconds() / 3600

    if state_or_ut.strip().lower() == "west bengal" and hours_until <= 24:
        return JourneyPath.URGENT_POLLING

    return JourneyPath.STANDARD_REGISTRATION
