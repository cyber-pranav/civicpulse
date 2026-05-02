"""
calendar_api.py — Google Calendar API Service Wrapper.

Generates calendar event payloads for:
  - Registration deadlines
  - Polling day reminders
  - Counting day reminders

Produces both Google Calendar deep-link URLs (for instant add),
structured event dicts for API-based insertion, and downloadable
.ics files for universal calendar support.
"""

from __future__ import annotations

import urllib.parse
from datetime import date, datetime, timedelta
from typing import Any

from backend.utils.date_helpers import (
    COUNTING_DAY,
    PHASE_II_DATE,
    format_date_indian,
)


def create_polling_day_event(
    polling_date: date = PHASE_II_DATE,
    booth_address: str = "Your assigned polling booth",
    polling_hours: str = "07:00 AM – 06:00 PM",
) -> dict[str, Any]:
    """
    Create a structured calendar event for polling day.

    Returns a dict that can be sent to Google Calendar API
    or used to generate a deep-link URL.

    Parameters
    ----------
    polling_date : date
        The election date.
    booth_address : str
        Address of the voter's assigned polling booth.
    polling_hours : str
        Human-readable polling hours string.

    Returns
    -------
    dict
        Structured Google Calendar event payload.
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


def create_counting_day_event(
    counting_date: date = COUNTING_DAY,
) -> dict[str, Any]:
    """
    Create a structured calendar event for counting day.

    Parameters
    ----------
    counting_date : date
        The counting/results date.

    Returns
    -------
    dict
        Structured Google Calendar event payload.
    """
    start = datetime.combine(counting_date, datetime.strptime("08:00", "%H:%M").time())
    end = datetime.combine(counting_date, datetime.strptime("20:00", "%H:%M").time())

    event = {
        "summary": "📊 Counting Day — Election Results!",
        "description": (
            "Today is counting day. Results for the West Bengal Phase II "
            "elections will be announced. Stay tuned to official channels. "
            "Follow live updates on the Election Commission of India website: "
            "https://results.eci.gov.in/"
        ),
        "location": "India — Follow results at results.eci.gov.in",
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
    """
    Create a calendar event for a registration deadline.

    Parameters
    ----------
    deadline_date : date
        The deadline date.
    title : str
        Human-readable title for the event.

    Returns
    -------
    dict
        Structured calendar event payload.
    """
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

    Parameters
    ----------
    title : str
        Event title/summary.
    event_date : date
        Date for the event.
    details : str
        Optional event description.
    location : str
        Optional location string.

    Returns
    -------
    str
        Google Calendar deep-link URL.
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


def generate_ics_content(
    title: str,
    event_date: date,
    description: str = "",
    location: str = "",
    duration_hours: int = 12,
) -> str:
    """
    Generate a standard .ics (iCalendar) file content string.

    Compatible with all major calendar applications (Google Calendar,
    Apple Calendar, Outlook, etc.).

    Parameters
    ----------
    title : str
        Event summary/title.
    event_date : date
        Start date of the event.
    description : str
        Event description text.
    location : str
        Event location string.
    duration_hours : int
        Duration of the event in hours.

    Returns
    -------
    str
        Valid iCalendar (.ics) file content.
    """
    start_dt = datetime.combine(event_date, datetime.strptime("08:00", "%H:%M").time())
    end_dt = start_dt + timedelta(hours=duration_hours)
    now = datetime.now(tz=__import__('datetime').timezone.utc)

    # Format dates for iCal (YYYYMMDDTHHMMSSZ)
    dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend = end_dt.strftime("%Y%m%dT%H%M%S")
    dtstamp = now.strftime("%Y%m%dT%H%M%SZ")

    # Escape special characters in iCal
    desc_escaped = description.replace("\n", "\\n").replace(",", "\\,")
    loc_escaped = location.replace(",", "\\,")

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//CivicPulse//Election Journey//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART;TZID=Asia/Kolkata:{dtstart}\r\n"
        f"DTEND;TZID=Asia/Kolkata:{dtend}\r\n"
        f"DTSTAMP:{dtstamp}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{desc_escaped}\r\n"
        f"LOCATION:{loc_escaped}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT2H\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Reminder\r\n"
        "END:VALARM\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT30M\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Reminder\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics


def generate_counting_day_ics() -> str:
    """
    Generate an .ics file for the Counting Day (May 4, 2026).

    Returns
    -------
    str
        Valid iCalendar content for counting day reminder.
    """
    return generate_ics_content(
        title="📊 Counting Day — Election Results Announcement",
        event_date=COUNTING_DAY,
        description=(
            "West Bengal Phase II election results will be announced today. "
            "Follow live updates on the Election Commission of India website: "
            "https://results.eci.gov.in/"
        ),
        location="India — Follow results at results.eci.gov.in",
        duration_hours=12,
    )


def get_all_reminder_links() -> list[dict[str, str]]:
    """
    Generate deep-link URLs for all key election dates.

    Returns a list of dicts with title, date, url, and ics availability.

    Returns
    -------
    list[dict]
        Calendar reminder entries with deep links and ICS availability.
    """
    events = [
        ("Voter Registration Deadline", date(2026, 3, 15)),
        ("Voter List Corrections Deadline", date(2026, 3, 20)),
        ("Final Voter List Published", date(2026, 4, 1)),
        ("🗳️ Phase II Polling Day — West Bengal", PHASE_II_DATE),
        ("📊 Counting Day — Results Announcement", COUNTING_DAY),
    ]
    return [
        {
            "title": title,
            "date": format_date_indian(d),
            "calendar_url": generate_calendar_deep_link(title, d),
            "has_ics": d == COUNTING_DAY,
        }
        for title, d in events
    ]
