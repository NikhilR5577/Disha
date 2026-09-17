# NavCare Current Architecture

**Date Documented:** August 2026
**Status:** Public Prototype (Frozen) -> Transitioning to Private Platform

## 1. System Overview
NavCare is an indoor wayfinding system designed specifically for healthcare environments, offering step-by-step navigation, accessible (wheelchair) routing, and localized voice interaction.

## 2. Core Stack
* **Frontend:** React + Vite, deployed on Vercel (`navcare.vercel.app`).
* **Backend:** Python + FastAPI, deployed on Render.
* **Database:** SQLite (local DB file, to be migrated to PostgreSQL for multi-tenant scalability).

## 3. Key Technical Components

### A. The Navigation Engine (Backend)
* Uses Dijkstra's algorithm for shortest-path routing.
* Models the hospital as a weighted directional graph (`Nodes` and `Edges`).
* Uses a global cache (`_cached_graph`) with `threading.Lock` to ensure high-concurrency requests resolve instantly without repeatedly hitting the database.
* Computes dual-language (English + Hindi) turn-by-turn instructions dynamically based on vector paths (Straight, Left, Right).

### B. The Mapping UI (Frontend)
* Built using SVG overlays on top of rasterized floorplan images.
* Implements `react-zoom-pan-pinch` for responsive, mobile-first interaction (pinch-to-zoom, pan).
* Coordinate system is normalized (0-100 `viewBox`) ensuring that SVG nodes plot accurately regardless of the screen's aspect ratio.

### C. Voice Localization Engine
* Uses Web Speech API for voice-to-text recognition.
* Implements a dynamic language toggle (`hi-IN` vs `en-US`) to perfectly capture native speech without heavy cross-language distortion.
* Uses a custom dictionary and fuzzy-matching logic to map natural speech (e.g., "पर्ची", "Khoon", "ICU") to strict backend Node IDs.

### D. Physical-Digital Bridge (QR System)
* Translates physical world locations into digital states using parameterized URLs (e.g., `?start=reception`).
* Employs both native mobile camera scanning and a robust in-app `@yudiel/react-qr-scanner` fallback.

## 4. Current Limitations (To Solve in Stage 3)
* The database and routing logic currently assume a single institution (Sagar District Hospital).
* Node IDs are hardcoded conceptually to a single map overlay.
* Needs an abstraction layer to support `Institution -> Building -> Floor` hierarchy.
