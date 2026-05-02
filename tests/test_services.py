"""
test_services.py — Unit Tests for Google Service Wrappers.

Validates mock fallbacks, URL generation, and ICS file creation.
"""
from __future__ import annotations
from datetime import date
import pytest
from backend.services.civic_api import get_mock_voter_info, CivicAPIError
from backend.services.maps_api import generate_directions_url, get_mock_time_to_booth
from backend.services.calendar_api import (
    generate_calendar_deep_link, generate_ics_content,
    generate_counting_day_ics, get_all_reminder_links,
    create_counting_day_event, create_polling_day_event,
)

class TestCivicAPIMock:
    def test_mock_returns_valid_structure(self):
        data = get_mock_voter_info("West Bengal")
        assert "election" in data
        assert "pollingLocations" in data
        assert "contests" in data
        assert len(data["contests"]) > 0

    def test_mock_has_candidates(self):
        data = get_mock_voter_info("Maharashtra")
        candidates = data["contests"][0]["candidates"]
        assert len(candidates) >= 2
        for c in candidates:
            assert "name" in c
            assert "party" in c

    def test_mock_has_polling_location(self):
        data = get_mock_voter_info("Delhi")
        assert len(data["pollingLocations"]) > 0
        loc = data["pollingLocations"][0]
        assert "address" in loc

class TestMapsAPI:
    def test_directions_url_format(self):
        url = generate_directions_url("Mumbai", "Polling Booth A")
        assert "google.com/maps" in url
        assert "Mumbai" in url

    def test_mock_time_to_booth(self):
        data = get_mock_time_to_booth("Home", "Booth")
        assert "duration_text" in data
        assert "distance_text" in data
        assert "directions_url" in data

class TestCalendarAPI:
    def test_deep_link_format(self):
        url = generate_calendar_deep_link("Test", date(2026, 5, 4))
        assert "calendar.google.com" in url
        assert "Test" in url

    def test_ics_content_valid(self):
        ics = generate_ics_content("Test Event", date(2026, 5, 4), "Details")
        assert "BEGIN:VCALENDAR" in ics
        assert "END:VCALENDAR" in ics
        assert "BEGIN:VEVENT" in ics
        assert "Test Event" in ics
        assert "VALARM" in ics

    def test_counting_day_ics(self):
        ics = generate_counting_day_ics()
        assert "Counting Day" in ics
        assert "BEGIN:VCALENDAR" in ics

    def test_all_reminder_links(self):
        links = get_all_reminder_links()
        assert len(links) >= 5
        counting = [l for l in links if "Counting" in l["title"]]
        assert len(counting) == 1
        assert counting[0]["has_ics"] is True

    def test_polling_day_event(self):
        event = create_polling_day_event()
        assert "summary" in event
        assert "reminders" in event

    def test_counting_day_event(self):
        event = create_counting_day_event()
        assert "Counting Day" in event["summary"]
        assert "results.eci.gov.in" in event["description"]
