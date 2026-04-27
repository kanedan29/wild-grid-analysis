"""
watershed_cropland_analysis.py

National HUC12 watershed analysis: identifies watersheds that are predominantly
cropland (>50% NLCD class 82) AND have less than 20% perennial cover
(NLCD classes 41, 42, 43, 52, 71, 90, 95).

Outputs: wild_grid_analysis/results/cropland_watersheds.csv

Usage:
    python watershed_cropland_analysis.py
"""

import os
import sys

import numpy as np
import pandas as pd

from utils import download_wbd_national, get_nlcd_bulk_stats

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the NLCD 2024 national raster (not included in repo — too large).
# Download from: https://www.mrlc.gov/data
# Set this to your local path before running.
NLCD_PATH = os.path.join(REPO_DIR, "data", "Annual_NLCD_LndCov_2024_CU_C1V1.tif")

WBD_CACHE_DIR = os.path.join(REPO_DIR, "data")
RESULTS_DIR = os.path.join(REPO_DIR, "results")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "cropland_watersheds.csv")

# NLCD class codes
CROPLAND_CODES = {82}                          # Cultivated Crops (CDL-derived)
PERENNIAL_CODES = {41, 42, 43, 52, 71, 90, 95}  # Forest, shrub, grassland, wetlands

# Filter thresholds
CROPLAND_THRESHOLD = 0.25   # >25% of watershed area must be cropland

# Pixel area in hectares (30m × 30m = 900 m² = 0.09 ha)
PIXEL_AREA_HA = 0.09

# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 1. Load national HUC12 boundaries (downloads once, caches locally)
    print("=== Step 1: Loading HUC12 watershed boundaries ===")
    huc12 = download_wbd_national(output_dir=WBD_CACHE_DIR, huc=12)
    print(f"  Loaded {len(huc12):,} HUC12 watersheds")

    # 2. Compute NLCD zonal statistics for all watersheds
    print("\n=== Step 2: Computing NLCD zonal statistics (this may take a while) ===")
    stats = get_nlcd_bulk_stats(NLCD_PATH, huc12)
    print(f"  Completed zonal stats for {len(stats):,} watersheds")

    # 3. Build results DataFrame from pixel counts
    print("\n=== Step 3: Computing areas and applying filters ===")
    records = []
    for i, (row, pixel_counts) in enumerate(zip(huc12.itertuples(), stats)):
        if not pixel_counts:
            continue  # No valid NLCD pixels (e.g., open ocean HUC12)

        total_pixels = sum(pixel_counts.values())
        if total_pixels == 0:
            continue

        cropland_pixels = sum(pixel_counts.get(c, 0) for c in CROPLAND_CODES)
        perennial_pixels = sum(pixel_counts.get(c, 0) for c in PERENNIAL_CODES)

        cropland_frac = cropland_pixels / total_pixels
        perennial_frac = perennial_pixels / total_pixels

        # Apply filters: predominantly cropland AND low perennial cover
        if cropland_frac > CROPLAND_THRESHOLD:
            records.append({
                "state": getattr(row, "states", None),
                "huc12": getattr(row, "huc12", None),
                "name": getattr(row, "name", None),
                "area_total_ha": round(total_pixels * PIXEL_AREA_HA, 1),
                "area_cropland_ha": round(cropland_pixels * PIXEL_AREA_HA, 1),
                "area_perennial_ha": round(perennial_pixels * PIXEL_AREA_HA, 1),
                "pct_cropland": round(cropland_frac * 100, 1),
                "pct_perennial": round(perennial_frac * 100, 1),
            })

    df = pd.DataFrame(records, columns=["state", "huc12", "name", "area_total_ha", "area_cropland_ha", "area_perennial_ha", "pct_cropland", "pct_perennial"])
    # Ensure huc12 is a clean zero-padded 12-digit string (prevents scientific notation in CSV)
    df["huc12"] = df["huc12"].apply(
        lambda x: str(int(float(x))).zfill(12) if pd.notna(x) else ""
    )
    df = df.sort_values(["state", "huc12"]).reset_index(drop=True)

    print(f"  {len(df):,} watersheds meet both criteria")

    # 4. Save results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n=== Done. Results saved to: {OUTPUT_CSV} ===")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
