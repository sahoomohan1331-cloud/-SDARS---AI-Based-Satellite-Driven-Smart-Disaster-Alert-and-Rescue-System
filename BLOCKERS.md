# SDARS Technical & Data Blockers Log

In accordance with SDARS Scientific Integrity Rule 3:
> *"If a data source is unavailable or labels for a hazard are too sparse, STOP and describe the problem in BLOCKERS.md. Do not substitute fake or proxy data silently."*

This file documents data unavailability, archived feed gaps, and technical constraints encountered in the historical pipeline.

---

## 1. Lightning Hazard Archive (v1 Deferred)

**Status:** BLOCKED / DEFERRED  
**Impacted Hazard:** Lightning (Hazard 6 of 8)  
**Date Logged:** 2026-10-24  

### Problem Description
Lightning (all 8 hazards, v1): no open, India-wide, hourly lightning archive is accessible. Blitzortung is volunteer-partial. Options for a future version: (a) pay for a commercial feed, (b) use IMD gridded lightning once available, (c) drop the hazard. Marking lightning as deferred for v1, not faked.

### Detail & Investigation
- Ground-based optical/RF detection networks such as Blitzortung rely on enthusiast stations and suffer from severe spatial bias and low detection efficiency across rural and coastal Odisha.
- Satellite optical lightning data (e.g. INSAT-3D/3DR Lightning Detection or MTG LI) is either not published in an open programmatic bulk archive for 1990–2024 or lacks verified ground calibration.
- Rather than training on synthetic lightning strikes or fabricating proxy labels, lightning hazard modeling is explicitly deferred in v1.

---

## 2. Convective Available Potential Energy (CAPE) in Open-Meteo ERA5

**Status:** SKIPPED / LOGGED  
**Impacted Variable:** Atmospheric Instability (`cape`)  
**Date Logged:** 2026-10-24  

### Problem Description
Open-Meteo Historical Weather API (`/v1/archive`) queries for variable `cape` return all `null` values across the entire Odisha bounding box (lat 17.8°N to 22.6°N, lon 81.3°E to 87.5°E) for ERA5 / ERA5-Land reanalysis.

### Resolution
In strict accordance with project rules against proxy or estimated substitutions, CAPE is omitted from the historical weather feature schema in `weather_6h.parquet` rather than substituting an arbitrary proxy. If thermodynamic soundings or regional mesoscale reanalysis (e.g. IMD NCUM reanalysis) become programmatically accessible, convective instability metrics will be incorporated.
