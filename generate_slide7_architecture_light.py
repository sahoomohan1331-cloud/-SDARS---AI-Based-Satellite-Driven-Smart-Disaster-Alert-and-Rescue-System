import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import textwrap
import os

def render_light_architecture():
    out_path = r'd:\SDARS map\sdars_slide7_architecture_light.png'
    os.makedirs(r'd:\SDARS map', exist_ok=True)

    # 16:9 widescreen canvas (16 x 9 inches @ 150 dpi = 2400 x 1350 px)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    FONT_FAMILY = 'Segoe UI'

    # Main Header
    ax.text(8.0, 8.55, "SDARS: 4-Tier Enterprise System Architecture", 
            ha='center', va='center', fontsize=23, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY)
    ax.text(8.0, 8.16, "Satellite-Driven Smart Disaster Alert & Rescue System  --  Scalable Asynchronous Architecture", 
            ha='center', va='center', fontsize=12.0, color='#475569', fontfamily=FONT_FAMILY)

    tiers = [
        {
            "tier_num": "TIER 4",
            "tier_name": "TACTICAL CLIENT & COMMAND INTERFACE",
            "badge_color": "#DC2626",
            "y": 6.35,
            "h": 1.55,
            "modules": [
                ("3D Planetary War Room", "CesiumJS WebGL globe, orbital satellite passes, volumetric hazard pillars & DEM flood models."),
                ("2D Command Radar", "Leaflet GIS with real-time hazard isochrone buffers, heatmaps & shelter status updates."),
                ("Safe Evacuation Portal", "Turn-by-turn mobile navigation bypassing hazard zones to reach nearest open hospitals."),
                ("Emergency Dispatch Daemon", "Automated TLS emergency email alerts, siren broadcasts & rescue fleet dispatch.")
            ]
        },
        {
            "tier_num": "TIER 3",
            "tier_name": "AI INFERENCE & SPATIAL REASONING",
            "badge_color": "#0D9488",
            "y": 4.45,
            "h": 1.55,
            "modules": [
                ("Random Forest Ensemble", "Multi-class classification covering Floods, Wildfires, Cyclones, Quakes & Landslides."),
                ("Calibrated Risk Scorer", "Dynamic severity index (Low to Critical) fused with real-time crowd verification."),
                ("Explainable AI (XAI)", "Feature contribution breakdown (Tree SHAP/Gini) for transparent command decisions."),
                ("OSRM Dijkstra Engine", "Topological road graph routing calculating shortest safe path avoiding hazard zones.")
            ]
        },
        {
            "tier_num": "TIER 2",
            "tier_name": "ASYNCHRONOUS BACKEND & GEODATABASE CORE",
            "badge_color": "#0284C7",
            "y": 2.55,
            "h": 1.55,
            "modules": [
                ("FastAPI Gateway", "High-throughput async REST endpoints & low-latency WebSocket event streaming (<400ms)."),
                ("Async Polling Workers", "Non-blocking background ingest schedulers managing external API rate limits & timeouts."),
                ("GeoJSON Transformer", "Coordinate reprojection (EPSG:4326), spatial filtering, clipping & schema validation."),
                ("Spatial Geodatabase", "SQLAlchemy ORM with SQLite / PostGIS spatial indexing & event audit trail.")
            ]
        },
        {
            "tier_num": "TIER 1",
            "tier_name": "MULTI-MODAL DATA INGESTION LAYER",
            "badge_color": "#4F46E5",
            "y": 0.65,
            "h": 1.55,
            "modules": [
                ("NASA GIBS / MODIS", "Thermal radiance flux, Land Surface Temperature (LST) & active wildfire hotspots."),
                ("NASA EONET & USGS", "Global natural event coordinates, seismic hypocenter telemetry & magnitude feeds."),
                ("Open-Meteo & NOAA", "1km atmospheric physics: wind vectors, barometric plunge, precipitation & DEM."),
                ("OSM & Field Reports", "OpenStreetMap road network, critical hospital GIS & geo-tagged citizen SOS reports.")
            ]
        }
    ]

    tier_x = 0.6
    tier_w = 14.8

    for t in tiers:
        ty = t["y"]
        th = t["h"]
        col = t["badge_color"]

        # Subtle Drop Shadow
        shadow = patches.FancyBboxPatch((tier_x + 0.04, ty - 0.03), tier_w, th,
                                        boxstyle="round,pad=0.06,rounding_size=0.16",
                                        facecolor='#E2E8F0', edgecolor='none', alpha=0.5)
        ax.add_patch(shadow)

        # Outer Tier Container (Soft Off-White with Subtle Accent Border)
        container = patches.FancyBboxPatch((tier_x, ty), tier_w, th,
                                          boxstyle="round,pad=0.06,rounding_size=0.16",
                                          facecolor='#F8FAFC', edgecolor=col,
                                          linewidth=1.5, alpha=1.0)
        ax.add_patch(container)

        # Tier Header Badge on Left
        badge_w = 2.4
        badge = patches.FancyBboxPatch((tier_x + 0.15, ty + 0.15), badge_w, th - 0.3,
                                      boxstyle="round,pad=0.04,rounding_size=0.12",
                                      facecolor=col, edgecolor='none', alpha=1.0)
        ax.add_patch(badge)

        # White Text in Tier Badge
        ax.text(tier_x + 0.15 + badge_w/2, ty + th/2 + 0.25, t["tier_num"],
                ha='center', va='center', fontsize=13.5, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY)
        
        words = t["tier_name"].split(" ")
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        ax.text(tier_x + 0.15 + badge_w/2, ty + th/2 - 0.07, line1,
                ha='center', va='center', fontsize=9.2, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY)
        ax.text(tier_x + 0.15 + badge_w/2, ty + th/2 - 0.33, line2,
                ha='center', va='center', fontsize=9.2, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY)

        # 4 Sub-module cards per tier
        mod_x_start = tier_x + badge_w + 0.35
        mod_w = (tier_w - badge_w - 0.7) / 4.0
        
        for m_idx, (m_title, m_desc) in enumerate(t["modules"]):
            mx = mod_x_start + m_idx * mod_w + 0.06
            mw = mod_w - 0.12
            my = ty + 0.12
            mh = th - 0.24

            m_card = patches.FancyBboxPatch((mx, my), mw, mh,
                                           boxstyle="round,pad=0.04,rounding_size=0.10",
                                           facecolor='#FFFFFF', edgecolor='#CBD5E1',
                                           linewidth=1.2, alpha=1.0)
            ax.add_patch(m_card)

            # Module Title (Corporate Navy/Accent, bold)
            ax.text(mx + mw/2, my + mh - 0.26, m_title,
                    ha='center', va='center', fontsize=10.0, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY)
            
            # Divider line inside module card
            ax.plot([mx + 0.15, mx + mw - 0.15], [my + mh - 0.44, my + mh - 0.44], color='#E2E8F0', lw=1.0)

            # Wrapped Module Description: Dark Slate (#334155), clean wrapping
            wrapped_desc = textwrap.fill(m_desc, width=25)
            ax.text(mx + mw/2, my + (mh - 0.46)/2, wrapped_desc,
                    ha='center', va='center', fontsize=8.8, color='#334155', fontfamily=FONT_FAMILY,
                    linespacing=1.2)

    # Draw Data Flow Connectors Between Tiers with protocols
    connectors = [
        (0.65 + 1.55, 2.55, "Raw Telemetry & GeoJSON Feeds (REST / HTTPS / WMS)", "#4F46E5"),
        (2.55 + 1.55, 4.45, "Cleaned Feature Vectors & Coordinate Bounding Boxes", "#0284C7"),
        (4.45 + 1.55, 6.35, "Severity Scores (0-100), Danger Isochrones & Dijkstra Routes (WebSockets)", "#0D9488")
    ]

    for y_bottom, y_top, label, conn_col in connectors:
        arrow_y_start = y_bottom
        arrow_y_end = y_top
        
        # Left and Right vertical data flow arrows
        for arrow_x in [3.4, 7.2, 11.0, 14.8]:
            arrow = FancyArrowPatch((arrow_x, arrow_y_start), (arrow_x, arrow_y_end),
                                    arrowstyle='<->', mutation_scale=12,
                                    color=conn_col, lw=2.0, linestyle='--')
            ax.add_patch(arrow)

        # Center label pill for protocol
        pill_w = 7.6
        pill_h = 0.28
        pill_x = 8.0 - pill_w/2
        pill_y = (arrow_y_start + arrow_y_end)/2 - pill_h/2
        
        pill = patches.FancyBboxPatch((pill_x, pill_y), pill_w, pill_h,
                                     boxstyle="round,pad=0.02,rounding_size=0.08",
                                     facecolor='#FFFFFF', edgecolor=conn_col,
                                     linewidth=1.4, alpha=1.0)
        ax.add_patch(pill)
        ax.text(8.0, (arrow_y_start + arrow_y_end)/2, f">> {label}",
                ha='center', va='center', fontsize=8.2, fontweight='bold', color=conn_col, fontfamily=FONT_FAMILY)

    # Footer metrics bar
    ax.text(8.0, 0.22, "Enterprise Specs: <400ms Pipeline Latency  *  99.98% High-Availability Asynchronous Architecture  *  Decoupled Modularity",
            ha='center', va='center', fontsize=9.8, fontweight='bold', color='#64748B', fontfamily=FONT_FAMILY)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='#FFFFFF')
    plt.close()
    print(f"SUCCESS: Generated {out_path}")

if __name__ == '__main__':
    render_light_architecture()
