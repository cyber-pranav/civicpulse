"""
calendar_api.py — Google Calendar API Service Wrapper.

Generates calendar event payloads for:
  - Registration deadlines
  - Polling day reminders

Produces both Google Calendar deep-link URLs (for instant add)
and structured event dicts for API-based insertion.
"""

from __future__ import annotations
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Any
from backend.utils.date_helpers import PHASE_II_DATE, format_date_indian


def create_polling_day_event(
    polling_date: date = PHASE_II_DATE,
    booth_address: str = "Your assigned polling booth",
    polling_hours: str = "07:00 AM – 06:00 PM",
) -> dict[str, Any]:
    """
    Create a structured calendar event for polling day.

    Returns a dict that can be sent to Google Calendar API
    or used to generate a deep-link URL.
    """
    start = datetime.combine(polling_date, datetime.strptime("07:00", "%H:%M").time())
    end = datetime.combine(polling_date, datetime.strptime("18:00", "%H:%M").time())

    event = {
        "summary": "🗳️ Voting Day — Don't Forget to Vote!",
        "description": (
            "Today is polling day. Remember to carry your original Voter ID card. "
            f"Polling hours: {polling_hours}."
        ),
        "location": booth_address,
        "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 120},
                {"method": "popup", "minutes": 30},
            ],
        },
    }
    return event


def create_registration_deadline_event(
    deadline_date: date,
    title: str = "Voter Registration Deadline",
) -> dict[str, Any]:
    """Create a calendar event for a registration deadline."""
    event = {
        "summary": f"⚠️ {title}",
        "description": f"Last date: {format_date_indian(deadline_date)}. Complete your registration before this date.",
        "start": {"date": deadline_date.isoformat()},
        "end": {"date": (deadline_date + timedelta(days=1)).isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 1440},  # 1 day before
                {"method": "popup", "minutes": 60},
            ],
        },
    }
    return event


def generate_calendar_deep_link(
    title: str,
    event_date: date,
    details: str = "",
    location: str = "",
) -> str:
    """
    Generate a Google Calendar quick-add deep-link URL.

    Opens the user's Google Calendar with a pre-filled event.
    """
    start_str = event_date.strftime("%Y%m%d")
    end_str = (event_date + timedelta(days=1)).strftime("%Y%m%d")

    params = urllib.parse.urlencode({
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_str}/{end_str}",
        "details": details,
        "location": location,
        "ctz": "Asia/Kolkata",
    })
    return f"https://calendar.google.com/calendar/render?{params}"


def get_all_reminder_links() -> list[dict[str, str]]:
    """
    Generate deep-link URLs for all key election dates.

    Returns a list of dicts with title, date, and url.
    """
    events = [
        ("Voter Registration Deadline", date(2026, 3, 15)),
        ("Voter List Corrections Deadline", date(2026, 3, 20)),
        ("Final Voter List Published", date(2026, 4, 1)),
        ("🗳️ Phase II Polling Day — West Bengal", PHASE_II_DATE),
    ]
    return [
        {
            "title": title,
            "date": format_date_indian(d),
            "calendar_url": generate_calendar_deep_link(title, d),
        }
        for title, d in events
    ]
