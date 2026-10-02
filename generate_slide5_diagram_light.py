import matplotlib.pyplot as plt
import matplotlib.patches as patches
import textwrap
import os

def render_light_process_flow():
    out_path = r'd:\SDARS map\sdars_slide5_process_flow_light.png'
    os.makedirs(r'd:\SDARS map', exist_ok=True)

    # 16:9 widescreen canvas (16 x 9 inches @ 150 dpi = 2400 x 1350 px)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    FONT_FAMILY = 'Segoe UI'

    # Main Header (Executive Corporate Styling)
    ax.text(8.0, 8.45, "SDARS: Multi-Modal Operational Lifecycle & Process Flow", 
            ha='center', va='center', fontsize=22, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY)
    ax.text(8.0, 8.05, "Autonomous Pipeline: Real-Time Ingest  ->  Multi-Hazard AI  ->  Spatial Rescue Dispatch", 
            ha='center', va='center', fontsize=12.0, color='#475569', fontfamily=FONT_FAMILY)

    # 5 Stages
    stages = [
        ("STAGE 1", "DATA INGESTION", "#1D4ED8", [
            ("NASA GIBS / MODIS", "Thermal radiance flux & active wildfire hotspot detection"),
            ("NASA EONET 2.0", "Active global wildfire, storm & volcanic event tracker"),
            ("Open-Meteo High-Res", "1km atmospheric weather, wind vectors & elevation DEM"),
            ("USGS Earthquake API", "Global seismic telemetry feeds & hypocenter depths"),
            ("OpenStreetMap GIS", "Road transport network & emergency shelter facilities")
        ]),
        ("STAGE 2", "FEATURE EXTRACTION", "#0284C7", [
            ("Thermal Radiance", "Hotspot identification & radiance intensity metrics"),
            ("NDVI Moisture Index", "Vegetative drought indices & burn-scar progression"),
            ("Barometric Plunge", "Pressure drop rate calculation (delta P / delta t)"),
            ("Topographic DEM", "Elevation contour slope & drainage basin geometry"),
            ("Citizen Corroboration", "Crowdsourced geo-tagged ground observations")
        ]),
        ("STAGE 3", "AI & XAI INFERENCE", "#0D9488", [
            ("Random Forest Ensemble", "Multi-class classifier for 7 major disaster types"),
            ("Calibrated Risk Scorer", "Dynamic severity index rating (Low -> Critical)"),
            ("Explainable AI (XAI)", "Feature contribution breakdown (Tree SHAP/Gini)"),
            ("Confidence Scaling", "Boosts model certainty via ground report matching"),
            ("Threshold Trigger", "Automated alert state activation upon risk breach")
        ]),
        ("STAGE 4", "IMPACT MAPPING", "#D97706", [
            ("Dynamic Isochrones", "Calculates expanding hazard buffer perimeters"),
            ("Topographic Flood", "Simulates flood water inundation over DEM model"),
            ("Critical Road Overlay", "Cross-references submerged or blocked roads"),
            ("OSRM Dijkstra Engine", "Topological safe evacuation route computation"),
            ("Shelter Locator", "Discovers nearest operational hospital nodes")
        ]),
        ("STAGE 5", "RAPID DISPATCH", "#DC2626", [
            ("3D War Room Push", "Sub-second WebSockets to CesiumJS globe (<400ms)"),
            ("2D Operations Radar", "Live Leaflet map with real-time hazard perimeters"),
            ("Automated Sirens", "Instant TLS emergency email & siren alert broadcast"),
            ("Safe GPS Routing", "Turn-by-turn mobile evacuation directions"),
            ("Rescue Fleet Sync", "Dispatches tactical response units & safe routing")
        ])
    ]

    card_width = 2.84
    card_height = 7.15
    y_card = 0.60
    x_starts = [0.55 + i * 3.05 for i in range(5)]

    for idx, (stg_num, stg_name, accent_color, bullets) in enumerate(stages):
        x = x_starts[idx]

        # Subtle Drop Shadow Effect
        shadow = patches.FancyBboxPatch((x + 0.04, y_card - 0.04), card_width, card_height,
                                        boxstyle="round,pad=0.06,rounding_size=0.18",
                                        facecolor='#E2E8F0', edgecolor='none', alpha=0.6)
        ax.add_patch(shadow)

        # Card Background (Clean Crisp White with subtle Slate Border)
        card = patches.FancyBboxPatch((x, y_card), card_width, card_height,
                                      boxstyle="round,pad=0.06,rounding_size=0.18",
                                      facecolor='#F8FAFC', edgecolor='#CBD5E1',
                                      linewidth=1.5, alpha=1.0)
        ax.add_patch(card)

        # Stage Header Badge (Top of Card)
        badge_h = 0.88
        badge_y = y_card + card_height - badge_h - 0.12
        badge = patches.FancyBboxPatch((x + 0.12, badge_y), card_width - 0.24, badge_h,
                                       boxstyle="round,pad=0.04,rounding_size=0.12",
                                       facecolor=accent_color, edgecolor='none', alpha=1.0)
        ax.add_patch(badge)
        
        # White Text in Stage Badges
        ax.text(x + card_width/2, badge_y + 0.54, stg_num,
                ha='center', va='center', fontsize=13.0, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY)
        ax.text(x + card_width/2, badge_y + 0.22, stg_name,
                ha='center', va='center', fontsize=11.5, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY)

        # Connect Stage Badges with Horizontal Directional Flow Arrows at the TOP
        if idx < 4:
            arrow_x_start = x + card_width + 0.02
            arrow_x_end = x_starts[idx + 1] - 0.02
            arrow_y = badge_y + badge_h / 2
            ax.annotate("", xy=(arrow_x_end, arrow_y), xytext=(arrow_x_start, arrow_y),
                        arrowprops=dict(arrowstyle="-|>", color='#2563EB', lw=2.5, mutation_scale=15))

        # Bullets inside Card
        y_bullet = badge_y - 0.35
        for title, desc in bullets:
            # Bullet title (Deep Navy / Accent Colored)
            ax.text(x + 0.16, y_bullet, f">> {title}", 
                    ha='left', va='top', fontsize=10.0, fontweight='bold', color=accent_color, fontfamily=FONT_FAMILY)
            
            # Dark Slate Text for Description (Easy on the eyes, high professional contrast)
            wrapped_desc = textwrap.fill(desc, width=27)
            ax.text(x + 0.26, y_bullet - 0.25, wrapped_desc, 
                    ha='left', va='top', fontsize=9.2, color='#334155', fontfamily=FONT_FAMILY,
                    linespacing=1.22)
            y_bullet -= 1.15

    # Bottom caption
    ax.text(8.0, 0.22, "Continuous Real-Time Loop: Automated telemetry refresh cycles update threat models and evacuation paths in sub-second intervals.",
            ha='center', va='center', fontsize=9.8, color='#64748B', fontfamily=FONT_FAMILY)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='#FFFFFF')
    plt.close()
    print(f"SUCCESS: Generated {out_path}")

if __name__ == '__main__':
    render_light_process_flow()
