# CivicPulse — Election Journey Orchestrator

> **Vertical:** Election Process Education  
> **Live Deployment:** [CivicPulse on Google Cloud Run](https://civicpulse-engine-gkdrd7zpea-uc.a.run.app)

---

## The Problem & Solution

**The Complexity Gap:** Elections are fundamental to democracy, but first-time voters and marginalized communities often face a "Complexity Gap" — confusing bureaucratic jargon, unclear eligibility rules, and anxiety around the physical act of voting using Electronic Voting Machines (EVMs). 

**Our Solution:** CivicPulse uses **Stateful Orchestration** to solve this gap. Instead of overwhelming the user with a static wall of information, the application intelligently tailors the educational journey based on the user's specific state (age, location, and progress). It converts a stressful bureaucratic maze into a clear, guided, step-by-step trail.

---

## Core Features (The 'Edge')

### 1. The Journey Trail
At the core of CivicPulse is a strict **state-machine logic** that guides users progressively:
*   **Eligibility & Onboarding:** Calculates eligibility dynamically. Underage users are securely diverted to a "Civic Education" node, while eligible users proceed.
*   **Registration Verification:** Guides users to confirm their status on the electoral roll.
*   **Candidate Research & Polling:** Progressively unlocks candidate profiles and EVM simulation.

### 2. Jargon-Killer
A built-in **NLP-lite layer** that acts as a real-time translator for government terminology. It automatically detects confusing bureaucratic terms (e.g., "Constituency", "VVPAT", "Electoral Roll") and overlays them with simplified, easily understood language ("your voting area", "official voter list"), maintaining contextual integrity while drastically improving comprehension.

### 3. Interactive EVM Simulator
A secure, non-recording mock-voting environment that allows users to practice casting a vote. It accurately mimics the interface of a real EVM and features a realistic, 7-second **VVPAT slip animation**, visually confirming the vote and building voter confidence prior to election day.

---

## Meaningful Google Services Integration

| Google Service | How It's Used | Where in Code |
|---|---|---|
| Google Civic Information API | Fetches real-time candidate data and polling locations by district | CandidatesModule, /api/candidates endpoint |
| Google Maps Platform | Calculates and deep-links route to user's polling booth | ReadinessModule, booth-routing feature |
| Google Calendar API | Creates .ics reminders for polling day and counting day | ReadinessModule, calendar-reminder feature |
| Gemini 1.5 Flash | Powers AI candidate insight cards and intelligent search | AIModule, CandidatesModule |
| Firebase Authentication | Google Sign-In for progress persistence | AuthModule |
| Google Analytics 4 | Tracks 7 custom civic engagement events | AnalyticsModule |
| Google Translate API | Translates UI into 7 Indian languages | TranslateModule |

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

*   **Zero-PII Architecture:** CivicPulse strictly adheres to Zero-PII principles. All user data (age, location) is processed entirely in ephemeral, in-memory structures (`_sessions`). No personal data is ever persisted to a database or written to disk.
*   **A11y Compliance:** The platform is engineered for maximum accessibility, featuring a High-Contrast mode toggle, native Voice-Assist integration via the Web Speech API, and fully semantic HTML for screen-reader compatibility.

---

## Tech Stack

*   **Backend:** Python (FastAPI / LangGraph)
*   **Frontend:** React / Vite / Tailwind CSS
*   **Cloud & APIs:** Google Cloud SDK

---

## Setup & Execution

### 1. Installation
Clone the repository and install the lightweight requirements:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Application
Start the FastAPI server. The app runs locally on port 8000:
```bash
python -m uvicorn backend.main:app --port 8000
```
Open `http://127.0.0.1:8000` in your browser.

### 3. Run the Test Suite
Execute the full test suite with Pytest to verify 100% compliance:
```bash
python -m pytest tests/ -v
```
