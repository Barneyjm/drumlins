"""Fetch USGS 3DEP 1/3 arc-second DEM over a bbox, mosaic, reproject to UTM at a target
resolution, and write a GeoTIFF plus a hydro-flattened-water mask."""
import sys, numpy as np, rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import from_bounds
from scipy import ndimage as ndi

TILES = [
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n43w077/USGS_13_n43w077_20230227.tif",
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n43w078/USGS_13_n43w078_20230227.tif",
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n44w077/USGS_13_n44w077_20260316.tif",
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n44w078/USGS_13_n44w078_20260316.tif",
]
BBOX = (-77.6, 42.75, -76.1, 43.45)   # lon_min, lat_min, lon_max, lat_max
DST_CRS, RES = "EPSG:32618", 10.0


def main(out="/home/claude/drumlins/data/ny_dem_10m.tif"):
    import os; os.makedirs(os.path.dirname(out), exist_ok=True)
    srcs = [rasterio.open("/vsicurl/" + u) for u in TILES]
    for s in srcs:
        print(s.name.split('/')[-1], s.crs, s.res, s.profile.get("tiled"), s.profile.get("blockxsize"))
    mosaic, tr = merge(srcs, bounds=BBOX, nodata=-999999.0)
    src_crs = srcs[0].crs
    z = mosaic[0].astype(np.float32)
    H, W = z.shape
    left, bottom, right, top = BBOX
    dtr, dw, dh = calculate_default_transform(src_crs, DST_CRS, W, H, left, bottom, right, top,
                                              resolution=RES)
    dst = np.full((dh, dw), np.nan, np.float32)
    reproject(z, dst, src_transform=tr, src_crs=src_crs, src_nodata=-999999.0,
              dst_transform=dtr, dst_crs=DST_CRS, dst_nodata=np.nan, resampling=Resampling.average)
    # water / hydro-flattened mask: exactly-flat patches
    zf = np.nan_to_num(dst, nan=-9999)
    rng = ndi.maximum_filter(zf, 5) - ndi.minimum_filter(zf, 5)
    flat = rng < 0.02
    lab, nl = ndi.label(flat)
    sizes = ndi.sum(flat, lab, range(1, nl + 1))
    big = np.isin(lab, np.where(sizes * RES * RES > 0.5e6)[0] + 1)
    water = ndi.binary_dilation(big, iterations=3) | ~np.isfinite(dst)
    prof = dict(driver="GTiff", height=dh, width=dw, count=2, dtype="float32", crs=DST_CRS,
                transform=dtr, compress="deflate", nodata=np.nan)
    with rasterio.open(out, "w", **prof) as o:
        o.write(dst, 1); o.write(water.astype(np.float32), 2)
    print("wrote", out, dst.shape, "water frac", water.mean().round(3))


if __name__ == "__main__":
    main(*sys.argv[1:])
