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
```text
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
│   └── test_services.py             # 8 tests — Google service mock fallbacks
├── .github/workflows/       # CI/CD: test on push, deploy to Cloud Run on merge
├── Dockerfile               # Multi-stage Alpine build
├── requirements.txt         # All dependencies including Google API libraries
└── pytest.ini               # Test configuration
```

---

## Testing — 85 Tests, 100% Pass Rate

| Test File | Coverage | Tests |
|---|---|---|
| `test_eligibility_logic.py` | Age boundaries, underage → Civic Education routing, first-time voter path | 15 |
| `test_jargon_killer_replacement.py` | Case-preserving multi-word term replacement, edge cases | 12 |
| `test_state_transition.py` | Journey state machine integrity, step-skip prevention | 20 |
| `test_sanitizer.py` | Zero-PII compliance, bleach sanitization, prompt injection defence | 18 |
| `test_integration.py` | All API endpoint status codes, request validation, error responses | 12 |
| `test_services.py` | Google service mock fallbacks, cache hit/miss behaviour | 8 |
| **Total** | | **85** |

Run tests: `python -m pytest tests/ -v`

---

## Security

- **Zero-PII Architecture** — all user data processed in ephemeral `_sessions`, never persisted to disk
- **bleach sanitization** — all user input sanitised before processing (`backend/utils/` + frontend `sanitizeHTML()`)
- **Rate limiting** — `slowapi` limits all API endpoints to 60 req/min per IP
- **Firebase token verification** — every authenticated route verifies JWT via Firebase Admin SDK
- **Security headers** — `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy` on every response
- **Content Security Policy** — CSP meta tag in `index.html` restricts script/style sources
- **No hardcoded secrets** — all API keys in environment variables via `backend/config.py`

---

## Accessibility

- Skip-to-main-content link as first body element
- Full landmark structure: `<header>`, `<nav aria-label>`, `<main id="main-content">`, `<footer>`
- EVM ballot implements WCAG roving tabindex radio group (ArrowUp/Down/Home/End)
- `aria-live="polite"` on VVPAT result area for screen reader announcements
- Focus trap in AI chat drawer via `FocusManager.trap()`
- `aria-hidden="true"` on all decorative icons
- High-contrast mode toggle persisted in `localStorage`
- `lang` attribute on `<html>` updates dynamically on language change
- All form inputs have explicit `<label>`, `aria-required`, `aria-describedby`
- `:focus-visible` outline on all interactive elements

---

## Performance

- Service Worker with cache-first (static) and network-first (API) strategies
- Lazy tab rendering — only Journey tab renders on initial load
- `sessionStorage` caches all API responses client-side
- TTL in-memory cache (`cachetools`) prevents redundant Google API calls server-side
- All inputs debounced 300ms via shared `debounce()` utility
- Multi-stage Alpine Docker build minimises image size
- `dns-prefetch` and `preconnect` hints for all external domains
- JSON-LD structured data for search engine discoverability
- PWA manifest for installability

---

## Setup

```bash
# Clone and install
git clone https://github.com/cyber-pranav/civicpulse.git
cd civicpulse
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add: GEMINI_API_KEY, GOOGLE_API_KEY, FIREBASE_CREDENTIALS_PATH

# Run locally
uvicorn backend.main:app --port 8000

# Run tests
python -m pytest tests/ -v
```

---

## Built For
HacSkill Virtual PromptWars — Election Process Education vertical
