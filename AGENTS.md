# SDARS Project Standards & Rules

## 1. UI Design Principles (Strict Anti-AI Visual Standards)
All user interfaces created or modified in this repository must actively avoid recognizable "AI-generated design tells":

1. **No Gradient Hero / Button Text**:
   - Use flat, solid brand colors for headlines (`#F8FAFC`, `#FFFFFF`).
   - Eliminate the default purple-to-blue AI gradient (`#6366f1` to `#a855f7`).
   - Use solid brand colors (Tactical Cyan `#00E5FF`, Dark Titanium `#0F172A`, Alert Red `#EF4444`).

2. **No Centered-Hero + 3-Cards Skeleton**:
   - Left-align heroes and headers.
   - Use intentional asymmetry: 1 dominant lead monitor card with unequal supporting metrics.

3. **True Visual Hierarchy**:
   - Vary card sizes, padding, and corner radius based on content priority.
   - Never use identical heights, padding, or radiuses across every card.

4. **Vector Icons Only (Lucide / SVG) — Never Emojis as Icons**:
   - Emojis render inconsistently across Android, iOS, and desktop browsers and signal an AI prototype.
   - Use consistent vector icon libraries (Lucide / SVGs) with shared stroke-width and styling.

5. **Distinct Typography Pairing**:
   - Display & Headings: `Plus Jakarta Sans` or `Space Grotesk` (technical, authoritative).
   - Body & Controls: `Inter`.
   - Data & Coordinates: `JetBrains Mono`.

6. **Subtle Purposeful Motion — No Unprompted Neon Glows**:
   - Remove bloated 50px neon box-shadows. Use clean 1px hairline borders (`rgba(255, 255, 255, 0.08)`).
   - Add purposeful, subtle easing (`cubic-bezier(0.16, 1, 0.3, 1)`).

---

## 2. Architecture & Networking Rules
- Never rely solely on client-side `navigator.geolocation` over insecure LAN HTTP origins (`http://192.168.x.x`). Always bridge through native Expo location or provide server-side IP fallback (`/api/geolocation/detect`).
- Keep backend processes, models, and endpoints robust with fallback timeouts.

---

## 3. Scientific Integrity Rules
1. **Never fabricate, estimate, or hardcode metrics, accuracy, or performance numbers.** Every number in docs must come from a script that writes it to `reports/metrics.json`.
2. **Never train or evaluate models on synthetic data.** Synthetic data is allowed only in `tests/fixtures/` for pipeline smoke tests.
3. **If a data source is unavailable or labels for a hazard are too sparse, STOP and describe the problem in `BLOCKERS.md`.** Do not substitute fake or proxy data silently.
4. **All train/test splits must be temporal** (train on earlier years, test on later years). No random splits.
5. **Features at time t may only use information available at or before t.** Every feature needs a leakage test.
6. **Report PR-AUC, recall, precision, false-alarm rate, and Brier score per hazard.** Never report plain accuracy as a headline metric.
7. **If a hazard performs poorly, label it "experimental" in docs and UI.** Do not hide it.
8. **Docs must match code.** Remove any claim that is not implemented.
