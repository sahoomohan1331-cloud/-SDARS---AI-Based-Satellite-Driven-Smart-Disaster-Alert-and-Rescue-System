"""Historical Weather Data Pipeline for SDARS.

Fetches historical reanalysis weather data from the Open-Meteo Historical Weather API
(ERA5 / ERA5-Land) for the Odisha, India bounding box.
Supports 0.5-degree regular grid points and named urban centers.
Caches raw responses as Parquet files, tracks completion via checkpoints,
and compiles standardized 6-hourly datasets in UTC.

Scientific Integrity Rules:
- No synthetic or estimated weather data is ever generated or substituted.
- Failed network requests raise explicit runtime exceptions.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

# Bounding box for Odisha, India
DEFAULT_LAT_MIN: float = 17.8
DEFAULT_LAT_MAX: float = 22.6
DEFAULT_LON_MIN: float = 81.3
DEFAULT_LON_MAX: float = 87.5
DEFAULT_STEP: float = 0.5

# Open-Meteo Archive API endpoint
DEFAULT_OPEN_METEO_URL: str = "https://archive-api.open-meteo.com/v1/archive"

# Major administrative and coastal urban centers in Odisha
NAMED_CITIES: list[tuple[str, float, float]] = [
    ("Bhubaneswar", 20.2961, 85.8245),
    ("Cuttack", 20.4625, 85.8830),
    ("Puri", 19.8135, 85.8312),
    ("Balasore", 21.4934, 86.9135),
    ("Berhampur", 19.3150, 84.7941),
    ("Sambalpur", 21.4669, 83.9812),
    ("Rourkela", 22.2604, 84.8536),
    ("Angul", 20.8444, 85.1511),
]

# Hourly variables requested from Open-Meteo ERA5 / ERA5-Land
HOURLY_VARIABLES: list[str] = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_gusts_10m",
    "precipitation",
    "cloud_cover",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
]

logger = logging.getLogger("fetch_history")


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


def build_grid(
    min_lat: float = DEFAULT_LAT_MIN,
    max_lat: float = DEFAULT_LAT_MAX,
    min_lon: float = DEFAULT_LON_MIN,
    max_lon: float = DEFAULT_LON_MAX,
    step: float = DEFAULT_STEP,
    include_cities: bool = False,
) -> list[dict[str, Any]]:
    """Build a list of grid cell dictionaries over the bounding box.

    When include_cities is False, generates the regular 0.5-degree grid cells.
    When include_cities is True, appends the 8 named Odisha urban centers.
    """
    grid: list[dict[str, Any]] = []

    # Generate regular 0.5-degree grid coordinates within bbox
    # Using np.arange with small epsilon to safely bound steps
    lat_values = [
        round(float(lat), 4)
        for lat in np.arange(min_lat, max_lat + 1e-6, step)
        if lat <= max_lat + 1e-6
    ]
    lon_values = [
        round(float(lon), 4)
        for lon in np.arange(min_lon, max_lon + 1e-6, step)
        if lon <= max_lon + 1e-6
    ]

    for lat in lat_values:
        for lon in lon_values:
            grid_id = f"grid_{lat:.1f}_{lon:.1f}"
            grid.append(
                {
                    "grid_id": grid_id,
                    "lat": lat,
                    "lon": lon,
                    "elevation": None,
                    "is_city": False,
                    "city_name": None,
                }
            )

    if include_cities:
        for name, lat, lon in NAMED_CITIES:
            slug = name.lower().replace(" ", "_")
            grid.append(
                {
                    "grid_id": f"city_{slug}",
                    "lat": float(lat),
                    "lon": float(lon),
                    "elevation": None,
                    "is_city": True,
                    "city_name": name,
                }
            )

    return grid


def get_checkpoint_key(grid_id: str, year: int) -> str:
    """Generate unique checkpoint key for a point-year pair."""
    return f"{grid_id}:{year}"


def load_checkpoints(checkpoint_file: Path) -> set[str]:
    """Load completed checkpoint keys from file."""
    if not checkpoint_file.exists():
        return set()
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("completed", []))
    except Exception as exc:
        logger.warning("Could not read checkpoint file %s: %s", checkpoint_file, exc)
        return set()


def save_checkpoint(checkpoint_file: Path, completed_keys: set[str]) -> None:
    """Save completed checkpoint keys to file atomically."""
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = checkpoint_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump({"completed": sorted(completed_keys)}, f, indent=2)
    temp_file.replace(checkpoint_file)


def fetch_open_meteo_batch(
    session: requests.Session,
    base_url: str,
    points: list[dict[str, Any]],
    start_date: str,
    end_date: str,
    max_retries: int = 5,
) -> list[dict[str, Any]]:
    """Fetch hourly historical data for a batch of coordinates from Open-Meteo.

    Retries with exponential backoff on HTTP 429 (rate-limit) and 5xx errors.
    Raises an exception on persistent failure. No synthetic values substituted.
    """
    if not points:
        return []

    latitudes = ",".join(str(p["lat"]) for p in points)
    longitudes = ",".join(str(p["lon"]) for p in points)

    params: dict[str, Any] = {
        "latitude": latitudes,
        "longitude": longitudes,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(HOURLY_VARIABLES),
        "timezone": "UTC",
    }

    base_delay = 2.0
    for attempt in range(max_retries):
        try:
            logger.info(
                "Request started: sending HTTP GET to Open-Meteo (%s) for %d coordinates (range: %s to %s)...",
                base_url,
                len(points),
                start_date,
                end_date,
            )
            response = session.get(base_url, params=params, timeout=60)
            if response.status_code == 200:
                logger.info(
                    "HTTP response received: 200 OK (%d bytes payload from Open-Meteo).",
                    len(response.content),
                )
                body = response.json()
                if isinstance(body, list):
                    return body
                return [body]

            if response.status_code in (429, 500, 502, 503, 504):
                sleep_secs = base_delay * (2**attempt) + random.uniform(0.1, 1.0)
                logger.warning(
                    "HTTP %d from Open-Meteo. Backing off for %.2fs (attempt %d/%d)...",
                    response.status_code,
                    sleep_secs,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(sleep_secs)
                continue

            # Non-retryable HTTP error
            response.raise_for_status()

        except (requests.RequestException, requests.Timeout) as exc:
            if attempt == max_retries - 1:
                logger.error("Network error fetching batch from Open-Meteo: %s", exc)
                raise RuntimeError(
                    f"Open-Meteo request failed after {max_retries} attempts: {exc}"
                ) from exc
            sleep_secs = base_delay * (2**attempt) + random.uniform(0.1, 1.0)
            logger.warning("Request exception (%s). Retrying in %.2fs...", exc, sleep_secs)
            time.sleep(sleep_secs)

    raise RuntimeError(
        f"Open-Meteo API failed after {max_retries} retries for points: {points}"
    )


def save_point_year_raw(
    point: dict[str, Any],
    year: int,
    raw_data: dict[str, Any],
    raw_base_dir: Path,
) -> Path:
    """Save raw hourly response for one point-year pair as Parquet."""
    grid_id = point["grid_id"]
    point_dir = raw_base_dir / grid_id
    point_dir.mkdir(parents=True, exist_ok=True)
    out_path = point_dir / f"{year}.parquet"

    hourly_dict = raw_data.get("hourly", {})
    times = hourly_dict.get("time", [])
    if not times:
        raise ValueError(f"No hourly timestamps returned for {grid_id} year {year}")

    df = pd.DataFrame({"time": times})
    df["timestamp_utc"] = pd.to_datetime(df["time"], utc=True)
    df["grid_id"] = grid_id
    df["lat"] = float(point["lat"])
    df["lon"] = float(point["lon"])

    for var in HOURLY_VARIABLES:
        values = hourly_dict.get(var, [])
        df[var] = pd.to_numeric(values, errors="coerce")

    elevation = raw_data.get("elevation")
    if elevation is not None:
        df["elevation"] = float(elevation)

    df.drop(columns=["time"], inplace=True)
    logger.info("Rows parsed: %d hourly observations for point %s (year %d).", len(df), grid_id, year)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    logger.info("Cache written: saved raw Parquet to %s (%d rows written).", out_path, len(df))
    return out_path


def compile_processed_datasets(
    raw_base_dir: Path,
    processed_dir: Path,
    points: list[dict[str, Any]],
    years: list[int],
    hourly: bool = False,
) -> tuple[Path, Path]:
    """Compile cached raw point-year files into processed weather and metadata parquets."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    weather_out = processed_dir / ("weather_hourly.parquet" if hourly else "weather_6h.parquet")
    metadata_out = processed_dir / "grid_metadata.parquet"

    weather_frames: list[pd.DataFrame] = []
    metadata_records: list[dict[str, Any]] = []

    for point in points:
        grid_id = point["grid_id"]
        point_frames: list[pd.DataFrame] = []
        point_elevation = point.get("elevation")

        for year in years:
            p_file = raw_base_dir / grid_id / f"{year}.parquet"
            if not p_file.exists():
                raise FileNotFoundError(
                    f"Raw cache file missing for {grid_id} year {year}: {p_file}"
                )

            df_raw = pd.read_parquet(p_file, engine="pyarrow")
            if "elevation" in df_raw.columns and point_elevation is None:
                valid_el = df_raw["elevation"].dropna()
                if not valid_el.empty:
                    point_elevation = float(valid_el.iloc[0])

            if not hourly:
                # 6-hourly sampling (00, 06, 12, 18 UTC)
                df_filtered = df_raw[df_raw["timestamp_utc"].dt.hour.isin([0, 6, 12, 18])].copy()
            else:
                df_filtered = df_raw.copy()

            point_frames.append(df_filtered)

        if point_frames:
            combined_point = pd.concat(point_frames, ignore_index=True)
            weather_frames.append(combined_point)

        metadata_records.append(
            {
                "grid_id": grid_id,
                "lat": float(point["lat"]),
                "lon": float(point["lon"]),
                "elevation": point_elevation,
                "is_city": bool(point.get("is_city", False)),
                "city_name": point.get("city_name"),
            }
        )

    if not weather_frames:
        raise ValueError("No weather data frames collected to compile processed dataset.")

    full_weather = pd.concat(weather_frames, ignore_index=True)
    full_weather.sort_values(by=["grid_id", "timestamp_utc"], inplace=True)
    full_weather.reset_index(drop=True, inplace=True)

    # Ensure timestamp is timezone-aware UTC
    if full_weather["timestamp_utc"].dt.tz is None:
        full_weather["timestamp_utc"] = full_weather["timestamp_utc"].dt.tz_localize("UTC")

    full_weather.to_parquet(weather_out, index=False, engine="pyarrow")
    logger.info("Saved processed weather dataset: %s (%d rows)", weather_out, len(full_weather))

    df_meta = pd.DataFrame(metadata_records)
    df_meta.sort_values(by="grid_id", inplace=True)
    df_meta.reset_index(drop=True, inplace=True)
    df_meta.to_parquet(metadata_out, index=False, engine="pyarrow")
    logger.info("Saved grid metadata: %s (%d points)", metadata_out, len(df_meta))

    return weather_out, metadata_out


def run_pipeline(
    years: list[int],
    batch_size: int = 10,
    include_cities: bool = True,
    hourly: bool = False,
    data_dir: Path | None = None,
    open_meteo_url: str = DEFAULT_OPEN_METEO_URL,
    force_point: str | None = None,
) -> tuple[Path, Path]:
    """Execute the end-to-end historical weather fetch pipeline."""
    base_data = data_dir or Path("data")
    raw_dir = base_data / "raw" / "open_meteo"
    processed_dir = base_data / "processed"
    checkpoint_file = raw_dir / "checkpoints.json"

    points = build_grid(include_cities=include_cities)
    total_points = len(points)
    logger.info(
        "Initialized pipeline for %d points (%s) across years: %s",
        total_points,
        "grid + named cities" if include_cities else "grid only",
        years,
    )

    completed_checkpoints = load_checkpoints(checkpoint_file)
    logger.info("Loaded %d previously completed checkpoint keys.", len(completed_checkpoints))

    session = requests.Session()

    for year in years:
        start_date = f"{year}-01-01"
        # Bound end_date to last complete month or end of year
        current_year = datetime.now().year
        if year == current_year:
            current_month = datetime.now().month
            if current_month > 1:
                last_complete_month = current_month - 1
                import calendar
                _, last_day = calendar.monthrange(year, last_complete_month)
                end_date = f"{year}-{last_complete_month:02d}-{last_day:02d}"
            else:
                end_date = f"{year}-01-01"
        else:
            end_date = f"{year}-12-31"

        logger.info("Processing year %d (date range: %s to %s)...", year, start_date, end_date)

        # Filter points needing fetch for this year
        pending_points: list[dict[str, Any]] = []
        for p in points:
            key = get_checkpoint_key(p["grid_id"], year)
            p_file = raw_dir / p["grid_id"] / f"{year}.parquet"
            if force_point and p["grid_id"] == force_point:
                if key in completed_checkpoints:
                    completed_checkpoints.discard(key)
                if p_file.exists():
                    try:
                        p_file.unlink()
                    except OSError:
                        pass
                pending_points.append(p)
                continue
            if key in completed_checkpoints and p_file.exists():
                continue
            pending_points.append(p)

        logger.info(
            "Year %d: %d points already cached, %d points pending.",
            year,
            total_points - len(pending_points),
            len(pending_points),
        )

        for i in range(0, len(pending_points), batch_size):
            batch = pending_points[i : i + batch_size]
            batch_indices = f"[{i + 1}-{i + len(batch)}/{len(pending_points)}]"
            logger.info("Fetching batch %s for year %d...", batch_indices, year)

            batch_results = fetch_open_meteo_batch(
                session=session,
                base_url=open_meteo_url,
                points=batch,
                start_date=start_date,
                end_date=end_date,
            )

            if len(batch_results) != len(batch):
                raise ValueError(
                    f"Mismatch in returned points for batch {batch_indices}: "
                    f"requested {len(batch)}, received {len(batch_results)}"
                )

            for pt, res in zip(batch, batch_results):
                save_point_year_raw(pt, year, res, raw_dir)
                completed_checkpoints.add(get_checkpoint_key(pt["grid_id"], year))

            save_checkpoint(checkpoint_file, completed_checkpoints)

    logger.info("All raw point-year Parquet files verified and cached.")
    return compile_processed_datasets(
        raw_base_dir=raw_dir,
        processed_dir=processed_dir,
        points=points,
        years=years,
        hourly=hourly,
    )


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point for fetch_history."""
    parser = argparse.ArgumentParser(description="SDARS Historical Weather Data Pipeline")
    parser.add_argument(
        "--years",
        nargs=2,
        type=int,
        metavar=("START_YEAR", "END_YEAR"),
        help="Start and end year for historical pull (e.g. --years 2024 2024)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size of coordinates per API call (default: 10)",
    )
    parser.add_argument(
        "--cities-only",
        action="store_true",
        help="Fetch only named cities instead of full grid",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base data directory (default: data)",
    )
    parser.add_argument(
        "--force-point",
        type=str,
        default=None,
        help="Force re-fetch of a specific grid point by bypassing cached checkpoint",
    )

    args = parser.parse_args(argv)

    log_path = Path(args.data_dir) / "logs" / "fetch_history.log"
    setup_logging(log_path)

    hourly_env = os.getenv("HOURLY", "false").lower() in ("true", "1", "yes")
    open_meteo_url = os.getenv("OPEN_METEO_BASE_URL", DEFAULT_OPEN_METEO_URL)

    if args.years:
        year_list = list(range(args.years[0], args.years[1] + 1))
    else:
        # Default full archive baseline from 1990 to current year
        current_year = datetime.now().year
        year_list = list(range(1990, current_year + 1))

    logger.info("Starting historical fetch pipeline with years: %s", year_list)
    weather_file, meta_file = run_pipeline(
        years=year_list,
        batch_size=args.batch_size,
        include_cities=True,
        hourly=hourly_env,
        data_dir=Path(args.data_dir),
        open_meteo_url=open_meteo_url,
        force_point=args.force_point,
    )

    logger.info("Pipeline complete. Output files: %s, %s", weather_file, meta_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
