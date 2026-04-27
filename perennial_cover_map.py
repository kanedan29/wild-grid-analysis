"""
perennial_cover_map.py

Generates a minimalist US map showing % perennial cover across HUC12 watersheds
with >=25% cropland cover. Styled after a sparse, line-weight-forward aesthetic
on a white background.

Output: wild_grid_analysis/results/perennial_cover_map.png
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
import matplotlib.cm as cm

REPO_DIR    = os.path.dirname(os.path.abspath(__file__))
WBD_CACHE   = os.path.join(REPO_DIR, "data", "wbd_huc12_national.gpkg")
RESULTS_CSV = os.path.join(REPO_DIR, "results", "cropland_watersheds.csv")
OUTPUT_PNG  = os.path.join(REPO_DIR, "results", "perennial_cover_map.png")

# ---------------------------------------------------------------------------
# City reference points (lon, lat)
# ---------------------------------------------------------------------------
CITIES = {
    "Seattle":         (-122.33, 47.61),
    "San Francisco":   (-122.42, 37.77),
    "Los Angeles":     (-118.24, 34.05),
    "Phoenix":         (-112.07, 33.45),
    "Denver":          (-104.99, 39.74),
    "Minneapolis":     (-93.27,  44.98),
    "Chicago":         (-87.63,  41.88),
    "Pittsburgh":      (-79.99,  40.44),
    "Washington, D.C.":(-77.04,  38.91),
    "New York":        (-74.01,  40.71),
    "Boston":          (-71.06,  42.36),
    "Atlanta":         (-84.39,  33.75),
    "Dallas":          (-96.80,  32.78),
    "Houston":         (-95.37,  29.76),
    "Miami":           (-80.19,  25.77),
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading results CSV ...")
df = pd.read_csv(RESULTS_CSV, dtype={"huc12": str})

print("Loading HUC12 boundaries ...")
gdf_full = gpd.read_file(WBD_CACHE, dtype={"huc12": str})
gdf_full["huc12"] = gdf_full["huc12"].astype(str).str.strip()
df["huc12"] = df["huc12"].astype(str).str.strip()

# Join perennial cover % onto geometries — filter to majority-cropland watersheds only
df_50 = df[df["pct_cropland"] > 50]
gdf = gdf_full.merge(df_50[["huc12", "pct_perennial"]], on="huc12", how="inner")
gdf = gdf.to_crs("EPSG:5070")  # Albers Equal Area

# US states for background context
print("Loading state boundaries ...")
states = gpd.read_file(
    "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip"
)
states = states[~states["STUSPS"].isin(["AK", "HI", "PR", "VI", "GU", "MP", "AS"])]
states = states.to_crs("EPSG:5070")

# ---------------------------------------------------------------------------
# Color mapping — diverging brown/yellow → green, threshold at 20%
# ---------------------------------------------------------------------------
# Colormap midpoint = 20% threshold via TwoSlopeNorm:
# values 0–20% map to the brown→yellow half; 20–100% map to the green half
cmap = mcolors.LinearSegmentedColormap.from_list(
    "peren",
    [
        "#6b3a1f",   # 0%   — dark brown
        "#c17f3a",   # ~10% — warm brown
        "#e8c97a",   # 20%  — yellow pivot (colormap midpoint)
        "#a8d08d",   # ~40% — light green
        "#4a9e5c",   # ~65% — medium green
        "#1a5c34",   # 100% — deep green
    ],
    N=256
)
norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=20, vmax=100)

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
print("Rendering map ...")
fig, ax = plt.subplots(1, 1, figsize=(18, 11), facecolor="white")
ax.set_facecolor("white")

# State outlines — very faint
states.boundary.plot(ax=ax, linewidth=0.4, edgecolor="#cccccc", zorder=1)

# Watersheds colored by pct_perennial
gdf.plot(
    ax=ax,
    column="pct_perennial",
    cmap=cmap,
    norm=norm,
    linewidth=0.05,
    edgecolor="none",
    zorder=2,
)


# Tighten extent to data bounds with a small buffer
buf = 150_000   # metres in EPSG:5070
minx, miny, maxx, maxy = gdf.total_bounds
ax.set_xlim(minx - buf, maxx + buf)
ax.set_ylim(miny - buf, maxy + buf)

# ---------------------------------------------------------------------------
# City labels
# ---------------------------------------------------------------------------
city_gdf = gpd.GeoDataFrame(
    list(CITIES.keys()),
    geometry=gpd.points_from_xy(
        [v[0] for v in CITIES.values()],
        [v[1] for v in CITIES.values()]
    ),
    crs="EPSG:4326"
).to_crs("EPSG:5070")
city_gdf.columns = ["name", "geometry"]

for _, row in city_gdf.iterrows():
    ax.annotate(
        row["name"],
        xy=(row.geometry.x, row.geometry.y),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=6.5,
        color="#444444",
        fontfamily="sans-serif",
        fontweight="light",
        zorder=5,
    )
    ax.plot(row.geometry.x, row.geometry.y, ".", markersize=2.5, color="#888888", zorder=4)

# ---------------------------------------------------------------------------
# Colorbar
# ---------------------------------------------------------------------------
cax = fig.add_axes([0.15, 0.08, 0.22, 0.012])  # [left, bottom, width, height]
cb = ColorbarBase(cax, cmap=cmap, norm=norm, orientation="horizontal")
cb.set_label("% perennial cover", fontsize=8, color="#444444", labelpad=4)
cb.ax.tick_params(labelsize=7, color="#888888", labelcolor="#444444")
cb.outline.set_edgecolor("#cccccc")
# Mark 20% threshold on colorbar
cb.ax.axvline(x=20, color="#e8c97a", linewidth=1.5, linestyle="--")
cb.ax.text(20, 1.6, "20%", ha="center", va="bottom", fontsize=6.5,
           color="#444444", transform=cb.ax.transData)

# ---------------------------------------------------------------------------
# Title & cleanup
# ---------------------------------------------------------------------------
ax.set_title(
    "Perennial cover in majority cropland watersheds (>50% cropland, HUC12)",
    fontsize=11,
    color="#333333",
    fontweight="light",
    pad=12,
    loc="center",
)

ax.set_axis_off()
plt.tight_layout(pad=0.5)

print(f"Saving to {OUTPUT_PNG} ...")
fig.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight", facecolor="white")
print("Done.")
