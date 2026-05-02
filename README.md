# CivicPulse — Election Journey Orchestrator

**Vertical:** Election Process Education

CivicPulse is a personalized, interactive Election Journey Orchestrator designed to prepare voters for Election Day. Our mission is to demystify the democratic process by guiding users step-by-step through a secure, comprehensive, and highly accessible readiness trail.

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

CivicPulse deeply integrates Google Services to provide dynamic, location-aware, and actionable intelligence:

*   **Google Civic Information API:** We fetch real-time candidate data, manifestos, and precise polling locations based dynamically on the user's registered district, rather than relying on hardcoded lists.
*   **Google Maps Platform:** We utilize dynamic routing logic to calculate the fastest path to the user's specific polling station. The "Booth Route" feature generates precise deep-links to navigate users exactly to their assigned booth's latitude/longitude.
*   **Google Calendar API:** An automated 'Remind Me' feature that generates `.ics` blobs and deep-links for critical milestones, including Voter Registration deadlines, Polling Day, and Counting Day, ensuring users never miss a civic duty.

---

## Testing & Validation

CivicPulse includes a comprehensive testing framework achieving a **100% Pass Rate** across 85 unit and integration tests.

**Contents of the `/tests` folder:**
*   `test_eligibility_logic.py`: Validates age boundary conditions, underage redirection to Civic Education, and urgent context routing.
*   `test_jargon_killer_replacement.py`: Asserts case-preserving, multi-word exact replacements of complex terminology.
*   `test_state_transition.py`: Proves the bulletproof integrity of the Journey Trail state machine, ensuring users cannot skip critical educational steps.
*   `test_sanitizer.py`: Validates Zero-PII compliance and prompt-injection defense.
*   `test_integration.py` & `test_services.py`: Tests the API endpoints and Google service mock fallbacks.

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
