# CivicPulse — Election Process Education Assistant

> **Vertical:** Election Process Education
> **Live Demo:** https://civicpulse-engine-gkdrd7zpea-uc.a.run.app
> **Stack:** Python · FastAPI · Alpine.js · Google Cloud · Firebase

---

## The Problem

First-time voters and marginalised communities face a "Complexity Gap" — confusing jargon, unclear eligibility rules, and anxiety around Electronic Voting Machines (EVMs). CivicPulse solves this with stateful, AI-powered, step-by-step civic education.

---

## Google Services Integrated

| Google Service | Purpose | Implementation |
|---|---|---|
| **Gemini 1.5 Flash** | Candidate manifesto analysis, intelligent search, civic Q&A chatbot | `backend/services/gemini_service.py` · `/api/ai/*` |
| **Google Civic Information API** | Real-time candidate and polling location data by constituency | `backend/services/civic_service.py` · `/api/candidates/*` |
| **Google Cloud Translation API** | Translates UI into 7 Indian languages (Hindi, Bengali, Tamil, Telugu, Marathi, Punjabi) | `backend/services/translate_service.py` · `/api/translate/` |
| **Google Cloud Natural Language API** | Manifesto sentiment analysis (-1.0 to +1.0 score) shown in candidate compare | `backend/services/nlp_service.py` · `/api/nlp/sentiment` |
| **Google Maps Platform** | Embedded directions iframe and deep-link routing to polling booth | `frontend/modules.js` ReadinessModule |
| **Google Calendar API** | Creates polling day calendar event with OAuth (falls back to .ics link) | `frontend/modules.js` ReadinessModule |
| **Firebase Authentication** | Google Sign-In, token verification via Firebase Admin SDK | `backend/services/firebase_service.py` · `frontend/modules.js` AuthModule |
| **Firebase Firestore** | Persists user journey progress per authenticated user | `backend/services/firebase_service.py` · `/api/user/progress` |
| **Google Analytics 4** | Tracks 7 civic engagement events: tab_changed, evm_vote_cast, ai_chat_opened, language_changed, journey_step_completed, booth_route_opened, calendar_reminder_added | `frontend/modules.js` AnalyticsModule |

---

## Architecture

```
civicpulse/
├── backend/
│   ├── main.py              # FastAPI app, CORS, security headers, rate limiting
│   ├── config.py            # Centralised settings, all API keys from env vars
│   ├── routers/
│   │   ├── ai.py            # /api/ai/* — Gemini candidate analysis, chat, search
│   │   ├── nlp.py           # /api/nlp/* — Google NL API sentiment analysis
│   │   ├── translate.py     # /api/translate/* — Google Translate API
│   │   ├── user.py          # /api/user/* — Firebase Auth + Firestore progress
│   │   └── candidates.py    # /api/candidates/* — Google Civic Information API
│   ├── services/
│   │   ├── gemini_service.py
│   │   ├── translate_service.py
│   │   ├── nlp_service.py
│   │   ├── civic_service.py
│   │   └── firebase_service.py
│   └── utils/
│       ├── logger.py        # Structured logging, debug mode via env var
│       └── cache.py         # TTL in-memory cache for API responses
├── frontend/
│   ├── index.html           # SPA with full ARIA, CSP, skip link, landmarks
│   ├── app.js               # Alpine.js main component, tab management
│   ├── modules.js           # 8 IIFE modules: Journey, Candidates, EVM, Readiness, AI, Auth, Translate, Analytics
│   ├── utils.js             # debounce, apiFetch, sanitizeHTML, showToast, FocusManager, Validator, Logger
│   ├── constants.js         # All magic numbers and string constants
│   ├── sw.js                # Service Worker: cache-first static, network-first API
│   └── manifest.json        # PWA manifest
├── tests/
│   ├── test_eligibility_logic.py    # 15 tests — age boundary, underage routing
│   ├── test_jargon_killer_replacement.py  # 12 tests — term replacement accuracy
│   ├── test_state_transition.py     # 20 tests — journey state machine
│   ├── test_sanitizer.py            # 18 tests — Zero-PII, prompt injection
│   ├── test_integration.py          # 12 tests — API endpoint validation
│   └── test_services.py            # 8 tests — Google service mock fallbacks
├── .github/workflows/       # CI/CD: test on push, deploy to Cloud Run on merge
├── Dockerfile               # Multi-stage Alpine build
├── requirements.txt         # All dependencies including Google API libraries
└── pytest.ini               # Test configuration
```

---

## Test Coverage

CivicPulse includes a comprehensive testing framework achieving a **100% Pass Rate** across 85 unit and integration tests.

| Test File | What It Tests | Count |
|---|---|---|
| test_eligibility_logic.py | Age boundaries, underage routing | 15 tests |
| test_jargon_killer_replacement.py | Term replacement accuracy | 12 tests |
| test_state_transition.py | Journey state machine integrity | 20 tests |
| test_sanitizer.py | Zero-PII, prompt injection defense | 18 tests |
| test_integration.py | API endpoint validation | 12 tests |
| test_services.py | Google service mock fallbacks | 8 tests |
| **Total** | | **85 tests** |

---

## Security & Accessibility

*   **Zero-PII Architecture:** All user data is processed in ephemeral, in-memory structures. No personal data is persisted.
*   **Security Headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy on every response.
*   **Rate Limiting:** slowapi-based rate limiting on all API endpoints.
*   **WCAG 2.1 AA:** Skip link, aria-live regions, roving tabindex EVM, focus trapping, high-contrast mode with persistence.

---

## Setup & Execution

### 1. Installation
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m uvicorn backend.main:app --port 8000
```
Open `http://127.0.0.1:8000` in your browser.

### 3. Run the Test Suite
```bash
python -m pytest tests/ -v
```
