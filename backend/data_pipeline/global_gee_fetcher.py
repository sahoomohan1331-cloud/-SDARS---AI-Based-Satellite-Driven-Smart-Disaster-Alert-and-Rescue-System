"""Google Earth Engine Global ERA5 Reanalysis Pipeline.

Extracts 6-hourly ERA5 historical atmospheric and land variables globally
via Earth Engine cloud export tasks partitioned by calendar year directly
into Google Drive without downloading massive raw global rasters locally.

Dataset: ECMWF/ERA5/HOURLY
Resolution: 6-hourly (00:00, 06:00, 12:00, 18:00 UTC)
Output: ee.batch.Export.table.toDrive CSV containing tabular point extractions.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

import ee

# 12 Target ERA5 Variables in ECMWF/ERA5/HOURLY
ERA5_HOURLY_VARIABLES: list[str] = [
    "temperature_2m",
    "dewpoint_temperature_2m",
    "surface_pressure",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
    "instantaneous_10m_wind_gust",
    "total_precipitation",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "convective_available_potential_energy",
    "total_cloud_cover",
]

DEFAULT_COLLECTION_ID: str = "ECMWF/ERA5/HOURLY"
DEFAULT_LAND_DATASET: str = "USDOS/LSIB_SIMPLE/2017"
DEFAULT_EXPORT_FOLDER: str = "SDARS_ERA5_Exports"

logger = logging.getLogger("global_gee_fetcher")


def setup_logging() -> logging.Logger:
    """Configure stdout logging."""
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def init_gee(project: str | None = None) -> None:
    """Initialize Google Earth Engine API using stored credentials.

    Uses ee.Initialize() with no arguments by default, or reads from
    EE_PROJECT / EARTHENGINE_PROJECT / GOOGLE_CLOUD_PROJECT if specified.

    Args:
        project: Optional Google Cloud project ID. If not provided, checks
                 environment variables, otherwise calls ee.Initialize().
    """
    project_id = (
        project
        or os.getenv("EE_PROJECT")
        or os.getenv("EARTHENGINE_PROJECT")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
    )

    # Filter out empty strings or template placeholders
    if project_id and project_id.strip() and not project_id.strip().startswith("your_"):
        active_project = project_id.strip()
        logger.info("Initializing Earth Engine with project: '%s'...", active_project)
        try:
            ee.Initialize(project=active_project)
            logger.info("Earth Engine successfully initialized with project: %s", active_project)
            return
        except Exception as exc:
            logger.warning("Initialization with project '%s' failed: %s. Falling back to default...", active_project, exc)

    logger.info("Initializing Earth Engine with default authenticated credentials...")
    try:
        ee.Initialize()
        logger.info("Earth Engine successfully initialized.")
    except Exception as exc:
        logger.error("Failed to initialize Earth Engine: %s", exc)
        raise


def generate_random_land_points(
    num_points: int = 2000, seed: int = 42
) -> ee.FeatureCollection:
    """Generate randomly distributed sample points constrained to global landmasses.

    Uses the simplified international boundaries dataset (USDOS/LSIB_SIMPLE/2017)
    as the land mask to ensure points fall on land surfaces.
    """
    logger.info("Generating %d random global land points (seed=%d)...", num_points, seed)
    land = ee.FeatureCollection(DEFAULT_LAND_DATASET)
    land_geom = land.geometry()

    raw_points = ee.FeatureCollection.randomPoints(
        region=land_geom, points=num_points, seed=seed
    )

    def attach_point_metadata(feature: ee.Feature) -> ee.Feature:
        coords = feature.geometry().coordinates()
        return feature.set({
            "point_id": feature.id(),
            "lon": coords.get(0),
            "lat": coords.get(1),
        })

    points_with_meta = raw_points.map(attach_point_metadata)
    return points_with_meta


def get_era5_collection_6hourly(
    start_date: str,
    end_date: str,
    variables: list[str] = ERA5_HOURLY_VARIABLES,
) -> ee.ImageCollection:
    """Filter ECMWF/ERA5/HOURLY to date range, target variables, and 6-hourly timesteps (00, 06, 12, 18 UTC)."""
    logger.info("Filtering %s collection between %s and %s...", DEFAULT_COLLECTION_ID, start_date, end_date)
    logger.info("Selecting %d variables: %s", len(variables), variables)

    col = (
        ee.ImageCollection(DEFAULT_COLLECTION_ID)
        .filterDate(start_date, end_date)
        .select(variables)
    )

    # Filter to 6-hourly timesteps: 00:00, 06:00, 12:00, 18:00 UTC
    six_hourly_filter = ee.Filter.Or(
        ee.Filter.calendarRange(0, 0, "hour"),
        ee.Filter.calendarRange(6, 6, "hour"),
        ee.Filter.calendarRange(12, 12, "hour"),
        ee.Filter.calendarRange(18, 18, "hour"),
    )

    filtered_col = col.filter(six_hourly_filter)
    return filtered_col


def extract_points_time_series(
    collection: ee.ImageCollection,
    points: ee.FeatureCollection,
) -> ee.FeatureCollection:
    """Extract raster values at all point locations for each image in the collection."""
    logger.info("Building point-time extraction graph across collection...")

    def sample_image(img: ee.Image) -> ee.FeatureCollection:
        time_str = img.date().format("YYYY-MM-dd HH:mm:ss")
        time_ms = img.get("system:time_start")

        samples = img.sampleRegions(
            collection=points,
            properties=["point_id", "lat", "lon"],
            scale=27830,  # ~0.25° ERA5 native resolution
            geometries=False,
        )

        return samples.map(lambda f: f.set({
            "timestamp_utc": time_str,
            "system_time_start": time_ms,
        }))

    sampled_table = collection.map(sample_image).flatten()
    return sampled_table


def submit_export_task(
    table: ee.FeatureCollection,
    description: str = "era5_global_sample_export",
    folder: str = DEFAULT_EXPORT_FOLDER,
    file_prefix: str = "era5_global_sample_202401",
    dry_run: bool = False,
) -> ee.batch.Task:
    """Submit an asynchronous table export task to Google Drive.

    Args:
        table: FeatureCollection containing tabular point extractions.
        description: Name of the task in GEE Task manager.
        folder: Google Drive folder to write CSV into.
        file_prefix: Output CSV filename prefix.
        dry_run: If True, creates task without starting it.

    Returns:
        The created ee.batch.Task object.
    """
    logger.info("Creating export task for Google Drive (folder: '%s', prefix: '%s')...", folder, file_prefix)

    task = ee.batch.Export.table.toDrive(
        collection=table,
        description=description,
        folder=folder,
        fileNamePrefix=file_prefix,
        fileFormat="CSV",
    )
    if not dry_run:
        task.start()
        logger.info("Task started. GEE Task ID: %s", task.id)
    else:
        logger.info("DRY-RUN: Task graph built successfully (not started).")
    return task


def export_global_dataset(
    start_year: int = 1990,
    end_year: int = 2025,
    points_count: int = 2000,
    folder: str = DEFAULT_EXPORT_FOLDER,
    project: str | None = None,
    dry_run: bool = False,
) -> list[ee.batch.Task]:
    """Execute annual chunked exports of global 6-hourly ERA5 reanalysis data to Google Drive.

    Chunks the temporal query by YEAR to avoid hitting GEE batch computation or
    table export memory limits, submitting one independent task per calendar year.

    Args:
        start_year: First year to export (e.g. 1990).
        end_year: Final year to export (inclusive, e.g. 2025).
        points_count: Number of randomly distributed global land sample points.
        folder: Target Google Drive folder name.
        project: Optional Google Cloud project ID for GEE.
        dry_run: If True, builds tasks without starting them.

    Returns:
        List of created Task objects.
    """
    init_gee(project=project)

    logger.info("=" * 80)
    logger.info("GEE ERA5 36-YEAR GLOBAL PIPELINE: %d - %d (%d land points)", start_year, end_year, points_count)
    logger.info("Chunking strategy: 1 task per year (%d total annual tasks)", end_year - start_year + 1)
    logger.info("Target Drive folder: '%s'", folder)
    logger.info("=" * 80)

    # 1. Generate consistent global points across all annual slices
    points = generate_random_land_points(num_points=points_count, seed=42)

    tasks: list[ee.batch.Task] = []

    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"
        end_date = f"{year + 1}-01-01"
        task_desc = f"era5_global_{points_count}pts_{year}"
        file_prefix = f"era5_global_{points_count}pts_{year}"

        logger.info("--- Preparing Year %d [%s to %s] ---", year, start_date, end_date)

        # 2. Filter collection for single year at 6-hourly timesteps
        col = get_era5_collection_6hourly(
            start_date=start_date,
            end_date=end_date,
            variables=ERA5_HOURLY_VARIABLES,
        )

        # 3. Extract time series table
        table = extract_points_time_series(col, points)

        # 4. Create and submit annual export task
        task = submit_export_task(
            table=table,
            description=task_desc,
            folder=folder,
            file_prefix=file_prefix,
            dry_run=dry_run,
        )
        tasks.append(task)

    logger.info("=" * 80)
    logger.info("Successfully queued %d annual export tasks to Google Drive.", len(tasks))
    logger.info("Visit https://code.earthengine.google.com/ and check the Tasks tab to monitor progress.")
    logger.info("=" * 80)

    return tasks


def run_test_sample(project: str | None = None) -> str:
    """Execute test run: 100 global land points, January 2024, 6-hourly, submit export."""
    init_gee(project=project)

    logger.info("=" * 75)
    logger.info("GEE ERA5 GLOBAL PIPELINE TEST: 100 Land Points (Jan 1 - Feb 1, 2024)")
    logger.info("=" * 75)

    # 1. 100 random global land points
    points = generate_random_land_points(num_points=100, seed=42)

    # 2. Filter collection for January 2024 (inclusive 2024-01-01 to 2024-02-01)
    col = get_era5_collection_6hourly(
        start_date="2024-01-01",
        end_date="2024-02-01",
        variables=ERA5_HOURLY_VARIABLES,
    )

    # 3. Extract time series table
    table = extract_points_time_series(col, points)

    # 4. Submit export task
    task = submit_export_task(
        table=table,
        description="era5_global_100pts_jan2024",
        folder=DEFAULT_EXPORT_FOLDER,
        file_prefix="era5_global_100pts_jan2024",
    )

    task_id = str(task.id)
    print("\n" + "=" * 80)
    print(f"GEE Task ID: {task_id}")
    print("Task submitted. Go to https://code.earthengine.google.com/ and check the Tasks tab.")
    print("=" * 80 + "\n")

    return task_id


def main():
    parser = argparse.ArgumentParser(description="Google Earth Engine Global ERA5 Data Fetcher")
    parser.add_argument("--project", type=str, default=None, help="Google Cloud project ID for GEE")
    parser.add_argument("--test-run", action="store_true", help="Submit test export task for 100 global points (Jan 2024)")
    parser.add_argument(
        "--export-years",
        nargs=2,
        type=int,
        metavar=("START_YEAR", "END_YEAR"),
        help="Export full annual chunked global dataset (e.g. --export-years 1990 2025)",
    )
    parser.add_argument("--points-count", type=int, default=2000, help="Number of random global land points (default: 2000)")
    parser.add_argument("--folder", type=str, default=DEFAULT_EXPORT_FOLDER, help="Google Drive folder name")
    parser.add_argument("--dry-run", action="store_true", help="Build export task graphs without starting them")
    args = parser.parse_args()

    setup_logging()

    if args.export_years:
        export_global_dataset(
            start_year=args.export_years[0],
            end_year=args.export_years[1],
            points_count=args.points_count,
            folder=args.folder,
            project=args.project,
            dry_run=args.dry_run,
        )
    elif args.test_run:
        run_test_sample(project=args.project)
    else:
        logger.info("No action specified. Use --test-run or --export-years <START_YEAR> <END_YEAR>.")


if __name__ == "__main__":
    main()
