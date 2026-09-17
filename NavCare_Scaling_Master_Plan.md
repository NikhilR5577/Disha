# NavCare Scaling Master Plan
## Transitioning from a Single Project to an Enterprise SaaS

This document outlines the complete architectural roadmap for scaling NavCare to support 100+ hospitals simultaneously while maintaining high performance and minimizing operational costs.

---

## Phase 1: The Developer Tool (mapper.exe)
To onboard new hospitals quickly, the manual database entry process will be replaced with a proprietary desktop application.

**Architecture:** Electron.js + React (Vite) + Local SQLite
**Key Features:**
1. **Multi-Floor Support:** Upload multiple SVG maps and link them using "Elevator/Stairs" nodes.
2. **Smart Mapping:** Figma-style smart snapping for exact X/Y alignment and arrow-key nudging.
3. **Advanced Routing Data:** 
   - Enforce 90-degree paths to prevent visual clipping.
   - **Wheelchair Tagging:** Mark specific paths as accessible/inaccessible.
   - **Path Penalties:** Apply 10x distance weights to force the algorithm to avoid restricted or narrow hallways.
4. **Auto-Save & Preview:** Real-time autosave to `navcare.db` and a fast "Test Route" blue-dot preview.

---

## Phase 2: Multi-Tenant Cloud Architecture
Instead of deploying separate servers for every hospital, NavCare will operate on a single, highly efficient SaaS architecture.

**The Multi-Tenant Model:**
- **Single Database:** Every table gets a `hospital_id` column.
- **Dynamic Frontend:** QR codes use URLs like `app.navcare.in/?hospital=apollo&node=uuid-123`. The frontend dynamically fetches Apollo's SVG and branding.
- **Physical QR Strategy:** QR codes will embed UUIDs (not room names). If a hospital renames or moves a room, the physical acrylic board remains the same; only the backend database is updated.

---

## Phase 3: Infrastructure & Hosting
You mentioned Google Servers (GCP). While Google Cloud Run and Cloud SQL are excellent enterprise options, they can be complex and expensive for startups. Here is the recommended cost-optimized stack:

### 1. Frontend (The Map UI)
- **Provider:** Cloudflare Pages (or Vercel, but Cloudflare is recommended for scale).
- **Cost:** $0 (Free Tier includes unlimited bandwidth, perfect for heavy SVG files).
- **Offline Strategy:** Implement as a PWA (Progressive Web App). Once a patient scans the first code, the map caches locally. This prevents "Dead Zone" loading failures deep inside hospital walls.

### 2. Backend (The Routing Engine)
- **Provider:** Render (Standard Tier) OR Google Cloud Run.
- **Cost:** ~$15 to $25 / month.
- **Optimization:** Implement **Redis Caching**. Instead of computing the A* shortest path for every user, the backend calculates it once and caches it. A $15 server can easily handle 50,000+ users a day with Redis.

### 3. Database (Analytics & Graph Data)
- **Provider:** Neon (Serverless Postgres) or Supabase.
- **Cost:** ~$20 to $25 / month.
- **Optimization:** Separate analytics writing from map reading. Batch visitor analytics in memory and write to the database every 5 minutes to prevent database locking.

---

## Summary of Economics (At 100 Hospitals)
- **Total Server Costs:** ~$40 to $50 / month.
- **Revenue Potential:** At ₹10,000/year per hospital (AMC) = ₹10,00,000/year (~₹83,000/month).
- **Profit Margin:** ~95%. The SaaS model allows near-infinite scaling with minimal overhead.
