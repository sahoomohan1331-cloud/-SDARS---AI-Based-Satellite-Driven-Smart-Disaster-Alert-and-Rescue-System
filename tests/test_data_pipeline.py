"""Unit and integration tests for SDARS historical data pipeline."""

from __future__ import annotations

import unittest.mock
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests

from backend.data_pipeline.fetch_history import (
    HOURLY_VARIABLES,
    NAMED_CITIES,
    build_grid,
    fetch_open_meteo_batch,
)


def test_grid_generation():
    """Verify that the 0.5-degree grid over the Odisha bbox has the exact expected cell count."""
    lat_min, lat_max = 17.8, 22.6
    lon_min, lon_max = 81.3, 87.5
    step = 0.5

    grid = build_grid(lat_min, lat_max, lon_min, lon_max, step=step, include_cities=False)

    # Compute expected number of regular grid cells
    lat_steps = len(
        [
            round(lat, 4)
            for lat in np.arange(lat_min, lat_max + 1e-6, step)
            if lat <= lat_max + 1e-6
        ]
    )
    lon_steps = len(
        [
            round(lon, 4)
            for lon in np.arange(lon_min, lon_max + 1e-6, step)
            if lon <= lon_max + 1e-6
        ]
    )
    expected_cells = lat_steps * lon_steps

    assert len(grid) == expected_cells
    assert len(grid) == 130  # 10 latitude steps x 13 longitude steps

    for cell in grid:
        assert lat_min <= cell["lat"] <= lat_max
        assert lon_min <= cell["lon"] <= lon_max
        assert cell["is_city"] is False
        assert cell["city_name"] is None

    # Test grid with named cities included
    full_grid = build_grid(lat_min, lat_max, lon_min, lon_max, step=step, include_cities=True)
    assert len(full_grid) == expected_cells + len(NAMED_CITIES)
    assert len(full_grid) == 138

    cities_in_grid = [c for c in full_grid if c["is_city"]]
    assert len(cities_in_grid) == len(NAMED_CITIES)
    for city in cities_in_grid:
        assert city["city_name"] is not None
        assert lat_min <= city["lat"] <= lat_max
        assert lon_min <= city["lon"] <= lon_max


def test_no_synthetic_fallback(monkeypatch):
    """Verify that if Open-Meteo returns HTTP 500, fetch raises and NEVER substitutes default values."""
    mock_response = unittest.mock.MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    mock_session = unittest.mock.MagicMock()
    mock_session.get.return_value = mock_response

    sample_point = [{"grid_id": "test_grid_01", "lat": 20.0, "lon": 85.0}]

    with pytest.raises(RuntimeError) as exc_info:
        fetch_open_meteo_batch(
            session=mock_session,
            base_url="https://archive-api.open-meteo.com/v1/archive",
            points=sample_point,
            start_date="2024-01-01",
            end_date="2024-01-02",
            max_retries=1,
        )

    assert "Open-Meteo API failed" in str(exc_info.value) or "500" in str(exc_info.value)


def test_parquet_schema():
    """Verify that processed weather_6h.parquet contains required columns and timezone-aware UTC timestamps."""
    weather_path = Path("data/processed/weather_6h.parquet")
    if not weather_path.exists():
        pytest.skip("weather_6h.parquet not found on disk (run smoke fetch first)")

    df = pd.read_parquet(weather_path)
    required_cols = [
        "grid_id",
        "lat",
        "lon",
        "timestamp_utc",
        *HOURLY_VARIABLES,
    ]

    for col in required_cols:
        assert col in df.columns, f"Missing required column '{col}' in {weather_path}"

    assert df["timestamp_utc"].dt.tz is not None
    assert str(df["timestamp_utc"].dt.tz).upper() == "UTC"

    # Verify 6-hourly sampling (0, 6, 12, 18 UTC)
    hours = df["timestamp_utc"].dt.hour.unique()
    assert set(hours).issubset({0, 6, 12, 18})


def test_terrain_schema():
    """Verify that processed terrain.parquet contains required columns and valid slopes."""
    terrain_path = Path("data/processed/terrain.parquet")
    if not terrain_path.exists():
        pytest.skip("terrain.parquet not found on disk (run terrain pipeline first)")

    df = pd.read_parquet(terrain_path)
    required_cols = [
        "grid_id",
        "mean_elevation_m",
        "max_elevation_m",
        "min_elevation_m",
        "max_slope_deg",
    ]

    for col in required_cols:
        assert col in df.columns, f"Missing required column '{col}' in {terrain_path}"

    assert (df["max_slope_deg"] >= 0.0).all(), "Slope degrees must be non-negative"
    assert (df["max_elevation_m"] >= df["min_elevation_m"]).all(), "Max elevation must be >= min elevation"


def test_datasets_md_exists():
    """Verify that data/DATASETS.md exists and documents every processed Parquet file on disk."""
    datasets_md = Path("data/DATASETS.md")
    assert datasets_md.exists(), "data/DATASETS.md must exist"

    content = datasets_md.read_text(encoding="utf-8")
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        for parquet_file in processed_dir.glob("*.parquet"):
            rel_name = parquet_file.name
            assert rel_name in content, f"Processed parquet file '{rel_name}' is not documented in data/DATASETS.md"
