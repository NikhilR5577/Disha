# NavCare Intellectual Property (IP) Inventory

**Date Documented:** August 2026

## 1. Trade Secrets (Confidential Know-How)
* **Voice-to-Node Dictionary Mapping Algorithm**: The specific fuzzy-matching dictionary and delay-based NLP workflow that accurately maps unstructured Indian accents (Hindi/English) via the Web Speech API into precise topological nodes without relying on expensive LLM calls.
* **Vector-based Turn Generation Logic**: The math inside `pathfinder.py` that computes angles between spatial coordinates (0-100 grid) to determine if a patient should turn "Left", "Right", or go "Straight" in dual languages dynamically based on their orientation.

## 2. Potential Patents (To Discuss with Patent Attorney)
* **System and Method for Hardware-less Indoor Healthcare Navigation**: Our method of using purely URL-parameterized static QR codes (`?start=loc_id`) combined with a web-based client (no app store download) to initialize location, combined with accessible (wheelchair) edge-routing in a directional graph.

## 3. Copyrights
* **Source Code**: The complete contents of the NavCare frontend (React/Vite) and backend (FastAPI/Python) repositories.
* **UI/UX Design**: The mobile-first "Bottom Sheet" mapping layout and Floating Action Button (FAB) configuration designed for intuitive hospital navigation.

## 4. Trademarks
* **"NavCare"**: The brand name for the platform.

## 5. Public Disclosures (Prior to Going Private)
* **GitHub Repository**: The code was briefly public on GitHub under `NikhilR5577/NavCare` before being restricted to Private in August 2026.
* **Deployed Endpoints**: The frontend was publicly accessible at `navcare.vercel.app` and backend at Render.

*Note: Proceeding with Stage 2 Prior-Art research before adding any further novel mechanisms.*
