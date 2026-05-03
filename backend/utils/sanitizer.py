"""
sanitizer.py — Input Sanitization & Security Utilities.

Implements Zero-PII philosophy: all user data is ephemeral (session-only)
and this module ensures inputs are cleaned before any processing.

Capabilities
------------
1. HTML / XSS sanitization via ``bleach``.
2. Prompt-injection detection heuristics.
3. PII stripping (Voter IDs, Aadhaar patterns, phone numbers).
4. Length limiting to prevent abuse.
"""

from __future__ import annotations

import re

import bleach

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_INPUT_LENGTH: int = 2000  # characters
ALLOWED_HTML_TAGS: list[str] = []  # strip ALL HTML
ALLOWED_ATTRIBUTES: dict[str, list[str]] = {}

# ---------------------------------------------------------------------------
# PII Patterns (Indian context)
# ---------------------------------------------------------------------------
# Voter ID (EPIC): 3 uppercase letters + 7 digits, e.g., ABC1234567
_VOTER_ID_RE = re.compile(r"\b[A-Z]{3}\d{7}\b")

# Aadhaar: 12 digits, often written as 4-4-4
_AADHAAR_RE = re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b")

# Indian mobile: optional +91, then 10 digits starting with 6-9
_PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?\b[6-9]\d{9}\b")

# Email addresses
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b")

_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_VOTER_ID_RE, "[VOTER_ID_REDACTED]"),
    (_AADHAAR_RE, "[AADHAAR_REDACTED]"),
    (_PHONE_RE, "[PHONE_REDACTED]"),
    (_EMAIL_RE, "[EMAIL_REDACTED]"),
]

# ---------------------------------------------------------------------------
# Prompt Injection Detection
# ---------------------------------------------------------------------------
_INJECTION_KEYWORDS: list[str] = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard the above",
    "you are now",
    "act as",
    "pretend you are",
    "system prompt",
    "override instructions",
    "forget everything",
    "new instructions",
    "reveal your prompt",
    "show me your instructions",
]


def sanitize_html(text: str) -> str:
    """
    Strip all HTML tags and attributes from user input.

    Uses ``bleach.clean`` with an empty allow-list so every tag is removed,
    preventing stored/reflected XSS.

    Parameters
    ----------
    text : str
        Raw user input.

    Returns
    -------
    str
        Plain text with HTML stripped.
    """
    return bleach.clean(
        text,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


def strip_pii(text: str) -> str:
    """
    Redact personally identifiable information from user input.

    Patterns redacted:
      - Voter ID (EPIC format)
      - Aadhaar numbers
      - Indian mobile numbers
      - Email addresses

    Parameters
    ----------
    text : str
        User input potentially containing PII.

    Returns
    -------
    str
        Text with PII tokens replaced by ``[REDACTED]`` placeholders.
    """
    for pattern, placeholder in _PII_PATTERNS:
        text = pattern.sub(placeholder, text)
    return text


def detect_prompt_injection(text: str) -> bool:
    """
    Heuristic check for common prompt-injection attempts.

    Parameters
    ----------
    text : str
        User input to scan.

    Returns
    -------
    bool
        ``True`` if a potential injection pattern is detected.
    """
    lowered = text.lower()
    return any(keyword in lowered for keyword in _INJECTION_KEYWORDS)


def enforce_length(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Truncate input to a safe maximum length.

    Parameters
    ----------
    text : str
        User input.
    max_length : int
        Character limit.

    Returns
    -------
    str
        Truncated text.
    """
    return text[:max_length]


def sanitize(text: str) -> tuple[str, bool]:
    """
    Full sanitization pipeline — the single entry-point for all user input.

    Pipeline order:
      1. Length enforcement.
      2. HTML / XSS stripping.
      3. PII redaction.
      4. Prompt-injection detection.

    Parameters
    ----------
    text : str
        Raw user input.

    Returns
    -------
    tuple[str, bool]
        (cleaned_text, is_suspicious)
        ``is_suspicious`` is ``True`` when prompt-injection heuristics fire.
    """
    text = enforce_length(text)
    text = sanitize_html(text)
    text = strip_pii(text)
    is_suspicious = detect_prompt_injection(text)
    return text, is_suspicious
