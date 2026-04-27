"""
utils.py

Core geospatial utility functions for the wild_grid_analysis project.
These are adapted from the MadAg wilding project library (lib/pylding.py).
"""

import os
import zipfile
import tempfile
import urllib.request

import numpy as np
import geopandas as gpd
import rasterio
from shapely.geometry import box
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds


def create_transform_and_shape(bound, crs="EPSG:5070", resolution=30):
    """
    Creates a consistent affine transform and raster shape for a given boundary.

    Args:
        bound (GeoDataFrame): Boundary in any CRS (will be reprojected).
        crs (str): Target CRS (default EPSG:5070).
        resolution (int): Pixel size in target CRS units (default 30m).

    Returns:
        tuple: (Affine transform, (height, width))
    """
    bound_proj = bound.to_crs(crs)
    minx, miny, maxx, maxy = bound_proj.total_bounds
    width = int(np.ceil((maxx - minx) / resolution))
    height = int(np.ceil((maxy - miny) / resolution))
    maxx = minx + (width * resolution)
    maxy = miny + (height * resolution)
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    return transform, (height, width)


def download_wbd_national(output_dir, huc=12):
    """
    Downloads the national Watershed Boundary Dataset (WBD) from the USGS National Map
    staged products S3 bucket and saves the specified HUC layer as a GeoPackage locally.
    On subsequent calls, loads from the cached file instead of re-downloading.

    Args:
        output_dir (str): Directory in which to save the cached GeoPackage.
        huc (int): HUC level to extract (default 12). Must be one of 2, 4, 6, 8, 10, 12.

    Returns:
        GeoDataFrame: HUC boundary data in EPSG:4326.
    """
    import os, zipfile, tempfile, urllib.request
    import geopandas as gpd

    layer_name = f"WBDHU{huc}"
    gpkg_path = os.path.join(output_dir, f"wbd_huc{huc}_national.gpkg")

    if os.path.exists(gpkg_path):
        print(f"Loading cached WBD HUC{huc} from {gpkg_path}")
        return gpd.read_file(gpkg_path).to_crs("EPSG:4326")

    url = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/WBD/National/GDB/WBD_National_GDB.zip"
    print(f"Downloading national WBD from {url} ...")

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "WBD_National_GDB.zip")
        urllib.request.urlretrieve(url, zip_path)

        print("Extracting archive ...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)

        gdb_path = None
        for root, dirs, files in os.walk(tmpdir):
            for d in dirs:
                if d.endswith(".gdb"):
                    gdb_path = os.path.join(root, d)
                    break
            if gdb_path:
                break

        if gdb_path is None:
            raise FileNotFoundError("Could not find a .gdb in the downloaded archive.")

        print(f"Reading layer {layer_name} ...")
        gdf = gpd.read_file(gdb_path, layer=layer_name)
        gdf = gdf.to_crs("EPSG:4326")

        os.makedirs(output_dir, exist_ok=True)
        print(f"Saving to {gpkg_path} ...")
        gdf.to_file(gpkg_path, driver="GPKG")

    return gdf


def get_nlcd_bulk_stats(nlcd_path, watersheds_gdf):
    """
    Computes per-watershed NLCD pixel counts for all watersheds in a single efficient
    pass using rasterstats.

    Args:
        nlcd_path (str): Path to the NLCD GeoTIFF (EPSG:5070, 30m).
        watersheds_gdf (GeoDataFrame): Watershed polygons in any CRS.

    Returns:
        list[dict]: One dict per watershed mapping NLCD class code (int) -> pixel count.
    """
    from rasterstats import zonal_stats

    with rasterio.open(nlcd_path) as src:
        nlcd_crs = src.crs
        nodata = src.nodata

    watersheds_proj = watersheds_gdf.to_crs(nlcd_crs)

    stats = zonal_stats(
        watersheds_proj,
        nlcd_path,
        categorical=True,
        nodata=nodata,
        all_touched=False,
    )

    cleaned = []
    for s in stats:
        if s is None:
            cleaned.append({})
        else:
            cleaned.append({int(k): v for k, v in s.items()})

    return cleaned
