"""
journey_manager.py — The Journey Controller.

Implements the ``JourneyManager`` class that owns a user session's
progression through the Election Journey state machine.

Responsibilities
----------------
1. Hold ephemeral session state (never persisted to disk — Zero-PII).
2. Enforce state-transition guards.
3. Produce stage-specific response payloads.
4. Trigger Emergency Simple Mode on confusion signals.
5. Orchestrate the VVPAT timer during polling simulation.

All public methods return structured dicts suitable for JSON serialisation
by the FastAPI layer.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime
from typing import Any, Optional

from backend.logic.state_machine import (
    JourneyPath,
    JourneyState,
    TransitionError,
    determine_path,
    validate_transition,
)
from backend.utils.date_helpers import (
    CURRENT_DATE,
    PHASE_II_DATE,
    calculate_age,
    format_date_indian,
    get_election_countdown,
    get_registration_deadlines,
    hours_until_election,
    is_eligible_to_vote,
)
from backend.utils.jargon_killer import translate
from backend.utils.sanitizer import sanitize


class JourneyManager:
    """
    Manages a single user's election-readiness journey.

    Each instance is ephemeral — tied to a session ID and discarded
    when the session ends.  **No data is written to disk.**

    Attributes
    ----------
    session_id : str
        UUID v4 identifying this session.
    state : JourneyState
        Current position in the journey.
    path : JourneyPath | None
        Determined after eligibility check (CIVIC_EDUCATION / URGENT /
        STANDARD).
    simple_mode : bool
        When ``True``, all responses are capped at 15 words.
    _previous_state : JourneyState | None
        Saved state before entering Emergency Simple Mode so we can resume.
    _age : int | None
        Computed age (ephemeral, never stored).
    _location : str | None
        User's state/UT (ephemeral).
    """

    def __init__(self) -> None:
        """Initialise a fresh journey session."""
        self.session_id: str = str(uuid.uuid4())
        self.state: JourneyState = JourneyState.UNINITIALIZED
        self.path: Optional[JourneyPath] = None
        self.simple_mode: bool = False
        self._previous_state: Optional[JourneyState] = None
        self._age: Optional[int] = None
        self._location: Optional[str] = None
        self._vote_cast: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_journey(self) -> dict[str, Any]:
        """
        Begin the journey — move from UNINITIALIZED → ELIGIBILITY_CHECK.

        Returns a welcome payload with the election countdown.
        """
        self._transition(JourneyState.ELIGIBILITY_CHECK)
        countdown = get_election_countdown()
        message = translate(
            f"Welcome to the Election Journey Orchestrator! {countdown} "
            "Let's make sure you're ready. First, I need to check your "
            "eligibility.  Please provide your date of birth and state of "
            "residence."
        )
        return self._response(message, needs_input=["dob", "location"])

    def check_eligibility(
        self,
        dob_iso: str,
        location: str,
    ) -> dict[str, Any]:
        """
        Stage 1 — Identity & Eligibility.

        Validates age and determines the journey path.

        Parameters
        ----------
        dob_iso : str
            Date of birth in ISO format (YYYY-MM-DD).
        location : str
            Indian state or union territory name.

        Returns
        -------
        dict
            Response payload with path determination.
        """
        self._require_state(JourneyState.ELIGIBILITY_CHECK)

        # Sanitize inputs
        location, suspicious = sanitize(location)
        if suspicious:
            return self._response(
                "Your input looks unusual. Please provide a valid Indian state or UT name.",
                error=True,
            )

        dob = date.fromisoformat(dob_iso)
        age = calculate_age(dob)
        self._age = age
        self._location = location.strip().title()

        # Determine path
        self.path = determine_path(age, location)

        if self.path == JourneyPath.CIVIC_EDUCATION:
            self._transition(JourneyState.CIVIC_EDUCATION)
            message = translate(
                f"You are {age} years old — not yet 18 on the qualifying date. "
                "You can't vote in this election, but your civic voice matters! "
                "Here's how you can prepare for your first vote and engage with "
                "democracy right now."
            )
            return self._response(
                message,
                path=self.path.value,
                civic_tips=self._get_civic_education_tips(),
            )

        # Eligible voter — advance to registration
        self._transition(JourneyState.REGISTRATION_VERIFIED)

        if self.path == JourneyPath.URGENT_POLLING:
            message = translate(
                f"⚡ URGENT — Phase II polling in West Bengal is TOMORROW "
                f"({format_date_indian(PHASE_II_DATE)}). "
                f"You are {age} years old and eligible to vote. "
                "Let's fast-track your polling prep. "
                "First, have you verified your name on the electoral roll?"
            )
        else:
            message = translate(
                f"Great news — you are {age} years old and eligible to vote! "
                f"Your state: {self._location}. "
                "Let's verify your registration. Have you checked whether your "
                "name appears on the electoral roll?"
            )

        return self._response(
            message,
            path=self.path.value,
            age=age,
            location=self._location,
            deadlines=get_registration_deadlines(),
            needs_input=["registration_status"],
        )

    def verify_registration(self, is_registered: bool) -> dict[str, Any]:
        """
        Stage 2 — Registration Logic.

        Provides step-by-step guidance based on registration status.

        Parameters
        ----------
        is_registered : bool
            Whether the user confirmed they are on the voter list.
        """
        self._require_state(JourneyState.REGISTRATION_VERIFIED)

        if is_registered:
            self._transition(JourneyState.CANDIDATE_RESEARCH)
            message = translate(
                "Your registration is confirmed. Now let's research the "
                "candidates in your constituency. I'll prepare simplified "
                "Candidate Cards with key information: Education, Criminal "
                "Record, Assets, and Key Promises."
            )
            return self._response(message, needs_input=["constituency_name"])
        else:
            steps = self._get_registration_steps()
            message = translate(
                "No worries — let's check the electoral roll for your name. "
                "Follow these steps:"
            )
            return self._response(message, registration_steps=steps)

    def get_candidate_cards(
        self,
        constituency: str,
        candidates_data: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Stage 3 — Candidate Research.

        Parses candidate profiles into simplified "Candidate Cards."

        Parameters
        ----------
        constituency : str
            Name of the voting area.
        candidates_data : list[dict], optional
            Raw candidate data (from Google Civic API or mock).
            If ``None``, uses demo data.
        """
        self._require_state(JourneyState.CANDIDATE_RESEARCH)

        constituency, _ = sanitize(constituency)

        if candidates_data is None:
            candidates_data = self._get_demo_candidates()

        cards = [
            self._build_candidate_card(c) for c in candidates_data
        ]

        self._transition(JourneyState.POLLING_SIMULATION)
        message = translate(
            f"Here are the Candidate Cards for {constituency}. "
            "Review them carefully. When you're ready, we'll do a virtual "
            "polling simulation so you know exactly what to expect on poll day."
        )
        return self._response(
            message,
            constituency=constituency,
            candidate_cards=cards,
            needs_input=["ready_for_simulation"],
        )

    async def run_polling_simulation(self) -> dict[str, Any]:
        """
        Stage 4 — Virtual Polling Simulation.

        Walks the user through a mock-voting experience and triggers
        a 7-second VVPAT slip timer.

        Returns
        -------
        dict
            Response with simulation steps and the VVPAT timer event.
        """
        self._require_state(JourneyState.POLLING_SIMULATION)

        steps = [
            "1. You arrive at the polling booth and join the queue.",
            "2. An official checks your Voter ID card and marks your finger with ink.",
            "3. You enter the voting compartment — it's private.",
            "4. You see the Electronic Voting Machine with candidate names and symbols.",
            "5. Press the button next to your chosen candidate.",
            "6. ✅ VOTE CAST — the machine beeps to confirm.",
            "7. The Voting Receipt Machine shows a printed slip for 7 seconds.",
            "8. Verify the slip matches your choice, then leave the booth.",
        ]

        # Trigger the 7-second VVPAT timer event
        vvpat_event = {
            "event": "VVPAT_SLIP_DISPLAY",
            "duration_seconds": 7,
            "message": translate(
                "The VVPAT slip is displayed for 7 seconds. "
                "Verify it matches your chosen candidate."
            ),
        }

        self._vote_cast = True
        self._transition(JourneyState.POLLING_READY)

        message = translate(
            "🗳️ Virtual Polling Simulation complete! Your vote has been cast. "
            "Here's your polling-day checklist so you're fully prepared."
        )

        return self._response(
            message,
            simulation_steps=[translate(s) for s in steps],
            vvpat_event=vvpat_event,
            checklist=self._get_polling_checklist(),
        )

    def complete_journey(self) -> dict[str, Any]:
        """
        Move to RESULTS_WAITING — the journey is complete.
        """
        self._require_state(JourneyState.POLLING_READY)
        self._transition(JourneyState.RESULTS_WAITING)
        message = translate(
            "🎉 You are fully prepared for polling day! "
            "After voting, results will be announced on counting day. "
            "Stay informed and encourage others to vote. "
            "Democracy works best when everyone participates."
        )
        return self._response(message)

    # ------------------------------------------------------------------
    # Emergency Simple Mode
    # ------------------------------------------------------------------

    def toggle_simple_mode(self) -> dict[str, Any]:
        """
        Enter or exit Emergency Simple Mode.

        In simple mode all responses are truncated to ≤ 15 words.
        """
        if self.simple_mode:
            # Exit simple mode — restore previous state.
            self.simple_mode = False
            if self._previous_state:
                self.state = self._previous_state
                self._previous_state = None
            return self._response("Simple Mode OFF. Full responses restored.")
        else:
            self.simple_mode = True
            self._previous_state = self.state
            return self._response("Simple Mode ON. Short answers only now.")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _transition(self, target: JourneyState) -> None:
        """Validate and execute a state transition."""
        validate_transition(self.state, target)
        self.state = target

    def _require_state(self, expected: JourneyState) -> None:
        """Raise if current state doesn't match *expected*."""
        if self.state != expected:
            raise TransitionError(
                f"Expected state {expected.value}, "
                f"but current state is {self.state.value}."
            )

    def _response(
        self,
        message: str,
        *,
        error: bool = False,
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Build a standardised response payload.

        If simple_mode is active, the message is truncated to 15 words.
        """
        if self.simple_mode and not error:
            words = message.split()
            message = " ".join(words[:15])
            if len(words) > 15:
                message += "…"

        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "state": self.state.value,
            "simple_mode": self.simple_mode,
            "message": message,
        }
        if error:
            payload["error"] = True
        payload.update(extra)
        return payload

    # ------------------------------------------------------------------
    # Data Generators (demo / placeholder data)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_civic_education_tips() -> list[str]:
        """Tips for users under 18."""
        return [
            "Learn about how elections work in India at eci.gov.in.",
            "Follow local news and understand the issues in your area.",
            "Discuss civic topics with family and friends.",
            "Pre-register for your Voter ID card as soon as you turn 18.",
            "Volunteer with voter-awareness campaigns in your community.",
        ]

    def _get_registration_steps(self) -> list[dict[str, str]]:
        """Step-by-step voter list verification instructions."""
        base_steps = [
            {
                "step": "1",
                "title": "Visit the National Voter Service Portal",
                "url": "https://voters.eci.gov.in/",
                "detail": "Click 'Search In Voter List' on the homepage.",
            },
            {
                "step": "2",
                "title": "Search by Details",
                "detail": (
                    "Enter your name, age, father's/husband's name, "
                    "and select your state and voting area."
                ),
            },
            {
                "step": "3",
                "title": "Or Search by Voter ID Number",
                "detail": "Enter your Voter ID number directly for faster lookup.",
            },
            {
                "step": "4",
                "title": "Download Your Voter Slip",
                "detail": (
                    "If found, download the e-voter slip showing your "
                    "booth number and serial number."
                ),
            },
        ]
        # Translate jargon in all text fields.
        for step in base_steps:
            step["detail"] = translate(step["detail"])
            step["title"] = translate(step["title"])
        return base_steps

    @staticmethod
    def _get_demo_candidates() -> list[dict[str, Any]]:
        """Demo candidate data for Candidate Cards."""
        return [
            {
                "name": "Arun Kumar",
                "party": "National Progress Party",
                "symbol": "🌾",
                "education": "MA Political Science, Calcutta University",
                "criminal_cases": 0,
                "assets_inr": 12_00_000,
                "promises": [
                    "Improve rural road connectivity",
                    "Free healthcare for families below poverty line",
                    "500 new primary schools",
                ],
            },
            {
                "name": "Priya Mukherjee",
                "party": "People's Democratic Front",
                "symbol": "🔔",
                "education": "B.Tech, IIT Kharagpur; MBA, IIM Calcutta",
                "criminal_cases": 0,
                "assets_inr": 45_00_000,
                "promises": [
                    "Digital literacy program for all villages",
                    "Clean drinking water in every household",
                    "50,000 new jobs in green energy",
                ],
            },
            {
                "name": "Rajesh Singh",
                "party": "Independent",
                "symbol": "⭐",
                "education": "BA, Burdwan University",
                "criminal_cases": 2,
                "assets_inr": 8_00_000,
                "promises": [
                    "Anti-corruption watchdog committee",
                    "Reduce local taxes by 20%",
                    "Weekly public grievance sessions",
                ],
            },
        ]

    @staticmethod
    def _build_candidate_card(raw: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a raw candidate profile into a simplified Candidate Card.

        The card highlights: Name, Party, Education, Criminal Record,
        Assets, and Key Promises.
        """
        criminal = raw.get("criminal_cases", 0)
        if criminal == 0:
            criminal_label = "✅ No criminal cases"
        else:
            criminal_label = f"⚠️ {criminal} pending criminal case(s)"

        assets = raw.get("assets_inr", 0)
        if assets >= 1_00_00_000:
            assets_label = f"₹{assets / 1_00_00_000:.1f} Crore"
        elif assets >= 1_00_000:
            assets_label = f"₹{assets / 1_00_000:.1f} Lakh"
        else:
            assets_label = f"₹{assets:,}"

        return {
            "name": raw.get("name", "Unknown"),
            "party": raw.get("party", "Unknown"),
            "symbol": raw.get("symbol", ""),
            "education": raw.get("education", "Not disclosed"),
            "criminal_record": criminal_label,
            "declared_assets": assets_label,
            "key_promises": raw.get("promises", []),
        }

    @staticmethod
    def _get_polling_checklist() -> list[str]:
        """Polling-day readiness checklist."""
        return [
            "✅ Carry your original Voter ID card (no photocopies).",
            "✅ Know your polling booth number and address.",
            "✅ Check polling hours (usually 7 AM – 6 PM).",
            "✅ Wear comfortable clothes — you may queue for a while.",
            "✅ Do NOT carry your phone into the voting compartment.",
            "✅ Do NOT take photos of the voting machine or your ballot.",
            "✅ After voting, check for the indelible ink mark on your finger.",
            "✅ Collect your voter slip from the booth if offered.",
        ]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise session state for API responses.

        This is ephemeral — never stored to disk.
        """
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "path": self.path.value if self.path else None,
            "simple_mode": self.simple_mode,
            "countdown": get_election_countdown(),
        }
