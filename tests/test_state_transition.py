"""
test_state_machine.py — Unit Tests for the Journey State Machine.

Validates transition rules, terminal states, and emergency mode.
"""
from __future__ import annotations
import pytest
from backend.logic.state_machine import (
    JourneyState, TRANSITION_TABLE,
    EMERGENCY_ELIGIBLE_STATES, TransitionError, validate_transition,
)

class TestTransitionTable:
    def test_all_states_have_entries(self):
        for state in JourneyState:
            if state != JourneyState.EMERGENCY_SIMPLE:
                assert state in TRANSITION_TABLE

    def test_terminal_states_empty(self):
        assert len(TRANSITION_TABLE[JourneyState.CIVIC_EDUCATION]) == 0
        assert len(TRANSITION_TABLE[JourneyState.RESULTS_WAITING]) == 0

    def test_initial_goes_to_eligibility(self):
        assert TRANSITION_TABLE[JourneyState.UNINITIALIZED] == {JourneyState.ELIGIBILITY_CHECK}

    def test_eligibility_branches(self):
        targets = TRANSITION_TABLE[JourneyState.ELIGIBILITY_CHECK]
        assert JourneyState.CIVIC_EDUCATION in targets
        assert JourneyState.REGISTRATION_VERIFIED in targets

    def test_linear_progression(self):
        assert JourneyState.CANDIDATE_RESEARCH in TRANSITION_TABLE[JourneyState.REGISTRATION_VERIFIED]
        assert JourneyState.POLLING_SIMULATION in TRANSITION_TABLE[JourneyState.CANDIDATE_RESEARCH]
        assert JourneyState.POLLING_READY in TRANSITION_TABLE[JourneyState.POLLING_SIMULATION]
        assert JourneyState.RESULTS_WAITING in TRANSITION_TABLE[JourneyState.POLLING_READY]

class TestValidateTransition:
    def test_valid_transition(self):
        assert validate_transition(JourneyState.UNINITIALIZED, JourneyState.ELIGIBILITY_CHECK)

    def test_invalid_transition(self):
        with pytest.raises(TransitionError):
            validate_transition(JourneyState.UNINITIALIZED, JourneyState.POLLING_READY)

    def test_skip_not_allowed(self):
        with pytest.raises(TransitionError):
            validate_transition(JourneyState.ELIGIBILITY_CHECK, JourneyState.POLLING_SIMULATION)

    def test_backward_not_allowed(self):
        with pytest.raises(TransitionError):
            validate_transition(JourneyState.CANDIDATE_RESEARCH, JourneyState.ELIGIBILITY_CHECK)

    def test_emergency_from_eligible(self):
        for state in EMERGENCY_ELIGIBLE_STATES:
            assert validate_transition(state, JourneyState.EMERGENCY_SIMPLE)

    def test_emergency_from_terminal_raises(self):
        with pytest.raises(TransitionError):
            validate_transition(JourneyState.CIVIC_EDUCATION, JourneyState.EMERGENCY_SIMPLE)

class TestEmergencyMode:
    def test_excludes_terminal(self):
        assert JourneyState.CIVIC_EDUCATION not in EMERGENCY_ELIGIBLE_STATES
        assert JourneyState.RESULTS_WAITING not in EMERGENCY_ELIGIBLE_STATES

    def test_includes_active(self):
        assert JourneyState.ELIGIBILITY_CHECK in EMERGENCY_ELIGIBLE_STATES
        assert JourneyState.REGISTRATION_VERIFIED in EMERGENCY_ELIGIBLE_STATES
