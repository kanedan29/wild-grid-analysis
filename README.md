# Wild Grid Analysis: Perennial Cover in Cropland Watersheds

Analysis supporting the [Mad Agriculture](https://madagriculture.org) wilding white paper. The goal is to identify US HUC12 watersheds that are predominantly agricultural yet have little perennial vegetation cover — the landscapes with the greatest opportunity for perennial cover adoption.

## What This Analysis Does

1. Loads all ~100,000 HUC12 subwatersheds nationally from the USGS Watershed Boundary Dataset
2. Computes per-watershed NLCD land cover statistics using the 2024 National Land Cover Database
3. Filters to watersheds where **>50% of area is cultivated cropland** (NLCD class 82)
4. Reports the **percentage of each watershed in perennial cover** (forest, shrubland, grassland, wetlands)
5. Outputs a CSV and map identifying where perennial cover is most lacking

## Key Findings

Of 12,412 majority-cropland HUC12 watersheds in the contiguous US:
- **8,729 (70%)** have less than 20% perennial cover
- These watersheds encompass **~195 million acres** of land, of which **~151 million acres** is cropland
- Bringing all of these watersheds to a 20% perennial cover threshold would require planting approximately **22.9 million acres** of perennial vegetation
- The deficit is concentrated in the Corn Belt (Iowa, Illinois, Minnesota, Indiana, Ohio) and the Central Valley of California

## Land Cover Definitions

**Cropland** — NLCD class 82 (Cultivated Crops), derived from the USDA Cropland Data Layer

**Perennial cover** — NLCD classes:
| Code | Cover type |
|------|-----------|
| 41 | Deciduous Forest |
| 42 | Evergreen Forest |
| 43 | Mixed Forest |
| 52 | Shrub/Scrub |
| 71 | Grassland/Herbaceous |
| 90 | Woody Wetlands |
| 95 | Emergent Herbaceous Wetlands |

## Data Sources

| Dataset | Source | Year |
|---------|--------|------|
| National Land Cover Database (NLCD) | [USGS/MRLC](https://www.mrlc.gov/data) | 2024 |
| Watershed Boundary Dataset (WBD), HUC12 | [USGS National Map](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset) | Current |

> **Note:** The NLCD raster (~4 GB) and WBD GeoPackage (~2.2 GB) are not included in this repository due to file size. See setup instructions below.

## Repository Structure

```
wild_grid_analysis/
├── watershed_cropland_analysis.py  # Main analysis script
├── perennial_cover_map.py          # Map generation script
├── quick_stats.py                  # Summary statistics
├── utils.py                        # Geospatial utility functions
├── data/                           # Large files (gitignored — see setup below)
│   └── wbd_huc12_national.gpkg     # Downloaded automatically on first run
└── results/
    ├── cropland_watersheds.csv     # Output: all qualifying watersheds
    └── perennial_cover_map.png     # Output: perennial cover map
```

## Setup

### Requirements

```
geopandas
rasterio
rasterstats
numpy
pandas
matplotlib
shapely
requests
```

With conda:
```bash
conda create -n wild_grid python=3.11
conda activate wild_grid
conda install -c conda-forge geopandas rasterio rasterstats numpy pandas matplotlib shapely
```

### Data Setup

1. **NLCD 2024**: Download `Annual_NLCD_LndCov_2024_CU_C1V1.tif` from [MRLC](https://www.mrlc.gov/data) and place it in `data/`
2. **WBD**: Downloaded automatically on first run and cached to `data/wbd_huc12_national.gpkg`

### Running the Analysis

```bash
python watershed_cropland_analysis.py   # generates results/cropland_watersheds.csv
python perennial_cover_map.py           # generates results/perennial_cover_map.png
python quick_stats.py                   # prints summary statistics
```

## Output

`results/cropland_watersheds.csv` — one row per qualifying HUC12 watershed:

| Column | Description |
|--------|-------------|
| `state` | State code(s) from WBD (comma-separated for multi-state watersheds) |
| `huc12` | 12-digit HUC code |
| `name` | Watershed name |
| `area_total_ha` | Total watershed area (hectares) |
| `area_cropland_ha` | Cultivated cropland area (hectares) |
| `area_perennial_ha` | Perennial cover area (hectares) |
| `pct_cropland` | Cropland as % of total watershed area |
| `pct_perennial` | Perennial cover as % of total watershed area |

## Citation

If you use this analysis, please cite:

> Mad Agriculture. (2026). *Wild Grid Analysis: Perennial Cover in US Cropland Watersheds*. GitHub. https://github.com/kanedan29/wild-grid-analysis

## License

MIT — see [LICENSE](LICENSE)
