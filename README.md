# NavCare - Hospital Digital Wayfinding Platform

A digital wayfinding platform that allows patients to scan a QR code inside a hospital, select or speak their destination, and receive an indoor route on their phone without installing an app.

## Project Architecture

This is a monorepo consisting of:
- `frontend/`: React + Vite + Tailwind CSS for the user-facing web app.
- `backend/`: FastAPI + Python for the routing engine and API.
- `data/`: Contains hospital maps and seed data.
- `docs/`: Project documentation and architecture details.

## MVP Scope (Phase 1)
- One building, one floor graph navigation.
- Scan QR (simulated) -> type destination -> calculate A* / Dijkstra shortest route -> display route.

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

### Backend Setup
1. `cd backend`
2. `python -m venv .venv`
3. Activate virtual environment (`source .venv/bin/activate` or `.venv\Scripts\activate`)
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --reload`
