# Design Standards: Anti-AI Visual Principles

Strict rules to eliminate all recognizable "AI-generated UI tells" across the codebase:

---

### Rule 1: No Gradient Text or Purple-to-Blue Gradients
- **The Tell**: Bold headlines with purple-to-blue gradient fills or full-background neon gradients.
- **The Rule**: Use flat, solid brand colors for text (e.g., `#F8FAFC`, `#00E5FF`). Gradients may only appear as subtle, single-pixel hairline borders or active indicator dots—never as body/heading text fills.
- **Color Palette**: Tactical aerospace & emergency rescue colors:
  - Backgrounds: Solid `#0B0F19`, `#111827`, `#161F30`
  - Text: Solid `#FFFFFF`, `#94A3B8`, `#64748B`
  - Accents: Precision Cyan (`#00E5FF`), Alert Crimson (`#EF4444`), Status Amber (`#F59E0B`), Safe Emerald (`#10B981`)

---

### Rule 2: Break Centered-Hero & 3-Card Skeletons
- **The Tell**: Centered hero heading + single CTA + 3 identical cards in a row.
- **The Rule**: Use intentional asymmetry:
  - Left-aligned tactical telemetry headers.
  - Asymmetric card hierarchy: 1 primary hero monitor (lead) + unequal telemetry chips (supporting).
  - Varied grid spans (e.g., 2fr / 1fr splits, timeline feeds, horizontal micro-scrolls).

---

### Rule 3: Visual Hierarchy Over Identical Cards
- **The Tell**: Identical border-radius, identical padding, and identical card heights everywhere making views feel flat.
- **The Rule**: Differentiate by information importance:
  - Primary threat cards get prominent stature, distinct border treatments, and tighter inner telemetry grids.
  - Micro-actions and filters stay compact and subordinate.
  - Spacing scales proportionally with element density.

---

### Rule 4: Real Vector Icons (Lucide / SVG), Never Emojis as Icons
- **The Tell**: Emojis used as UI icons (render differently per OS, look like cartoon prototypes).
- **The Rule**: Use Lucide icons or crisp inline SVGs with consistent stroke-width (1.75px–2px), uniform sizing (16px, 20px, 24px), and muted monochrome or purposeful semantic color fills.

---

### Rule 5: Type Personality & Font Pairing
- **The Tell**: Generic `Inter` applied uniformly to everything.
- **The Rule**: Pair typefaces purposefully:
  - **Headings & Display**: `Plus Jakarta Sans` or `Space Grotesk` (clean, technical, authoritative).
  - **Body & Controls**: `Inter` (neutral, legible at small sizes).
  - **Telemetry & Coordinates**: `JetBrains Mono` (tabular, precise).

---

### Rule 6: Purposeful Motion, No Unprompted Neon Glows
- **The Tell**: Uncontrolled 50px neon blurs and box-shadow glows; instant jarring hover snaps.
- **The Rule**:
  - Remove bloated neon box-shadows. Use subtle, crisp hairline borders (`1px solid rgba(255, 255, 255, 0.08)`).
  - Add smooth cubic-bezier transitions (`cubic-bezier(0.16, 1, 0.3, 1)`) on interactive states with slight scale (e.g., `active: scale(0.98)`).
