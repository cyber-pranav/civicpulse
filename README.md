# CivicPulse - Hackathon Submission

## Overview

CivicPulse is a personalized, interactive Election Journey Orchestrator. It guides voters step-by-step from checking their eligibility to casting a mock vote, all in a secure, zero-PII manner.

The project aligns strictly with the hackathon requirements: it uses a lightweight frontend combined with a robust Python Stateful Backend. **The entire source repository is well under the 10MB limit.**

## Architecture & Approach

### 1. Dynamic Single-Page Application (SPA) - Frontend
We converted the static UI/UX designs into a dynamic SPA using **Alpine.js** and **Tailwind CSS**. 
- **Lightweight Framework**: Alpine.js was chosen to eliminate complex build steps and keep the frontend incredibly small (no `node_modules` required for the client).
- **Responsive & Accessible**: The UI seamlessly adapts to mobile and desktop screens. It integrates accessibility features like High Contrast Mode and Voice Assist (via the Web Speech API).
- **State-Driven Rendering**: The UI updates dynamically based on the state returned by the backend. The Vertical Progress Stepper is bound to the `journey_state` machine.

### 2. Python Stateful Backend - Logic
The backend is built with **FastAPI** to serve both the REST API and the static frontend assets.
- **State Machine Architecture**: A strict linear sequence of states (e.g., `UNINITIALIZED` -> `ELIGIBILITY_CHECK` -> `REGISTRATION_VERIFIED` -> `CANDIDATE_RESEARCH` -> `POLLING_SIMULATION` -> `POLLING_READY`) ensures the user's journey is tracked reliably without skipping steps.
- **Zero-PII Storage**: All user data (age, location, etc.) is held securely in an ephemeral in-memory session store (`_sessions` dict). No personal information is ever persisted to a database, ensuring maximum privacy and compliance.

### 3. Google Services Integration

The project successfully wires Google Services to enhance the user experience:
- **Civic Information API**: Used to fetch the official candidate list based on the user's location. When the Onboarding form is submitted, the backend fetches dynamic candidate cards to replace static mock data in the "Candidate Compare" view.
- **Google Maps Links**: After successfully retrieving the polling station location from the Civic API, the backend generates a direct Google Maps deep link. This deep link powers the "Booth Checklist & Routing" section so the voter can easily navigate to the booth.
- **Calendar API**: Deep-links are exposed to set Google Calendar reminders for key election dates (like Polling Day and Counting Day).

## Feature Logic Integrations

- **Jargon-Killer**: All complex terminologies across the app are wrapped in a hoverable UI component, providing a simplified explanation mapped from a backend glossary (e.g. replacing "Constituency" with "your voting area").
- **EVM Simulator**: The interactive Electronic Voting Machine (EVM) allows voters to safely practice casting a mock vote. It triggers visual feedback, auditory confirmation (a beep sound using the Web Audio API), and displays a 7-second VVPAT (Voter Verifiable Paper Audit Trail) slip animation for realistic verification.
- **Urgency Alerts**: The system calculates deadlines against the current date (April 28, 2026). If a voter's location is "West Bengal", a pulsing red "Verify Registration" alert triggers to emphasize the phase's urgency.

## Run Locally

1. Create a virtual environment and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
3. Visit `http://127.0.0.1:8000` in your web browser.

## Directory Structure

```
.
├── backend/
│   ├── logic/          # Core state machine & session manager
│   ├── services/       # Google Civic, Maps & Calendar APIs wrappers
│   ├── utils/          # Formatting, sanitization, jargon dictionaries
│   └── main.py         # FastAPI application and route definitions
├── frontend/
│   ├── app.js          # Alpine.js logic & interactions
│   └── index.html      # Consolidated UI components
├── README.md           # Project documentation
└── requirements.txt    # Python dependencies
```
