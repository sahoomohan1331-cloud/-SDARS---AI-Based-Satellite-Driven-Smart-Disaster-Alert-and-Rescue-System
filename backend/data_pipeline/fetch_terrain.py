"""SRTM 30 m (SRTM GL1) Terrain and Slope Aggregation Pipeline for SDARS.

Downloads NASA SRTM GL1 1-arc-second (~30 m resolution) elevation tiles
for the Odisha, India bounding box (lat 17.8 to 22.6 N, lon 81.3 to 87.5 E).
Aggregates high-resolution 30 m elevation to 0.5-degree grid cells, computing:
- mean_elevation_m
- max_elevation_m
- min_elevation_m
- max_slope_deg (derived from 30 m sub-cell gradients, capturing sub-cell terrain variability)
- p95_slope_deg (95th percentile sub-cell slope, robust to single-pixel outliers)

Source: Public NASA SRTM elevation tiles hosted on AWS Skadi (free, no key required).
(OpenTopography requires a personal API key and is documented accordingly).

Outputs:
- data/raw/srtm/*.hgt.gz (raw downloaded tile archive)
- data/processed/terrain.parquet (cell-level aggregated terrain metrics)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import logging
import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.ndimage import gaussian_filter

from backend.data_pipeline.fetch_history import (
    DEFAULT_LAT_MAX,
    DEFAULT_LAT_MIN,
    DEFAULT_LON_MAX,
    DEFAULT_LON_MIN,
    DEFAULT_STEP,
    build_grid,
)

logger = logging.getLogger("fetch_terrain")

# AWS Skadi public SRTM 30 m elevation tile endpoint (free, no API key required)
SKADI_BASE_URL: str = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"

# SRTM 1-arc-second tile dimensions and pixel spacing
TILE_SIZE: int = 3601
ARCSEC_PER_DEGREE: float = 3600.0
METRES_PER_ARCSEC_LAT: float = 30.87  # ~30.87 metres per arc-second at equator/tropics


def setup_logging(log_file: Path | None = None) -> logging.Logger:
    """Configure stdout and optional file logging."""
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_tile_name(lat: int, lon: int) -> str:
    """Return the SRTM tile identifier for lower-left corner (e.g. N20E085)."""
    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"
    return f"{lat_prefix}{abs(lat):02d}{lon_prefix}{abs(lon):03d}"


def get_tile_url(lat: int, lon: int) -> str:
    """Construct the AWS Skadi download URL for a 1-degree SRTM tile."""
    tile_name = get_tile_name(lat, lon)
    lat_prefix = "N" if lat >= 0 else "S"
    folder = f"{lat_prefix}{abs(lat):02d}"
    return f"{SKADI_BASE_URL}/{folder}/{tile_name}.hgt.gz"


def download_tile(
    lat: int,
    lon: int,
    raw_dir: Path,
    session: requests.Session | None = None,
) -> Path | None:
    """Download a single SRTM tile if not already cached.

    Returns Path to cached .hgt.gz file, or None if the tile is ocean (404).
    """
    tile_name = get_tile_name(lat, lon)
    tile_path = raw_dir / f"{tile_name}.hgt.gz"
    if tile_path.exists() and tile_path.stat().st_size > 0:
        return tile_path

    url = get_tile_url(lat, lon)
    req_session = session or requests.Session()

    try:
        response = req_session.get(url, timeout=45)
        if response.status_code == 200:
            raw_dir.mkdir(parents=True, exist_ok=True)
            temp_path = tile_path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            temp_path.replace(tile_path)
            logger.info("Downloaded SRTM tile %s (%d KB)", tile_name, len(response.content) // 1024)
            return tile_path
        if response.status_code == 404:
            logger.info("Tile %s not found on Skadi (likely ocean/void). Treating as sea level.", tile_name)
            return None
        logger.warning("HTTP %d downloading SRTM tile %s from %s", response.status_code, tile_name, url)
        return None
    except requests.RequestException as exc:
        logger.warning("Request error downloading %s: %s", tile_name, exc)
        return None


def read_hgt_tile(tile_path: Path) -> np.ndarray:
    """Read and decompress an SRTM 1-arc-second HGT file into a numpy float array.

    HGT format: 3601 x 3601 16-bit signed integers in big-endian byte order (>i2).
    SRTM void value (-32768) and invalid depressions (< -500 m) are masked to NaN.
    """
    with gzip.open(tile_path, "rb") as f:
        buf = f.read()

    expected_bytes = TILE_SIZE * TILE_SIZE * 2
    if len(buf) != expected_bytes:
        raise ValueError(
            f"Invalid HGT buffer size in {tile_path}: expected {expected_bytes}, got {len(buf)}"
        )

    arr = np.frombuffer(buf, dtype=">i2").reshape((TILE_SIZE, TILE_SIZE)).astype(np.float32)
    # Mask void value (-32768) and clamp negative bathymetry (ocean water elevation is 0.0 m)
    arr[arr < 0] = 0.0
    return arr


class TileManager:
    """Manages caching and extraction of SRTM 30 m DEM patches across tiles."""

    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._tile_cache: dict[tuple[int, int], np.ndarray | None] = {}

    def get_tile_array(self, tile_lat: int, tile_lon: int) -> np.ndarray | None:
        """Load 3601x3601 DEM array for a 1-degree tile, or None for ocean."""
        key = (tile_lat, tile_lon)
        if key in self._tile_cache:
            return self._tile_cache[key]

        tile_name = get_tile_name(tile_lat, tile_lon)
        tile_path = self.raw_dir / f"{tile_name}.hgt.gz"

        if not tile_path.exists():
            downloaded = download_tile(tile_lat, tile_lon, self.raw_dir)
            if downloaded is None:
                self._tile_cache[key] = None
                return None
            tile_path = downloaded

        try:
            arr = read_hgt_tile(tile_path)
            self._tile_cache[key] = arr
            return arr
        except Exception as exc:
            logger.warning("Failed to parse SRTM tile %s: %s", tile_name, exc)
            self._tile_cache[key] = None
            return None

    def extract_patch(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
    ) -> np.ndarray:
        """Extract a continuous 30 m DEM elevation patch over the bounding box.

        Stitches across 1-degree tile boundaries if needed.
        """
        # Determine pixel dimensions at 1 arc-second resolution
        num_rows = int(round((max_lat - min_lat) * ARCSEC_PER_DEGREE))
        num_cols = int(round((max_lon - min_lon) * ARCSEC_PER_DEGREE))

        if num_rows <= 0 or num_cols <= 0:
            return np.zeros((1, 1), dtype=np.float32)

        patch = np.full((num_rows, num_cols), fill_value=np.nan, dtype=np.float32)

        lat_tiles = range(int(math.floor(min_lat)), int(math.ceil(max_lat)))
        lon_tiles = range(int(math.floor(min_lon)), int(math.ceil(max_lon)))

        for t_lat in lat_tiles:
            for t_lon in lon_tiles:
                arr = self.get_tile_array(t_lat, t_lon)

                # Overlap between tile [t_lat, t_lat + 1] and requested patch
                sub_min_lat = max(min_lat, float(t_lat))
                sub_max_lat = min(max_lat, float(t_lat + 1))
                sub_min_lon = max(min_lon, float(t_lon))
                sub_max_lon = min(max_lon, float(t_lon + 1))

                if sub_min_lat >= sub_max_lat or sub_min_lon >= sub_max_lon:
                    continue

                # Destination indices in patch array
                # Row 0 in patch corresponds to max_lat
                dest_r_start = int(round((max_lat - sub_max_lat) * ARCSEC_PER_DEGREE))
                dest_r_end = int(round((max_lat - sub_min_lat) * ARCSEC_PER_DEGREE))
                dest_c_start = int(round((sub_min_lon - min_lon) * ARCSEC_PER_DEGREE))
                dest_c_end = int(round((sub_max_lon - min_lon) * ARCSEC_PER_DEGREE))

                if arr is None:
                    # Ocean tile: elevation 0 m
                    patch[dest_r_start:dest_r_end, dest_c_start:dest_c_end] = 0.0
                else:
                    # Source indices in 3601 x 3601 tile array
                    # Row 0 in tile is (t_lat + 1)
                    src_r_start = int(round((float(t_lat + 1) - sub_max_lat) * ARCSEC_PER_DEGREE))
                    src_r_end = int(round((float(t_lat + 1) - sub_min_lat) * ARCSEC_PER_DEGREE))
                    src_c_start = int(round((sub_min_lon - float(t_lon)) * ARCSEC_PER_DEGREE))
                    src_c_end = int(round((sub_max_lon - float(t_lon)) * ARCSEC_PER_DEGREE))

                    # Bound slices safely
                    src_slice = arr[src_r_start:src_r_end, src_c_start:src_c_end]
                    patch_slice_shape = patch[dest_r_start:dest_r_end, dest_c_start:dest_c_end].shape

                    if src_slice.shape == patch_slice_shape:
                        patch[dest_r_start:dest_r_end, dest_c_start:dest_c_end] = src_slice
                    else:
                        min_r = min(src_slice.shape[0], patch_slice_shape[0])
                        min_c = min(src_slice.shape[1], patch_slice_shape[1])
                        patch[
                            dest_r_start : dest_r_start + min_r,
                            dest_c_start : dest_c_start + min_c,
                        ] = src_slice[:min_r, :min_c]

        # Fill remaining void NaNs over ocean with 0.0 m
        if np.isnan(patch).all():
            patch[:] = 0.0
        else:
            ocean_mask = np.isnan(patch)
            patch[ocean_mask] = 0.0

        return patch


def compute_terrain_metrics_from_30m_dem(
    cell_lat: float,
    cell_lon: float,
    tile_manager: TileManager,
    cell_step: float = DEFAULT_STEP,
) -> dict[str, float]:
    """Compute terrain elevation and slope metrics from 30 m SRTM DEM within a 0.5-degree cell.

    IMPORTANT: Slope is computed from high-resolution 30 m DEM gradients within the cell,
    NOT from neighbouring 0.5-degree cell centres. This captures true sub-cell terrain variability.
    """
    half_step = cell_step / 2.0
    cell_min_lat = cell_lat - half_step
    cell_max_lat = cell_lat + half_step
    cell_min_lon = cell_lon - half_step
    cell_max_lon = cell_lon + half_step

    # Extract 30 m DEM patch covering the ~0.5 x 0.5 degree window (~1800 x 1800 pixels)
    dem_patch = tile_manager.extract_patch(cell_min_lat, cell_max_lat, cell_min_lon, cell_max_lon)

    # Elevation metrics (over land and sea-level surface)
    dem_patch = np.maximum(dem_patch, 0.0)
    mean_el = float(np.nanmean(dem_patch))
    max_el = float(np.nanmax(dem_patch))
    min_el = float(np.nanmin(dem_patch))

    # Compute slope at 30 m resolution
    # dy = spacing along latitude in metres (~30.87 m per arc-second)
    # dx = spacing along longitude in metres at given latitude
    dy = METRES_PER_ARCSEC_LAT
    dx = METRES_PER_ARCSEC_LAT * math.cos(math.radians(cell_lat))
    dx = max(dx, 1.0)  # Avoid division by zero

    # Filter single-pixel radar DSM sensor noise with a 3-pixel (~90 m) gaussian kernel
    dem_smooth = gaussian_filter(dem_patch, sigma=3.0)
    gy, gx = np.gradient(dem_smooth, dy, dx)
    slope_rad = np.arctan(np.sqrt(gy**2 + gx**2))
    slope_deg = np.degrees(slope_rad)
    max_slope = float(np.nanmax(slope_deg))
    p95_slope = float(np.nanpercentile(slope_deg, 95))

    return {
        "mean_elevation_m": round(mean_el, 2),
        "max_elevation_m": round(max_el, 2),
        "min_elevation_m": round(min_el, 2),
        "max_slope_deg": round(max(max_slope, 0.0), 2),
        "p95_slope_deg": round(max(p95_slope, 0.0), 2),
    }


def download_all_bbox_tiles(
    raw_dir: Path,
    lat_min: float = DEFAULT_LAT_MIN,
    lat_max: float = DEFAULT_LAT_MAX,
    lon_min: float = DEFAULT_LON_MIN,
    lon_max: float = DEFAULT_LON_MAX,
    max_workers: int = 6,
) -> None:
    """Pre-download all required SRTM tiles for the bounding box in parallel."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    lat_range = range(int(math.floor(lat_min)), int(math.ceil(lat_max)))
    lon_range = range(int(math.floor(lon_min)), int(math.ceil(lon_max)))
    tile_coords = [(la, lo) for la in lat_range for lo in lon_range]

    logger.info("Surveying %d SRTM tiles across Odisha bbox...", len(tile_coords))

    def fetch_one(coords: tuple[int, int]) -> None:
        download_tile(coords[0], coords[1], raw_dir)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(fetch_one, tile_coords))

    logger.info("SRTM tile download complete. All tiles ready in %s", raw_dir)


def run_terrain_pipeline(
    data_dir: Path | None = None,
    include_cities: bool = True,
    max_workers: int = 6,
) -> Path:
    """Execute the end-to-end SRTM 30 m terrain aggregation pipeline."""
    base_data = data_dir or Path("data")
    raw_dir = base_data / "raw" / "srtm"
    processed_dir = base_data / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_file = processed_dir / "terrain.parquet"

    # Pre-download all tiles in bounding box
    download_all_bbox_tiles(raw_dir, max_workers=max_workers)

    tile_manager = TileManager(raw_dir)
    grid_points = build_grid(include_cities=include_cities)
    logger.info("Aggregating 30 m SRTM terrain for %d grid points...", len(grid_points))

    records: list[dict[str, Any]] = []
    for idx, pt in enumerate(grid_points, start=1):
        grid_id = pt["grid_id"]
        lat = float(pt["lat"])
        lon = float(pt["lon"])

        metrics = compute_terrain_metrics_from_30m_dem(lat, lon, tile_manager)
        records.append(
            {
                "grid_id": grid_id,
                "mean_elevation_m": metrics["mean_elevation_m"],
                "max_elevation_m": metrics["max_elevation_m"],
                "min_elevation_m": metrics["min_elevation_m"],
                "max_slope_deg": metrics["max_slope_deg"],
                "p95_slope_deg": metrics["p95_slope_deg"],
            }
        )

        if idx % 20 == 0 or idx == len(grid_points):
            logger.info("Aggregated terrain for %d/%d cells...", idx, len(grid_points))

    df_terrain = pd.DataFrame(records)
    df_terrain.sort_values(by="grid_id", inplace=True)
    df_terrain.reset_index(drop=True, inplace=True)

    df_terrain.to_parquet(out_file, index=False, engine="pyarrow")
    logger.info("Saved terrain dataset to %s (%d rows)", out_file, len(df_terrain))
    return out_file


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point for fetch_terrain."""
    parser = argparse.ArgumentParser(description="SDARS SRTM 30 m Terrain Pipeline")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base data directory (default: data)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=6,
        help="Concurrency for tile downloads (default: 6)",
    )

    args = parser.parse_args(argv)
    log_path = Path(args.data_dir) / "logs" / "fetch_terrain.log"
    setup_logging(log_path)

    run_terrain_pipeline(data_dir=Path(args.data_dir), max_workers=args.max_workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
