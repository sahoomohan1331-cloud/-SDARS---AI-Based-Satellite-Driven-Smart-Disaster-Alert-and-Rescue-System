import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
import os

def render_light_wireframes():
    out_path = r'd:\SDARS map\sdars_slide6_wireframes_light.png'
    os.makedirs(r'd:\SDARS map', exist_ok=True)

    # 16:9 widescreen canvas (16 x 9 inches @ 150 dpi = 2400 x 1350 px)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    FONT_FAMILY = 'Segoe UI'

    # Main Slide Title & Subtitle (Executive Corporate Styling)
    ax.text(8.0, 8.58, "SDARS: UI/UX Wireframes & Tactical Command Suite", 
            ha='center', va='center', fontsize=23, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY)
    ax.text(8.0, 8.16, "High-Fidelity System Mockups: Real-Time GIS Evacuation Navigator & 3D WebGL Disaster War Room", 
            ha='center', va='center', fontsize=12.0, color='#475569', fontfamily=FONT_FAMILY)

    # Coordinates for Dual UI Mockup Windows
    win_y = 1.05
    win_h = 6.85
    win_w = 7.15
    w1_x = 0.65
    w2_x = 8.20

    # Helper: Draw Clean Modern Browser Frame
    def draw_browser_frame(x, y, w, h, title, url, accent_color):
        # Shadow
        shadow = FancyBboxPatch((x + 0.05, y - 0.04), w, h,
                                boxstyle="round,pad=0.06,rounding_size=0.16",
                                facecolor='#E2E8F0', edgecolor='none', alpha=0.6, zorder=1)
        ax.add_patch(shadow)

        # Outer Window Frame (Modern Slate)
        win_bg = FancyBboxPatch((x, y), w, h,
                               boxstyle="round,pad=0.06,rounding_size=0.16",
                               facecolor='#FFFFFF', edgecolor='#CBD5E1',
                               linewidth=1.5, alpha=1.0, zorder=2)
        ax.add_patch(win_bg)

        # Title Bar (Clean Light Gray)
        tb_h = 0.52
        tb_y = y + h - tb_h - 0.08
        title_bar = FancyBboxPatch((x + 0.08, tb_y), w - 0.16, tb_h,
                                   boxstyle="round,pad=0.03,rounding_size=0.10",
                                   facecolor='#F1F5F9', edgecolor='#E2E8F0',
                                   linewidth=1.0, zorder=3)
        ax.add_patch(title_bar)

        # Window Dots
        dot_colors = ['#EF4444', '#F59E0B', '#10B981']
        for i, dc in enumerate(dot_colors):
            dot = plt.Circle((x + 0.32 + i * 0.22, tb_y + tb_h/2), 0.07, color=dc, zorder=4)
            ax.add_patch(dot)

        # URL Bar
        url_w = 3.6
        url_h = 0.32
        url_box = FancyBboxPatch((x + 1.2, tb_y + 0.10), url_w, url_h,
                                 boxstyle="round,pad=0.02,rounding_size=0.06",
                                 facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=0.8, zorder=4)
        ax.add_patch(url_box)
        ax.text(x + 1.35, tb_y + tb_h/2, f"https://sdars.internal/{url}", 
                va='center', fontsize=7.6, color='#475569', fontfamily=FONT_FAMILY, zorder=5)

        # Status Badge
        ax.text(x + w - 0.30, tb_y + tb_h/2, "● LIVE WEBSOCKET", 
                ha='right', va='center', fontsize=7.6, fontweight='bold', color=accent_color, fontfamily=FONT_FAMILY, zorder=5)

        # Content Canvas Area
        cv_y = y + 0.14
        cv_h = h - tb_h - 0.30
        cv_w = w - 0.24
        content_box = FancyBboxPatch((x + 0.12, cv_y), cv_w, cv_h,
                                     boxstyle="round,pad=0.04,rounding_size=0.08",
                                     facecolor='#F8FAFC', edgecolor='#E2E8F0',
                                     linewidth=1.0, zorder=3)
        ax.add_patch(content_box)
        return cv_y, cv_h, cv_w

    # =========================================================================
    # MOCKUP 1 (LEFT): 2D TACTICAL GIS EVACUATION NAVIGATOR
    # =========================================================================
    c1_y, c1_h, c1_w = draw_browser_frame(w1_x, win_y, win_w, win_h, 
                                          "SDARS - Tactical Navigation", "navigator.html", "#0284C7")

    # App Navigation Bar
    app_nav_h = 0.42
    app_nav_y = c1_y + c1_h - app_nav_h - 0.08
    app_nav = FancyBboxPatch((w1_x + 0.20, app_nav_y), c1_w - 0.16, app_nav_h,
                             boxstyle="round,pad=0.02,rounding_size=0.06",
                             facecolor='#0F172A', edgecolor='none', zorder=4)
    ax.add_patch(app_nav)
    ax.text(w1_x + 0.35, app_nav_y + app_nav_h/2, "SDARS TACTICAL GIS", 
            va='center', fontsize=8.6, fontweight='bold', color='#38BDF8', fontfamily=FONT_FAMILY, zorder=5)
    ax.text(w1_x + c1_w - 0.25, app_nav_y + app_nav_h/2, "DASHBOARD  |  [MAP RADAR]  |  NAVIGATOR  |  WAR ROOM", 
            ha='right', va='center', fontsize=7.4, color='#94A3B8', fontfamily=FONT_FAMILY, zorder=5)

    # Left Routing Sidebar (Clean White Card)
    sb_w = 2.45
    sb_h = c1_h - app_nav_h - 0.24
    sb_y = c1_y + 0.12
    sb_x = w1_x + 0.20
    sidebar = FancyBboxPatch((sb_x, sb_y), sb_w, sb_h,
                             boxstyle="round,pad=0.03,rounding_size=0.06",
                             facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
    ax.add_patch(sidebar)

    ax.text(sb_x + 0.15, sb_y + sb_h - 0.25, "ROUTING & SAFE EVACUATION", 
            fontsize=8.4, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY, zorder=5)
    
    box_w = sb_w - 0.30
    # Origin Input
    orig_box = FancyBboxPatch((sb_x + 0.15, sb_y + sb_h - 0.82), box_w, 0.42,
                              boxstyle="round,pad=0.02,rounding_size=0.05",
                              facecolor='#FEF2F2', edgecolor='#EF4444', linewidth=1.0, zorder=5)
    ax.add_patch(orig_box)
    ax.text(sb_x + 0.25, sb_y + sb_h - 0.61, "A: User SOS (Sector 4)", 
            fontsize=7.6, fontweight='bold', color='#B91C1C', fontfamily=FONT_FAMILY, zorder=6)

    # Destination Input
    dest_box = FancyBboxPatch((sb_x + 0.15, sb_y + sb_h - 1.35), box_w, 0.42,
                              boxstyle="round,pad=0.02,rounding_size=0.05",
                              facecolor='#F0FDF4', edgecolor='#10B981', linewidth=1.0, zorder=5)
    ax.add_patch(dest_box)
    ax.text(sb_x + 0.25, sb_y + sb_h - 1.14, "B: District Safe Shelter #2", 
            fontsize=7.6, fontweight='bold', color='#047857', fontfamily=FONT_FAMILY, zorder=6)

    # OSRM Metrics Box
    stat_box = FancyBboxPatch((sb_x + 0.15, sb_y + sb_h - 2.50), box_w, 1.02,
                              boxstyle="round,pad=0.03,rounding_size=0.06",
                              facecolor='#F8FAFC', edgecolor='#0D9488', linewidth=1.2, zorder=5)
    ax.add_patch(stat_box)
    ax.text(sb_x + 0.25, sb_y + sb_h - 1.62, "OPTIMAL SAFE ROUTE (OSRM)", 
            fontsize=7.6, fontweight='bold', color='#0D9488', fontfamily=FONT_FAMILY, zorder=6)
    ax.text(sb_x + 0.25, sb_y + sb_h - 1.88, "• Clearance: 1.8 km from danger", 
            fontsize=7.2, color='#334155', fontfamily=FONT_FAMILY, zorder=6)
    ax.text(sb_x + 0.25, sb_y + sb_h - 2.12, "• Evacuation ETA: 11 mins (6.4 km)", 
            fontsize=7.2, color='#334155', fontfamily=FONT_FAMILY, zorder=6)
    ax.text(sb_x + 0.25, sb_y + sb_h - 2.36, "• Hazard Exposure: 0% (Bypassed)", 
            fontsize=7.2, fontweight='bold', color='#059669', fontfamily=FONT_FAMILY, zorder=6)

    # Turn-by-Turn Directions
    ax.text(sb_x + 0.15, sb_y + sb_h - 2.75, "TURN-BY-TURN DIRECTIONS:", 
            fontsize=7.6, fontweight='bold', color='#64748B', fontfamily=FONT_FAMILY, zorder=5)
    
    steps = [
        ("1. Head North on Ring Rd", "Avoid active low-lying underpass"),
        ("2. Turn East onto Sector Bypass", "Path clear of predicted inundation"),
        ("3. Merge onto Elevated Highway", "Designated emergency relief corridor"),
        ("4. Arrive at District Shelter", "Facility open, capacity: 88%")
    ]
    step_y = sb_y + sb_h - 3.10
    for s_title, s_note in steps:
        ax.text(sb_x + 0.18, step_y, s_title, fontsize=7.2, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY, zorder=5)
        ax.text(sb_x + 0.30, step_y - 0.22, s_note, fontsize=6.8, color='#64748B', fontfamily=FONT_FAMILY, zorder=5)
        step_y -= 0.56

    # Action Button
    btn_box = FancyBboxPatch((sb_x + 0.15, sb_y + 0.15), box_w, 0.40,
                             boxstyle="round,pad=0.02,rounding_size=0.06",
                             facecolor='#0284C7', edgecolor='none', zorder=5)
    ax.add_patch(btn_box)
    ax.text(sb_x + sb_w/2, sb_y + 0.35, "START GPS TURN-BY-TURN", 
            ha='center', va='center', fontsize=7.6, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY, zorder=6)

    # Map Canvas (Clean GIS Light Viewport)
    map_x = sb_x + sb_w + 0.15
    map_w = c1_w - sb_w - 0.35
    map_h = sb_h
    map_y = sb_y
    map_frame = FancyBboxPatch((map_x, map_y), map_w, map_h,
                               boxstyle="round,pad=0.03,rounding_size=0.06",
                               facecolor='#E2E8F0', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
    ax.add_patch(map_frame)

    # Street Grid
    roads = [
        ([map_x + 0.2, map_x + map_w - 0.2], [map_y + 1.2, map_y + 1.2]),
        ([map_x + 0.2, map_x + map_w - 0.2], [map_y + 2.5, map_y + 2.5]),
        ([map_x + 0.2, map_x + map_w - 0.2], [map_y + 4.2, map_y + 4.2]),
        ([map_x + 0.8, map_x + 0.8], [map_y + 0.2, map_y + map_h - 0.2]),
        ([map_x + 2.1, map_x + 2.1], [map_y + 0.2, map_y + map_h - 0.2]),
        ([map_x + 3.4, map_x + 3.4], [map_y + 0.2, map_y + map_h - 0.2])
    ]
    for rx, ry in roads:
        ax.plot(rx, ry, color='#CBD5E1', lw=2.5, solid_capstyle='round', zorder=5)
        ax.plot(rx, ry, color='#FFFFFF', lw=1.5, solid_capstyle='round', zorder=6)

    # Active Hazard Polygon
    h_pts = np.array([
        [map_x + 1.2, map_y + 1.8],
        [map_x + 2.5, map_y + 1.5],
        [map_x + 2.9, map_y + 2.6],
        [map_x + 2.4, map_y + 3.6],
        [map_x + 1.4, map_y + 3.5],
        [map_x + 0.9, map_y + 2.7]
    ])
    h_poly = Polygon(h_pts, closed=True, facecolor='#EF4444', edgecolor='#DC2626', 
                     linewidth=1.8, alpha=0.40, zorder=7)
    ax.add_patch(h_poly)

    o_pts = np.array([
        [map_x + 0.9, map_y + 1.5],
        [map_x + 2.8, map_y + 1.2],
        [map_x + 3.3, map_y + 2.6],
        [map_x + 2.7, map_y + 4.0],
        [map_x + 1.2, map_y + 3.9],
        [map_x + 0.6, map_y + 2.7]
    ])
    o_poly = Polygon(o_pts, closed=True, facecolor='#F59E0B', edgecolor='#D97706', 
                     linewidth=1.2, linestyle='--', alpha=0.25, zorder=6)
    ax.add_patch(o_poly)
    ax.text(map_x + 1.9, map_y + 2.55, "INUNDATION HAZARD\n(Water Level: 1.4m)\nROADS BLOCKED", 
            ha='center', va='center', fontsize=7.4, fontweight='bold', color='#991B1B', fontfamily=FONT_FAMILY, zorder=8)

    # Safe Route (Green Polyline)
    rt_pts_x = [map_x + 0.8, map_x + 0.8, map_x + 1.2, map_x + 2.1, map_x + 3.4, map_x + 3.4, map_x + 3.8]
    rt_pts_y = [map_y + 0.9, map_y + 4.2, map_y + 4.4, map_y + 4.4, map_y + 4.4, map_y + 3.0, map_y + 1.2]
    ax.plot(rt_pts_x, rt_pts_y, color='#059669', lw=4.5, solid_capstyle='round', zorder=9)
    ax.plot(rt_pts_x, rt_pts_y, color='#34D399', lw=2.0, solid_capstyle='round', zorder=10)

    # Pins
    ax.plot(rt_pts_x[0], rt_pts_y[0], 'o', color='#EF4444', markersize=9, markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=11)
    ax.text(rt_pts_x[0] + 0.15, rt_pts_y[0] + 0.12, "A: User SOS", fontsize=7.2, fontweight='bold', color='#DC2626', fontfamily=FONT_FAMILY, zorder=12)

    ax.plot(rt_pts_x[-1], rt_pts_y[-1], 's', color='#059669', markersize=10, markeredgecolor='#FFFFFF', markeredgewidth=1.5, zorder=11)
    ax.text(rt_pts_x[-1] - 0.12, rt_pts_y[-1] - 0.28, "B: Safe Shelter\n(Cap: 88%)", ha='right', fontsize=7.2, fontweight='bold', color='#047857', fontfamily=FONT_FAMILY, zorder=12)

    # Leaflet Layer Badge
    lc_box = FancyBboxPatch((map_x + map_w - 1.45, map_y + map_h - 1.15), 1.35, 1.05,
                            boxstyle="round,pad=0.02,rounding_size=0.05",
                            facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, alpha=0.96, zorder=9)
    ax.add_patch(lc_box)
    ax.text(map_x + map_w - 1.35, map_y + map_h - 0.25, "MAP LAYERS", fontsize=6.8, fontweight='bold', color='#0284C7', fontfamily=FONT_FAMILY, zorder=10)
    ax.text(map_x + map_w - 1.35, map_y + map_h - 0.48, "[x] Hazard Isochrone", fontsize=6.4, color='#334155', fontfamily=FONT_FAMILY, zorder=10)
    ax.text(map_x + map_w - 1.35, map_y + map_h - 0.70, "[x] Open Evac Shelters", fontsize=6.4, color='#334155', fontfamily=FONT_FAMILY, zorder=10)
    ax.text(map_x + map_w - 1.35, map_y + map_h - 0.92, "[x] Flood Inundation DEM", fontsize=6.4, color='#334155', fontfamily=FONT_FAMILY, zorder=10)

    # =========================================================================
    # MOCKUP 2 (RIGHT): 3D DISASTER WAR ROOM
    # =========================================================================
    c2_y, c2_h, c2_w = draw_browser_frame(w2_x, win_y, win_w, win_h, 
                                          "SDARS - 3D Planetary War Room", "3d-view.html", "#0D9488")

    # App Navigation Bar
    app_nav2 = FancyBboxPatch((w2_x + 0.20, app_nav_y), c2_w - 0.16, app_nav_h,
                              boxstyle="round,pad=0.02,rounding_size=0.06",
                              facecolor='#0F172A', edgecolor='none', zorder=4)
    ax.add_patch(app_nav2)
    ax.text(w2_x + 0.35, app_nav_y + app_nav_h/2, "SDARS 3D WAR ROOM", 
            va='center', fontsize=8.6, fontweight='bold', color='#34D399', fontfamily=FONT_FAMILY, zorder=5)
    ax.text(w2_x + c2_w - 0.25, app_nav_y + app_nav_h/2, "CESIUMJS WEBGL ACCELERATED  |  REAL-TIME TELEMETRY", 
            ha='right', va='center', fontsize=7.4, color='#94A3B8', fontfamily=FONT_FAMILY, zorder=5)

    # Left Control Drawer in 3D Viewport (White Card)
    c3d_w = 2.40
    c3d_h = sb_h
    c3d_x = w2_x + 0.20
    c3d_y = sb_y
    ctrl_box = FancyBboxPatch((c3d_x, c3d_y), c3d_w, c3d_h,
                              boxstyle="round,pad=0.03,rounding_size=0.06",
                              facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.0, zorder=4)
    ax.add_patch(ctrl_box)

    ax.text(c3d_x + 0.15, c3d_y + c3d_h - 0.25, "WAR ROOM CONTROLS", 
            fontsize=8.4, fontweight='bold', color='#0F172A', fontfamily=FONT_FAMILY, zorder=5)

    toggles = [
        ("3D Buildings", "ON", "#059669"),
        ("3D Terrain (Elevation DEM)", "ON", "#059669"),
        ("Atmospheric Fog", "ON", "#059669"),
        ("Day / Night Illumination", "ON", "#059669")
    ]
    tog_y = c3d_y + c3d_h - 0.58
    for t_name, t_val, t_col in toggles:
        ax.text(c3d_x + 0.15, tog_y, t_name, fontsize=7.0, color='#334155', fontfamily=FONT_FAMILY, zorder=5)
        ax.text(c3d_x + c3d_w - 0.18, tog_y, f"[{t_val}]", ha='right', fontsize=7.0, fontweight='bold', color=t_col, fontfamily=FONT_FAMILY, zorder=5)
        tog_y -= 0.32

    tog_y -= 0.10
    ax.text(c3d_x + 0.15, tog_y, "LIVE SATELLITE CONSTELLATION", fontsize=7.6, fontweight='bold', color='#0284C7', fontfamily=FONT_FAMILY, zorder=5)
    tog_y -= 0.30
    
    sats = [
        ("• ISS Alpha", "408 km altitude", "#0284C7"),
        ("• Sentinel-2A", "786 km altitude", "#0D9488"),
        ("• NOAA-20 VIIRS", "824 km altitude", "#6366F1"),
        ("• Landsat-9 OLI", "705 km altitude", "#8B5CF6")
    ]
    for s_name, s_alt, s_col in sats:
        ax.text(c3d_x + 0.15, tog_y, s_name, fontsize=7.0, fontweight='bold', color=s_col, fontfamily=FONT_FAMILY, zorder=5)
        ax.text(c3d_x + c3d_w - 0.18, tog_y, s_alt, ha='right', fontsize=6.8, color='#64748B', fontfamily=FONT_FAMILY, zorder=5)
        tog_y -= 0.30

    tog_y -= 0.10
    ax.text(c3d_x + 0.15, tog_y, "STRATEGIC CRISIS SIMULATOR", fontsize=7.6, fontweight='bold', color='#D97706', fontfamily=FONT_FAMILY, zorder=5)
    tog_y -= 0.30
    ax.text(c3d_x + 0.15, tog_y, "Flood Inundation Engine", fontsize=7.0, color='#334155', fontfamily=FONT_FAMILY, zorder=5)
    ax.text(c3d_x + c3d_w - 0.18, tog_y, "[ACTIVE]", ha='right', fontsize=7.0, fontweight='bold', color='#DC2626', fontfamily=FONT_FAMILY, zorder=5)
    tog_y -= 0.38

    btn_tour = FancyBboxPatch((c3d_x + 0.15, c3d_y + 0.15), c3d_w - 0.30, 0.40,
                              boxstyle="round,pad=0.02,rounding_size=0.06",
                              facecolor='#0D9488', edgecolor='none', zorder=5)
    ax.add_patch(btn_tour)
    ax.text(c3d_x + c3d_w/2, c3d_y + 0.35, "START 3D CRISIS TOUR", 
            ha='center', va='center', fontsize=7.6, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY, zorder=6)

    # Right Canvas: CesiumJS 3D Viewport
    globe_x = c3d_x + c3d_w + 0.15
    globe_w = c2_w - c3d_w - 0.35
    globe_h = sb_h
    globe_y = sb_y
    globe_frame = FancyBboxPatch((globe_x, globe_y), globe_w, globe_h,
                                 boxstyle="round,pad=0.03,rounding_size=0.06",
                                 facecolor='#0F172A', edgecolor='#1E293B', linewidth=1.0, zorder=4)
    ax.add_patch(globe_frame)

    # Digital Twin Curved Horizon
    gx = np.linspace(globe_x, globe_x + globe_w, 100)
    gy = globe_y + 0.4 + 1.1 * np.sin(np.pi * (gx - globe_x) / globe_w)
    ax.fill_between(gx, globe_y + 0.05, gy, facecolor='#1E293B', alpha=0.95, zorder=5)
    ax.plot(gx, gy, color='#38BDF8', lw=2.0, zorder=6)

    # Telemetry Box (Top Left)
    hud_w = 2.15
    hud_h = 1.35
    hud_x = globe_x + 0.15
    hud_y = globe_y + globe_h - hud_h - 0.15
    hud_box = FancyBboxPatch((hud_x, hud_y), hud_w, hud_h,
                             boxstyle="round,pad=0.03,rounding_size=0.05",
                             facecolor='#020617', edgecolor='#38BDF8', linewidth=1.0, alpha=0.95, zorder=7)
    ax.add_patch(hud_box)
    ax.text(hud_x + 0.12, hud_y + hud_h - 0.22, "TELEMETRY STREAM", fontsize=7.2, fontweight='bold', color='#38BDF8', fontfamily=FONT_FAMILY, zorder=8)
    ax.text(hud_x + 0.12, hud_y + hud_h - 0.48, "• Wind: 84 km/h NNW", fontsize=6.8, color='#E2E8F0', fontfamily=FONT_FAMILY, zorder=8)
    ax.text(hud_x + 0.12, hud_y + hud_h - 0.72, "• Pressure: 988 hPa", fontsize=6.8, color='#F87171', fontfamily=FONT_FAMILY, zorder=8)
    ax.text(hud_x + 0.12, hud_y + hud_h - 0.96, "• Soil Saturation: 94%", fontsize=6.8, color='#38BDF8', fontfamily=FONT_FAMILY, zorder=8)
    ax.text(hud_x + 0.12, hud_y + hud_h - 1.20, "• AI Threat: CRITICAL", fontsize=6.8, fontweight='bold', color='#EF4444', fontfamily=FONT_FAMILY, zorder=8)

    # Orbit Arc (Right Side of Viewport)
    sat_arc_x = np.linspace(globe_x + 1.8, globe_x + globe_w - 0.2, 50)
    sat_arc_y = np.linspace(globe_y + globe_h - 0.5, globe_y + globe_h - 2.0, 50)
    ax.plot(sat_arc_x, sat_arc_y, color='#00E5FF', lw=1.5, linestyle='-.', zorder=6)
    
    sat_idx = 15
    ax.plot(sat_arc_x[sat_idx], sat_arc_y[sat_idx], 's', color='#FFFFFF', markersize=7, markeredgecolor='#00E5FF', markeredgewidth=1.8, zorder=8)
    ax.text(sat_arc_x[sat_idx] + 0.15, sat_arc_y[sat_idx] + 0.15, "Sentinel-2A Orbit (786 km)", 
            fontsize=7.2, fontweight='bold', color='#38BDF8', fontfamily=FONT_FAMILY, zorder=9)

    cone_pts = [
        [sat_arc_x[sat_idx], sat_arc_y[sat_idx]],
        [globe_x + 1.8, globe_y + 0.8],
        [globe_x + 3.4, globe_y + 0.9]
    ]
    ax.add_patch(Polygon(cone_pts, closed=True, facecolor='#00E5FF', edgecolor='#38BDF8', alpha=0.10, linestyle=':', zorder=5))

    pins = [
        (globe_x + 1.6, globe_y + 0.9, "Flood Inundation Core", "#3B82F6"),
        (globe_x + 3.2, globe_y + 1.2, "Wildfire Hotspot (MODIS)", "#EF4444")
    ]
    for px, py, plbl, pcol in pins:
        ax.plot(px, py, 'o', color=pcol, markersize=8, markeredgecolor='#FFFFFF', markeredgewidth=1.2, zorder=7)
        ax.text(px, py - 0.24, plbl, ha='center', fontsize=6.8, fontweight='bold', color='#FFFFFF', fontfamily=FONT_FAMILY, zorder=8)

    # Footer
    ax.text(8.0, 0.45, "SDARS Production UX: Multi-Agency Design System  •  Sub-Second WebSocket Pipeline  •  Zero-Setup Offline Tile Caching",
            ha='center', va='center', fontsize=9.4, fontweight='bold', color='#64748B', fontfamily=FONT_FAMILY)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='#FFFFFF')
    plt.close()
    print(f"SUCCESS: Generated {out_path}")

if __name__ == '__main__':
    render_light_wireframes()
